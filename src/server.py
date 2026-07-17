# src/server.py
import os
from pathlib import Path
from threading import Lock
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks

from src.postmortem_generator import generate_postmortem
from src.slack_source import fetch_slack_thread, post_slack_message, extract_human_chat_text

app = FastAPI()
_LAST_PROCESSED_STATUS_BY_ALERT: dict[str, str] = {}
_STATUS_LOCK = Lock()

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


def normalize_status(status: str) -> str:
    normalized = status.strip().lower()
    if normalized in {"alert", "warning", "warn", "critical", "triggered", "firing"}:
        return "Triggered"
    if normalized in {"ok", "recovered", "resolved", "healthy"}:
        return "Recovered"
    if any(keyword in normalized for keyword in {" >", ">="}):
        return "Triggered"
    if any(keyword in normalized for keyword in {" <=", "<"}):
        return "Recovered"
    return status


def get_runbook_path(alert_title: str) -> Path:
    return Path(__file__).resolve().parent / f"{alert_title}.md"


def should_process_alert(alert_title: str, status: str) -> bool:
    with _STATUS_LOCK:
        previous_status = _LAST_PROCESSED_STATUS_BY_ALERT.get(alert_title)
        if previous_status == status:
            return False

        _LAST_PROCESSED_STATUS_BY_ALERT[alert_title] = status
        return True


def read_runbook(alert_title: str) -> str:
    runbook_path = get_runbook_path(alert_title)
    try:
        return runbook_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"🚨 *ALERT FIRING:* {alert_title}\n\n(Runbook {runbook_path.name} not found locally.)"

def process_incident(alert_title: str, status: str):
    """This runs in the background using your existing Phase 1 & 2 logic."""
    load_environment_from_dotenv()
    channel_id = os.getenv("SLACK_CHANNEL_ID")
    bot_token = os.getenv("SLACK_BOT_TOKEN")

    if not channel_id or not bot_token:
        print("Missing Slack credentials.")
        return

    if not should_process_alert(alert_title, status):
        print(f"Duplicate webhook ignored for {alert_title} at status {status}.")
        return

    # Datadog will now send "Triggered" for alerts
    if status == "Triggered":
        print(f"Alert {alert_title} firing. Attempting to fetch runbook...")
        message = read_runbook(alert_title)

        post_slack_message(channel_id, bot_token, message)
        print(f"Initial runbook posted for {alert_title}")
        
    # Datadog will now send "Recovered" when the CPU drops
    elif status == "Recovered":
        print(f"Alert {alert_title} resolved. Generating postmortem...")
        
        payload = fetch_slack_thread(channel_id, bot_token)
        transcript = extract_human_chat_text(payload)
        
        client = create_gemini_client()
        postmortem = generate_postmortem(client, transcript)
        
        post_slack_message(channel_id, bot_token, postmortem)
        print("Successfully posted postmortem to Slack!")

@app.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    
    alert_title = payload.get("alert_title", "Unknown Alert")
    status = payload.get("status", "firing")
    status = normalize_status(status)
    
    print(f"🚨 INCOMING WEBHOOK: {alert_title} is {status}")
    print(f"Payload: {payload}")
    
    # Hand off the execution to the background task
    background_tasks.add_task(process_incident, alert_title, status)
    
    return {"status": "success", "message": "Webhook received, processing in background."}