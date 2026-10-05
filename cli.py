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
            answer, previous_response_id = ask_ai(user_message, previous_response_id)
            print("\nAI: ", answer)
        except Exception as e:
            print("\nERROR:", type(e).__name__, e)
