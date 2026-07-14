from pathlib import Path

from src import main


def test_main_reads_fixture_parses_transcript_generates_and_prints(monkeypatch, capsys):
    fake_payload = {"messages": [{"ts": "1", "text": "human message"}]}
    loaded_paths = []

    def fake_load_slack_thread(path):
        loaded_paths.append(path)
        return fake_payload

    monkeypatch.setattr(main, "load_slack_thread", fake_load_slack_thread)
    monkeypatch.setattr(main, "extract_human_chat_text", lambda payload: "human transcript")
    monkeypatch.setattr(main, "generate_postmortem", lambda client, transcript: f"postmortem: {transcript}")
    monkeypatch.setattr(main, "create_gemini_client", lambda: object())

    main.main(["custom_thread.json"])

    captured = capsys.readouterr()
    assert captured.out.strip() == "postmortem: human transcript"
    assert loaded_paths[0].name == "custom_thread.json"


def test_main_prints_transcript_without_calling_gemini(monkeypatch, capsys):
    fake_payload = {"messages": [{"ts": "1", "text": "human transcript"}]}

    monkeypatch.setattr(main, "load_slack_thread", lambda path: fake_payload)
    monkeypatch.setattr(main, "extract_human_chat_text", lambda payload: "human transcript")

    def fail_if_called():
        raise AssertionError("Gemini should not be called in transcript preview mode")

    monkeypatch.setattr(main, "create_gemini_client", fail_if_called)
    monkeypatch.setattr(main, "generate_postmortem", lambda client, transcript: "should not be used")

    main.main(["--print-transcript"])

    captured = capsys.readouterr()
    assert captured.out.strip() == "human transcript"


def test_load_environment_from_dotenv_sets_missing_values(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GOOGLE_API_KEY=test-key\n"
        "IGNORED_VALUE=hello world\n"
        "# comment\n"
        "EMPTY_LINE=\n"
    )
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("IGNORED_VALUE", raising=False)

    main.load_environment_from_dotenv(env_file)

    assert Path(env_file).exists()
    assert __import__("os").environ["GOOGLE_API_KEY"] == "test-key"
    assert __import__("os").environ["IGNORED_VALUE"] == "hello world"


def test_load_environment_from_dotenv_overrides_existing_values(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GOOGLE_API_KEY=from-dotenv\n")

    monkeypatch.setenv("GOOGLE_API_KEY", "stale-shell-value")

    main.load_environment_from_dotenv(env_file)

    assert __import__("os").environ["GOOGLE_API_KEY"] == "from-dotenv"


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


def test_main_can_read_from_slack_source(monkeypatch, capsys):
    fake_payload = {"messages": [{"ts": "1", "text": "slack transcript"}]}

    monkeypatch.setattr(main, "fetch_slack_thread", lambda channel_id, bot_token, limit: fake_payload)
    monkeypatch.setattr(main, "extract_human_chat_text", lambda payload: "slack transcript")
    monkeypatch.setattr(main, "create_gemini_client", lambda: object())
    monkeypatch.setattr(main, "generate_postmortem", lambda client, transcript: f"postmortem: {transcript}")
    monkeypatch.setenv("SLACK_CHANNEL_ID", "C123")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")

    main.main(["--source", "slack"])

    captured = capsys.readouterr()
    assert captured.out.strip() == "postmortem: slack transcript"