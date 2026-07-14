import argparse
import json
import os
from pathlib import Path

from src.incident_parser import extract_human_chat_text
from src.postmortem_generator import generate_postmortem


def load_slack_thread(path: Path) -> dict:
    return json.loads(path.read_text())


def load_environment_from_dotenv(env_path: Path | None = None) -> None:
    if env_path is None:
        env_path = Path(__file__).resolve().parents[1] / ".env"

    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
            continue

        key, value = stripped_line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def create_gemini_client():
    from google import genai

    return genai.Client()


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    default_path = Path(__file__).resolve().parents[1] / "data" / "mock_slack_thread.json"
    parser.add_argument("slack_thread_path", nargs="?", default=str(default_path))
    parser.add_argument("--print-transcript", action="store_true")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    load_environment_from_dotenv()
    args = parse_args(argv)
    payload = load_slack_thread(Path(args.slack_thread_path))
    transcript = extract_human_chat_text(payload)
    if args.print_transcript:
        print(transcript)
        return
    client = create_gemini_client()
    postmortem = generate_postmortem(client, transcript)
    print(postmortem)


if __name__ == "__main__":
    main()
