# backend/agents/policy_auditor.py
# ClaimFlow — Policy Auditor Agent
#
# Checks a claim against insurance_kb.json clauses (local mode).
# When CLAIMFLOW_AWS_ENABLED=true and kb_config.json has a valid KB ID,
# it queries the Bedrock Knowledge Base instead.
#
# Interface expected by policy_node in nodes.py:
#   result = run({...})
#   result["success"]                  → bool
#   result["data"]["eligible"]         → bool
#   result["data"]["irdai_compliant"]  → bool
#   result["data"]["requires_human"]   → bool
#   result["data"]["regulation_used"]  → str
#   result["data"]["policy_clauses"]   → list[str]
#   result["data"]["notes"]            → str

import json
import logging
import os
import re
import time
from pathlib import Path

logger = logging.getLogger("claimflow.policy_auditor")

# ── File paths ────────────────────────────────────────────────────────────────
_DATA_DIR   = Path(__file__).resolve().parent.parent / "data_json"
_KB_FILE    = _DATA_DIR / "insurance_kb.json"
_KB_CONFIG  = _DATA_DIR / "kb_config.json"

# ── PII patterns for local masking ───────────────────────────────────────────
_PII_PATTERNS = [
    re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"),   # Aadhaar
    re.compile(r"\b\d{10}\b"),                         # phone
]


def _mask_pii(text: str) -> str:
    for pat in _PII_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def _load_kb() -> list[dict]:
    """Load insurance_kb.json → list of {clause, page, text} dicts."""
    if not _KB_FILE.exists():
        logger.error(f"Knowledge base file not found: {_KB_FILE}")
        return []
    with open(_KB_FILE, encoding="utf-8") as f:
        return json.load(f)


def _load_kb_config() -> dict:
    if not _KB_CONFIG.exists():
        return {}
    with open(_KB_CONFIG, encoding="utf-8") as f:
        return json.load(f)


# Cache at module load
_KB_CLAUSES = _load_kb()
_KB_CFG     = _load_kb_config()

# ── Exclusion keywords per claim type ────────────────────────────────────────
_EXCLUSIONS: dict[str, list[str]] = {
    "health": [
        "cosmetic", "aesthetic", "dental", "vaccination",
        "outpatient", "gym", "wear and tear",
    ],
    "motor": [
        "alcohol", "intentional", "wear and tear",
        "non-genuine spare", "pre-existing vehicle damage",
    ],
    "crop":     ["intentional"],
    "property": ["intentional"],
}


# ── Bedrock Knowledge Base query (used when AWS is live) ─────────────────────

def _query_bedrock_kb(query: str, kb_id: str, region: str, n_results: int = 5) -> list[dict]:
    """
    Retrieve relevant clauses from Bedrock Knowledge Base.
    Returns list of {text, clause, score} dicts.
    Falls back to [] on any error so local check takes over.
    """
    try:
        import boto3
        client = boto3.client(
            "bedrock-agent-runtime",
            region_name           = region,
            aws_access_key_id     = os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token     = os.getenv("AWS_SESSION_TOKEN"),
        )
        response = client.retrieve(
            knowledgeBaseId = kb_id,
            retrievalQuery  = {"text": query},
            retrievalConfiguration = {
                "vectorSearchConfiguration": {"numberOfResults": n_results}
            },
        )
        results = []
        for r in response.get("retrievalResults", []):
            content = r.get("content", {}).get("text", "")
            score   = r.get("score", 0.0)
            results.append({"text": content, "score": score})
        return results
    except Exception as exc:
        logger.warning(f"[policy_auditor] Bedrock KB query failed: {exc} — using local KB")
        return []


# ── Local deterministic check ─────────────────────────────────────────────────

def _local_policy_check(
    claim_type: str,
    description: str,
    claim_amount: float,
    vision_result: dict,
    forensic_result: dict,
) -> dict:
    claim_type_lower = (claim_type or "").lower()
    desc_lower       = (description or "").lower()

    matched_clauses: list[str] = []
    exclusion_hits:  list[str] = []
    notes:           list[str] = []

    # 1. Exclusion check
    for keyword in _EXCLUSIONS.get(claim_type_lower, []):
        if keyword in desc_lower:
            exclusion_hits.append(keyword)

    # 2. Match relevant clauses from KB JSON
    for entry in _KB_CLAUSES:
        text_lower = entry.get("text", "").lower()
        if claim_type_lower in text_lower or any(
            kw in text_lower
            for kw in ["claim", "coverage", "covered", "excluded", "not covered"]
        ):
            matched_clauses.append(
                f"Clause {entry.get('clause', '?')}: {entry.get('text', '')}"
            )

    # 3. Financial threshold — Clause 7.1
    requires_human = False
    if claim_amount and float(claim_amount) > 200_000:
        requires_human = True
        notes.append(f"Claim ₹{claim_amount:,.0f} exceeds ₹2L auto-approval limit (Clause 7.1)")

    # 4. Pre-authorization for planned admissions — Clause 6.1
    if claim_type_lower == "health" and (
        "planned" in desc_lower or "elective" in desc_lower
    ):
        notes.append("Pre-authorization required for planned admissions (Clause 6.1)")

    # 5. Motor theft needs FIR — Clause 17.2
    if claim_type_lower == "motor" and "theft" in desc_lower:
        notes.append("FIR copy mandatory for theft claims (Clause 17.2)")

    # 6. Eligibility
    eligible       = len(exclusion_hits) == 0
    irdai_compliant = eligible

    if exclusion_hits:
        notes.append(f"Exclusion keywords found: {', '.join(exclusion_hits)}")

    return {
        "eligible":        eligible,
        "irdai_compliant": irdai_compliant,
        "requires_human":  requires_human,
        "policy_clauses":  matched_clauses[:5],
        "exclusion_hits":  exclusion_hits,
        "regulation_used": "insurance_kb.json (local)",
        "notes":           " | ".join(notes) if notes else "No issues found",
    }


def run(input_data: dict) -> dict:
    """
    Synchronous entry point called by policy_node.

    Tries Bedrock Knowledge Base first (when AWS enabled + KB ID configured).
    Falls back to local insurance_kb.json check.
    """
    start = time.time()
    try:
        claim_type      = input_data.get("claim_type", "")
        description     = _mask_pii(input_data.get("description") or "")
        claim_amount    = float(
            input_data.get("billed_amount")
            or input_data.get("claim_amount")
            or 0
        )
        vision_result   = input_data.get("vision_result") or {}
        forensic_result = input_data.get("forensic_result") or {}

        # Pull amount from vision structured_data if not in raw_input
        if claim_amount == 0:
            sd = vision_result.get("structured_data") or {}
            claim_amount = float(
                sd.get("bill_amount") or sd.get("repair_amount") or 0
            )

        # ── Try Bedrock KB if AWS is enabled ──────────────────────────────────
        aws_enabled = str(os.getenv("CLAIMFLOW_AWS_ENABLED", "false")).lower() == "true"
        kb_id       = _KB_CFG.get("knowledge_base_id", "")
        region      = _KB_CFG.get("region") or os.getenv("AWS_REGION", "us-east-1")

        bedrock_clauses: list[str] = []
        if aws_enabled and kb_id and kb_id != "PLACEHOLDER":
            query   = f"{claim_type} claim: {description[:300]}"
            results = _query_bedrock_kb(query, kb_id, region)
            bedrock_clauses = [r["text"] for r in results if r.get("text")]

        # ── Always run local deterministic check ──────────────────────────────
        result = _local_policy_check(
            claim_type      = claim_type,
            description     = description,
            claim_amount    = claim_amount,
            vision_result   = vision_result,
            forensic_result = forensic_result,
        )

        # Merge Bedrock KB results into policy_clauses if available
        if bedrock_clauses:
            result["policy_clauses"] = bedrock_clauses[:5]
            result["regulation_used"] = f"Bedrock KB ({kb_id})"

        logger.info(
            f"[policy_auditor] eligible={result['eligible']} | "
            f"irdai={result['irdai_compliant']} | "
            f"human={result['requires_human']} | "
            f"kb={'bedrock' if bedrock_clauses else 'local'} | "
            f"latency={round(time.time()-start, 3)}s"
        )

        return {"success": True, "data": result, "error": None}

    except Exception as exc:
        logger.error(f"[policy_auditor] failed: {exc}", exc_info=True)
        return {
            "success": False,
            "data": {
                "eligible":        True,   # fail-open
                "irdai_compliant": True,
                "requires_human":  False,
                "policy_clauses":  [],
                "regulation_used": "fallback",
                "notes":           f"Policy check failed: {exc}",
            },
            "error": str(exc),
        }
