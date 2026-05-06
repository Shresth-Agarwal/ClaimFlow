import asyncio
import json
import os
import re
import time
from urllib.parse import urlparse

try:
    boto3 = __import__("boto3")
except Exception:  # pragma: no cover - optional runtime dependency
    boto3 = None

USE_MOCK = True
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
DEFAULT_AWS_REGION = "us-east-1"
FORENSIC_STRAND_META = {
    "strand_name": "forensic_strand",
    "strand_version": "1.0.0",
    "capabilities": [
        "deterministic_validation",
        "bedrock_reasoning",
        "cross_evidence_analysis",
        "damage_assessment",
        "settlement_estimation",
        "explainable_output",
    ],
}


def _to_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _forensic_execution_meta(bedrock_enabled: bool) -> dict:
    return {
        "strand_name": FORENSIC_STRAND_META["strand_name"],
        "strand_version": FORENSIC_STRAND_META["strand_version"],
        "execution_mode": "hybrid_execution" if bedrock_enabled else "deterministic_execution",
        "reasoning_mode": "deterministic_first_with_optional_bedrock",
        "strand_capabilities": FORENSIC_STRAND_META["capabilities"],
    }


def _run_deterministic_analysis(prompt: str) -> str:
    """
    Lightweight deterministic claim analysis based on:
    - vision_output: {domain, document_type, structured_data, visual_indicators}
    - processed_evidences: list of evidence objects

    The first line of the prompt is expected to be a JSON context payload.
    """
    first_line = prompt.split("\n", 1)[0].strip()
    try:
        context = json.loads(first_line) if first_line.startswith("{") else {}
    except Exception:
        context = {}

    vision_output = context.get("vision_output") or {}
    processed_evidences = context.get("processed_evidences") or []

    domain = (vision_output.get("domain") or "").lower() or "unknown"
    document_type = (vision_output.get("document_type") or "").lower() or (vision_output.get("structured_data") or {}).get(
        "document_type"
    )
    document_type = (document_type or "unknown").lower()
    structured_data = vision_output.get("structured_data") or {}
    visual_indicators = vision_output.get("visual_indicators") or []

    consistency_checks: list[str] = []
    suspicious_indicators: list[str] = []
    analysis_summary: list[str] = []

    claim_confidence = 1.0

    def _reduce(amount: float, reason: str, bucket: str) -> None:
        nonlocal claim_confidence
        try:
            amount = float(amount)
        except Exception:
            amount = 0.0
        if amount <= 0:
            return
        claim_confidence = max(0.0, claim_confidence - amount)
        if bucket == "consistency":
            consistency_checks.append(reason)
        elif bucket == "suspicious":
            suspicious_indicators.append(reason)
        else:
            analysis_summary.append(reason)

    def _add_summary(msg: str) -> None:
        if msg and msg not in analysis_summary:
            analysis_summary.append(msg)

    def _parse_date(s: str | None) -> tuple[int, int, int] | None:
        if not s:
            return None
        s = s.strip()
        try:
            # Supports dd-Mon-yyyy, dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd
            m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
            if m:
                return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
            if m:
                return (int(m.group(3)), int(m.group(2)), int(m.group(1)))
            m = re.match(r"^(\d{1,2})[-/](jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[-/](\d{4})$", s, re.I)
            if m:
                mon_map = {
                    "jan": 1,
                    "feb": 2,
                    "mar": 3,
                    "apr": 4,
                    "may": 5,
                    "jun": 6,
                    "jul": 7,
                    "aug": 8,
                    "sep": 9,
                    "oct": 10,
                    "nov": 11,
                    "dec": 12,
                }
                return (int(m.group(3)), mon_map[m.group(2).lower()], int(m.group(1)))
        except Exception:
            return None
        return None

    def _is_before(a: tuple[int, int, int] | None, b: tuple[int, int, int] | None) -> bool | None:
        if not a or not b:
            return None
        return a < b

    # -----------------------
    # Domain-aware analysis
    # -----------------------
    try:
        if domain == "motor":
            if any(v in (str(x).lower() for x in visual_indicators) for v in ("rust", "pre_existing_rust")):
                _reduce(0.18, "Pre-existing rust indicator present in evidence.", "suspicious")

            repair_amount = structured_data.get("repair_amount")
            damage_severity = (structured_data.get("damage_severity") or "").lower()
            if repair_amount is not None:
                try:
                    amt = float(repair_amount)
                    if damage_severity in ("minor",) and amt > 25000:
                        _reduce(0.15, "Repair amount appears high relative to minor visible damage.", "consistency")
                    elif damage_severity in ("moderate",) and amt > 90000:
                        _reduce(0.12, "Repair amount appears high relative to moderate visible damage.", "consistency")
                except Exception:
                    _reduce(0.05, "Repair amount could not be validated (non-numeric).", "consistency")

            # Duplicate repair invoices by matching bill/invoice identifiers if present.
            invoice_ids: list[str] = []
            for ev in processed_evidences:
                if not isinstance(ev, dict):
                    continue
                vo = ev.get("vision_output") or {}
                sd = vo.get("structured_data") or {}
                dt = (vo.get("document_type") or sd.get("document_type") or "").lower()
                if dt in ("repair_invoice", "invoice"):
                    inv = sd.get("invoice_number") or sd.get("bill_number") or sd.get("invoice_id")
                    if isinstance(inv, str) and inv.strip():
                        invoice_ids.append(inv.strip().lower())
            if invoice_ids:
                dupes = {x for x in invoice_ids if invoice_ids.count(x) > 1}
                if dupes:
                    _reduce(0.2, "Duplicate repair invoice identifiers detected across evidences.", "suspicious")

            _add_summary("Motor claim evidence reviewed for pre-existing damage and estimate consistency.")

        elif domain == "health":
            bill_no = structured_data.get("bill_number")
            if not bill_no:
                _reduce(0.12, "Hospital bill number missing; reduces traceability.", "consistency")

            admission_date = structured_data.get("admission_date")
            discharge_date = structured_data.get("discharge_date")
            a = _parse_date(admission_date)
            d = _parse_date(discharge_date)
            before = _is_before(d, a)
            if before is True:
                _reduce(0.25, "Discharge date occurs before admission date.", "suspicious")
            elif before is False:
                _add_summary("Admission and discharge date ordering appears consistent.")

            bill_amount = structured_data.get("bill_amount")
            try:
                if bill_amount is None:
                    _reduce(0.08, "Bill amount missing; cannot validate claim magnitude.", "consistency")
                else:
                    amt = float(bill_amount)
                    if amt > 250000:
                        _reduce(0.15, "Bill amount is unusually high; requires additional justification.", "consistency")
                    if amt <= 0:
                        _reduce(0.18, "Bill amount is non-positive; likely parsing or document issue.", "suspicious")
            except Exception:
                _reduce(0.06, "Bill amount is not a valid number; cannot validate.", "consistency")

            # Cross-evidence: bill vs discharge summary if both exist.
            has_bill = document_type == "hospital_bill"
            has_discharge = False
            for ev in processed_evidences:
                if not isinstance(ev, dict):
                    continue
                vo = ev.get("vision_output") or {}
                dt = (vo.get("document_type") or (vo.get("structured_data") or {}).get("document_type") or "").lower()
                if dt == "discharge_summary":
                    has_discharge = True
                    ds = vo.get("structured_data") or {}
                    ds_adm = _parse_date(ds.get("admission_date"))
                    ds_dis = _parse_date(ds.get("discharge_date"))
                    if a and ds_adm and ds_adm != a:
                        _reduce(0.12, "Admission date differs between bill and discharge summary.", "consistency")
                    if d and ds_dis and ds_dis != d:
                        _reduce(0.12, "Discharge date differs between bill and discharge summary.", "consistency")
            if has_bill and not has_discharge:
                _reduce(0.08, "Discharge summary not provided alongside hospital bill.", "consistency")

            # Duplicate invoice IDs across evidence set.
            ids = []
            if isinstance(bill_no, str) and bill_no.strip():
                ids.append(bill_no.strip().lower())
            for ev in processed_evidences:
                if not isinstance(ev, dict):
                    continue
                vo = ev.get("vision_output") or {}
                sd = vo.get("structured_data") or {}
                inv = sd.get("bill_number") or sd.get("invoice_number") or sd.get("invoice_id")
                if isinstance(inv, str) and inv.strip():
                    ids.append(inv.strip().lower())
            dupes = {x for x in ids if ids.count(x) > 1}
            if dupes and len(processed_evidences) > 1:
                _reduce(0.12, "Duplicate invoice/bill identifiers detected across evidences.", "suspicious")

            _add_summary("Health claim evidence reviewed for document completeness and date/amount consistency.")

        elif domain == "crop":
            # Keep lightweight: rely on vision indicators and evidence metadata.
            if any(v in (str(x).lower() for x in visual_indicators) for v in ("drought", "pest_damage", "pest")):
                _add_summary("Crop damage indicators present and recorded.")

            # Timestamp inconsistencies if evidence includes timestamps.
            timestamps: list[str] = []
            for ev in processed_evidences:
                if not isinstance(ev, dict):
                    continue
                ts = ev.get("timestamp") or ev.get("captured_at")
                if isinstance(ts, str) and ts.strip():
                    timestamps.append(ts.strip())
            if len(set(timestamps)) != len(timestamps) and timestamps:
                _reduce(0.1, "Duplicate field image timestamps detected; possible reuse.", "suspicious")

            _add_summary("Crop claim reviewed for basic temporal and duplication indicators.")

        elif domain == "property":
            # FIR availability check (common requirement).
            has_fir = False
            has_ownership = False
            for ev in processed_evidences:
                if not isinstance(ev, dict):
                    continue
                vo = ev.get("vision_output") or {}
                dt = (vo.get("document_type") or (vo.get("structured_data") or {}).get("document_type") or "").lower()
                if dt == "fir":
                    has_fir = True
                if dt == "ownership_document":
                    has_ownership = True
            if not has_fir:
                _reduce(0.15, "Required FIR evidence missing for property claim context.", "consistency")
            if not has_ownership:
                _reduce(0.1, "Ownership document missing; limits address/ownership validation.", "consistency")

            if any(v in (str(x).lower() for x in visual_indicators) for v in ("fire_damage", "flood_marks", "structural_cracks")):
                _add_summary("Property damage indicators present and recorded.")

            _add_summary("Property claim reviewed for required documentation and damage/evidence consistency.")

        else:
            _reduce(0.1, "Unknown domain; limited consistency validation possible.", "consistency")
            _add_summary("Evidence reviewed with generic validation rules due to unknown domain.")
    except Exception:
        # Never fail the entire analysis.
        _reduce(0.05, "One or more validation steps failed; partial analysis returned.", "summary")

    # -----------------------
    # Cross-evidence checks
    # -----------------------
    try:
        # Simple duplicate detection: repeated evidence paths.
        paths = []
        for ev in processed_evidences:
            if isinstance(ev, dict):
                p = ev.get("path") or ev.get("url")
                if isinstance(p, str) and p.strip():
                    paths.append(p.strip().lower())
        if paths:
            dup_paths = {p for p in paths if paths.count(p) > 1}
            if dup_paths:
                _reduce(0.12, "Duplicate evidence files detected (same path reused).", "suspicious")
    except Exception:
        _reduce(0.03, "Cross-evidence duplicate validation failed; continuing.", "summary")

    claim_confidence = max(0.0, min(1.0, float(claim_confidence)))
    if claim_confidence >= 0.8:
        risk_level = "low"
    elif claim_confidence >= 0.5:
        risk_level = "moderate"
    else:
        risk_level = "high"

    # Keep legacy fields for backward compatibility (derived, non-accusatory).
    legacy_fraud_score = round(1.0 - claim_confidence, 2)
    legacy_anomalies_detected = bool(suspicious_indicators)
    legacy_anomaly_type = suspicious_indicators[:]
    legacy_verdict = "suspicious" if risk_level == "high" else "valid"
    legacy_reason = "; ".join(analysis_summary[:3]) if analysis_summary else "No strong risk indicators detected."
    damage_assessment = build_damage_assessment(
        domain, structured_data, visual_indicators, claim_confidence, suspicious_indicators, consistency_checks
    )

    return json.dumps(
        {
            "claim_confidence": round(claim_confidence, 2),
            "risk_level": risk_level,
            "consistency_checks": consistency_checks,
            "suspicious_indicators": suspicious_indicators,
            "analysis_summary": analysis_summary,
            "confidence": round(claim_confidence, 2),
            # Legacy compatibility (deprecated)
            "anomalies_detected": legacy_anomalies_detected,
            "anomaly_type": legacy_anomaly_type,
            "fraud_score": legacy_fraud_score,
            "verdict": legacy_verdict,
            "reason": legacy_reason,
            "damage_assessment": damage_assessment,
        }
    )


def _invoke_mock_model(prompt: str) -> str:
    # Backward-compatible alias used by existing flow.
    return _run_deterministic_analysis(prompt)


def estimate_damage_cost(
    domain: str,
    structured_data: dict,
    visual_indicators: list,
    suspicious_indicators: list[str],
    consistency_checks: list[str],
) -> tuple[float, str, list[str]]:
    notes: list[str] = []
    severity = "moderate"
    lowered_visual = {str(v).lower() for v in (visual_indicators or [])}

    if domain == "motor":
        invoice = structured_data.get("repair_amount") or structured_data.get("bill_amount")
        severity_hint = (structured_data.get("damage_severity") or "").lower()
        if severity_hint in {"minor", "moderate", "severe"}:
            severity = severity_hint
        elif any(v in lowered_visual for v in {"cracks", "structural_cracks"}):
            severity = "severe"
        elif any(v in lowered_visual for v in {"dents", "dent"}):
            severity = "moderate"
        else:
            severity = "minor"
        base = {"minor": 12000.0, "moderate": 45000.0, "severe": 110000.0}[severity]
        if invoice is not None:
            try:
                inv = float(invoice)
                base = (base * 0.45) + (inv * 0.55)
                notes.append("Repair invoice considered in motor damage estimate.")
            except Exception:
                notes.append("Repair invoice could not be parsed; using severity-led estimate.")
        if any("rust" in s.lower() for s in suspicious_indicators):
            base *= 0.85
            notes.append("Pre-existing rust indicator reduced estimated payable damage.")
        return max(1000.0, round(base, 2)), severity, notes

    if domain == "health":
        severity = "moderate"
        bill_amount = structured_data.get("bill_amount")
        admission = structured_data.get("admission_date")
        discharge = structured_data.get("discharge_date")
        base = 35000.0
        if bill_amount is not None:
            try:
                base = float(bill_amount)
                notes.append("Hospital bill amount used as primary medical damage signal.")
            except Exception:
                notes.append("Bill amount unreadable; using baseline medical estimate.")
        if admission and discharge:
            notes.append("Admission/discharge timeline available for health assessment.")
        if any("high" in c.lower() and "bill amount" in c.lower() for c in consistency_checks):
            severity = "severe"
            base *= 0.82
            notes.append("Potential overbilling risk detected; estimate adjusted conservatively.")
        return max(1000.0, round(base, 2)), severity, notes

    if domain == "property":
        severity = "moderate"
        if any(v in lowered_visual for v in {"fire_damage", "flood_marks", "structural_cracks"}):
            severity = "severe"
        base = {"moderate": 90000.0, "severe": 220000.0}[severity]
        estimate = structured_data.get("repair_amount") or structured_data.get("bill_amount")
        if estimate is not None:
            try:
                est = float(estimate)
                base = (base * 0.4) + (est * 0.6)
                notes.append("Provided property estimate blended with visual severity baseline.")
            except Exception:
                notes.append("Property estimate unreadable; baseline applied.")
        return max(2000.0, round(base, 2)), severity, notes

    if domain == "crop":
        severity = "moderate"
        if any(v in lowered_visual for v in {"drought", "pest_damage", "flood"}):
            severity = "severe"
        base = 25000.0 if severity == "moderate" else 60000.0
        return round(base, 2), severity, ["Crop loss estimate derived from damage indicator severity."]

    return 15000.0, "moderate", ["Generic estimate used due to unknown domain."]


def evaluate_claim_inflation(
    domain: str,
    estimated_damage_cost: float,
    suspicious_indicators: list[str],
    consistency_checks: list[str],
) -> tuple[str, float, list[str]]:
    notes: list[str] = []
    risk_score = 0.0
    joined = " ".join((suspicious_indicators or []) + (consistency_checks or [])).lower()
    if "duplicate" in joined:
        risk_score += 0.28
        notes.append("Duplicate evidence or billing markers increase inflation risk.")
    if "high relative" in joined or "unusually high" in joined:
        risk_score += 0.25
        notes.append("Amount-to-damage mismatch suggests possible inflation.")
    if "missing" in joined:
        risk_score += 0.12
        notes.append("Missing corroborating documents increase uncertainty.")
    if domain == "motor" and "rust" in joined:
        risk_score += 0.18
        notes.append("Pre-existing damage indicators increase inflation likelihood.")
    risk_score = max(0.0, min(1.0, risk_score))
    if risk_score >= 0.6:
        level = "high"
    elif risk_score >= 0.3:
        level = "moderate"
    else:
        level = "low"
    return level, risk_score, notes


def estimate_settlement_amount(
    estimated_damage_cost: float, claim_confidence: float, inflation_score: float
) -> tuple[float, float, list[str]]:
    notes: list[str] = []
    payout_conf = max(0.2, min(0.98, (claim_confidence * 0.8) + ((1.0 - inflation_score) * 0.2)))
    settlement = estimated_damage_cost * (0.65 + (0.3 * payout_conf)) * (1.0 - 0.35 * inflation_score)
    notes.append("Settlement recommendation uses confidence and inflation-risk weighting.")
    return round(max(500.0, settlement), 2), round(payout_conf, 2), notes


def build_damage_assessment(
    domain: str,
    structured_data: dict,
    visual_indicators: list,
    claim_confidence: float,
    suspicious_indicators: list[str],
    consistency_checks: list[str],
) -> dict:
    estimated_cost, severity, damage_notes = estimate_damage_cost(
        domain, structured_data, visual_indicators, suspicious_indicators, consistency_checks
    )
    inflation_risk, inflation_score, inflation_notes = evaluate_claim_inflation(
        domain, estimated_cost, suspicious_indicators, consistency_checks
    )
    settlement, payout_conf, settlement_notes = estimate_settlement_amount(
        estimated_cost, claim_confidence, inflation_score
    )
    notes = damage_notes + inflation_notes + settlement_notes
    return {
        "severity": severity,
        "estimated_damage_cost": round(estimated_cost, 2),
        "recommended_settlement": settlement,
        "payout_confidence": payout_conf,
        "inflation_risk": inflation_risk,
        "assessment_notes": notes[:8],
    }


def merge_estimation_reasoning(damage_assessment: dict, reasoning: dict) -> dict:
    merged = dict(damage_assessment or {})
    updates = reasoning.get("damage_assessment_updates") or {}
    if isinstance(updates, dict):
        for key in ("severity", "inflation_risk"):
            value = updates.get(key)
            if isinstance(value, str) and value.strip():
                merged[key] = value.strip().lower()
        for key in ("estimated_damage_cost", "recommended_settlement", "payout_confidence"):
            try:
                if key in updates and updates.get(key) is not None:
                    merged[key] = float(updates[key])
            except Exception:
                pass
    notes = list(merged.get("assessment_notes") or [])
    for n in reasoning.get("assessment_notes_additions") or []:
        if isinstance(n, str) and n and n not in notes:
            notes.append(n)
    merged["assessment_notes"] = notes[:10]
    if "payout_confidence" in merged:
        merged["payout_confidence"] = round(max(0.0, min(1.0, float(merged["payout_confidence"]))), 2)
    for amount_key in ("estimated_damage_cost", "recommended_settlement"):
        if amount_key in merged:
            merged[amount_key] = round(max(0.0, float(merged[amount_key])), 2)
    return merged


def _bedrock_runtime_config(input_payload: dict | None = None) -> dict:
    payload = input_payload or {}
    env_aws_enabled = _to_bool(os.getenv("CLAIMFLOW_AWS_ENABLED"), False)
    return {
        "enabled": _to_bool(payload.get("bedrock_enabled"), env_aws_enabled),
        "region": payload.get("aws_region") or DEFAULT_AWS_REGION,
        "model_id": payload.get("bedrock_model_id") or MODEL_ID,
        "max_tokens": int(payload.get("bedrock_max_tokens") or 400),
        "temperature": float(payload.get("bedrock_temperature") or 0.2),
        "timeout_sec": float(payload.get("bedrock_timeout_sec") or 8.0),
    }


def _invoke_bedrock_reasoning(
    vision_output: dict, processed_evidences: list, deterministic_result: dict, cfg: dict
) -> dict:
    if not cfg.get("enabled"):
        return {}
    if boto3 is None:
        raise RuntimeError("boto3 not available for Bedrock invocation.")

    runtime = boto3.client("bedrock-runtime", region_name=cfg["region"])
    prompt_payload = {
        "vision_output": vision_output,
        "processed_evidences": processed_evidences[:20] if isinstance(processed_evidences, list) else [],
        "deterministic_result": deterministic_result,
    }
    prompt = (
        "You are an insurance claim intelligence assistant. "
        "Enhance deterministic analysis using semantic/context reasoning only. "
        "Do not replace deterministic facts. "
        "Return strict JSON with keys: "
        "consistency_additions (list[str]), suspicious_additions (list[str]), "
        "analysis_summary_additions (list[str]), confidence_adjustment (float between -0.15 and 0.15), "
        "risk_level_override (low|moderate|high|null), "
        "damage_assessment_updates (object with optional severity, estimated_damage_cost, recommended_settlement, payout_confidence, inflation_risk), "
        "assessment_notes_additions (list[str]).\n\n"
        f"Context:\n{json.dumps(prompt_payload, ensure_ascii=True)}"
    )
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": cfg["max_tokens"],
        "temperature": cfg["temperature"],
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    }
    response = runtime.invoke_model(modelId=cfg["model_id"], body=json.dumps(body))
    raw = response.get("body").read() if response.get("body") else b"{}"
    parsed = json.loads(raw.decode("utf-8"))
    content = parsed.get("content") or []
    text = ""
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text", "")
            break
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"{.*}", text, re.DOTALL)
        return json.loads(m.group(0)) if m else {}


def _merge_reasoning(deterministic: dict, reasoning: dict) -> dict:
    merged = dict(deterministic or {})

    consistency = list(merged.get("consistency_checks") or [])
    suspicious = list(merged.get("suspicious_indicators") or [])
    summary = list(merged.get("analysis_summary") or [])

    for item in reasoning.get("consistency_additions") or []:
        if isinstance(item, str) and item and item not in consistency:
            consistency.append(item)
    for item in reasoning.get("suspicious_additions") or []:
        if isinstance(item, str) and item and item not in suspicious:
            suspicious.append(item)
    for item in reasoning.get("analysis_summary_additions") or []:
        if isinstance(item, str) and item and item not in summary:
            summary.append(item)

    base_conf = float(merged.get("claim_confidence") or merged.get("confidence") or 0.0)
    try:
        adjustment = float(reasoning.get("confidence_adjustment") or 0.0)
    except Exception:
        adjustment = 0.0
    adjustment = max(-0.15, min(0.15, adjustment))
    claim_confidence = max(0.0, min(1.0, base_conf + adjustment))

    risk_level = merged.get("risk_level") or "high"
    override = reasoning.get("risk_level_override")
    if override in {"low", "moderate", "high"}:
        risk_level = override
    else:
        if claim_confidence >= 0.8:
            risk_level = "low"
        elif claim_confidence >= 0.5:
            risk_level = "moderate"
        else:
            risk_level = "high"

    merged["claim_confidence"] = round(claim_confidence, 2)
    merged["confidence"] = round(claim_confidence, 2)
    merged["risk_level"] = risk_level
    merged["consistency_checks"] = consistency
    merged["suspicious_indicators"] = suspicious
    merged["analysis_summary"] = summary
    merged["anomalies_detected"] = bool(suspicious)
    merged["anomaly_type"] = suspicious[:]
    merged["fraud_score"] = round(1.0 - claim_confidence, 2)
    merged["verdict"] = "suspicious" if risk_level == "high" else "valid"
    merged["reason"] = "; ".join(summary[:3]) if summary else "No strong risk indicators detected."
    merged["damage_assessment"] = merge_estimation_reasoning(merged.get("damage_assessment") or {}, reasoning or {})
    return merged


FORENSIC_PROMPT = """You are an Insurance Claim Analysis & Risk Validation Agent.

Your job is to analyze claim consistency, evidence quality, anomaly indicators, risk indicators, and cross-evidence validation.

IMPORTANT:
- Do NOT make hard fraud accusations.
- Be explainable and deterministic.
- Use only the provided structured outputs from the Vision Agent and evidence metadata.

OUTPUT FORMAT (STRICT JSON ONLY):
{
  "claim_confidence": float (0 to 1),
  "risk_level": "low" | "moderate" | "high",
  "consistency_checks": [list of strings],
  "suspicious_indicators": [list of strings],
  "analysis_summary": [list of strings],
  "confidence": float (0 to 1)
}
If output is not valid JSON, regenerate until it is valid.
"""


async def run(input: dict) -> dict:
    start_time = time.time()
    bedrock_cfg = _bedrock_runtime_config(input)
    strand_meta = _forensic_execution_meta(bool(bedrock_cfg.get("enabled")))
    try:
        image_url = input.get("image_url")
        vision_output = input.get("vision_output") or {}
        processed_evidences = input.get("processed_evidences")
        domain = (vision_output.get("domain") or "unknown").lower()

        print(
            "Forensic config:",
            {
                "aws_enabled": _to_bool(os.getenv("CLAIMFLOW_AWS_ENABLED"), False),
                "bedrock_enabled": bool(bedrock_cfg.get("enabled")),
                "domain": domain,
            },
        )

        # Backward compatibility: support legacy single-image input.
        if processed_evidences is None and image_url:
            processed_evidences = [{"type": "image", "path": image_url}]

        if processed_evidences is None:
            return {
                "success": False,
                "data": {
                    "claim_confidence": 0.0,
                    "risk_level": "high",
                    "consistency_checks": ["No evidences provided for analysis."],
                    "suspicious_indicators": [],
                    "analysis_summary": ["No input provided for analysis."],
                    "confidence": 0.0,
                },
                "error": "Missing required field: processed_evidences (or legacy image_url)",
                "meta": {
                    "latency_sec": round(time.time() - start_time, 4),
                    "fallback_used": False,
                    "bedrock_mode_used": False,
                    "strand_name": strand_meta["strand_name"],
                    "strand_version": strand_meta["strand_version"],
                    "execution_mode": strand_meta["execution_mode"],
                    "reasoning_mode": strand_meta["reasoning_mode"],
                    "strand_capabilities": strand_meta["strand_capabilities"],
                },
            }

        def _infer_media_type(url: str) -> str:
            path = urlparse(url).path.lower()
            if path.endswith(".png"):
                return "image/png"
            if path.endswith(".webp"):
                return "image/webp"
            if path.endswith(".gif"):
                return "image/gif"
            return "image/jpeg"

        def _extract_json_dict(text: str) -> dict:
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
            match = re.search(r"{.*}", text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            raise json.JSONDecodeError("No valid JSON object found", text, 0)

        def _validate_required_keys(data: dict) -> None:
            required = {
                "claim_confidence",
                "risk_level",
                "consistency_checks",
                "suspicious_indicators",
                "analysis_summary",
                "confidence",
                "damage_assessment",
            }
            if not required.issubset(data.keys()):
                missing = sorted(required - set(data.keys()))
                raise ValueError(f"Missing required keys: {', '.join(missing)}")

        def _invoke_model() -> tuple[dict, bool, bool]:
            # Step 1: deterministic baseline (always available).
            context = {"vision_output": vision_output, "processed_evidences": processed_evidences}
            deterministic_text = _run_deterministic_analysis(f"{json.dumps(context)}\n{FORENSIC_PROMPT}")
            deterministic_data = _extract_json_dict(deterministic_text)
            _validate_required_keys(deterministic_data)

            # Step 2: optional Bedrock semantic augmentation.
            if not bedrock_cfg.get("enabled"):
                print("Bedrock activation: skipped (bedrock_enabled is false)")
                print("Forensic reasoning mode: deterministic only")
                return deterministic_data, False, False

            try:
                print("Bedrock activation: executing hybrid branch")
                reasoning = _invoke_bedrock_reasoning(vision_output, processed_evidences, deterministic_data, bedrock_cfg)
                merged = _merge_reasoning(deterministic_data, reasoning if isinstance(reasoning, dict) else {})
                _validate_required_keys(merged)
                print("Forensic reasoning mode: deterministic + bedrock")
                return merged, True, False
            except Exception as exc:
                print(f"Bedrock fallback triggered: {exc}")
                return deterministic_data, True, True

        try:
            data, bedrock_mode_used, fallback_used = await asyncio.to_thread(_invoke_model)
        except Exception as exc:
            return {
                "success": False,
                "data": {},
                "error": f"Model call failed: {exc}",
                "meta": {
                    "latency_sec": round(time.time() - start_time, 4),
                    "fallback_used": False,
                    "bedrock_mode_used": False,
                    "strand_name": strand_meta["strand_name"],
                    "strand_version": strand_meta["strand_version"],
                    "execution_mode": strand_meta["execution_mode"],
                    "reasoning_mode": strand_meta["reasoning_mode"],
                    "strand_capabilities": strand_meta["strand_capabilities"],
                },
            }

        if not isinstance(data, dict):
            return {
                "success": False,
                "data": {},
                "error": "Model response is not a valid JSON object",
                "meta": {
                    "latency_sec": round(time.time() - start_time, 4),
                    "fallback_used": False,
                    "bedrock_mode_used": False,
                    "strand_name": strand_meta["strand_name"],
                    "strand_version": strand_meta["strand_version"],
                    "execution_mode": strand_meta["execution_mode"],
                    "reasoning_mode": strand_meta["reasoning_mode"],
                    "strand_capabilities": strand_meta["strand_capabilities"],
                },
            }

        return {
            "success": True,
            "data": data,
            "error": None,
            "meta": {
                "latency_sec": round(time.time() - start_time, 4),
                "fallback_used": fallback_used,
                "bedrock_mode_used": bedrock_mode_used,
                "strand_name": strand_meta["strand_name"],
                "strand_version": strand_meta["strand_version"],
                "execution_mode": strand_meta["execution_mode"],
                "reasoning_mode": strand_meta["reasoning_mode"],
                "strand_capabilities": strand_meta["strand_capabilities"],
            },
        }
    except (json.JSONDecodeError, ValueError) as exc:
        fallback = {
            "confidence": 0.0,
            "claim_confidence": 0.0,
            "risk_level": "high",
            "consistency_checks": ["Fallback response due to invalid model JSON output."],
            "suspicious_indicators": [],
            "analysis_summary": ["Fallback response due to invalid model JSON output."],
            "damage_assessment": {
                "severity": "unknown",
                "estimated_damage_cost": 0.0,
                "recommended_settlement": 0.0,
                "payout_confidence": 0.0,
                "inflation_risk": "unknown",
                "assessment_notes": ["Fallback assessment due to invalid model JSON output."],
            },
        }
        return {
            "success": True,
            "data": fallback,
            "error": f"JSON parsing failed: {exc}",
            "meta": {
                "latency_sec": round(time.time() - start_time, 4),
                "fallback_used": True,
                "bedrock_mode_used": bool(bedrock_cfg.get("enabled")),
                "strand_name": strand_meta["strand_name"],
                "strand_version": strand_meta["strand_version"],
                "execution_mode": strand_meta["execution_mode"],
                "reasoning_mode": strand_meta["reasoning_mode"],
                "strand_capabilities": strand_meta["strand_capabilities"],
            },
        }
    except Exception as exc:
        return {
            "success": False,
            "data": {},
            "error": str(exc),
            "meta": {
                "latency_sec": round(time.time() - start_time, 4),
                "fallback_used": False,
                "bedrock_mode_used": bool(bedrock_cfg.get("enabled")),
                "strand_name": strand_meta["strand_name"],
                "strand_version": strand_meta["strand_version"],
                "execution_mode": strand_meta["execution_mode"],
                "reasoning_mode": strand_meta["reasoning_mode"],
                "strand_capabilities": strand_meta["strand_capabilities"],
            },
        }


if __name__ == "__main__":
    import asyncio

    test_input = {
        "vision_output": {
            "domain": "health",
            "document_type": "hospital_bill",
            "structured_data": {
                "patient_name": "Pankaj Kumar",
                "bill_number": "NOI-ICS-27146",
                "bill_amount": 57450.0,
                "admission_date": "15-Oct-2024",
                "discharge_date": "17-Oct-2024",
            },
            "visual_indicators": [],
        },
        "processed_evidences": [{"type": "hospital_bill", "path": "hospital.png"}],
        "bedrock_enabled": True,
        "aws_region": "us-east-1",
        "bedrock_model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "bedrock_max_tokens": 120,
        "bedrock_temperature": 0.1,
    }

    result = asyncio.run(run(test_input))

    print("\n=== FORENSIC OUTPUT ===")
    print(result)
