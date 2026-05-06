# backend/database/mock_claims_db.py
# In-memory claims store — used when USE_MOCK_DB=true or DynamoDB is unavailable.
# Mirrors the exact same async API as dynamo_db.py claim functions.

import logging
from typing import Optional

logger = logging.getLogger("claimflow.mock_claims_db")

# Simple in-memory store: claim_id → claim dict
_claims: dict[str, dict] = {}


async def save_claim(item: dict) -> None:
    claim_id = item.get("claim_id", "unknown")
    _claims[claim_id] = dict(item)
    logger.info(f"[mock] save_claim: {claim_id}")


async def get_claim(claim_id: str) -> Optional[dict]:
    return _claims.get(claim_id)


async def update_claim(claim_id: str, updates: dict) -> None:
    if claim_id not in _claims:
        _claims[claim_id] = {"claim_id": claim_id}
    _claims[claim_id].update(updates)
    logger.info(f"[mock] update_claim: {claim_id} — fields: {list(updates.keys())}")


async def get_claims_by_status(status: str) -> list:
    return [c for c in _claims.values() if c.get("status") == status]
