def extract_human_chat_text(payload):
    messages = payload.get("messages", [])
    human_messages = [
        message
        for message in sorted(messages, key=lambda message: message.get("ts", ""))
        if "bot_id" not in message
    ]
    return "\n".join(message.get("text", "") for message in human_messages)
