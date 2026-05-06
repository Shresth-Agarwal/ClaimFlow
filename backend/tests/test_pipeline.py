"""
ClaimFlow — LangGraph Pipeline Test Script
==========================================
Run this directly to test the full pipeline end-to-end with a local image.

Usage:
    python -m backend.tests.test_pipeline --image path/to/your/image.jpg --type health
    python -m backend.tests.test_pipeline --image path/to/your/image.jpg --type motor
    python -m backend.tests.test_pipeline --image path/to/your/image.jpg --type property
    python -m backend.tests.test_pipeline --image path/to/your/image.jpg --type crop

    # No image — runs with a text-only claim (no OCR)
    python -m backend.tests.test_pipeline --type health

Examples with the test.jpeg in the project root:
    python -m backend.tests.test_pipeline --image test.jpeg --type health
"""

import asyncio
import json
import sys
import os
import argparse
from datetime import datetime, timezone

# Make sure backend package is importable when running from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Force mock DB so no DynamoDB needed
os.environ.setdefault("USE_MOCK_DB", "true")
os.environ.setdefault("CLAIMFLOW_AWS_ENABLED", "false")


def _print_section(title: str, data):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    if isinstance(data, dict):
        print(json.dumps(data, indent=2, default=str))
    else:
        print(data)


async def run_test(image_path: str | None, claim_type: str):
    from backend.graph.state import create_initial_state
    from backend.graph.pipeline import run_claim_pipeline

    claim_id = f"TEST-{datetime.now(timezone.utc).strftime('%H%M%S')}"

    # Build raw_input — include image path if provided
    raw_input: dict = {
        "claim_type":          claim_type,
        "description":         f"Test {claim_type} claim submitted via test script",
        "policy_number":       "POL-TEST-001",
        "days_since_incident": 2,
        "language":            "en",
        "submitted_at":        datetime.now(timezone.utc).isoformat(),
    }

    if image_path:
        abs_path = os.path.abspath(image_path)
        if not os.path.exists(abs_path):
            print(f"[ERROR] Image not found: {abs_path}")
            sys.exit(1)
        raw_input["photo_local_path"] = abs_path
        print(f"\n[INFO] Using image: {abs_path}")
    else:
        print("\n[INFO] No image provided — running text-only claim (vision will return low-confidence result)")

    # Add claim-type-specific fields
    if claim_type == "motor":
        raw_input.update({
            "vehicle_make": "Maruti Swift",
            "vehicle_year": 2021,
            "vehicle_reg":  "MH01AB1234",
        })
    elif claim_type == "health":
        raw_input.update({
            "hospital_name": "City General Hospital",
            "billed_amount": 45000.0,
            "procedure_code": "HOSP-001",
        })
    elif claim_type == "property":
        raw_input.update({
            "incident_location": "Mumbai",
            "incident_date":     "2026-04-15",
        })
    elif claim_type == "crop":
        raw_input.update({
            "incident_location": "Punjab",
            "incident_date":     "2026-04-10",
        })

    initial_state = create_initial_state(
        claim_id             = claim_id,
        claim_type           = claim_type,
        user_id              = "test-user-001",
        nationality          = "IN",
        country_of_residence = "IN",
        raw_input            = raw_input,
    )

    print(f"\n[INFO] Starting pipeline for claim: {claim_id}")
    print(f"[INFO] Claim type: {claim_type}")
    print(f"[INFO] Pipeline nodes: inclusion → vision → forensic → policy → guardrail → router → ...")

    try:
        final_state = await run_claim_pipeline(initial_state)
    except Exception as e:
        print(f"\n[FATAL] Pipeline crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ── Print results ──────────────────────────────────────────────────────────
    print(f"\n{'#'*60}")
    print(f"  PIPELINE COMPLETE — {claim_id}")
    print(f"{'#'*60}")

    routing  = final_state.get("routing_decision", "unknown")
    status   = final_state.get("final_status", "unknown")
    estimate = (final_state.get("vision_result") or {}).get("damage_estimate_inr")
    fraud    = (final_state.get("forensic_result") or {}).get("fraud_score")

    print(f"\n  Routing Decision : {routing.upper()}")
    print(f"  Final Status     : {status}")
    print(f"  Damage Estimate  : ₹{estimate:,.0f}" if estimate else "  Damage Estimate  : N/A")
    print(f"  Fraud Score      : {fraud}/100" if fraud is not None else "  Fraud Score      : N/A")

    _print_section("VISION AGENT OUTPUT", final_state.get("vision_result") or {})
    _print_section("FORENSIC AGENT OUTPUT", final_state.get("forensic_result") or {})
    _print_section("POLICY AUDITOR OUTPUT", final_state.get("policy_result") or {})

    # Audit trail
    print(f"\n{'='*60}")
    print("  AUDIT TRAIL (node-by-node)")
    print(f"{'='*60}")
    for entry in (final_state.get("audit_trail") or []):
        ts   = entry.get("timestamp", "")[-8:]   # just HH:MM:SS
        node = entry.get("node", "?").ljust(22)
        msg  = entry.get("message", "")
        print(f"  [{ts}] {node} → {msg}")

    # Simple summary from forensic
    simple = (final_state.get("forensic_result") or {}).get("simple_summary") or {}
    if simple:
        _print_section("SIMPLE SUMMARY (for UI)", simple)

    print(f"\n{'#'*60}")
    print(f"  TEST COMPLETE")
    print(f"{'#'*60}\n")

    return final_state


def main():
    parser = argparse.ArgumentParser(description="Test the ClaimFlow LangGraph pipeline")
    parser.add_argument("--image", type=str, default=None,
                        help="Path to image file (jpg/png). Use test.jpeg in project root.")
    parser.add_argument("--type",  type=str, default="health",
                        choices=["health", "motor", "crop", "property"],
                        help="Claim type (default: health)")
    args = parser.parse_args()

    asyncio.run(run_test(args.image, args.type))


if __name__ == "__main__":
    main()
