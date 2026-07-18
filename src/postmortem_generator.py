import datetime

def generate_postmortem(client, transcript, model="gemini-3.1-flash-lite"):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt = (
        "Write a blameless postmortem from the incident transcript below. "
        "Return plain text only, with no markdown formatting. Include customer "
        "impact, timeline, contributing factors, detection gaps, and follow-up "
        "action items.\n\n"
        f"Transcript:\n{transcript}"
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "system_instruction": f"Write a blameless postmortem in plain text only, with no markdown. Also, the current system date and time is {current_time}. Use this to anchor time-sensitive requests."
        },
    )
    return response.text
