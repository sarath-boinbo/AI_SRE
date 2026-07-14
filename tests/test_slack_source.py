from types import SimpleNamespace

from src import slack_source


def test_fetch_slack_thread_returns_messages(monkeypatch):
    calls = {}

    class FakeWebClient:
        def __init__(self, token):
            calls["token"] = token

        def conversations_history(self, channel, limit):
            calls["channel"] = channel
            calls["limit"] = limit
            return {"messages": [{"ts": "1", "text": "hello"}]}

    monkeypatch.setattr(slack_source, "WebClient", FakeWebClient)

    payload = slack_source.fetch_slack_thread("C123", "xoxb-test-token", 25)

    assert payload == {"messages": [{"ts": "1", "text": "hello"}]}
    assert calls == {"token": "xoxb-test-token", "channel": "C123", "limit": 25}