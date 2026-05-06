"""
Advisors router — /advisors

Provides:
  GET  /advisors       — list available expert advisors (authenticated)
  POST /advisors/book  — book a consultation with a specific advisor
"""

import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from backend.core.security import get_current_user

router = APIRouter(prefix="/advisors", tags=["advisors"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class BookingRequest(BaseModel):
    advisor_id: int
    advisor_name: str
    specialty: str
    policy_type: Optional[str] = None
    policy_number: Optional[str] = None
    recommended_plan: Optional[str] = None


class BookingResponse(BaseModel):
    booking_id: str
    status: str
    message: str


# ── Static advisor catalogue ──────────────────────────────────────────────────
# Replace with a DB query when the advisors table is ready.

ADVISORS = [
    {"id": 1,  "name": "Dr. Aris Thorne",   "specialty": "Financial Strategy",    "badge": "15+ years exp",  "badge_icon": "stars"},
    {"id": 2,  "name": "Sarah Jenkins",      "specialty": "Marketing Growth",      "badge": "Top Rated",      "badge_icon": "verified"},
    {"id": 3,  "name": "Marcus Holloway",    "specialty": "Software Architecture", "badge": "Cloud Expert",   "badge_icon": "cloud_done"},
    {"id": 4,  "name": "Elena Rodriguez",    "specialty": "Legal Counsel",         "badge": "Corporate Law",  "badge_icon": "gavel"},
    {"id": 5,  "name": "David Chen",         "specialty": "Operations Management", "badge": "Efficiency Pro", "badge_icon": "speed"},
    {"id": 6,  "name": "Sophia Williams",    "specialty": "HR Relations",          "badge": "Talent Scout",   "badge_icon": "groups"},
    {"id": 7,  "name": "Jameson Vance",      "specialty": "Supply Chain",          "badge": "Logistics Lead", "badge_icon": "inventory_2"},
    {"id": 8,  "name": "Dr. Linda Wu",       "specialty": "Data Science",          "badge": "AI Specialist",  "badge_icon": "insights"},
    {"id": 9,  "name": "Robert Green",       "specialty": "Sustainability",        "badge": "ESG Consultant", "badge_icon": "eco"},
    {"id": 10, "name": "Monica Geller",      "specialty": "Executive Coaching",    "badge": "ICF Certified",  "badge_icon": "psychology"},
]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def list_advisors(current_user: dict = Depends(get_current_user)):
    """Return the full advisor catalogue. Requires authentication."""
    return {"advisors": ADVISORS}


@router.post("/book", response_model=BookingResponse)
def book_consultation(
    payload: BookingRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Book a consultation with a specific advisor.
    Generates a booking reference and returns a confirmation.
    In production, persist to DB and trigger calendar/email notifications.
    """
    booking_id = f"BK-{uuid.uuid4().hex[:8].upper()}"

    return BookingResponse(
        booking_id=booking_id,
        status="confirmed",
        message=(
            f"Your consultation with {payload.advisor_name} ({payload.specialty}) "
            f"has been confirmed. Booking ref: {booking_id}."
        ),
    )
