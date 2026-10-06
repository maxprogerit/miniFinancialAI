import json
from dataclasses import dataclass, field

from openai import OpenAI
from openai.types.responses import Response
from pydantic import BaseModel

from app.core.config import settings
from app.tools import TOOLS_BY_NAME, OPENAI_TOOLS

client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)


@dataclass
class AgentResult:
    answer: BaseModel
    response_id: str
    tool_calls: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float | None = None

SYSTEM_INSTRUCTIONS = (
    "You are a financial assistant for a single authenticated user. "
    "Gather whatever data you need by calling the available data tools, "
    "as many times and in as many rounds as needed. "
    "You must always end the conversation by calling exactly one "
    "finish_* tool with your final answer - never answer in plain text. "
    "If a tool result contains an 'error' field (for example an unknown "
    "category), do not silently retry with a guessed value or finish with "
    "an empty/zero result as if that answered the question - call "
    "finish_with_refusal and include the tool's error message, so the user "
    "knows why their question couldn't be answered as asked."
)

# Hard cap on tool-calling rounds per request.
MAX_ITERATIONS = 8


def _add_usage(response: Response, totals: dict) -> None:
    if response.usage is not None:
        totals["input_tokens"] += response.usage.input_tokens
        totals["output_tokens"] += response.usage.output_tokens
        totals["total_tokens"] += response.usage.total_tokens


def _cost_usd(usage_totals: dict) -> float | None:
    input_price = settings.openai_input_price_per_million
    output_price = settings.openai_output_price_per_million
    if input_price is None or output_price is None:
        return None
    return (
        usage_totals["input_tokens"] * input_price
        + usage_totals["output_tokens"] * output_price
    ) / 1_000_000


def ask_ai(user_message: str, previous_response_id: str | None = None) -> AgentResult:
    create_kwargs = {
        "model": settings.openai_model,
        "input": user_message,
        "instructions": SYSTEM_INSTRUCTIONS,
        "tools": OPENAI_TOOLS,
    }
    if previous_response_id:
        create_kwargs["previous_response_id"] = previous_response_id

    response = client.responses.create(**create_kwargs)

    tool_calls: list[str] = []
    usage_totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    _add_usage(response, usage_totals)

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

        # Every call in a round needs an output, finish_* calls included.
        finish_answer = None
        tool_outputs = []

        for call in function_calls:
            tool = TOOLS_BY_NAME[call.name]
            arguments = json.loads(call.arguments)
            tool_calls.append(call.name)

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
        _add_usage(response, usage_totals)

        if finish_answer is not None:
            return AgentResult(
                answer=finish_answer,
                response_id=response.id,
                tool_calls=tool_calls,
                cost_usd=_cost_usd(usage_totals),
                **usage_totals,
            )

    raise RuntimeError(
        f"Agent did not call a finish_* tool within {MAX_ITERATIONS} rounds."
    )
