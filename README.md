# ☁️ Cloud Bill Watcher

> Automated AWS cost monitoring — daily email alerts when your cloud spend spikes unexpectedly.

![CI/CD](https://github.com/purvarane2002/cloud-bill-watcher/actions/workflows/deploy.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-FF9900?logo=amazonaws&logoColor=white)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker&logoColor=white)

---

## The problem it solves

Developers using AWS often forget to turn resources off or accidentally trigger unexpected usage. By the time the month-end bill arrives it's too late. Cloud Bill Watcher sends you an email **every single morning** — a spike alert if costs jumped more than 20%, or a quiet confirmation that everything is normal.

---

## How it works

![Architecture diagram](docs/architecture.png)

Every morning at **9am UTC**:

1. **EventBridge** fires automatically — like a daily alarm clock
2. **AWS Lambda** wakes up and runs `handler.py` — a serverless Python function
3. Lambda calls **Cost Explorer** to fetch yesterday's and today's spend
4. **Python logic** calculates the percentage change and decides: spike or normal?
5. **SNS** delivers the email to your inbox within seconds

All 5 AWS services are provisioned automatically by **Terraform** with a single `terraform apply` command. The Python code is packaged as a **Docker container** stored in **ECR** so Lambda always runs the same environment.

---

## The two emails you get

**When costs spike (>20% increase):**
```
Subject: [ALERT] AWS costs up 27.3% today

Yesterday:  $4.21
Today:      $5.36
Change:     +27.3%

Action required: check AWS console for unexpected usage.
```

**Every other day (normal heartbeat):**
```
Subject: [OK] AWS daily cost report — +7.9%

Yesterday:  $3.90
Today:      $4.21
Change:     +7.9%

All good. System running normally.
```

> **Why send an email even when nothing is wrong?**
> This is the heartbeat pattern — you get daily proof that both your AWS costs AND the monitoring system itself are working. If emails stop arriving, something broke.

---

## Tech stack

| Tool | Purpose |
|---|---|
| **Python 3.11** | Lambda function logic (`handler.py`) |
| **AWS Lambda** | Serverless compute — runs the function |
| **AWS EventBridge** | Cron scheduler — triggers Lambda daily at 9am UTC |
| **AWS Cost Explorer** | Provides daily spend data via API |
| **AWS SNS** | Email notification delivery |
| **AWS ECR** | Stores the Docker container image |
| **AWS CloudWatch** | Logs every Lambda run |
| **AWS IAM** | Least-privilege permissions for Lambda |
| **Docker** | Packages the Python code into a container |
| **Terraform** | Provisions all AWS infrastructure as code |
| **GitHub Actions** | CI/CD pipeline — test, build, deploy on every push |

---

## Project structure

```
cloud-bill-watcher/
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI/CD: test → build Docker → push ECR → deploy Lambda
├── src/
│   └── handler.py            # The entire Lambda brain — 60 lines of Python
├── terraform/
│   ├── main.tf               # All 10 AWS resources as code
│   ├── variables.tf          # Input: alert email address
│   └── outputs.tf            # Outputs: Lambda name, ECR URL, SNS ARN
├── tests/
│   └── test_handler.py       # 3 pytest unit tests for spike detection logic
├── docs/
│   └── architecture.png      # Architecture diagram
├── Dockerfile                # linux/amd64 container for Lambda
├── requirements.txt          # boto3, pytest
└── .gitignore                # excludes .terraform/, tfstate, __pycache__
```

---

## CI/CD pipeline

Every push to `main` triggers a two-job GitHub Actions pipeline:

```
Push to main
     │
     ▼
┌─────────────────────────┐
│  Job 1: test            │
│  - install dependencies │
│  - run pytest (3 tests) │
│  - if fail: STOP        │
└────────────┬────────────┘
             │ only if tests pass
             ▼
┌─────────────────────────────────────────┐
│  Job 2: deploy                          │
│  - connect to AWS via GitHub Secrets    │
│  - docker buildx build (linux/amd64)   │
│  - push image to ECR                    │
│  - terraform apply                      │
│  - aws lambda update-function-code      │
└─────────────────────────────────────────┘
```

Broken code can never reach production — the pipeline stops at the test job if any test fails.

---

## Running tests locally

```bash
pip install pytest boto3
pytest tests/ -v
```

Expected output:

```
tests/test_handler.py::test_spike_above_20_percent     PASSED
tests/test_handler.py::test_no_spike_under_20_percent  PASSED
tests/test_handler.py::test_zero_yesterday_no_crash    PASSED
```

---

## Setup and deployment

### Prerequisites

- AWS account with Cost Explorer enabled (not on by default — enable in AWS Console as root user)
- AWS CLI configured: `aws configure`
- Terraform installed: `brew install terraform`
- Docker Desktop running

### Step 1 — Clone

```bash
git clone https://github.com/purvarane2002/cloud-bill-watcher
cd cloud-bill-watcher
```

### Step 2 — Deploy infrastructure

```bash
cd terraform
terraform init
terraform apply -var="alert_email=your@email.com"
```

Confirm the SNS subscription email AWS sends to your inbox before continuing.

### Step 3 — Build and push Docker image

```bash
ECR_URL=$(terraform output -raw ecr_repository_url)

aws ecr get-login-password --region eu-west-2 | \
  docker login --username AWS --password-stdin $ECR_URL

docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  -t $ECR_URL:latest \
  --push .
```

> The `--platform linux/amd64` flag is required when building on an Apple M1/M2 Mac. Lambda runs on AMD64 — without this flag it rejects the image.

### Step 4 — Deploy Lambda

```bash
aws lambda update-function-code \
  --function-name cloud-bill-watcher \
  --image-uri $ECR_URL:latest \
  --region eu-west-2
```

### Step 5 — Enable CI/CD (optional)

Add these secrets to GitHub Settings → Secrets → Actions:

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | Your IAM access key |
| `AWS_SECRET_ACCESS_KEY` | Your IAM secret key |
| `ALERT_EMAIL` | Email address for alerts |

After this, every push to `main` tests and deploys automatically.

---

## Real errors faced while building this

| Error | Cause | Fix |
|---|---|---|
| Lambda rejects Docker image | M2 Mac builds ARM64; Lambda needs AMD64 | `--platform linux/amd64 --provenance=false` |
| `AccessDeniedException` on Cost Explorer | Not enabled on AWS account | Enable as root user in AWS Console (takes up to 24h) |
| GitHub push rejected — 648MB file | `.terraform/` folder committed accidentally | Added to `.gitignore`, removed history with `git filter-branch` |
| Terraform state conflict in CI/CD | Local and pipeline both try to create same resources | `|| true` workaround — proper fix is S3 remote backend |
| SNS emails not arriving | Subscription not confirmed | Click confirmation link in the email AWS sends you |
| `Inconsistent lock file` | `main.tf` recreated, lock file out of sync | `terraform init -upgrade` |

---

## AWS running costs

| Service | Usage | Monthly cost |
|---|---|---|
| Lambda | 30 invocations × ~3 seconds | ~$0.00 (free tier) |
| EventBridge | 30 scheduled events | ~$0.00 (free tier) |
| SNS | 30 email deliveries | ~$0.00 (free tier) |
| ECR | 1 Docker image ~50MB | ~$0.005 |
| Cost Explorer API | 30 API calls × $0.01 | ~$0.30 |

**Total: under $0.50/month.**

---

## Key design decisions

**Why Lambda instead of an EC2 server?**
The function runs for ~3 seconds once a day. A server running 24/7 for 3 seconds of daily work wastes 99.99% of its uptime and costs ~30x more.

**Why Docker over a zip package?**
The exact same container tested locally runs in AWS — no environment differences, no missing libraries.

**Why Terraform over clicking in the AWS Console?**
All 10 AWS resources are version-controlled and reproducible. Rebuilding the entire environment from scratch takes 2 minutes with `terraform apply`.

**Why send an email even on normal days?**
The heartbeat pattern. If you only alert on spikes, a silent day could mean "costs are fine" or "monitoring broke." Daily reports confirm both.

---

## Planned improvements

- [ ] Terraform S3 remote backend for proper CI/CD state management
- [ ] Per-service cost breakdown — identify which AWS service caused a spike
- [ ] 30-day Grafana dashboard for visual cost trend tracking

---

## Author

**Purva Rane** — MSc Software Engineering with Cloud Computing (Distinction), City University London

[![GitHub](https://img.shields.io/badge/GitHub-purvarane2002-black?logo=github)](https://github.com/purvarane2002)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-purvarane-blue?logo=linkedin)](https://linkedin.com/in/purvarane)
