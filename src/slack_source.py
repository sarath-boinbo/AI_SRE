from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def fetch_slack_thread(channel_id, bot_token, limit=50):
    slack_client = WebClient(token=bot_token)

    try:
        result = slack_client.conversations_history(channel=channel_id, limit=limit)
    except SlackApiError as exc:
        raise RuntimeError(f"Error communicating with Slack: {exc.response['error']}") from exc

    return {"messages": result.get("messages", [])}