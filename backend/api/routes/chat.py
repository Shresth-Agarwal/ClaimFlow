"""
ClaimFlow Chat API
==================
Unified chat interface that handles:
1. Conversational queries (policy questions, status checks, help)
2. Claim submissions with documents/voice (triggers LangGraph pipeline)
3. Session management with DynamoDB storage
"""

import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List

from backend.core.security import get_current_user
from backend.agents.chat_agent import handle_chat_query
from backend.services.dynamodb_service import get_db_service
from backend.graph.state import create_initial_state
from backend.graph.pipeline import run_claim_pipeline

logger = logging.getLogger("claimflow.chat")
router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Get services
db_service = get_db_service()


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST/RESPONSE SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    claim_id: Optional[str] = None
    requires_pipeline: bool = False
    suggested_actions: List[str] = []
    conversation_history: List[dict] = []


# ─────────────────────────────────────────────────────────────────────────────
# SESSION MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

async def _get_or_create_session(session_id: Optional[str], user_id: str) -> tuple[str, dict]:
    """Get existing session or create new one."""
    if not session_id:
        session_id = f"chat-{uuid.uuid4().hex[:8]}"
    
    session = await db_service.get_session(session_id)
    
    if not session:
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "conversation_history": [],
            "context": {}
        }
        await db_service.save_session(session)
    
    return session_id, session


async def _add_to_history(session_id: str, user_message: str, bot_response: str, intent: str):
    """Add exchange to conversation history."""
    new_exchange = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_message": user_message,
        "bot_response": bot_response,
        "intent": intent
    }
    
    # Get current session
    session = await db_service.get_session(session_id)
    if session:
        history = session.get("conversation_history", [])
        history.append(new_exchange)
        
        # Keep only last 20 exchanges
        if len(history) > 20:
            history = history[-20:]
        
        await db_service.update_session(session_id, {
            "conversation_history": history
        })


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 1 — SIMPLE CHAT (text only)
# POST /api/chat/message
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    body: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    """
    Main chat endpoint for text-only conversations.
    Handles policy questions, status checks, help, etc.
    """
    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    session_id, session = await _get_or_create_session(body.session_id, user_id)
    
    logger.info(f"[chat] {session_id}: {body.message[:50]}...")
    
    try:
        # Process message through chat agent
        result = await handle_chat_query(
            user_message=body.message,
            user_id=user_id,
            session_context=session.get("context", {})
        )
        
        # Update session history
        await _add_to_history(session_id, body.message, result["response"], result["intent"])
        
        # Get recent history for response
        updated_session = await db_service.get_session(session_id)
        recent_history = (updated_session.get("conversation_history", []))[-5:]
        
        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            intent=result["intent"],
            claim_id=result.get("claim_id"),
            requires_pipeline=result.get("requires_pipeline", False),
            suggested_actions=result.get("suggested_actions", []),
            conversation_history=recent_history
        )
        
    except Exception as e:
        logger.error(f"[chat] Error in session {session_id}: {e}", exc_info=True)
        error_response = "Sorry, I encountered an error. Please try again or contact support."
        await _add_to_history(session_id, body.message, error_response, "error")
        
        return ChatResponse(
            response=error_response,
            session_id=session_id,
            intent="error",
            suggested_actions=["Try again", "Contact support"]
        )


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 2 — CHAT WITH CLAIM SUBMISSION
# POST /api/chat/submit-claim
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/submit-claim")
async def chat_submit_claim(
    message: str = Form(...),
    claim_type: str = Form(...),
    session_id: Optional[str] = Form(None),
    documents: List[UploadFile] = File(...),
    audio_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Chat endpoint that accepts documents/voice and triggers the full LangGraph pipeline.
    User can describe their claim in natural language + upload supporting docs.
    """
    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    session_id, session = await _get_or_create_session(session_id, user_id)
    
    claim_id = f"CLM-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    logger.info(f"[chat] {session_id}: Claim submission - {claim_type} with {len(documents)} documents")
    
    try:
        # Save uploaded files to S3
        import boto3
        s3_client = boto3.client('s3')
        s3_bucket = os.getenv("CLAIMFLOW_S3_BUCKET")
        
        document_s3_uris = []
        audio_s3_uri = None
        
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

        # Extract structured fields from user message using simple NLP
        import re
        message_lower = message.lower()
        
        # Try to extract policy number
        policy_match = re.search(r'policy\s*(?:number|no\.?|#)?\s*:?\s*([a-z0-9\-/]+)', message_lower)
        policy_number = policy_match.group(1).upper() if policy_match else None
        
        # Try to extract dates
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', message)
        incident_date = date_match.group(1) if date_match else None
        
        # Build raw input from user message and uploaded docs
        raw_input = {
            "claim_type": claim_type,
            "description": message,
            "policy_number": policy_number,
            "incident_date": incident_date,
            "document_s3_uris": document_s3_uris,
            "audio_s3_uri": audio_s3_uri,
            "submitted_via": "chat",
            "session_id": session_id,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Add claim-type-specific defaults
        if claim_type == "health":
            raw_input.update({
                "hospital_name": "Not specified",
                "procedure_code": "CHAT-SUBMIT"
            })
        elif claim_type == "motor":
            raw_input.update({
                "vehicle_make": "Not specified",
                "vehicle_year": 2020
            })
        
        # Create initial state and run pipeline
        initial_state = create_initial_state(
            claim_id=claim_id,
            claim_type=claim_type,
            user_id=user_id,
            nationality=current_user.get("nationality", "IN"),
            country_of_residence=current_user.get("country_of_residence", "IN"),
            raw_input=raw_input
        )
        
        # Save to DynamoDB
        await db_service.save_claim({
            "claim_id": claim_id,
            "user_id": user_id,
            "claim_type": claim_type,
            "status": "processing",
            "session_id": session_id,
            "description": message,
            "document_count": len(documents),
            "has_audio": audio_file is not None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        
        # Run the pipeline
        final_state = await run_claim_pipeline(initial_state)
        
        routing = final_state.get("routing_decision", "human_queue")
        status = final_state.get("final_status", "pending_review")
        fraud_score = (final_state.get("forensic_result") or {}).get("fraud_score")
        estimate = (final_state.get("vision_result") or {}).get("damage_estimate_inr")
        
        # Update DynamoDB with results
        await db_service.update_claim(claim_id, {
            "status": status,
            "routing_decision": routing,
            "fraud_score": fraud_score,
            "damage_estimate": estimate,
            "settlement_amount_inr": estimate if status == "approved" else None,
            "vision_result": final_state.get("vision_result"),
            "forensic_result": final_state.get("forensic_result"),
            "policy_result": final_state.get("policy_result"),
            "inclusion_result": final_state.get("inclusion_result"),
            "audit_trail": final_state.get("audit_trail", []),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        
        # Generate user-friendly response
        if routing == "auto_approve":
            bot_response = (
                f"🎉 Great news! Your {claim_type} claim **{claim_id}** has been automatically approved!\n\n"
                f"💰 **Settlement Amount**: ₹{estimate:,.0f}\n"
                f"⏱️ **Payment Timeline**: 2-3 business days\n\n"
                f"You'll receive a confirmation email shortly with payment details."
            )
        elif routing == "human_queue":
            bot_response = (
                f"📋 Your {claim_type} claim **{claim_id}** has been submitted successfully!\n\n"
                f"🔍 **Status**: Under review by our claims team\n"
                f"⏱️ **Timeline**: You'll hear back within 24 hours\n"
                f"📊 **Initial Assessment**: {fraud_score:.0f}/100 risk score\n\n"
                f"I'll notify you as soon as there's an update!"
            )
        elif routing == "reject":
            bot_response = (
                f"❌ Unfortunately, your {claim_type} claim **{claim_id}** could not be approved at this time.\n\n"
                f"This may be due to policy coverage limitations or documentation issues. "
                f"Please contact your insurance advisor for detailed feedback."
            )
        else:  # investigate
            bot_response = (
                f"🔍 Your {claim_type} claim **{claim_id}** is undergoing additional verification.\n\n"
                f"Our AI agents are conducting a detailed review to ensure accurate processing. "
                f"This typically takes 2-4 hours. I'll update you as soon as it's complete!"
            )
        
        # Update session history and context
        await _add_to_history(session_id, f"[CLAIM SUBMISSION] {message}", bot_response, "claim_submitted")
        await db_service.update_session(session_id, {
            "context": {"last_claim_id": claim_id}
        })
        
        return {
            "response": bot_response,
            "session_id": session_id,
            "intent": "claim_submitted",
            "claim_id": claim_id,
            "requires_pipeline": False,
            "status": status,
            "routing_decision": routing,
            "fraud_score": fraud_score,
            "damage_estimate": estimate,
            "documents_processed": len(documents),
            "audio_processed": audio_file is not None,
            "suggested_actions": [
                "Check claim status",
                "Ask questions about the decision",
                "Submit another claim"
            ]
        }
        
    except Exception as e:
        logger.error(f"[chat] Claim submission error in session {session_id}: {e}", exc_info=True)
        error_response = f"Sorry, there was an error processing your {claim_type} claim. Please try again or contact support."
        await _add_to_history(session_id, f"[CLAIM SUBMISSION ERROR] {message}", error_response, "error")
        
        return {
            "response": error_response,
            "session_id": session_id,
            "intent": "error",
            "suggested_actions": ["Try again", "Contact support"]
        }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 3 — GET CHAT HISTORY
# GET /api/chat/{session_id}/history
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{session_id}/history")
async def get_chat_history(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get conversation history for a chat session."""
    session = await db_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    
    # Users can only access their own sessions
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "session_id": session_id,
        "conversation_history": session.get("conversation_history", []),
        "context": session.get("context", {}),
        "created_at": session.get("created_at")
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 4 — GET USER'S CHAT SESSIONS
# GET /api/chat/my-sessions
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/my-sessions")
async def get_my_chat_sessions(
    current_user: dict = Depends(get_current_user)
):
    """Get all chat sessions for the current user."""
    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    sessions = await db_service.get_user_sessions(user_id)
    
    # Sort by creation date (newest first)
    sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {
        "sessions": sessions,
        "total_count": len(sessions)
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 5 — CLEAR CHAT SESSION
# DELETE /api/chat/{session_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{session_id}")
async def clear_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Clear/reset a chat session."""
    session = await db_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Clear conversation history but keep session
    await db_service.update_session(session_id, {
        "conversation_history": [],
        "context": {}
    })
    
    return {"message": f"Chat session {session_id} cleared successfully"}