from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from backend.core.security import get_current_user, require_role
from backend.services.identity_service import IdentityVerificationService
from backend.database.mock_db import db

router = APIRouter(prefix="/agents", tags=["agents"])
identity_service = IdentityVerificationService(db)

@router.post("/verify")
def verify_identity(document_data: dict, current_user: dict = Depends(get_current_user)):
    """Allows an unverified agent to submit mock documents to become verified."""
    if current_user.get("role") != "agent":
        raise HTTPException(status_code=403, detail="Only agents can verify identity")
    
    return identity_service.verify_agent(current_user["id"], document_data)

@router.post("/verify-id-proof")
async def verify_id_proof(
    id_type: str = Form(...),
    id_number: str = Form(...),
    proof: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload ID proof for an agent and verify with the future vision agent integration."""
    if current_user.get("role") != "agent":
        raise HTTPException(status_code=403, detail="Only agents can verify identity")

    return await identity_service.verify_agent_with_id_proof(
        current_user["id"],
        id_type,
        id_number,
        proof,
    )

@router.get("/sensitive-data")
def get_sensitive_data(current_user: dict = Depends(require_role("agent"))):
    """Only accessible by agents who have a verified=True status."""
    return {"message": "Access granted to sensitive agent information."}    

@router.get("/profile")
def get_agent_profile(current_user: dict = Depends(get_current_user)):
    """
    Allows any agent (verified or unverified) to view their profile.
    Fetches fresh data from the database to reflect current verification status.
    """
    if current_user.get("role") != "agent":
        raise HTTPException(status_code=403, detail="Only agents can access this endpoint")
    
    # Fetch fresh user data from the database using the ID from the token
    agent = db.get_by_id(current_user["id"])
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    return {
        "id": agent.id,
        "username": agent.username,
        "email": agent.email,
        "role": agent.role,
        "verified": agent.verified
    }