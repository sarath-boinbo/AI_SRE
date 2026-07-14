import json
from pathlib import Path

from src.incident_parser import extract_human_chat_text


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data" / "mock_slack_thread.json"


def test_extract_human_chat_text_filters_bots_and_preserves_order():
    payload = json.loads(FIXTURE_PATH.read_text())

    result = extract_human_chat_text(payload)

    assert result == (
        "Seeing elevated 5xx errors on the checkout API since 14:55 UTC.\n"
        "Confirming. Grafana shows error rate jumped from 0.4% to 18% in the last 5 minutes.\n"
        "I’m checking recent deploys now. Last release went out at 14:47 UTC.\n"
        "Found it. The payments-service config change added a timeout that’s too low for the new retry path.\n"
        "Rolling back the config now and watching the error rate.\n"
        "Rollback completed. Error rate is down to 0.7% and latency is recovering.\n"
        "We should capture the customer impact window, detection gap, and why the timeout change escaped review."
    )
