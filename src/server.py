# src/server.py
import os
from fastapi import FastAPI, Request, BackgroundTasks

from src.main import load_environment_from_dotenv, create_gemini_client
from src.postmortem_generator import generate_postmortem
from src.slack_source import fetch_slack_thread, post_slack_message, extract_human_chat_text

app = FastAPI()

def process_incident(alert_title: str, status: str):
    """This runs in the background using your existing Phase 1 & 2 logic."""
    load_environment_from_dotenv()
    channel_id = os.getenv("SLACK_CHANNEL_ID")
    bot_token = os.getenv("SLACK_BOT_TOKEN")

    if not channel_id or not bot_token:
        print("Missing Slack credentials.")
        return

    if status == "firing":
        # For now, just post an initial alert message using slack module
        message = f"🚨 *ALERT FIRING:* {alert_title}\n\nInvestigating..."
        post_slack_message(channel_id, bot_token, message)
        print(f"Initial alert posted for {alert_title}")
        
    elif status == "resolved":
        print(f"Alert {alert_title} resolved. Generating postmortem...")
        
        payload = fetch_slack_thread(channel_id, bot_token)
        
        # Reuse pipeline execution order from main.py
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
    
    print(f"🚨 INCOMING WEBHOOK: {alert_title} is {status}")
    
    # Hand off the execution to the background task
    background_tasks.add_task(process_incident, alert_title, status)
    
    return {"status": "success", "message": "Webhook received, processing in background."}