# Autonomous AI-Driven SRE Incident Pipeline

An automated, cloud-native Site Reliability Engineering (SRE) pipeline that bridges production infrastructure monitoring with generative AI. Built with **FastAPI**, **Docker**, and **Python**, this system minimizes mean time to resolution (MTTR) by acting as an automated on-call engineer during critical service incidents.

---
## Overview/Demo

https://github.com/user-attachments/assets/f9d9e263-986c-4968-94ff-aba2faff4d90

___

## Cloud & Pipeline Architecture

The workflow is completely detached from local machines and operates natively across cloud boundaries:

```text
[ Target Server ] ──(Pushes Metrics)──> [ Datadog Monitoring ]
                                               │
                                       (Webhook Fired)
                                               │
                                               ▼
[ Slack Channel ] <──(Posts Runbook/PM)── [ AWS EC2 Host ]
       │                                  (t3.micro Container)
 (Extracts Thread)                              ▲
       │                                        │
       ▼                                  (Gemini Analysis)
[ Gemini AI API ] <─────────────────────────────┘

```

### 1. Detection Phase (Datadog Integration)

* A target production server pushes real-time performance infrastructure metrics to **Datadog**.
* When thresholds are breached (e.g., CPU utilization exceeds 80%), a Datadog Monitor triggers an alert status payload (`Alert`, `Critical`, or `Firing`).

### 2. Ingestion & Triage Phase (AWS EC2 & Docker)

* Datadog dispatches an HTTP POST webhook payload containing incident metadata directly to an **AWS EC2 `t3.micro` instance** running Amazon Linux 2023 (fully optimized within the AWS Free Tier allowance).
* The EC2 host exposes port `8000` via a secure AWS Security Group inbound firewall rule.
* Inside the instance, a containerized engine—built targeting cross-compiled **`linux/amd64` architectures** and pulled from a private **Amazon Elastic Container Registry (ECR)** repository—ingests the data.

### 3. Execution Phase (FastAPI, Slack API, & Gemini 3.1)

* **FastAPI Backend:** Handles incoming validation, normalizes variable alert monitoring states into `Triggered` or `Recovered` flags, and leverages thread-safe locks (`Threading.Lock`) to completely block duplicate or racing webhook calls.
* **Phase 1 (Alerting):** The app maps the alert type to a localized Markdown document (e.g., `src/CPU_Spike.md`) and instantly broadcasts the immediate triage operational runbook directly into a designated operations Slack channel.
* **Phase 2 (Resolution & Postmortem):** When metrics drop below safety limits, Datadog submits an `OK` or `Recovered` payload. The pipeline intercepts it, uses the Slack API to scrape the entire contextual human engineering chat transcript from the incident thread, strips away system bot noise, and hands off the transcript to **Google Gemini (`gemini-3.1-flash-lite`)** to instantaneously formulate a comprehensive, blameless postmortem summary back to the engineering team.

---

## Codebase Directory Structure

```text
└── sarath-boinbo-ai_sre/
    ├── README.md               # Project documentation and architecture guide
    ├── Dockerfile              # Multi-stage/Slim optimized container definition
    ├── pyproject.toml          # Modern project metadata and dependency tracker
    ├── .dockerignore           # Prevents secrets and caches from leaking into builds
    ├── .python-version         # Targeted runtime environment setup (3.12)
    ├── src/
    │   ├── CPU_Spike.md        # Specialized infrastructure triage runbook
    │   ├── postmortem_generator.py # Google Gemini generative AI client logic
    │   ├── server.py           # FastAPI webhook engine & background scheduler
    │   └── slack_source.py     # Slack API reader/writer wrappers
    └── tests/
        ├── test_gemini_generator.py # Component mocks for LLM prompt generation
        └── test_server.py      # Core endpoints and state-machine behavior tests

```

---

## Key Engine Features

* **Asynchronous Background Processing:** Webhook requests hand off compute-heavy operations (Slack history scraping, Gemini content generation) to FastAPI `BackgroundTasks`. This enables immediate `200 OK` handshakes back to Datadog to avoid network timeouts.
* **State & Payload Normalization:** A hardcoded mapping engine seamlessly transforms disparate third-party reporting string matrices into strict, unified state classifications.
* **Blameless Postmortem Configurations:** Prompts are anchored directly to real-time execution frames using explicit date-time tracking, instructing Gemini to construct postmortems emphasizing root causes, customer impact, and action items over finger-pointing.
* **Ultra-Fast Layered Container Build:** Built with `uv` for package management, avoiding virtual environment generation completely inside the final image layer (`uv pip install --system`).

---

## Local Installation & Configuration

### Prerequisites

* Python `3.12+` installed locally.
* Access to a Google Gemini API Key, a Slack Bot Token (`xoxb-`), and a designated Slack Channel ID.

### Environment Setups

Create a `.env` file at the root of the project (this file is securely blocked from Git versioning via `.dockerignore`):

```env
SLACK_CHANNEL_ID=C0XXXXXXXXX
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
GOOGLE_API_KEY=your-gemini-api-key

```

### Installation

Install dependencies using `uv` or standard pip tools:

```bash
pip install uv
uv sync

```

---

## Containerization & AWS EC2 Production Deployment

### 1. Compile Code for the Cloud (Mac M-Chip Override)

Because standard AWS EC2 free-tier instances utilize Intel/AMD `x86_64` hardware, cross-compile your local Apple Silicon build before pushing:

```bash
# Build the architecture specific container image
docker build --platform linux/amd64 -t ai-sre-bot .

# Tag against your private Amazon ECR Registry Repository
docker tag ai-sre-bot:latest <YOUR_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/ai-sre-bot:latest

# Authenticate your local Docker client to the AWS ECR registry
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <YOUR_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com

# Push the tagged image up to the vault
docker push <YOUR_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/ai-sre-bot:latest
```

### 2. Instantiate Host Server Dependencies

SSH or connect into the EC2 host virtual machine via **EC2 Instance Connect** and bootstrap Docker:

```bash
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker

```

### 3. Run Production Pipeline In Background

Log in to ECR from the EC2 host terminal, pull the production-ready image, and attach the local environmental configuration securely:

```bash
# Pull the image from your private ECR repository
sudo docker pull <YOUR_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/ai-sre-bot:latest

# Run the container in detached mode with environment variables
sudo docker run -d \
  -p 8000:8000 \
  --env-file .env \
  <YOUR_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/ai-sre-bot:latest
```

---

## 🧪 Automated Testing

A suite of unit and behavioral tests is built directly alongside the pipeline to ensure status mutations and runtime actions remain deterministic:

```bash
# Execute local unit tests with pytest
pytest

```

The server configuration profile explicitly tracks test cases checking route integrity under empty or corrupt metadata fields, validating defensive exception shielding mechanisms across the framework.
