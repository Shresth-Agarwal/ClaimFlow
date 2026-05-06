"""
ClaimFlow Guided Insurance Chat Agent
======================================
Stateful multi-turn agent that guides users through the full insurance
claim lifecycle. Supports text, image/document analysis, voice transcripts,
and generates a structured summary report at session end.

Conversation flow (wizard):
  GREETING -> CLAIM_TYPE -> INCIDENT_DETAILS -> DOCUMENT_COLLECTION
  -> POLICY_VERIFICATION -> REVIEW -> SUMMARY_GENERATED

Each turn the agent:
  1. Reads the full conversation history for context
  2. Determines the current wizard step from session context
  3. Validates / extracts structured fields from the user input
  4. Asks the next targeted question or confirms completion
  5. Returns suggested actions appropriate to the step
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("claimflow.chat_agent")

# ── Knowledge base ────────────────────────────────────────────────────────────
try:
    from backend.agents.policy_auditor import _load_kb, _load_kb_config
    _KB_CLAUSES: List[Dict] = _load_kb()
    _KB_CFG: Dict = _load_kb_config()
except Exception:
    logger.warning("Policy auditor KB not available – running with empty KB")
    _KB_CLAUSES = []
    _KB_CFG = {}

# ── Wizard step constants ─────────────────────────────────────────────────────
STEP_GREETING          = "greeting"
STEP_CLAIM_TYPE        = "claim_type"
STEP_INCIDENT_DETAILS  = "incident_details"
STEP_POLICY_NUMBER     = "policy_number"
STEP_DOCUMENT_COLLECT  = "document_collection"
STEP_CONTACT_INFO      = "contact_info"
STEP_REVIEW            = "review"
STEP_SUMMARY_GENERATED = "summary_generated"

# Steps in order
WIZARD_STEPS = [
    STEP_GREETING,
    STEP_CLAIM_TYPE,
    STEP_INCIDENT_DETAILS,
    STEP_POLICY_NUMBER,
    STEP_DOCUMENT_COLLECT,
    STEP_CONTACT_INFO,
    STEP_REVIEW,
    STEP_SUMMARY_GENERATED,
]

# ── Document requirements per claim type ─────────────────────────────────────
REQUIRED_DOCS: Dict[str, List[str]] = {
    "health": [
        "Hospital bill / invoice",
        "Discharge summary",
        "Doctor prescription",
        "Lab / diagnostic reports",
        "ID proof (Aadhaar / PAN)",
    ],
    "motor": [
        "Repair invoice from authorised workshop",
        "Photos of vehicle damage",
        "Registration Certificate (RC)",
        "Driving licence",
        "Police FIR (if theft or major accident)",
    ],
    "property": [
        "Police FIR copy",
        "Photos of damaged property",
        "Ownership / title documents",
        "Repair estimate from contractor",
    ],
    "crop": [
        "Field / crop damage photos",
        "Land ownership / Khasra documents",
        "Weather report or disaster certificate",
        "Bank passbook copy",
    ],
}

# ── Suggested actions per step ────────────────────────────────────────────────
STEP_ACTIONS: Dict[str, List[str]] = {
    STEP_GREETING:         ["File a new claim", "Check claim status", "Ask about coverage"],
    STEP_CLAIM_TYPE:       ["Health claim", "Motor claim", "Property claim", "Crop claim"],
    STEP_INCIDENT_DETAILS: ["Continue", "Add more details", "Upload a photo"],
    STEP_POLICY_NUMBER:    ["I don't have my policy number", "Continue"],
    STEP_DOCUMENT_COLLECT: ["I've uploaded all documents", "What documents do I need?", "Upload photo"],
    STEP_CONTACT_INFO:     ["Use my registered email", "Continue"],
    STEP_REVIEW:           ["Submit claim", "Edit details", "Generate summary report"],
    STEP_SUMMARY_GENERATED:["Download report", "Submit claim now", "Ask a question"],
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _extract_claim_id(text: str) -> Optional[str]:
    m = re.search(r"\b(CLM-\d{8}-[A-Z0-9]{6}|TEST-\d{6})\b", text, re.IGNORECASE)
    return m.group(1).upper() if m else None


def _extract_claim_type(text: str) -> Optional[str]:
    t = text.lower()
    if any(w in t for w in ["health", "hospital", "medical", "medicine", "doctor", "treatment"]):
        return "health"
    if any(w in t for w in ["motor", "car", "vehicle", "bike", "accident", "auto"]):
        return "motor"
    if any(w in t for w in ["property", "house", "home", "building", "fire", "flood"]):
        return "property"
    if any(w in t for w in ["crop", "farm", "agriculture", "harvest", "field"]):
        return "crop"
    return None


def _extract_policy_number(text: str) -> Optional[str]:
    m = re.search(r"(?:policy\s*(?:no|number|#)?\s*:?\s*)([A-Z0-9\-/]{5,20})", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r"\b([A-Z]{2,4}[-/]?\d{4,12})\b", text)
    return m.group(1).upper() if m else None


def _extract_date(text: str) -> Optional[str]:
    m = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
    return m.group(1) if m else None


def _extract_amount(text: str) -> Optional[float]:
    m = re.search(r"(?:rs\.?|inr|rupees?|₹)\s*([\d,]+(?:\.\d{1,2})?)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"([\d,]+(?:\.\d{1,2})?)\s*(?:rs\.?|inr|rupees?|₹)", text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def _search_kb(query: str) -> List[str]:
    q = query.lower()
    hits = []
    for entry in _KB_CLAUSES:
        text = entry.get("text", "").lower()
        if any(w in text for w in q.split() if len(w) > 3):
            hits.append(f"Clause {entry.get('clause', '?')}: {entry.get('text', '')}")
    return hits[:3]


def _build_history_summary(history: List[Dict]) -> str:
    """Compact representation of conversation history for context injection."""
    if not history:
        return "No prior conversation."
    lines = []
    for h in history[-10:]:          # last 10 exchanges
        lines.append(f"User: {h.get('user_message', '')[:120]}")
        lines.append(f"Agent: {h.get('bot_response', '')[:120]}")
    return "\n".join(lines)


def _get_step(ctx: Dict) -> str:
    return ctx.get("wizard_step", STEP_GREETING)


def _advance_step(ctx: Dict, to: str) -> Dict:
    ctx = dict(ctx)
    ctx["wizard_step"] = to
    return ctx

# ─────────────────────────────────────────────────────────────────────────────
# WIZARD STEP HANDLERS
# ─────────────────────────────────────────────────────────────────────────────

def _handle_greeting(msg: str, ctx: Dict) -> tuple:
    """First turn: welcome + detect intent."""
    claim_id = _extract_claim_id(msg)
    if claim_id:
        return None, ctx, "claim_status"   # hand off to status handler

    claim_type = _extract_claim_type(msg)
    t = msg.lower()

    if any(w in t for w in ["status", "check", "track"]):
        response = (
            "Sure! Please share your **Claim ID** (format: CLM-YYYYMMDD-XXXXXX) "
            "and I'll pull up the latest status for you."
        )
        return response, ctx, "claim_status_prompt"

    if any(w in t for w in ["coverage", "covered", "policy", "eligible"]):
        return None, ctx, "policy_query"

    if claim_type:
        ctx = _advance_step(ctx, STEP_INCIDENT_DETAILS)
        ctx["claim_type"] = claim_type
        docs = "\n".join(f"  • {d}" for d in REQUIRED_DOCS[claim_type])
        response = (
            f"I'll guide you through filing a **{claim_type.title()} Insurance Claim** step by step.\n\n"
            f"**Documents you'll need:**\n{docs}\n\n"
            f"Let's start — please describe **what happened** and **when** the incident occurred."
        )
        return response, ctx, "wizard"

    # Generic greeting
    ctx = _advance_step(ctx, STEP_CLAIM_TYPE)
    response = (
        "Hello! I'm your **ClaimFlow Insurance Assistant**. I can help you:\n\n"
        "🏥 **File a Health claim** — hospital bills, treatment costs\n"
        "🚗 **File a Motor claim** — vehicle damage, accidents\n"
        "🏠 **File a Property claim** — home damage, fire, flood\n"
        "🌾 **File a Crop claim** — agricultural loss\n"
        "🔍 **Check claim status** — track an existing claim\n"
        "📋 **Policy questions** — understand your coverage\n\n"
        "What would you like to do today?"
    )
    return response, ctx, "greeting"


def _handle_claim_type(msg: str, ctx: Dict) -> tuple:
    """Identify claim type from user reply."""
    claim_type = _extract_claim_type(msg)
    if not claim_type:
        response = (
            "I didn't catch the claim type. Please choose one:\n\n"
            "• **Health** — medical / hospital\n"
            "• **Motor** — vehicle damage\n"
            "• **Property** — home / building\n"
            "• **Crop** — agricultural loss"
        )
        return response, ctx, "wizard"

    ctx["claim_type"] = claim_type
    ctx = _advance_step(ctx, STEP_INCIDENT_DETAILS)
    docs = "\n".join(f"  • {d}" for d in REQUIRED_DOCS[claim_type])
    response = (
        f"Got it — **{claim_type.title()} claim**.\n\n"
        f"**Documents you'll need:**\n{docs}\n\n"
        f"Now, please describe **what happened** and **when** the incident occurred. "
        f"Include as much detail as possible — date, location, and nature of the loss."
    )
    return response, ctx, "wizard"


def _handle_incident_details(msg: str, ctx: Dict) -> tuple:
    """Collect incident description, date, and amount."""
    ctx = dict(ctx)
    date = _extract_date(msg)
    amount = _extract_amount(msg)

    if date:
        ctx["incident_date"] = date
    if amount:
        ctx["claimed_amount"] = amount
    if len(msg.strip()) > 20:
        ctx["incident_description"] = msg.strip()

    ctx = _advance_step(ctx, STEP_POLICY_NUMBER)
    response = (
        "Thank you for the details. I've noted:\n"
        + (f"  📅 **Incident date**: {date}\n" if date else "  📅 Incident date: *not detected — please mention it*\n")
        + (f"  💰 **Claimed amount**: ₹{amount:,.0f}\n" if amount else "")
        + "\nNext — what is your **Policy Number**? "
        "(You can find it on your policy document or insurance card.)"
    )
    return response, ctx, "wizard"


def _handle_policy_number(msg: str, ctx: Dict) -> tuple:
    """Capture policy number."""
    ctx = dict(ctx)
    t = msg.lower()

    if any(w in t for w in ["don't have", "dont have", "not sure", "no policy", "unknown"]):
        ctx["policy_number"] = "NOT_PROVIDED"
        ctx = _advance_step(ctx, STEP_DOCUMENT_COLLECT)
        response = (
            "No problem — we can look it up later. Let's move on.\n\n"
            + _document_prompt(ctx.get("claim_type", "health"))
        )
        return response, ctx, "wizard"

    policy = _extract_policy_number(msg)
    if policy:
        ctx["policy_number"] = policy
        ctx = _advance_step(ctx, STEP_DOCUMENT_COLLECT)
        response = (
            f"✅ Policy number **{policy}** noted.\n\n"
            + _document_prompt(ctx.get("claim_type", "health"))
        )
        return response, ctx, "wizard"

    response = (
        "I couldn't detect a policy number in your message. "
        "Please share it in a format like **POL-123456** or **SRK-294022**, "
        "or type \"I don't have it\" to skip."
    )
    return response, ctx, "wizard"


def _document_prompt(claim_type: str) -> str:
    docs = "\n".join(f"  • {d}" for d in REQUIRED_DOCS.get(claim_type, []))
    return (
        f"**Document Collection**\n\n"
        f"Please upload the following documents using the 📎 attach button:\n{docs}\n\n"
        f"You can upload them one at a time. Type **'done'** when you've uploaded everything, "
        f"or ask me what a specific document should look like."
    )


def _handle_document_collection(msg: str, ctx: Dict, attachments: List[Dict]) -> tuple:
    """Track document uploads and guide user."""
    ctx = dict(ctx)
    t = msg.lower()

    # Record any attachments
    docs_received = ctx.get("documents_received", [])
    for att in attachments:
        docs_received.append({
            "name": att.get("name", "unknown"),
            "type": att.get("type", "unknown"),
            "analysis": att.get("analysis", {}),
        })
    ctx["documents_received"] = docs_received

    # Check if user says done or has uploaded enough
    if any(w in t for w in ["done", "uploaded", "all documents", "that's all", "thats all", "finished"]):
        ctx = _advance_step(ctx, STEP_CONTACT_INFO)
        response = (
            f"✅ I've received **{len(docs_received)} document(s)**.\n\n"
            "Almost there! Please confirm your **contact details**:\n"
            "• Email address for claim updates\n"
            "• Phone number\n\n"
            "Or type **'use registered'** to use the details from your account."
        )
        return response, ctx, "wizard"

    # Acknowledge upload
    if attachments:
        names = ", ".join(a.get("name", "file") for a in attachments)
        analysis_notes = []
        for att in attachments:
            a = att.get("analysis", {})
            if a.get("document_type"):
                analysis_notes.append(f"  • **{att['name']}** → detected as *{a['document_type']}*")
            if a.get("amount"):
                analysis_notes.append(f"    Amount found: ₹{a['amount']:,.0f}")
        note = "\n".join(analysis_notes) if analysis_notes else ""
        remaining = len(REQUIRED_DOCS.get(ctx.get("claim_type", "health"), [])) - len(docs_received)
        response = (
            f"📎 Received: **{names}**\n{note}\n\n"
            + (f"Please upload the remaining **{remaining} document(s)** or type **'done'** if complete."
               if remaining > 0 else "All required documents appear to be uploaded. Type **'done'** to continue.")
        )
        return response, ctx, "wizard"

    # User asking what documents are needed
    if any(w in t for w in ["what", "which", "need", "require", "list"]):
        return _document_prompt(ctx.get("claim_type", "health")), ctx, "wizard"

    response = (
        f"I have **{len(docs_received)} document(s)** so far. "
        "Please continue uploading using the 📎 button, or type **'done'** when finished."
    )
    return response, ctx, "wizard"


def _handle_contact_info(msg: str, ctx: Dict, user_email: str) -> tuple:
    """Capture contact details."""
    ctx = dict(ctx)
    t = msg.lower()

    if any(w in t for w in ["use registered", "my account", "same email", "registered"]):
        ctx["contact_email"] = user_email
        ctx["contact_confirmed"] = True
    else:
        email_m = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", msg, re.IGNORECASE)
        phone_m = re.search(r"(?:\+91|0)?[6-9]\d{9}", msg)
        if email_m:
            ctx["contact_email"] = email_m.group(0)
        if phone_m:
            ctx["contact_phone"] = phone_m.group(0)
        ctx["contact_confirmed"] = bool(email_m or phone_m)

    ctx = _advance_step(ctx, STEP_REVIEW)
    return None, ctx, "wizard"   # fall through to review handler


def _handle_review(ctx: Dict) -> tuple:
    """Show collected data for user confirmation."""
    claim_type = ctx.get("claim_type", "unknown").title()
    lines = [
        "**Claim Summary — Please Review**\n",
        f"📋 **Claim Type**: {claim_type}",
        f"📅 **Incident Date**: {ctx.get('incident_date', 'Not provided')}",
        f"📝 **Description**: {ctx.get('incident_description', 'Not provided')[:200]}",
        f"🔖 **Policy Number**: {ctx.get('policy_number', 'Not provided')}",
        f"💰 **Claimed Amount**: {'₹{:,.0f}'.format(ctx['claimed_amount']) if ctx.get('claimed_amount') else 'Not specified'}",
        f"📎 **Documents**: {len(ctx.get('documents_received', []))} uploaded",
        f"📧 **Contact**: {ctx.get('contact_email', 'Not provided')}",
        "",
        "Does everything look correct? You can:",
        "• Type **'submit'** to file the claim",
        "• Type **'report'** to generate a detailed summary report",
        "• Tell me what to correct",
    ]
    return "\n".join(lines), ctx, "wizard"


def _handle_summary_generation(ctx: Dict, history: List[Dict]) -> Dict:
    """Build the structured summary report from all collected data."""
    now = datetime.now(timezone.utc).isoformat()
    claim_type = ctx.get("claim_type", "unknown")

    # Build full conversation transcript
    transcript = []
    for h in history:
        transcript.append({
            "timestamp": h.get("timestamp", ""),
            "user": h.get("user_message", ""),
            "agent": h.get("bot_response", ""),
            "intent": h.get("intent", ""),
            "input_type": h.get("input_type", "text"),
        })

    # Collect all extracted fields
    extracted_fields = {
        "claim_type":            claim_type,
        "incident_date":         ctx.get("incident_date"),
        "incident_description":  ctx.get("incident_description"),
        "policy_number":         ctx.get("policy_number"),
        "claimed_amount":        ctx.get("claimed_amount"),
        "contact_email":         ctx.get("contact_email"),
        "contact_phone":         ctx.get("contact_phone"),
        "documents_received":    ctx.get("documents_received", []),
        "nationality":           ctx.get("nationality", "IN"),
        "country_of_residence":  ctx.get("country_of_residence", "IN"),
    }

    # Document analysis summary
    doc_summary = []
    for doc in ctx.get("documents_received", []):
        a = doc.get("analysis", {})
        doc_summary.append({
            "filename":      doc.get("name"),
            "detected_type": a.get("document_type", "unknown"),
            "amount_found":  a.get("amount"),
            "date_found":    a.get("date"),
            "confidence":    a.get("confidence", 0),
        })

    # Completeness check
    required = REQUIRED_DOCS.get(claim_type, [])
    missing_docs = []
    if len(ctx.get("documents_received", [])) < len(required):
        missing_docs = required[len(ctx.get("documents_received", [])):]

    completeness_pct = int(
        (len(ctx.get("documents_received", [])) / max(len(required), 1)) * 100
    )

    report = {
        "report_id":          f"RPT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "generated_at":       now,
        "session_id":         ctx.get("session_id", ""),
        "user_id":            ctx.get("user_id", ""),
        "claim_type":         claim_type,
        "extracted_fields":   extracted_fields,
        "document_analysis":  doc_summary,
        "missing_documents":  missing_docs,
        "completeness_pct":   completeness_pct,
        "conversation_turns": len(history),
        "transcript":         transcript,
        "ready_for_pipeline": completeness_pct >= 50 and bool(ctx.get("incident_description")),
        "pipeline_input": {
            "claim_type":            claim_type,
            "description":           ctx.get("incident_description", ""),
            "policy_number":         ctx.get("policy_number"),
            "incident_date":         ctx.get("incident_date"),
            "claimed_amount":        ctx.get("claimed_amount"),
            "document_count":        len(ctx.get("documents_received", [])),
            "submitted_via":         "guided_chat",
            "nationality":           ctx.get("nationality", "IN"),
            "country_of_residence":  ctx.get("country_of_residence", "IN"),
        },
    }
    return report

# ─────────────────────────────────────────────────────────────────────────────
# POLICY Q&A
# ─────────────────────────────────────────────────────────────────────────────

def _handle_policy_query(msg: str) -> Dict:
    hits = _search_kb(msg)
    if hits:
        body = "\n".join(f"• {h}" for h in hits)
        response = f"Based on your policy documents:\n\n{body}\n\nFor specific eligibility, please submit your claim for assessment."
    else:
        response = (
            "I couldn't find a specific clause for that query. "
            "Here's what I know by claim type:\n\n"
            "**Health**: Covers hospitalisation, surgery, ICU, day-care procedures.\n"
            "**Motor**: Covers own-damage, third-party liability, theft.\n"
            "**Property**: Covers fire, flood, earthquake, burglary.\n"
            "**Crop**: Covers natural calamities, pest damage, drought.\n\n"
            "Would you like to file a claim or ask something more specific?"
        )
    return {
        "response": response,
        "intent": "policy_query",
        "claim_id": None,
        "requires_pipeline": False,
        "suggested_actions": ["File a claim", "Ask another question", "Check claim status"],
        "context_updates": {},
        "summary_report": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLAIM STATUS LOOKUP
# ─────────────────────────────────────────────────────────────────────────────

async def _handle_claim_status(msg: str, user_id: str) -> Dict:
    claim_id = _extract_claim_id(msg)
    if not claim_id:
        return {
            "response": (
                "Please share your **Claim ID** (format: CLM-YYYYMMDD-XXXXXX) "
                "and I'll look it up right away."
            ),
            "intent": "claim_status_prompt",
            "claim_id": None,
            "requires_pipeline": False,
            "suggested_actions": ["Enter claim ID"],
            "context_updates": {},
            "summary_report": None,
        }

    try:
        from backend.services.dynamodb_service import get_db_service
        db = get_db_service()
        claim = await db.get_claim(claim_id)
    except Exception as e:
        logger.error(f"DB error fetching {claim_id}: {e}")
        claim = None

    if not claim:
        return {
            "response": f"I couldn't find claim **{claim_id}**. Please double-check the ID.",
            "intent": "claim_status",
            "claim_id": claim_id,
            "requires_pipeline": False,
            "suggested_actions": ["Submit a new claim", "Contact support"],
            "context_updates": {},
            "summary_report": None,
        }

    status    = claim.get("status", "unknown")
    routing   = claim.get("routing_decision", "")
    estimate  = claim.get("damage_estimate")
    fraud     = claim.get("fraud_score")

    if status == "approved":
        body = (
            f"✅ **Approved!**\n"
            + (f"💰 Settlement: ₹{estimate:,.0f}\n" if estimate else "")
            + "Payment will be processed within 2 business days."
        )
    elif status == "rejected":
        body = "❌ **Rejected.** Please contact your advisor for detailed feedback."
    elif status in ("pending_review", "processing") or routing == "human_queue":
        body = (
            "⏳ **Under review** by our claims team.\n"
            + (f"Risk score: {fraud:.0f}/100\n" if fraud is not None else "")
            + "Expected update within 24 hours."
        )
    else:
        body = f"🔄 **{status.replace('_', ' ').title()}** — {routing or 'processing'}"

    return {
        "response": f"**Claim {claim_id}**\n\n{body}",
        "intent": "claim_status",
        "claim_id": claim_id,
        "requires_pipeline": False,
        "suggested_actions": ["Ask a question", "Submit another claim"],
        "context_updates": {},
        "summary_report": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

async def handle_chat_query(
    user_message: str,
    user_id: str,
    session_context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict]] = None,
    attachments: Optional[List[Dict]] = None,
    user_email: str = "",
) -> Dict[str, Any]:
    """
    Process one turn of the guided insurance chat.

    Args:
        user_message:         The user's text input (may include voice transcript).
        user_id:              Authenticated user ID.
        session_context:      Mutable wizard state dict persisted in DynamoDB session.
        conversation_history: Full list of prior exchanges from DynamoDB.
        attachments:          List of {name, type, analysis} dicts for uploaded files.
        user_email:           Registered email for contact-info step.

    Returns dict with keys:
        response, intent, claim_id, requires_pipeline,
        suggested_actions, context_updates, summary_report
    """
    ctx       = dict(session_context or {})
    history   = list(conversation_history or [])
    atts      = list(attachments or [])
    step      = _get_step(ctx)
    msg       = user_message.strip()
    t         = msg.lower()

    logger.info(f"[chat] user={user_id} step={step} msg={msg[:60]!r}")

    # ── Global overrides (work from any step) ─────────────────────────────────
    # Claim status check
    if _extract_claim_id(msg) or any(w in t for w in ["status", "track my claim", "check claim"]):
        if step not in (STEP_GREETING, STEP_CLAIM_TYPE):
            result = await _handle_claim_status(msg, user_id)
            result["context_updates"] = ctx
            return result

    # Policy question
    if any(w in t for w in ["covered", "coverage", "eligible", "what does", "does my policy"]):
        result = _handle_policy_query(msg)
        result["context_updates"] = ctx
        return result

    # Summary / report request
    if any(w in t for w in ["report", "summary", "generate report", "download"]):
        if step in (STEP_REVIEW, STEP_SUMMARY_GENERATED, STEP_DOCUMENT_COLLECT):
            report = _handle_summary_generation(ctx, history)
            ctx = _advance_step(ctx, STEP_SUMMARY_GENERATED)
            ctx["summary_report"] = report
            response = (
                "✅ **Summary Report Generated!**\n\n"
                f"📋 Report ID: **{report['report_id']}**\n"
                f"📊 Completeness: **{report['completeness_pct']}%**\n"
                f"💬 Conversation turns: **{report['conversation_turns']}**\n"
                f"📎 Documents: **{len(report['document_analysis'])}**\n"
                + (f"⚠️ Missing: {', '.join(report['missing_documents'])}\n" if report["missing_documents"] else "")
                + "\nYou can now **submit the claim** or **download the report**."
            )
            return {
                "response": response,
                "intent": "summary_generated",
                "claim_id": None,
                "requires_pipeline": report["ready_for_pipeline"],
                "suggested_actions": STEP_ACTIONS[STEP_SUMMARY_GENERATED],
                "context_updates": ctx,
                "summary_report": report,
            }

    # Submit request
    if any(w in t for w in ["submit", "file claim", "proceed", "confirm"]):
        if step in (STEP_REVIEW, STEP_SUMMARY_GENERATED):
            report = _handle_summary_generation(ctx, history)
            ctx["summary_report"] = report
            ctx = _advance_step(ctx, STEP_SUMMARY_GENERATED)
            return {
                "response": (
                    "🚀 Your claim is ready to submit!\n\n"
                    "I've compiled all the information. "
                    "Click **Submit Claim** below to send it to our processing pipeline."
                ),
                "intent": "ready_to_submit",
                "claim_id": None,
                "requires_pipeline": True,
                "suggested_actions": ["Submit claim now", "Download report first"],
                "context_updates": ctx,
                "summary_report": report,
            }

    # ── Wizard step routing ───────────────────────────────────────────────────
    if step == STEP_GREETING:
        response, ctx, intent = _handle_greeting(msg, ctx)
        if response is None and intent == "claim_status":
            result = await _handle_claim_status(msg, user_id)
            result["context_updates"] = ctx
            return result
        if response is None and intent == "policy_query":
            result = _handle_policy_query(msg)
            result["context_updates"] = ctx
            return result

    elif step == STEP_CLAIM_TYPE:
        response, ctx, intent = _handle_claim_type(msg, ctx)

    elif step == STEP_INCIDENT_DETAILS:
        response, ctx, intent = _handle_incident_details(msg, ctx)

    elif step == STEP_POLICY_NUMBER:
        response, ctx, intent = _handle_policy_number(msg, ctx)

    elif step == STEP_DOCUMENT_COLLECT:
        response, ctx, intent = _handle_document_collection(msg, ctx, atts)

    elif step == STEP_CONTACT_INFO:
        response, ctx, intent = _handle_contact_info(msg, ctx, user_email)
        if response is None:
            # Fall through to review
            response, ctx, intent = _handle_review(ctx)

    elif step == STEP_REVIEW:
        response, ctx, intent = _handle_review(ctx)

    elif step == STEP_SUMMARY_GENERATED:
        # Let the user keep chatting freely — answer anything
        # Check for specific actions first
        if any(w in t for w in ["submit", "file", "send claim", "submit claim"]):
            report = ctx.get("summary_report") or _handle_summary_generation(ctx, history)
            ctx["summary_report"] = report
            return {
                "response": (
                    "🚀 **Claim ready to submit!**\n\n"
                    "All your information has been compiled. "
                    "Click **Submit Claim Now** in the banner below to send it to our processing pipeline."
                ),
                "intent": "ready_to_submit",
                "claim_id": None,
                "requires_pipeline": True,
                "suggested_actions": ["Submit claim now", "Download report first", "Ask a question"],
                "context_updates": ctx,
                "summary_report": report,
            }

        # Free-form: answer policy questions, status checks, or general chat
        hits = _search_kb(msg)
        if hits:
            body = "\n".join(f"• {h}" for h in hits)
            response = f"Based on your policy:\n\n{body}\n\nIs there anything else I can help you with?"
        elif any(w in t for w in ["hello", "hi", "hey", "thanks", "thank you", "okay", "ok", "yes", "no", "sure"]):
            response = (
                "Happy to help! Your claim summary is ready whenever you are.\n\n"
                "You can **submit the claim**, **download the report**, or ask me anything about your policy or claim."
            )
        elif len(msg) > 10:
            response = (
                f"Great question! Here is what I can tell you:\n\n"
                f"Your **{ctx.get('claim_type', 'insurance').title()} claim** has been fully prepared. "
                f"Regarding your question, I would recommend contacting your insurance advisor for specific details, "
                f"or I can help you submit the claim now so our team can review it.\n\n"
                f"Is there anything specific about your claim or policy I can clarify?"
            )
        else:
            response = "I am here! Ask me anything, or type **submit** to file your claim."

        intent = "free_chat"

    else:
        response = "I'm not sure where we are. Let's start fresh — what can I help you with?"
        ctx = _advance_step(ctx, STEP_GREETING)
        intent = "reset"

    new_step = _get_step(ctx)
    return {
        "response": response,
        "intent": intent,
        "claim_id": None,
        "requires_pipeline": False,
        "suggested_actions": STEP_ACTIONS.get(new_step, ["Continue"]),
        "context_updates": ctx,
        "summary_report": None,
    }
