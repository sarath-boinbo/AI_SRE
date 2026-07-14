from src import main


def test_main_reads_from_slack_generates_and_posts(monkeypatch, capsys):
    fake_payload = {"messages": [{"ts": "1", "text": "human message"}]}
    posted_messages = []

    monkeypatch.setattr(main, "load_environment_from_dotenv", lambda env_path=None: None)
    monkeypatch.setattr(main, "fetch_slack_thread", lambda channel_id, bot_token: fake_payload)
    monkeypatch.setattr(main, "extract_human_chat_text", lambda payload: "human transcript")
    monkeypatch.setattr(main, "create_gemini_client", lambda: object())
    monkeypatch.setattr(main, "generate_postmortem", lambda client, transcript: f"postmortem: {transcript}")
    monkeypatch.setattr(
        main,
        "post_slack_message",
        lambda channel_id, bot_token, text: posted_messages.append((channel_id, bot_token, text)),
    )
    monkeypatch.setenv("SLACK_CHANNEL_ID", "C123")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")

    main.main()

    captured = capsys.readouterr()
    assert captured.out.strip() == "Successfully posted to Slack!"
    assert posted_messages == [("C123", "xoxb-test-token", "postmortem: human transcript")]


def test_create_gemini_client_uses_api_key_and_developer_api(monkeypatch):
    calls = {}

    class FakeGenAI:
        def Client(self, **kwargs):
            calls.update(kwargs)
            return object()

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setitem(__import__("sys").modules, "google.genai", FakeGenAI())

    client = main.create_gemini_client()

    assert client is not None
    assert calls["api_key"] == "test-key"
    assert calls["vertexai"] is False