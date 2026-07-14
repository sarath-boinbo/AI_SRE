def generate_postmortem(client, transcript, model="gemini-3.1-flash-lite"):
    prompt = (
        "Write a blameless postmortem from the incident transcript below. "
        "Include customer impact, timeline, contributing factors, detection gaps, "
        "and follow-up action items.\n\n"
        f"Transcript:\n{transcript}"
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"system_instruction": "Write a blameless postmortem."},
    )
    return response.text
