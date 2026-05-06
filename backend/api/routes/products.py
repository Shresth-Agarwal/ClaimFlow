"""
Products router — /products

Provides:
  GET  /products            — list all insurance product domains (public)
  POST /products/recommend  — AI-driven plan recommendation based on claim context
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from backend.core.security import get_current_user

router = APIRouter(prefix="/products", tags=["products"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class RecommendationRequest(BaseModel):
    policy_type: str
    policy_number: Optional[str] = None
    insured_amount: Optional[float] = None
    message_count: Optional[int] = 0


class RecommendationResponse(BaseModel):
    recommended_plan: str
    premium_estimate: str
    reasoning: str


# ── Static product catalogue ──────────────────────────────────────────────────

PRODUCTS = [
    {
        "id": "health-family-floater",
        "name": "Family Floater",
        "category": "Health & Wellness",
        "description": "Cashless hospitalisation across 10,000+ network hospitals for the whole family.",
    },
    {
        "id": "health-critical-illness",
        "name": "Critical Illness",
        "category": "Health & Wellness",
        "description": "Lump-sum payout on diagnosis of 36 critical illnesses.",
    },
    {
        "id": "health-senior-citizen",
        "name": "Senior Citizen",
        "category": "Health & Wellness",
        "description": "Tailored coverage for individuals above 60 with no pre-policy medical tests.",
    },
    {
        "id": "motor-private-car",
        "name": "Private Car",
        "category": "Motor Insurance",
        "description": "Comprehensive own-damage + third-party cover for private vehicles.",
    },
    {
        "id": "motor-two-wheeler",
        "name": "Two Wheeler",
        "category": "Motor Insurance",
        "description": "Instant policy issuance for bikes and scooters.",
    },
    {
        "id": "motor-commercial",
        "name": "Commercial Vehicle",
        "category": "Motor Insurance",
        "description": "Fleet-level coverage with dedicated claim managers.",
    },
    {
        "id": "agri-pmfby",
        "name": "PM Fasal Bima Yojana",
        "category": "Agri & Rural",
        "description": "Government-backed crop insurance against natural calamities.",
    },
    {
        "id": "property-home",
        "name": "Home Cover",
        "category": "Property & Assets",
        "description": "Structure and contents protection against fire, theft, and natural disasters.",
    },
]

# Simple rule-based recommendation map (replace with ML model call when ready)
_RECOMMENDATION_MAP = {
    "comprehensive motor": {
        "plan": "Motor Protect Plus",
        "premium": "₹2,100",
        "reason": "Based on your Comprehensive Motor claim, Motor Protect Plus offers the best own-damage ratio and fastest garage network.",
    },
    "health": {
        "plan": "Optima Restore",
        "premium": "₹1,450",
        "reason": "Optima Restore's no-claim bonus restoration feature is ideal for your health profile.",
    },
    "property": {
        "plan": "Home Shield Pro",
        "premium": "₹850",
        "reason": "Home Shield Pro covers both structure and contents with a 48-hour claim settlement SLA.",
    },
}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def list_products():
    """Return the full insurance product catalogue. No auth required."""
    return {"products": PRODUCTS}


@router.post("/recommend", response_model=RecommendationResponse)
def recommend_plan(
    payload: RecommendationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Return an AI-driven plan recommendation based on the user's claim context.
    Currently uses a rule-based lookup; swap `_RECOMMENDATION_MAP` lookup for
    an LLM/ML call when the model is ready.
    """
    key = payload.policy_type.lower()

    # Find the best matching key
    matched = None
    for k in _RECOMMENDATION_MAP:
        if k in key:
            matched = _RECOMMENDATION_MAP[k]
            break

    if not matched:
        matched = {
            "plan": "Elite Health Plus",
            "premium": "₹1,250",
            "reason": "Our most popular all-round plan based on your profile.",
        }

    return RecommendationResponse(
        recommended_plan=matched["plan"],
        premium_estimate=matched["premium"],
        reasoning=matched["reason"],
    )
