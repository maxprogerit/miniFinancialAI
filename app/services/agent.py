import json

from openai import OpenAI

from app.core.config import settings
from app.tools import TOOLS_BY_NAME, OPENAI_TOOLS

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_INSTRUCTIONS = (
    "You are a financial assistant for a single authenticated user. "
    "Gather whatever data you need by calling the available data tools, "
    "as many times and in as many rounds as needed. "
    "You must always end the conversation by calling exactly one "
    "finish_* tool with your final answer - never answer in plain text."
)

# Hard cap on tool-calling rounds per request, so a model that never calls a
# finish_* tool can't loop forever and run up API cost.
MAX_ITERATIONS = 8


def ask_ai(user_message: str, previous_response_id: str | None = None):
    create_kwargs = {
        "model": settings.openai_model,
        "input": user_message,
        "instructions": SYSTEM_INSTRUCTIONS,
        "tools": OPENAI_TOOLS,
    }
    if previous_response_id:
        create_kwargs["previous_response_id"] = previous_response_id

    response = client.responses.create(**create_kwargs)

    for _ in range(MAX_ITERATIONS):

        function_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        if not function_calls:
            raise ValueError(
                "The model answered without calling any tool - "
                "no structured output to validate against."
            )

        # Build one function_call_output per call in this round - every call
        # the model made needs a result before we can submit anything back,
        # whether that call is a data tool or the finish_* tool. Mixing a
        # finish_* call into the same round as a data-tool call used to drop
        # the data tool's output entirely and return early.
        finish_answer = None
        tool_outputs = []

        for call in function_calls:
            tool = TOOLS_BY_NAME[call.name]
            arguments = json.loads(call.arguments)

            if tool.response_model is not None:
                finish_answer = tool.response_model.model_validate(arguments)
                result = {"acknowledged": True}
            else:
                try:
                    result = tool.handler(arguments) # type: ignore
                except ValueError as e:
                    result = {"error": str(e)}

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result)
                }
            )

        response = client.responses.create(
            model=settings.openai_model,
            previous_response_id=response.id,
            input=tool_outputs,
            tools=OPENAI_TOOLS # type: ignore
        )

        if finish_answer is not None:
            return finish_answer, response.id

    raise RuntimeError(
        f"Agent did not call a finish_* tool within {MAX_ITERATIONS} rounds."
    )
