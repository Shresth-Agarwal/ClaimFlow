# ClaimFlow Agent Builder
### AI-Powered Insurance Claims Automation on AWS
**Cognizant Technoverse 2026 — Team Akira | Top 24 / 22,000+ teams**

> A farmer in Maharashtra sends a WhatsApp voice note in Marathi. In under 90 seconds, his crop insurance claim is assessed, fraud-checked, policy-audited, and resolved — without speaking to a single person.

---

## What is ClaimFlow?

ClaimFlow is a multi-agent AI platform that automates end-to-end insurance claims processing. Insurance managers drag pre-built AI agent nodes onto a visual canvas, configure thresholds, and deploy a fully functional claims pipeline on AWS in under 10 minutes — zero ML expertise required.

**Claim types supported:** Motor · Health · Crop / Agriculture · Property

**Countries supported:** India (IRDAI) · United Kingdom (FCA) · UAE (CBUAE) · USA

---

## The Problem

India processed **71.2 million** insurance claims in FY2024.
- **16.3%** took 3–6 months to settle
- **₹30,401 crore** lost to fraud annually
- **600 million** Indians cannot access the claims process in their own language
- Manual triage, serial workflows, and English-only interfaces lock out the people who need coverage most

---

## How It Works

```
Claimant (WhatsApp voice / photo / form)
        ↓
Inclusion Agent     — voice-to-text in 11 languages via Bhashini + AWS Transcribe
        ↓
Vision Agent        — Claude 3.5 Sonnet (Bedrock Strands) assesses damage from photos
        ↓
Forensic Agent      — fraud score 0–100 via Neptune cross-claim graph
        ↓
Policy Auditor      — RAG over policy PDFs via Bedrock Knowledge Base
        ↓
Guardrail Gate      — PII masking, topic filters, grounding check via Bedrock Guardrails
        ↓
Confidence Router   — LangGraph conditional edge decides outcome
        ↓
Auto Approve · Human Review · Reject
        ↓
WhatsApp / SMS / Email notification via AWS SNS
```

### The Investigator Loop — Our Signature Feature

When the fraud score lands in the ambiguous range (50–75/100), instead of routing to a human, the **Forensic Agent autonomously challenges the Vision Agent** to re-examine the photos — looking specifically for pre-existing damage, paint fade, and wear inconsistencies. They loop up to 3 times. Two AI agents negotiating with each other, mid-investigation, without a human in the loop.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph — state machine, conditional edges, human-in-loop interrupt |
| Sub-agent management | Amazon Bedrock Strands |
| Foundation model | Claude 4.6 Sonnet on Amazon Bedrock |
| Session memory | Bedrock Agent Core |
| Policy document RAG | Bedrock Knowledge Base + LlamaIndex |
| Safety & compliance | Bedrock Guardrails — PII masking, topic filters, grounding |
| Database | DynamoDB — claim state + LangGraph checkpoints |
| Multilingual | AWS Transcribe |
| Vision / detection | YOLOv10 + SAM (Segment Anything Model) |
| Backend API | FastAPI — 17 REST endpoints |
| Frontend | React + React Flow — no-code canvas |
| PDF generation | ReportLab |
---

## Project Structure

```
ClaimFlow/
├── backend/
│   ├── agents/
│   │   ├── vision_agent.py        # Bedrock Strands — YOLOv10 + SAM
│   │   ├── forensic_agent.py      # Neptune fraud graph
│   │   ├── inclusion_agent.py     # Bhashini + AWS Transcribe
│   │   └── policy_auditor.py      # Bedrock KB RAG
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py            # Cognito login + agent ID verification
│   │       ├── claims.py          # 11 claim routes
│   │       ├── agents.py          # Adjuster queue + decision
│   │       └── users.py           # User profile
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── security.py            # JWT middleware
│   ├── database/
│   │   ├── interfaces.py          # DynamoDB operations
│   │   └── mock_db.py             # Local dev fallback
│   ├── graph/
│   │   ├── state.py               # ClaimState + create_initial_state()
│   │   ├── nodes.py               # All 9 node functions
│   │   ├── pipeline.py            # Graph builder + runner
│   │   └── __init__.py
│   ├── guardrails/
│   │   └── config.py              # Bedrock Guardrails configuration
│   ├── services/
│   │   ├── auth_service.py
│   │   └── identity_service.py    # Claude vision agent ID verification
│   └── main.py                    # FastAPI app entry point
└── frontend/
    └── ...                        # React + React Flow canvas
```

---

## API Routes

| Method | Route | Description |
|---|---|---|
| POST | `/api/auth/register` | Claimant self-registration |
| POST | `/api/auth/login` | Login — returns JWT |
| POST | `/api/auth/agent/verify-id` | Claude verifies agent ID badge photo |
| POST | `/api/auth/refresh` | Refresh access token |
| POST | `/api/claim/submit` | Submit claim — triggers LangGraph pipeline |
| POST | `/api/claim/submit-with-photo` | Multipart — form + photo upload |
| GET | `/api/claim/{id}/status` | Poll claim status |
| GET | `/api/claim/{id}/report` | Full report + audit trail |
| GET | `/api/claim/{id}/vision` | Vision Agent result |
| GET | `/api/claim/{id}/fraud` | Forensic Agent result (agents only) |
| GET | `/api/claim/{id}/policy` | Policy Auditor result |
| GET | `/api/adjuster/queue` | Claims pending human review |
| POST | `/api/adjuster/{id}/decision` | Adjuster approve / reject |
| POST | `/api/voice/transcribe` | Audio → structured claim fields |
| GET | `/api/policies` | Browse available policies |
| GET | `/api/advisors` | Advisor directory |
| POST | `/api/chat/message` | Chatbot conversation turn |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- AWS account with Bedrock, DynamoDB, Cognito, Neptune access
- AWS CLI configured

### Environment Variables

Create a `.env` file in `/backend`:

```env
AWS_REGION=ap-south-1

# Cognito
COGNITO_USER_POOL_ID=ap-south-1_XXXXXXXX
COGNITO_CLIENT_ID=your_client_id
COGNITO_AGENT_POOL_ID=ap-south-1_YYYYYYYY
COGNITO_AGENT_CLIENT_ID=your_agent_client_id

# Bedrock Strands — fill in after Bedrock Console setup
VISION_AGENT_ID=PLACEHOLDER
VISION_AGENT_ALIAS=PLACEHOLDER
FORENSIC_AGENT_ID=PLACEHOLDER
FORENSIC_AGENT_ALIAS=PLACEHOLDER

# Bedrock Agent Core
AGENT_CORE_AGENT_ID=PLACEHOLDER
AGENT_CORE_AGENT_ALIAS=PLACEHOLDER

# Bedrock Guardrails
GUARDRAIL_ID=PLACEHOLDER
GUARDRAIL_VERSION=DRAFT

# DynamoDB
DYNAMODB_TABLE=claimflow-claims
DYNAMODB_CHECKPOINT_TABLE=claimflow-checkpoints
```

### DynamoDB Tables

Create two tables in AWS Console:

| Table | Partition Key | Sort Key |
|---|---|---|
| `claimflow-claims` | `claim_id` (String) | — |
| `claimflow-checkpoints` | `thread_id` (String) | `checkpoint_id` (String) |

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

API docs available at `http://localhost:8000/docs`

---

## Key Numbers

| Metric | Value |
|---|---|
| Claim resolution speed | 75% faster |
| AI damage assessment | Under 60 seconds |
| Languages supported | 11 |
| Annual fraud losses addressable | ₹30,000 Cr |
| Insurer onboarding time | Under 10 minutes |
| Break-even point | 8,000 claims/year |
| Cost saved per claim | ₹2,400 – ₹4,000 |

---

## Team Akira

| Name | Role |
|---|---|
| Shresth Agarwal | Team Leader · LangGraph Architect · FastAPI · AWS DynamoDB |
| Srivalli Mallapragada | Vision Agent (Bedrock Strands) · Forensic Agent |
| Praharshitha Koduri | Policy Auditor · Guardrails · Inclusion Agent · Chatbot |
| Tanish Suri | React Frontend · React Flow Canvas · UI/UX |

**College:** Teegala Krishna Reddy Engineering College, Hyderabad
**Hackathon:** Cognizant Technoverse 2026 — Final Round, Pune

---

## License

This project was built for Cognizant Technoverse 2026. All rights reserved by Team Akira.
