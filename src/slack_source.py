from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def extract_human_chat_text(payload):
    messages = payload.get("messages", [])
    human_messages = [
        message
        for message in sorted(messages, key=lambda message: message.get("ts", ""))
        if "bot_id" not in message
    ]
    return "\n".join(message.get("text", "") for message in human_messages)


def fetch_slack_thread(channel_id, bot_token, limit=50):
    slack_client = WebClient(token=bot_token)

    try:
        result = slack_client.conversations_history(channel=channel_id, limit=limit)
    except SlackApiError as exc:
        raise RuntimeError(
            f"Error communicating with Slack: {exc.response['error']}"
        ) from exc

    return {"messages": result.get("messages", [])}


def post_slack_message(channel_id, bot_token, text):
    slack_client = WebClient(token=bot_token)

    try:
        return slack_client.chat_postMessage(channel=channel_id, text=text)
    except SlackApiError as exc:
        raise RuntimeError(
            f"Error communicating with Slack: {exc.response['error']}"
        ) from exc
