from src.postmortem_generator import generate_postmortem


class FakeModels:
    def __init__(self):
        self.last_call = None

    def generate_content(self, *, model, contents, config):
        self.last_call = {
            "model": model,
            "contents": contents,
            "config": config,
        }
        return type("Response", (), {"text": "generated postmortem"})()


class FakeClient:
    def __init__(self):
        self.models = FakeModels()


def test_generate_postmortem_uses_gemini_client_and_returns_text():
    client = FakeClient()
    transcript = "Seeing elevated 5xx errors on the checkout API since 14:55 UTC."

    result = generate_postmortem(client, transcript)
    last_call = client.models.last_call

    assert result == "generated postmortem"
    assert last_call is not None
    assert last_call["model"] == "gemini-2.0-flash"
    assert transcript in last_call["contents"]
    assert "customer impact" in last_call["contents"].lower()
    assert "timeline" in last_call["contents"].lower()
    assert "blameless postmortem" in last_call["config"]["system_instruction"].lower()
