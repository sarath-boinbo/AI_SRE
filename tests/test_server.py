# tests/test_server.py
from fastapi.testclient import TestClient

from src.server import app
import src.server

# Initialize the test client with your FastAPI app
client = TestClient(app)

def test_webhook_returns_success_and_triggers_background_task(monkeypatch):
    # 1. Setup a spy to intercept the background task
    task_calls = []
    
    def mock_process_incident(alert_title, status):
        # Instead of doing real work, just record what arguments were passed
        task_calls.append((alert_title, status))

    # Patch the process_incident function in the server module
    monkeypatch.setattr(src.server, "process_incident", mock_process_incident)

    # 2. Execute the POST request using the test client
    payload = {"alert_title": "Database CPU Spike", "status": "resolved"}
    response = client.post("/webhook", json=payload)

    # 3. Assert the server responds instantly with a 200 OK
    assert response.status_code == 200
    assert response.json() == {
        "status": "success", 
        "message": "Webhook received, processing in background."
    }

    # 4. Assert the background task was correctly queued and executed with the right payload
    assert len(task_calls) == 1
    assert task_calls[0] == ("Database CPU Spike", "Recovered")

def test_webhook_handles_missing_fields_with_defaults(monkeypatch):
    # Setup the spy
    task_calls = []
    monkeypatch.setattr(src.server, "process_incident", lambda a, s: task_calls.append((a, s)))

    # Execute a POST request with an empty JSON payload
    response = client.post("/webhook", json={})

    # Assert the server still responds with a 200 OK
    assert response.status_code == 200
    
    # Assert the server correctly applied the default fallback values
    assert len(task_calls) == 1
    assert task_calls[0] == ("Unknown Alert", "Triggered")


def test_normalize_status_maps_datadog_states():
    assert src.server.normalize_status("ALERT") == "Triggered"
    assert src.server.normalize_status("OK") == "Recovered"
    assert src.server.normalize_status("No Data") == "No Data"


def test_normalize_status_maps_datadog_message_payload():
    # Test that a spike above the threshold triggers the alert
    assert src.server.normalize_status(
        "system.cpu.user over *** was > 80.0 on average during the last 1m**."
    ) == "Triggered"

    # Test that dropping below the threshold resolves the alert
    assert src.server.normalize_status(
        "system.cpu.user over *** was <= 80.0 on average during the last 1m**."
    ) == "Recovered"


def test_read_runbook_uses_server_directory(tmp_path, monkeypatch):
    # Place the runbook directly in tmp_path so it is a sibling to the mock server.py
    runbook = tmp_path / "CPU_Spike.md"
    runbook.write_text("runbook contents", encoding="utf-8")
    
    # Mock the server.py location
    monkeypatch.setattr(src.server, "__file__", str(tmp_path / "server.py"))

    # Now the paths will align perfectly
    assert src.server.read_runbook("CPU_Spike") == "runbook contents"


def test_should_process_alert_ignores_duplicate_status(monkeypatch):
    monkeypatch.setattr(src.server, "_LAST_PROCESSED_STATUS_BY_ALERT", {})

    assert src.server.should_process_alert("CPU_Spike", "Triggered") is True
    assert src.server.should_process_alert("CPU_Spike", "Triggered") is False
    assert src.server.should_process_alert("CPU_Spike", "Recovered") is True