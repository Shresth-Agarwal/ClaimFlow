# ClaimFlow — Claims Router
# Comprehensive API endpoints for claims processing with DynamoDB integration

import uuid
import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List

from backend.core.security import get_current_user
from backend.graph.state import create_initial_state
from backend.graph.pipeline import run_claim_pipeline, resume_claim_pipeline
from backend.services.dynamodb_service import get_db_service
from backend.services.pdf_service import generate_claim_pdf

logger = logging.getLogger("claimflow.routes.claims")
router = APIRouter(prefix="/api/claims", tags=["Claims"])
adjuster_router = APIRouter(prefix="/api/adjuster", tags=["Adjuster"])

# Get DynamoDB service
db_service = get_db_service()


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST / RESPONSE SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class ClaimSubmitRequest(BaseModel):
    claim_type:             str                     # "motor" | "health" | "crop" | "property"
    description:            str
    # Motor specific
    vehicle_make:           Optional[str] = None
    vehicle_year:           Optional[int] = None
    vehicle_reg:            Optional[str] = None
    # Health specific
    procedure_code:         Optional[str] = None
    billed_amount:          Optional[float] = None
    hospital_name:          Optional[str] = None
    # Common
    incident_date:          Optional[str] = None
    incident_location:      Optional[str] = None
    policy_number:          Optional[str] = None
    days_since_incident:    Optional[int] = 0
    language:               Optional[str] = "en"


class AdjusterDecisionRequest(BaseModel):
    decision: str                                   # "approve" | "reject"
    notes:    Optional[str] = ""


class ClaimStatusResponse(BaseModel):
    claim_id:           str
    status:             str
    routing_decision:   str
    fraud_score:        Optional[float]
    damage_estimate:    Optional[float]
    settlement_amount:  Optional[float]
    created_at:         str
    updated_at:         str


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 1 — SUBMIT CLAIM (JSON)
# POST /api/claims/submit
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/submit", status_code=202)
async def submit_claim(
    body: ClaimSubmitRequest,
    current_user: dict = Depends(get_current_user),
):
    """Submit a new claim with structured data."""
    claim_id = f"CLM-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    user_id = str(current_user.get("user_id") or current_user.get("id", ""))

    raw_input = body.model_dump(exclude_none=True)
    raw_input["submitted_at"] = datetime.now(timezone.utc).isoformat()

    initial_state = create_initial_state(
        claim_id=claim_id,
        claim_type=body.claim_type,
        user_id=user_id,
        nationality=current_user.get("nationality", "IN"),
        country_of_residence=current_user.get("country_of_residence", "IN"),
        raw_input=raw_input,
    )

    # Save initial record to DynamoDB
    await db_service.save_claim({
        "claim_id": claim_id,
        "user_id": user_id,
        "claim_type": body.claim_type,
        "status": "processing",
        "description": body.description,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    logger.info(f"[{claim_id}] Claim submitted by user {user_id}")

    try:
        # Run the pipeline
        final_state = await run_claim_pipeline(initial_state)

        routing = final_state.get("routing_decision", "human_queue")
        status = final_state.get("final_status", "pending_review")
        settlement = final_state.get("settlement_amount_inr")

        # Update DynamoDB with results
        await db_service.update_claim(claim_id, {
            "status": status,
            "routing_decision": routing,
            "fraud_score": (final_state.get("forensic_result") or {}).get("fraud_score"),
            "damage_estimate": (final_state.get("vision_result") or {}).get("damage_estimate_inr"),
            "settlement_amount_inr": settlement,
            "vision_result": final_state.get("vision_result"),
            "forensic_result": final_state.get("forensic_result"),
            "policy_result": final_state.get("policy_result"),
            "audit_trail": final_state.get("audit_trail", []),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "claim_id": claim_id,
            "status": status,
            "routing_decision": routing,
            "fraud_score": (final_state.get("forensic_result") or {}).get("fraud_score"),
            "damage_estimate": (final_state.get("vision_result") or {}).get("damage_estimate_inr"),
            "settlement_amount": settlement,
            "message": _decision_message(routing),
        }

    except Exception as e:
        logger.error(f"[{claim_id}] Pipeline error: {e}", exc_info=True)
        await db_service.update_claim(claim_id, {"status": "error", "error": str(e)})
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 2 — SUBMIT CLAIM WITH DOCUMENTS
# POST /api/claims/submit-with-documents
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/submit-with-documents", status_code=202)
async def submit_claim_with_documents(
    claim_type: str = Form(...),
    description: str = Form(...),
    vehicle_make: Optional[str] = Form(None),
    vehicle_year: Optional[int] = Form(None),
    vehicle_reg: Optional[str] = Form(None),
    policy_number: Optional[str] = Form(None),
    incident_date: Optional[str] = Form(None),
    incident_location: Optional[str] = Form(None),
    language: Optional[str] = Form("en"),
    documents: List[UploadFile] = File(...),
    audio_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """Submit claim with document uploads and optional voice input."""
    claim_id = f"CLM-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    user_id = str(current_user.get("user_id") or current_user.get("id", ""))

    # Save uploaded documents to S3
    import boto3
    s3_client = boto3.client('s3')
    s3_bucket = os.getenv("CLAIMFLOW_S3_BUCKET")
    
    document_s3_uris = []
    audio_s3_uri = None
    
    try:
        # Upload documents
        for i, doc in enumerate(documents):
            doc_bytes = await doc.read()
            s3_key = f"claims/{claim_id}/documents/{i}_{doc.filename}"
            
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=doc_bytes,
                ContentType=doc.content_type or 'application/octet-stream'
            )
            
            document_s3_uris.append(f"s3://{s3_bucket}/{s3_key}")
        
        # Upload audio if provided
        if audio_file:
            audio_bytes = await audio_file.read()
            audio_s3_key = f"claims/{claim_id}/audio/{audio_file.filename}"
            
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=audio_s3_key,
                Body=audio_bytes,
                ContentType=audio_file.content_type or 'audio/wav'
            )
            
            audio_s3_uri = f"s3://{s3_bucket}/{audio_s3_key}"

        # Build raw input
        raw_input = {
            "claim_type": claim_type,
            "description": description,
            "vehicle_make": vehicle_make,
            "vehicle_year": vehicle_year,
            "vehicle_reg": vehicle_reg,
            "policy_number": policy_number,
            "incident_date": incident_date,
            "incident_location": incident_location,
            "language": language,
            "document_s3_uris": document_s3_uris,
            "audio_s3_uri": audio_s3_uri,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }

        initial_state = create_initial_state(
            claim_id=claim_id,
            claim_type=claim_type,
            user_id=user_id,
            nationality=current_user.get("nationality", "IN"),
            country_of_residence=current_user.get("country_of_residence", "IN"),
            raw_input=raw_input,
        )

        # Save initial record
        await db_service.save_claim({
            "claim_id": claim_id,
            "user_id": user_id,
            "claim_type": claim_type,
            "status": "processing",
            "description": description,
            "document_count": len(documents),
            "has_audio": audio_file is not None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        # Run pipeline
        final_state = await run_claim_pipeline(initial_state)

        routing = final_state.get("routing_decision", "human_queue")
        status = final_state.get("final_status", "pending_review")
        settlement = final_state.get("settlement_amount_inr")

        # Update with results
        await db_service.update_claim(claim_id, {
            "status": status,
            "routing_decision": routing,
            "fraud_score": (final_state.get("forensic_result") or {}).get("fraud_score"),
            "damage_estimate": (final_state.get("vision_result") or {}).get("damage_estimate_inr"),
            "settlement_amount_inr": settlement,
            "vision_result": final_state.get("vision_result"),
            "forensic_result": final_state.get("forensic_result"),
            "policy_result": final_state.get("policy_result"),
            "inclusion_result": final_state.get("inclusion_result"),
            "audit_trail": final_state.get("audit_trail", []),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "claim_id": claim_id,
            "status": status,
            "routing_decision": routing,
            "fraud_score": (final_state.get("forensic_result") or {}).get("fraud_score"),
            "damage_estimate": (final_state.get("vision_result") or {}).get("damage_estimate_inr"),
            "settlement_amount": settlement,
            "documents_processed": len(documents),
            "audio_processed": audio_file is not None,
            "message": _decision_message(routing),
        }

    except Exception as e:
        logger.error(f"[{claim_id}] Document processing error: {e}", exc_info=True)
        await db_service.update_claim(claim_id, {"status": "error", "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 3 — GET CLAIM STATUS
# GET /api/claims/{claim_id}/status
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{claim_id}/status", response_model=ClaimStatusResponse)
async def get_claim_status(
    claim_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get current status of a claim."""
    claim = await db_service.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Access control
    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    if current_user["role"] == "user" and claim["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return ClaimStatusResponse(
        claim_id=claim_id,
        status=claim.get("status", "processing"),
        routing_decision=claim.get("routing_decision", "pending"),
        fraud_score=claim.get("fraud_score"),
        damage_estimate=claim.get("damage_estimate"),
        settlement_amount=claim.get("settlement_amount_inr"),
        created_at=claim.get("created_at", ""),
        updated_at=claim.get("updated_at", ""),
    )


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 4 — GET FULL CLAIM REPORT
# GET /api/claims/{claim_id}/report
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{claim_id}/report")
async def get_claim_report(
    claim_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get comprehensive claim report."""
    claim = await db_service.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    if current_user["role"] == "user" and claim["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return claim


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 5 — GENERATE PDF REPORT
# GET /api/claims/{claim_id}/pdf
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{claim_id}/pdf")
async def generate_claim_pdf_report(
    claim_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Generate and return PDF report download URL."""
    claim = await db_service.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    if current_user["role"] == "user" and claim["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Generate PDF and get download URL
        pdf_url = await generate_claim_pdf(claim)
        
        return {
            "claim_id": claim_id,
            "pdf_url": pdf_url,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "expires_in": "7 days"
        }
        
    except Exception as e:
        logger.error(f"PDF generation failed for claim {claim_id}: {e}")
        raise HTTPException(status_code=500, detail="PDF generation failed")


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 6 — GET USER'S CLAIMS
# GET /api/claims/my-claims
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/my-claims")
async def get_my_claims(
    current_user: dict = Depends(get_current_user),
):
    """Get all claims for the current user."""
    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    claims = await db_service.get_claims_by_user(user_id)
    
    # Sort by creation date (newest first)
    claims.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {
        "claims": claims,
        "total_count": len(claims)
    }


# ─────────────────────────────────────────────────────────────────────────────
# ADJUSTER ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@adjuster_router.get("/queue")
async def get_adjuster_queue(current_user: dict = Depends(get_current_user)):
    """Get all claims pending human review."""
    if current_user["role"] not in ["agent", "admin"]:
        raise HTTPException(status_code=403, detail="Agent access required")

    pending_claims = await db_service.get_claims_by_status("pending_review")
    
    # Sort by creation date (oldest first for FIFO processing)
    pending_claims.sort(key=lambda x: x.get("created_at", ""))
    
    return {
        "queue": pending_claims,
        "count": len(pending_claims)
    }


@adjuster_router.post("/{claim_id}/decision")
async def adjuster_decision(
    claim_id: str,
    body: AdjusterDecisionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Submit adjuster decision and resume pipeline."""
    if current_user["role"] not in ["agent", "admin"]:
        raise HTTPException(status_code=403, detail="Agent access required")

    if body.decision not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Decision must be 'approve' or 'reject'")

    claim = await db_service.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    adjuster_id = str(current_user.get("user_id") or current_user.get("id", ""))
    logger.info(f"[{claim_id}] Adjuster {adjuster_id} decided: {body.decision}")

    try:
        # Resume pipeline with adjuster decision
        final_state = await resume_claim_pipeline(
            claim_id=claim_id,
            adjuster_decision=body.decision,
            adjuster_notes=body.notes or "",
        )

        # Update claim with final results
        await db_service.update_claim(claim_id, {
            "status": final_state.get("final_status"),
            "adjuster_id": adjuster_id,
            "adjuster_decision": body.decision,
            "adjuster_notes": body.notes,
            "settlement_amount_inr": final_state.get("settlement_amount_inr"),
            "decided_at": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "claim_id": claim_id,
            "final_status": final_state.get("final_status"),
            "settlement_amount": final_state.get("settlement_amount_inr"),
            "message": f"Claim {body.decision}d successfully",
        }

    except Exception as e:
        logger.error(f"[{claim_id}] Resume pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _decision_message(decision: str) -> str:
    """Get user-friendly message for routing decision."""
    return {
        "auto_approve": "Your claim has been automatically approved. You will be notified shortly.",
        "human_queue": "Your claim is under review by our team. We will notify you within 24 hours.",
        "reject": "Your claim could not be approved at this time. Please contact your advisor.",
        "investigate": "Your claim is undergoing additional verification.",
    }.get(decision or "", "Claim submitted successfully.")