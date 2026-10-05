from app.services.agent import ask_ai

if __name__ == "__main__":

    previous_response_id = None
    while True:
        user_message = input("\nYou: ").strip()

        if not user_message:
            continue

        if user_message.lower() in {"exit", "quit"}:
            break

        try:
            result = ask_ai(user_message, previous_response_id)
            previous_response_id = result.response_id
            print("\nAI: ", result.answer)
            print("Tools used:", result.tool_calls)
            print("Tokens:", result.total_tokens)
        except Exception as e:
            print("\nERROR:", type(e).__name__, e)
