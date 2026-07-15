import os
from pathlib import Path

from dotenv import load_dotenv

from src.postmortem_generator import generate_postmortem
from src.slack_source import fetch_slack_thread, post_slack_message, extract_human_chat_text


def load_environment_from_dotenv(env_path: Path | None = None) -> None:
    if env_path is None:
        env_path = Path(__file__).resolve().parents[1] / ".env"

    if not env_path.exists():
        return

    load_dotenv(env_path, override=True)


def create_gemini_client():
    from google import genai

    api_key = os.getenv("GOOGLE_API_KEY")
    return genai.Client(api_key=api_key, vertexai=False)


def main() -> None:
    load_environment_from_dotenv()
    channel_id = os.getenv("SLACK_CHANNEL_ID")
    bot_token = os.getenv("SLACK_BOT_TOKEN")

    if not channel_id:
        raise RuntimeError("SLACK_CHANNEL_ID is required")
    if not bot_token:
        raise RuntimeError("SLACK_BOT_TOKEN is required")

    payload = fetch_slack_thread(channel_id, bot_token)

    transcript = extract_human_chat_text(payload)
    client = create_gemini_client()
    postmortem = generate_postmortem(client, transcript)
    post_slack_message(channel_id, bot_token, postmortem)
    print("Successfully posted to Slack!")


if __name__ == "__main__":
    main()
