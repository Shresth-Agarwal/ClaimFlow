# backend/graph/state.py
# ClaimFlow — LangGraph State Definition
# Shresth owns this file.
#
# Shared memory object that flows through every node in the pipeline.
# LangGraph checkpoints this to DynamoDB after every node.
#
# AWS Services:
#   DynamoDB     — checkpointer stores pipeline progress here
#   Agent Core   — session_id links to Bedrock Agent Core for chatbot memory

import operator
from datetime import datetime, timezone
from typing import Annotated


def create_initial_state(
    claim_id: str,
    claim_type: str,
    user_id: str,
    nationality: str,
    country_of_residence: str,
    raw_input: dict,
) -> dict:
    """
    Returns a fresh state dict for a new claim.
    Call this in POST /api/claims/submit before invoking the graph.

    claim_type           : "motor" | "health" | "crop" | "property"
    nationality          : ISO code — "IN", "GB", "AE", "US"
    country_of_residence : determines which regulatory PDF RAG loads

    Example:
        state = create_initial_state(
            claim_id             = "CLM-20260506-8821",
            claim_type           = "motor",
            user_id              = "user-abc123",
            nationality          = "IN",
            country_of_residence = "GB",
            raw_input = {
                "photo_s3_key":        "claims/CLM-20260506-8821/photo.jpg",
                "vehicle_make":        "Maruti Swift",
                "vehicle_year":        2021,
                "policy_number":       "POL-9988",
                "days_since_incident": 3,
            }
        )
    """
    return {
        # ── Identity ───────────────────────────────────────────────────────
        "claim_id":               claim_id,
        "claim_type":             claim_type,
        "session_id":             claim_id,   # same value — used as Agent Core session ID

        # ── Claimant context ───────────────────────────────────────────────
        "user_id":                user_id,
        "nationality":            nationality,
        "country_of_residence":   country_of_residence,

        # ── Raw input ──────────────────────────────────────────────────────
        "raw_input":              raw_input,

        # ── Agent results (None until each node writes its result) ─────────
        "inclusion_result":       None,   # Praharshitha: voice → structured fields
        "vision_result":          None,   # Srivalli:     Strands damage estimate
        "forensic_result":        None,   # Srivalli:     fraud score 0–100
        "policy_result":          None,   # Praharshitha: RAG policy audit

        # ── Investigator loop ──────────────────────────────────────────────
        "investigator_iteration": 0,      # increments each loop, max 3
        "investigator_challenge": None,   # focused re-examination prompt

        # ── Router output ──────────────────────────────────────────────────
        "routing_decision":       "human_queue",

        # ── Human review ───────────────────────────────────────────────────
        "adjuster_decision":      None,   # "approve" | "reject"
        "adjuster_notes":         None,

        # ── Final ──────────────────────────────────────────────────────────
        "final_status":           None,   # "approved" | "rejected" | "pending"
        "settlement_amount_inr":  None,

        # ── Audit trail ────────────────────────────────────────────────────
        # operator.add tells LangGraph to MERGE lists across node updates
        # so every node's entries accumulate — nothing gets overwritten
        "audit_trail":            [],
    }


def audit_entry(node_name: str, message: str) -> dict:
    """Creates one audit trail entry. Import and use inside every node."""
    return {
        "node":      node_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message":   message,
    }