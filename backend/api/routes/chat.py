"""
ClaimFlow Chat API  — v2
========================
Routes:
  POST /api/chat/message          text-only turn (with full context)
  POST /api/chat/multimodal       text + files + audio in one request
  GET  /api/chat/{id}/history     full conversation history
  GET  /api/chat/{id}/summary     generate / retrieve summary report
  GET  /api/chat/my-sessions      list user sessions
  DELETE /api/chat/{id}           clear session
"""

import os
import uuid
import logging
import base64
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from backend.core.security import get_current_user
from backend.agents.chat_agent import handle_chat_query, _handle_summary_generation
from backend.services.dynamodb_service import get_db_service

logger = logging.getLogger("claimflow.chat")
router = APIRouter(prefix="/api/chat", tags=["Chat"])
db_service = get_db_service()


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
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
    summary_report: Optional[dict] = None
    wizard_step: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# SESSION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

async def _get_or_create_session(session_id: Optional[str], user_id: str):
    if not session_id:
        session_id = f"chat-{uuid.uuid4().hex[:8]}"
    session = await db_service.get_session(session_id)
    if not session:
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "conversation_history": [],
            "context": {},
        }
        await db_service.save_session(session)
    return session_id, session


async def _persist_turn(
    session_id: str,
    user_message: str,
    bot_response: str,
    intent: str,
    input_type: str,
    context_updates: dict,
):
    """Append one exchange and update wizard context atomically."""
    session = await db_service.get_session(session_id)
    if not session:
        return

    history = session.get("conversation_history", [])
    history.append({
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "user_message": user_message,
        "bot_response": bot_response,
        "intent":       intent,
        "input_type":   input_type,
    })
    # Keep unlimited history (summary report needs it all)
    await db_service.update_session(session_id, {
        "conversation_history": history,
        "context": context_updates,
    })


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 1 — TEXT CHAT
# POST /api/chat/message
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    body: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id    = str(current_user.get("user_id") or current_user.get("id", ""))
    user_email = current_user.get("email", "")
    session_id, session = await _get_or_create_session(body.session_id, user_id)

    logger.info(f"[chat/message] {session_id}: {body.message[:60]!r}")

    result = await handle_chat_query(
        user_message=body.message,
        user_id=user_id,
        session_context=session.get("context", {}),
        conversation_history=session.get("conversation_history", []),
        attachments=[],
        user_email=user_email,
    )

    await _persist_turn(
        session_id,
        body.message,
        result["response"],
        result["intent"],
        "text",
        result.get("context_updates", {}),
    )

    updated = await db_service.get_session(session_id)
    recent  = (updated.get("conversation_history", []))[-5:]

    return ChatResponse(
        response=result["response"],
        session_id=session_id,
        intent=result["intent"],
        claim_id=result.get("claim_id"),
        requires_pipeline=result.get("requires_pipeline", False),
        suggested_actions=result.get("suggested_actions", []),
        conversation_history=recent,
        summary_report=result.get("summary_report"),
        wizard_step=result.get("context_updates", {}).get("wizard_step"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 2 — MULTIMODAL CHAT
# POST /api/chat/multimodal
# Accepts text + optional files + optional audio blob
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/multimodal")
async def chat_multimodal(
    message:    str                    = Form(default=""),
    session_id: Optional[str]          = Form(default=None),
    files:      List[UploadFile]       = File(default=[]),
    audio:      Optional[UploadFile]   = File(default=None),
    current_user: dict = Depends(get_current_user),
):
    user_id    = str(current_user.get("user_id") or current_user.get("id", ""))
    user_email = current_user.get("email", "")
    session_id, session = await _get_or_create_session(session_id, user_id)

    logger.info(
        f"[chat/multimodal] {session_id}: msg={message[:40]!r} "
        f"files={len(files)} audio={audio is not None}"
    )

    # ── Process audio → transcript ────────────────────────────────────────────
    voice_transcript = ""
    if audio:
        try:
            audio_bytes = await audio.read()
            # Browser MediaRecorder produces webm/ogg; use Web Speech result if available
            # For now store raw bytes and note the transcript will come from frontend
            voice_transcript = message  # frontend sends Web Speech transcript as message
            logger.info(f"[chat/multimodal] audio received: {len(audio_bytes)} bytes")
        except Exception as e:
            logger.warning(f"Audio processing error: {e}")

    # ── Process uploaded files ────────────────────────────────────────────────
    attachments = []
    for f in files:
        try:
            raw = await f.read()
            content_type = f.content_type or ""
            analysis = {}

            if content_type.startswith("image/"):
                # Run vision agent analysis
                try:
                    import tempfile, os as _os
                    suffix = "." + (f.filename or "img.jpg").rsplit(".", 1)[-1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(raw)
                        tmp_path = tmp.name
                    from backend.agents.vision_agent import process_image
                    analysis = await process_image({"file_path": tmp_path})
                    _os.unlink(tmp_path)
                except Exception as ve:
                    logger.warning(f"Vision analysis failed for {f.filename}: {ve}")
                    analysis = {"document_type": "image", "confidence": 0}

            elif content_type == "application/pdf" or (f.filename or "").endswith(".pdf"):
                try:
                    import tempfile, os as _os
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(raw)
                        tmp_path = tmp.name
                    from backend.agents.document_agent import process_document
                    doc_result = await process_document({"file_path": tmp_path})
                    _os.unlink(tmp_path)
                    analysis = {
                        "document_type": doc_result.get("document_type", "pdf"),
                        "amount":        doc_result.get("structured_data", {}).get("amount"),
                        "date":          doc_result.get("structured_data", {}).get("date"),
                        "confidence":    doc_result.get("confidence", 0),
                        "text_preview":  doc_result.get("text", "")[:300],
                    }
                except Exception as de:
                    logger.warning(f"Document analysis failed for {f.filename}: {de}")
                    analysis = {"document_type": "document", "confidence": 0}

            attachments.append({
                "name":     f.filename or "upload",
                "type":     content_type,
                "size":     len(raw),
                "analysis": analysis,
            })
        except Exception as e:
            logger.error(f"File processing error {f.filename}: {e}")

    # ── Compose effective message ─────────────────────────────────────────────
    effective_msg = message.strip()
    if not effective_msg and attachments:
        effective_msg = f"I have uploaded {len(attachments)} file(s) for my claim."
    if not effective_msg and voice_transcript:
        effective_msg = voice_transcript

    input_type = "text"
    if audio and files:
        input_type = "audio+files"
    elif audio:
        input_type = "audio"
    elif files:
        input_type = "files"

    # ── Run agent ─────────────────────────────────────────────────────────────
    result = await handle_chat_query(
        user_message=effective_msg,
        user_id=user_id,
        session_context=session.get("context", {}),
        conversation_history=session.get("conversation_history", []),
        attachments=attachments,
        user_email=user_email,
    )

    await _persist_turn(
        session_id,
        effective_msg,
        result["response"],
        result["intent"],
        input_type,
        result.get("context_updates", {}),
    )

    updated = await db_service.get_session(session_id)
    recent  = (updated.get("conversation_history", []))[-5:]

    return {
        "response":          result["response"],
        "session_id":        session_id,
        "intent":            result["intent"],
        "claim_id":          result.get("claim_id"),
        "requires_pipeline": result.get("requires_pipeline", False),
        "suggested_actions": result.get("suggested_actions", []),
        "conversation_history": recent,
        "summary_report":    result.get("summary_report"),
        "wizard_step":       result.get("context_updates", {}).get("wizard_step"),
        "attachments_processed": len(attachments),
        "input_type":        input_type,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 3 — SUMMARY REPORT
# GET /api/chat/{session_id}/summary
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    session = await db_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    ctx     = session.get("context", {})
    history = session.get("conversation_history", [])

    # Return cached report if already generated
    if ctx.get("summary_report"):
        return ctx["summary_report"]

    # Generate fresh
    report = _handle_summary_generation(ctx, history)
    await db_service.update_session(session_id, {
        "context": {**ctx, "summary_report": report}
    })
    return report


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 4 — HISTORY
# GET /api/chat/{session_id}/history
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{session_id}/history")
async def get_chat_history(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    session = await db_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "session_id":           session_id,
        "conversation_history": session.get("conversation_history", []),
        "context":              session.get("context", {}),
        "created_at":           session.get("created_at"),
        "wizard_step":          session.get("context", {}).get("wizard_step", "greeting"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 5 — MY SESSIONS
# GET /api/chat/my-sessions
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/my-sessions")
async def get_my_sessions(current_user: dict = Depends(get_current_user)):
    user_id  = str(current_user.get("user_id") or current_user.get("id", ""))
    sessions = await db_service.get_user_sessions(user_id)
    sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"sessions": sessions, "total_count": len(sessions)}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 6 — CLEAR SESSION
# DELETE /api/chat/{session_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{session_id}")
async def clear_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    session = await db_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_id = str(current_user.get("user_id") or current_user.get("id", ""))
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db_service.update_session(session_id, {
        "conversation_history": [],
        "context": {},
    })
    return {"message": f"Session {session_id} cleared"}
