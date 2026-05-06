# backend/graph/nodes.py
# ClaimFlow — LangGraph Node Functions
# Shresth owns this file.
#
# Each function = one node in the LangGraph pipeline.
# A node receives the full state dict, returns ONLY the fields it changed.
# LangGraph merges the returned dict back into state automatically.
#
# AWS Services used across nodes:
#   Bedrock Strands      — Vision Agent (stubbed until Srivalli has Agent IDs)
#   Bedrock Agent Core   — session memory for chatbot continuity
#   Bedrock Knowledge Base — RAG for policy PDFs (called inside policy_auditor.py)
#   Bedrock Guardrails   — called inside guardrail_node
#
# Node order (defined in pipeline.py):
#   inclusion → vision → forensic → policy → guardrail → router
#       ↓ (if investigate)
#   investigator → vision → forensic → router  (loops max 3x)
#       ↓ (if human_queue)
#   human_review → notification
#       ↓ (if auto_approve or reject)
#   notification → END

import json
import logging
import os

import boto3
from dotenv import load_dotenv

from backend.graph.state import audit_entry

load_dotenv()

logger = logging.getLogger("claimflow.nodes")

# ─────────────────────────────────────────────────────────────────────────────
# AWS CLIENTS
# Credentials loaded from .env — supports temporary session tokens (AWS Academy)
# ─────────────────────────────────────────────────────────────────────────────
AWS_REGION   = os.getenv("AWS_REGION",            "us-east-1")
AWS_KEY      = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET   = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION  = os.getenv("AWS_SESSION_TOKEN")

_boto_kwargs = dict(
    region_name          = AWS_REGION,
    aws_access_key_id    = AWS_KEY,
    aws_secret_access_key= AWS_SECRET,
    aws_session_token    = AWS_SESSION,
)

try:
    bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", **_boto_kwargs)
    bedrock_runtime       = boto3.client("bedrock-runtime",       **_boto_kwargs)
    bedrock_guardrails    = boto3.client("bedrock",               **_boto_kwargs)
except Exception as _boto_init_err:
    logger.warning(f"AWS client init skipped (no credentials): {_boto_init_err}")
    bedrock_agent_runtime = None
    bedrock_runtime       = None
    bedrock_guardrails    = None

# ── Strands Agent IDs (fill in once Srivalli sets up Bedrock Console) ────────
VISION_AGENT_ID       = os.getenv("VISION_AGENT_ID",    "PLACEHOLDER")
VISION_AGENT_ALIAS    = os.getenv("VISION_AGENT_ALIAS",  "PLACEHOLDER")
FORENSIC_AGENT_ID     = os.getenv("FORENSIC_AGENT_ID",  "PLACEHOLDER")
FORENSIC_AGENT_ALIAS  = os.getenv("FORENSIC_AGENT_ALIAS","PLACEHOLDER")

# ── Bedrock Agent Core ────────────────────────────────────────────────────────
# Agent Core manages chatbot session memory across turns.
# Each claim gets its own session_id = claim_id.
AGENT_CORE_AGENT_ID   = os.getenv("AGENT_CORE_AGENT_ID",   "PLACEHOLDER")
AGENT_CORE_AGENT_ALIAS= os.getenv("AGENT_CORE_AGENT_ALIAS", "PLACEHOLDER")

# ── Bedrock Guardrail ─────────────────────────────────────────────────────────
GUARDRAIL_ID          = os.getenv("GUARDRAIL_ID",      "PLACEHOLDER")
GUARDRAIL_VERSION     = os.getenv("GUARDRAIL_VERSION",  "DRAFT")


# ─────────────────────────────────────────────────────────────────────────────
# STRANDS INVOCATION HELPER
# Calls a Bedrock Strands agent and returns the response text.
# Stubbed when Agent IDs are PLACEHOLDER — swap to real call once IDs are ready.
# ─────────────────────────────────────────────────────────────────────────────

def _invoke_strands_agent(
    agent_id: str,
    agent_alias: str,
    session_id: str,
    prompt: str,
    stub_response: dict,
) -> dict:
    """
    Invokes a Bedrock Strands agent.

    When agent_id is still PLACEHOLDER (Srivalli hasn't set up console yet),
    returns stub_response so the rest of the pipeline keeps running.

    Once Srivalli gives you the Agent ID + Alias ID:
    1. Set VISION_AGENT_ID and VISION_AGENT_ALIAS in your .env
    2. The stub block is bypassed automatically — no other code changes needed.

    Returns: parsed dict from the agent's JSON response
    """
    # ── STUB: remove this block once Agent IDs are ready ─────────────────────
    if agent_id == "PLACEHOLDER":
        logger.warning(f"Strands agent {agent_id} not configured — returning stub")
        return stub_response
    # ─────────────────────────────────────────────────────────────────────────

    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId      = agent_id,
            agentAliasId = agent_alias,
            sessionId    = session_id,   # Agent Core tracks this session
            inputText    = prompt,
        )

        # Agent Core streams response in chunks — collect all text chunks
        full_response = ""
        for event in response["completion"]:
            if "chunk" in event:
                full_response += event["chunk"]["bytes"].decode("utf-8")

        # Agents return JSON — strip markdown fences if present
        clean = full_response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip()

        return json.loads(clean)

    except Exception as e:
        logger.error(f"Strands agent invocation failed: {e}")
        return stub_response


# ─────────────────────────────────────────────────────────────────────────────
# NODE 1 — INCLUSION AGENT
# Praharshitha owns inclusion_agent.py — this node calls her function.
# Handles voice-to-text + multilingual field extraction.
# If claim came via form (no audio), passes through raw_input unchanged.
# ─────────────────────────────────────────────────────────────────────────────

def inclusion_node(state: dict) -> dict:
    import asyncio
    import concurrent.futures
    
    claim_id  = state["claim_id"]
    raw_input = state["raw_input"]
    
    # Check for audio and document inputs
    has_audio = any(key in raw_input for key in ["audio_s3_uri", "audio_base64", "audio_file_path"])
    has_documents = "document_s3_uris" in raw_input and raw_input["document_s3_uris"]

    logger.info(f"[{claim_id}] inclusion_node — has_audio={has_audio}, has_documents={has_documents}")

    inclusion_result = {
        "transcribed_text": "",
        "detected_language": raw_input.get("language", "en"),
        "extracted_fields": raw_input.copy(),
        "processed_documents": [],
        "voice_processing": None,
        "document_processing": []
    }
    
    audit_messages = []

    # Process voice input if available
    if has_audio:
        try:
            from backend.agents.voice_agent import process_voice_input
            
            voice_input = {
                "language_hint": raw_input.get("language", "en-IN"),
                "claim_context": {
                    "claim_type": state.get("claim_type"),
                    "user_id": state.get("user_id")
                }
            }
            
            # Add audio source
            if "audio_s3_uri" in raw_input:
                voice_input["audio_s3_uri"] = raw_input["audio_s3_uri"]
            elif "audio_base64" in raw_input:
                voice_input["audio_base64"] = raw_input["audio_base64"]
            elif "audio_file_path" in raw_input:
                voice_input["audio_file_path"] = raw_input["audio_file_path"]
            
            # Run voice processing in thread pool to avoid event loop issues
            def _run_voice():
                return asyncio.run(process_voice_input(voice_input))
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                voice_result = pool.submit(_run_voice).result(timeout=180)
            
            if voice_result["success"]:
                inclusion_result.update({
                    "transcribed_text": voice_result["transcribed_text"],
                    "detected_language": voice_result["original_language"],
                    "voice_processing": voice_result
                })
                
                # Merge extracted fields from voice
                voice_fields = voice_result.get("extracted_fields", {})
                inclusion_result["extracted_fields"].update(voice_fields)
                
                audit_messages.append(
                    f"Voice processed: {voice_result['original_language']} -> "
                    f"en, confidence={voice_result['confidence']:.2f}, "
                    f"fields={list(voice_fields.keys())}"
                )
            else:
                audit_messages.append(f"Voice processing failed: {voice_result['error']}")
                
        except Exception as e:
            logger.error(f"[{claim_id}] Voice processing error: {e}")
            audit_messages.append(f"Voice processing error: {e}")

    # Process documents if available
    if has_documents:
        try:
            from backend.agents.document_agent import process_document
            
            processed_docs = []
            
            for i, doc_s3_uri in enumerate(raw_input["document_s3_uris"]):
                try:
                    doc_input = {
                        "s3_uri": doc_s3_uri,
                        "use_textract": True,
                        "enhance_images": True,
                        "extract_tables": True
                    }
                    
                    # Run document processing in thread pool
                    def _run_doc():
                        return asyncio.run(process_document(doc_input))
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        doc_result = pool.submit(_run_doc).result(timeout=300)
                    
                    if doc_result["success"]:
                        processed_docs.append({
                            "s3_uri": doc_s3_uri,
                            "document_type": doc_result["document_type"],
                            "text": doc_result["text"],
                            "structured_data": doc_result["structured_data"],
                            "confidence": doc_result["confidence"],
                            "processing_method": doc_result["processing_method"]
                        })
                        
                        # Merge structured data from documents
                        doc_fields = doc_result.get("structured_data", {})
                        for key, value in doc_fields.items():
                            if key not in inclusion_result["extracted_fields"] and value:
                                inclusion_result["extracted_fields"][key] = value
                        
                        audit_messages.append(
                            f"Doc {i+1}: {doc_result['document_type']}, "
                            f"confidence={doc_result['confidence']:.2f}, "
                            f"method={doc_result['processing_method']}"
                        )
                    else:
                        audit_messages.append(f"Doc {i+1} processing failed: {doc_result['error']}")
                        
                except Exception as e:
                    logger.error(f"[{claim_id}] Document {i+1} processing error: {e}")
                    audit_messages.append(f"Doc {i+1} error: {e}")
            
            inclusion_result["document_processing"] = processed_docs
            
        except Exception as e:
            logger.error(f"[{claim_id}] Document processing error: {e}")
            audit_messages.append(f"Document processing error: {e}")

    # If no audio or documents, just pass through
    if not has_audio and not has_documents:
        audit_messages.append("Form submission — no voice/document processing needed")

    # Update raw_input with merged fields
    merged_input = {**raw_input, **inclusion_result["extracted_fields"]}

    return {
        "raw_input": merged_input,
        "inclusion_result": inclusion_result,
        "audit_trail": [audit_entry("inclusion_node", " | ".join(audit_messages))],
    }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 2 — VISION AGENT
# Calls vision_agent.run() directly — handles OCR, domain detection, and
# structured extraction.  Falls back to Bedrock Strands when Agent IDs are set.
# ─────────────────────────────────────────────────────────────────────────────

def vision_node(state: dict) -> dict:
    import asyncio
    from backend.agents.vision_agent import run as vision_run

    claim_id  = state["claim_id"]
    iteration = state.get("investigator_iteration", 0)
    challenge = state.get("investigator_challenge")
    raw       = state.get("raw_input") or {}
    inclusion_result = state.get("inclusion_result") or {}

    logger.info(f"[{claim_id}] vision_node — iteration={iteration}")

    # ── If Bedrock Strands is configured, use it ──────────────────────────────
    if VISION_AGENT_ID != "PLACEHOLDER":
        prompt = (
            f"INVESTIGATOR RE-EXAMINATION (iteration {iteration})\n"
            f"Previous vision result:\n{json.dumps(state.get('vision_result'), indent=2)}\n"
            f"CHALLENGE:\n{challenge}"
            if challenge else
            f"Assess the insurance claim damage.\nClaim details:\n{json.dumps(raw, indent=2)}\n"
            f"Claim type: {state['claim_type']}"
        )
        stub = {
            "damage_estimate_inr": 4200.0, "damage_confidence": 0.85,
            "damage_zones": ["front_bumper"], "explanation": "STUB",
            "parts_detected": ["bumper"], "pre_existing_damage_found": False, "anomalies": [],
        }
        result = _invoke_strands_agent(
            agent_id=VISION_AGENT_ID, agent_alias=VISION_AGENT_ALIAS,
            session_id=state["session_id"], prompt=prompt, stub_response=stub,
        )
        return {
            "vision_result": result,
            "audit_trail": [audit_entry("vision_node",
                f"{'[RE-EXAM] ' if challenge else ''}Strands estimate: "
                f"₹{result.get('damage_estimate_inr', 0):,.0f} | "
                f"Confidence: {result.get('damage_confidence', 0):.0%}")],
        }

    # ── Local vision_agent.run() ──────────────────────────────────────────────
    # Check if we have processed documents from inclusion_node
    processed_docs = inclusion_result.get("document_processing", [])
    
    # Find the best image/document to analyze
    image_ref = None
    document_context = {}
    
    # Priority 1: Look for processed documents with high confidence
    for doc in processed_docs:
        if doc.get("confidence", 0) > 0.7 and doc.get("document_type") != "unknown":
            # Use the S3 URI of the processed document
            image_ref = doc["s3_uri"]
            document_context = {
                "document_type": doc["document_type"],
                "extracted_text": doc.get("text", ""),
                "structured_data": doc.get("structured_data", {}),
                "processing_method": doc.get("processing_method")
            }
            break
    
    # Priority 2: Fall back to raw input image references
    if not image_ref:
        image_ref = (
            raw.get("photo_local_path")
            or raw.get("image_url")
            or raw.get("evidence_url")
            or raw.get("s3_uri")
            or (raw.get("document_s3_uris", [{}])[0] if raw.get("document_s3_uris") else None)
            or ""
        )

    vision_input = {
        "image_url": image_ref,
        "claim_type": state.get("claim_type", ""),
        "aws_enabled": False,   # flip to True when AWS creds are live
        "document_context": document_context  # Pass document processing results
    }

    # On re-examination pass, hint the agent about what to look for
    if challenge:
        vision_input["investigator_challenge"] = challenge
        vision_input["previous_vision_result"] = state.get("vision_result")

    # LangGraph nodes are synchronous; agents are async.
    # Run in a fresh thread with its own event loop to avoid
    # "event loop already running" errors inside uvicorn/FastAPI.
    import concurrent.futures
    def _run_vision():
        return asyncio.run(vision_run(vision_input))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        agent_response = pool.submit(_run_vision).result(timeout=120)

    if not agent_response.get("success"):
        # Vision failed — return a safe low-confidence result so pipeline continues
        logger.warning(f"[{claim_id}] vision_agent failed: {agent_response.get('error')}")
        result = {
            "domain":               state.get("claim_type", "unknown"),
            "damage_estimate_inr":  None,
            "damage_confidence":    0.0,
            "damage_zones":         [],
            "visual_indicators":    [],
            "structured_data":      {},
            "document_type":        "unknown",
            "error":                agent_response.get("error"),
        }
    else:
        data   = agent_response.get("data", {})
        result = {
            # Fields forensic_node and router_node read
            "domain":               data.get("domain", state.get("claim_type", "unknown")),
            "document_type":        data.get("document_type"),
            "structured_data":      data.get("structured_data", {}),
            "visual_indicators":    data.get("visual_indicators", []),
            "damage_estimate_inr":  data.get("damage_estimate_inr"),
            "damage_confidence":    data.get("damage_confidence", 0.0),
            "damage_zones":         data.get("damage_zones", []),
            # Handwriting / OCR metadata
            "handwriting_detected": data.get("handwriting_detected", False),
            "ocr_recovery_applied": data.get("ocr_recovery_applied", False),
            # Document processing integration
            "document_context_used": bool(document_context),
            "processed_documents_count": len(processed_docs),
            # Pass through full data for downstream use
            **data,
        }

    audit_message = (
        f"{'[RE-EXAM] ' if challenge else ''}"
        f"Domain: {result.get('domain')} | "
        f"DocType: {result.get('document_type')} | "
        f"Estimate: ₹{result.get('damage_estimate_inr') or 0:,.0f} | "
        f"Confidence: {result.get('damage_confidence', 0):.0%} | "
        f"OCR: {agent_response.get('meta', {}).get('ocr_source', 'none')}"
    )
    
    if document_context:
        audit_message += f" | Doc context: {document_context['document_type']}"

    return {
        "vision_result": result,
        "audit_trail": [audit_entry("vision_node", audit_message)],
    }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 3 — FORENSIC AGENT
# Calls forensic_agent.run() directly — deterministic rule engine + optional
# Bedrock Claude augmentation.  Falls back to Bedrock Strands when IDs are set.
# ─────────────────────────────────────────────────────────────────────────────

def forensic_node(state: dict) -> dict:
    import asyncio
    from backend.agents.forensic_agent import run as forensic_run

    claim_id     = state["claim_id"]
    vision_result = state.get("vision_result") or {}
    logger.info(f"[{claim_id}] forensic_node")

    # ── If Bedrock Strands is configured, use it ──────────────────────────────
    if FORENSIC_AGENT_ID != "PLACEHOLDER":
        prompt = (
            f"Analyse this insurance claim for fraud indicators.\n"
            f"Claim details:\n{json.dumps(state['raw_input'], indent=2)}\n"
            f"Vision assessment:\n{json.dumps(vision_result, indent=2)}"
        )
        stub = {
            "fraud_score": 12.0, "fraud_explanation": "STUB",
            "flagged_entities": [], "cross_claim_hits": 0, "risk_level": "LOW",
        }
        result = _invoke_strands_agent(
            agent_id=FORENSIC_AGENT_ID, agent_alias=FORENSIC_AGENT_ALIAS,
            session_id=state["session_id"], prompt=prompt, stub_response=stub,
        )
        return {
            "forensic_result": result,
            "audit_trail": [audit_entry("forensic_node",
                f"Strands fraud score: {result.get('fraud_score', 0)}/100 | "
                f"Risk: {result.get('risk_level', 'N/A')}")],
        }

    # ── Local forensic_agent.run() ────────────────────────────────────────────
    # Build processed_evidences from raw_input so the forensic agent has
    # something to cross-check even when no explicit evidence list is provided.
    raw = state.get("raw_input") or {}
    processed_evidences = raw.get("processed_evidences") or []
    if not processed_evidences:
        # Synthesise a minimal evidence entry from whatever image ref we have
        image_ref = (
            raw.get("photo_local_path")
            or raw.get("image_url")
            or raw.get("evidence_url")
            or raw.get("s3_uri")
        )
        if image_ref:
            processed_evidences = [{"type": "document", "path": image_ref}]

    forensic_input = {
        "vision_output":       vision_result,
        "processed_evidences": processed_evidences,
        "bedrock_enabled":     False,   # flip to True when AWS creds are live
    }

    import concurrent.futures
    def _run_forensic():
        return asyncio.run(forensic_run(forensic_input))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        agent_response = pool.submit(_run_forensic).result(timeout=120)

    if not agent_response.get("success"):
        logger.warning(f"[{claim_id}] forensic_agent failed: {agent_response.get('error')}")
        result = {
            "fraud_score":       50.0,
            "fraud_explanation": agent_response.get("error", "Forensic analysis failed"),
            "flagged_entities":  [],
            "cross_claim_hits":  0,
            "risk_level":        "MEDIUM",
            # Keep forensic fields for router
            "claim_confidence":  0.5,
            "risk_level_lower":  "moderate",
        }
    else:
        data = agent_response.get("data", {})
        # Map forensic_agent output → fields router_node reads
        risk_map = {"low": "LOW", "moderate": "MEDIUM", "high": "HIGH"}
        risk_lower = (data.get("risk_level") or "moderate").lower()
        result = {
            # Router reads fraud_score (0-100 scale)
            "fraud_score":        round((1.0 - float(data.get("claim_confidence", 0.5))) * 100, 1),
            "fraud_explanation":  "; ".join((data.get("analysis_summary") or [])[:3])
                                  or "No strong risk indicators detected.",
            "flagged_entities":   data.get("suspicious_indicators", []),
            "cross_claim_hits":   len([
                x for x in (data.get("suspicious_indicators") or [])
                if "duplicate" in x.lower()
            ]),
            "risk_level":         risk_map.get(risk_lower, "MEDIUM"),
            # Keep full forensic output for report endpoint
            **data,
        }

    return {
        "forensic_result": result,
        "audit_trail": [audit_entry(
            "forensic_node",
            f"Fraud score: {result.get('fraud_score', 0)}/100 | "
            f"Risk: {result.get('risk_level', 'N/A')} | "
            f"Confidence: {result.get('claim_confidence', 'N/A')} | "
            f"Flagged: {result.get('flagged_entities', [])}"
        )],
    }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 5 — POLICY AUDITOR 
# Praharshitha owns policy_auditor.py.
# Uses Bedrock Knowledge Base RAG to read policy PDFs.
# Selects regulatory PDF based on nationality + country_of_residence.
# ─────────────────────────────────────────────────────────────────────────────

def policy_node(state: dict) -> dict:
    claim_id = state["claim_id"]
    logger.info(f"[{claim_id}] policy_node — {state['nationality']}/{state['country_of_residence']}")

    try:
        from backend.agents.policy_auditor import run as policy_run

        result = policy_run({
            **state["raw_input"],
            "claim_type":           state["claim_type"],
            "nationality":          state["nationality"],
            "country_of_residence": state["country_of_residence"],
            "vision_result":        state.get("vision_result"),
            "forensic_result":      state.get("forensic_result"),
        })

        if not result["success"]:
            raise ValueError(result["error"])

        data = result["data"]
        return {
            "policy_result": data,
            "audit_trail": [audit_entry(
                "policy_node",
                f"Eligible: {data.get('eligible')} "
                f"| Compliant: {data.get('irdai_compliant')} "
                f"| Requires human: {data.get('requires_human')} "
                f"| Regulation: {data.get('regulation_used', 'N/A')}"
            )],
        }

    except Exception as e:
        logger.error(f"[{claim_id}] policy_node error: {e}")
        # Fail-open: don't block the pipeline on a policy check error
        stub = {
            "eligible":        True,
            "irdai_compliant": True,
            "requires_human":  False,
            "policy_clauses":  [],
            "regulation_used": "fallback",
            "notes":           f"Policy check error: {e}",
        }
        return {
            "policy_result": stub,
            "audit_trail": [audit_entry("policy_node", f"ERROR (fail-open): {e}")],
        }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 6 — GUARDRAIL GATE
# Bedrock Guardrails: PII masking, topic filters, grounding check.
# Falls back to local checks if Guardrail ID not configured yet.
# ─────────────────────────────────────────────────────────────────────────────

def guardrail_node(state: dict) -> dict:
    claim_id = state["claim_id"]
    logger.info(f"[{claim_id}] guardrail_node")

    issues = []

    # ── Local safety checks (always run) ──────────────────────────────────────
    vision   = state.get("vision_result")   or {}
    forensic = state.get("forensic_result") or {}
    policy   = state.get("policy_result")   or {}

    estimate = vision.get("damage_estimate_inr") or 0
    try:
        estimate = float(estimate)
    except (TypeError, ValueError):
        estimate = 0.0
    if estimate < 0:
        issues.append("Negative damage estimate")
    if estimate > 10_000_000:
        issues.append(f"Estimate ₹{estimate:,.0f} exceeds auto-process ceiling of ₹1Cr")

    explanation = forensic.get("fraud_explanation", "")
    for phrase in ["is committing fraud", "is a fraudster", "definitely fake", "is lying"]:
        if phrase.lower() in explanation.lower():
            issues.append("Fraud explanation contains direct accusation — blocked by guardrail")
            break

    if "error" in policy:
        issues.append("Policy auditor returned an error")

    # ── Bedrock Guardrails API (runs when GUARDRAIL_ID is configured) ─────────
    if GUARDRAIL_ID != "PLACEHOLDER" and bedrock_runtime is not None:
        try:
            # Build text to evaluate — combine all agent outputs
            text_to_check = json.dumps({
                "vision_explanation":   vision.get("explanation", ""),
                "fraud_explanation":    forensic.get("fraud_explanation", ""),
                "policy_notes":         policy.get("notes", ""),
            })

            guardrail_response = bedrock_runtime.apply_guardrail(
                guardrailIdentifier = GUARDRAIL_ID,
                guardrailVersion    = GUARDRAIL_VERSION,
                source              = "OUTPUT",
                content             = [{"text": {"text": text_to_check}}],
            )

            if guardrail_response.get("action") == "GUARDRAIL_INTERVENED":
                for assessment in guardrail_response.get("assessments", []):
                    # PII found — log it but don't block (PII gets masked, not blocked)
                    if assessment.get("sensitiveInformationPolicy", {}).get("piiEntities"):
                        logger.info(f"[{claim_id}] PII detected and masked by Bedrock Guardrails")
                    # Topic policy violation — this blocks
                    for topic in assessment.get("topicPolicy", {}).get("topics", []):
                        if topic.get("action") == "BLOCKED":
                            issues.append(f"Topic policy violation: {topic.get('name')}")

        except Exception as e:
            logger.warning(f"[{claim_id}] Bedrock Guardrails call failed: {e} — local checks only")

    passed = len(issues) == 0

    return {
        # Store guardrail result inside raw_input so router can read it
        # without adding new top-level state fields
        "raw_input": {
            **state["raw_input"],
            "_guardrail_passed": passed,
            "_guardrail_issues": issues,
        },
        "audit_trail": [audit_entry(
            "guardrail_node",
            f"Guardrails {'PASSED' if passed else 'FAILED'}"
            + (f" — Issues: {issues}" if issues else "")
            + (" | Bedrock Guardrails active" if GUARDRAIL_ID != "PLACEHOLDER" else " | Local checks only")
        )],
    }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 6 — CONFIDENCE ROUTER
# Reads all agent results and makes the routing decision.
# This is the brain of the pipeline.
# ─────────────────────────────────────────────────────────────────────────────

def router_node(state: dict) -> dict:
    claim_id = state["claim_id"]
    logger.info(f"[{claim_id}] router_node")

    vision    = state.get("vision_result")   or {}
    forensic  = state.get("forensic_result") or {}
    policy    = state.get("policy_result")   or {}
    raw       = state.get("raw_input")       or {}

    guardrail_passed = raw.get("_guardrail_passed", True)
    fraud_score      = float(forensic.get("fraud_score", 50.0))
    confidence       = float(vision.get("damage_confidence", 0.5))
    eligible         = policy.get("eligible", False)
    irdai_ok         = policy.get("irdai_compliant", False)
    iteration        = state.get("investigator_iteration", 0)

    # ── Pull extra signals from forensic output ───────────────────────────────
    claim_confidence  = float(forensic.get("claim_confidence", 0.5))
    risk_level        = (forensic.get("risk_level") or "MEDIUM").upper()
    suspicious        = forensic.get("suspicious_indicators") or forensic.get("flagged_entities") or []
    consistency_fails = forensic.get("consistency_checks") or []
    damage_assessment = forensic.get("damage_assessment") or {}
    inflation_risk    = (damage_assessment.get("inflation_risk") or "low").lower()

    # ── Human-review edge cases ───────────────────────────────────────────────
    # These are the specific conditions that REQUIRE a human adjuster.
    # Everything else either auto-approves or auto-rejects.
    human_review_reasons: list[str] = []

    # 1. Guardrail blocked the output
    if not guardrail_passed:
        human_review_reasons.append(f"Guardrail failed: {raw.get('_guardrail_issues', [])}")

    # 2. High fraud / risk score — but not so high we auto-reject
    if 50 <= fraud_score <= 75:
        human_review_reasons.append(f"Ambiguous fraud score {fraud_score:.0f}/100")

    # 3. Forensic found suspicious indicators (date mismatch, duplicate docs, etc.)
    if suspicious:
        human_review_reasons.append(f"Suspicious indicators: {suspicious[:2]}")

    # 4. Multiple consistency failures (missing docs, amount mismatches)
    if len(consistency_fails) >= 2:
        human_review_reasons.append(f"{len(consistency_fails)} consistency checks failed")

    # 5. High inflation risk on the damage estimate
    if inflation_risk == "high":
        human_review_reasons.append("High inflation risk on damage estimate")

    # 6. Very large claim amount (> ₹2L) regardless of confidence
    estimate = vision.get("damage_estimate_inr") or 0
    try:
        estimate = float(estimate)
    except (TypeError, ValueError):
        estimate = 0.0
    if estimate > 200_000:
        human_review_reasons.append(f"Large claim ₹{estimate:,.0f} requires adjuster sign-off")

    # 7. Low vision confidence on a non-trivial claim
    if confidence < 0.5 and estimate > 10_000:
        human_review_reasons.append(f"Low vision confidence {confidence:.0%} on ₹{estimate:,.0f} claim")

    # 8. Policy not eligible or not compliant — but not a hard reject
    #    (could be a data entry issue — let adjuster verify)
    if not eligible and not irdai_ok:
        human_review_reasons.append("Policy eligibility and compliance both unverified")

    # 9. Policy auditor explicitly flagged this for human review (e.g. > ₹2L)
    if policy.get("requires_human"):
        human_review_reasons.append("Policy auditor requires human sign-off")

    # ── Decision tree ─────────────────────────────────────────────────────────

    if fraud_score > 75:
        # Hard reject — too risky to even send to human
        decision = "reject"
        reason   = f"Fraud score too high: {fraud_score:.0f}/100"

    elif not eligible and irdai_ok is False and not human_review_reasons:
        # Definitively ineligible (policy auditor confirmed) — auto reject
        decision = "reject"
        reason   = "Claim not covered by policy"

    elif human_review_reasons and iteration < 3 and (50 <= fraud_score <= 75):
        # Ambiguous fraud — try investigator loop first before human
        decision = "investigate"
        reason   = f"Ambiguous fraud score {fraud_score:.0f}/100 — investigator loop iteration {iteration + 1}"

    elif human_review_reasons:
        # One or more edge cases triggered — needs human adjuster
        decision = "human_queue"
        reason   = " | ".join(human_review_reasons)

    elif (
        confidence     >  0.80
        and fraud_score < 30
        and claim_confidence > 0.75
        and eligible
        and irdai_ok
        and guardrail_passed
        and inflation_risk in ("low",)
        and estimate <= 200_000
    ):
        # All green — auto approve
        decision = "auto_approve"
        reason   = (
            f"All checks passed — vision confidence {confidence:.0%}, "
            f"fraud {fraud_score:.0f}/100, claim confidence {claim_confidence:.0%}"
        )

    else:
        # Anything that doesn't clearly pass or fail → human queue
        decision = "human_queue"
        reason   = (
            f"Confidence {confidence:.0%} | Fraud {fraud_score:.0f}/100 | "
            f"Eligible {eligible} | Compliant {irdai_ok} — needs adjuster review"
        )

    return {
        "routing_decision": decision,
        "audit_trail": [audit_entry("router_node", f"Decision: {decision.upper()} — {reason}")],
    }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 7 — INVESTIGATOR LOOP
# The wow feature — agents negotiating with each other.
# Forensic Agent sends a focused challenge to Vision Agent.
# Loops back through vision → forensic → router (max 3 times).
# ─────────────────────────────────────────────────────────────────────────────

def investigator_node(state: dict) -> dict:
    claim_id  = state["claim_id"]
    iteration = state.get("investigator_iteration", 0)
    vision    = state.get("vision_result")   or {}
    forensic  = state.get("forensic_result") or {}

    new_iteration = iteration + 1
    logger.info(f"[{claim_id}] investigator_node — iteration {new_iteration}/3")

    fraud_score = forensic.get("fraud_score",       50)
    confidence  = vision.get("damage_confidence",  0.5)
    flagged     = forensic.get("flagged_entities",  [])
    zones       = vision.get("damage_zones",        [])

    challenge = f"""INVESTIGATOR RE-EXAMINATION — Iteration {new_iteration}/3

Forensic Agent flagged this claim with fraud score {fraud_score}/100.
Your previous confidence was {confidence:.0%} on zones: {zones}
Flagged entities: {flagged}

Re-examine the photos specifically for:
1. Is damage in {zones} consistent with the reported accident direction?
2. Is there paint fade, oxidation or rust suggesting pre-existing damage?
3. Does wear on surrounding panels match vehicle age?
4. Are there body filler or repair marks near the claimed damage?
5. Does the damage pattern match a single incident or accumulated damage?

Update your damage_confidence to reflect these findings.
If pre-existing damage is found, lower confidence significantly."""

    # If max iterations reached — pipeline.py will route to human_queue
    if new_iteration >= 3:
        return {
            "investigator_iteration": new_iteration,
            "investigator_challenge": challenge,
            "routing_decision":       "human_queue",
            "audit_trail": [audit_entry(
                "investigator_node",
                f"Max iterations ({new_iteration}/3) reached — forcing human_queue"
            )],
        }

    return {
        "investigator_iteration": new_iteration,
        "investigator_challenge": challenge,
        "audit_trail": [audit_entry(
            "investigator_node",
            f"Iteration {new_iteration}/3 — challenge sent to Vision Agent. "
            f"Fraud: {fraud_score}/100 | Confidence: {confidence:.0%}"
        )],
    }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 8 — HUMAN REVIEW
# Pipeline pauses BEFORE this node (interrupt_before in pipeline.py).
# Only runs after adjuster posts their decision via /api/adjuster/{id}/decision.
# Adjuster decision is injected into state before resume.
# ─────────────────────────────────────────────────────────────────────────────

def human_review_node(state: dict) -> dict:
    claim_id = state["claim_id"]
    decision = state.get("adjuster_decision", "pending")
    notes    = state.get("adjuster_notes", "")

    logger.info(f"[{claim_id}] human_review_node — adjuster: {decision}")

    final_status = "approved" if decision == "approve" else "rejected"

    return {
        "final_status": final_status,
        "audit_trail": [audit_entry(
            "human_review_node",
            f"Adjuster decision: {decision.upper()} | Notes: {notes or 'None'}"
        )],
    }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 9 — NOTIFICATION
# Final node. Sends WhatsApp/SMS/email via AWS SNS.
# In hackathon mode: logs the notification message.
# ─────────────────────────────────────────────────────────────────────────────

def notification_node(state: dict) -> dict:
    claim_id     = state["claim_id"]
    decision     = state.get("routing_decision",     "human_queue")
    final_status = state.get("final_status")
    vision       = state.get("vision_result")        or {}
    estimate     = vision.get("damage_estimate_inr", 0)

    if not final_status:
        final_status = {
            "auto_approve": "approved",
            "reject":       "rejected",
        }.get(decision, "pending")

    messages = {
        "approved": f"✅ Claim {claim_id} approved. Settlement: ₹{estimate:,.0f}. Payment within 2 business days.",
        "rejected": f"❌ Claim {claim_id} could not be approved. Please contact your advisor.",
        "pending":  f"⏳ Claim {claim_id} is under review. We'll notify you within 24 hours.",
    }

    message    = messages.get(final_status, messages["pending"])
    settlement = estimate if final_status == "approved" else None

    # Production: replace with boto3 SNS publish
    # sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message)
    logger.info(f"[{claim_id}] NOTIFICATION — {final_status.upper()}: {message}")

    return {
        "final_status":          final_status,
        "settlement_amount_inr": settlement,
        "audit_trail": [audit_entry(
            "notification_node",
            f"Notification sent — {final_status.upper()}"
            + (f" | Settlement: ₹{settlement:,.0f}" if settlement else "")
        )],
    }