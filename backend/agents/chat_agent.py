"""
ClaimFlow Chat Agent
===================
Handles conversational queries that don't require the full claims pipeline.
Examples:
- "What's covered under my health policy?"
- "How do I submit a claim?"
- "What documents do I need for motor insurance?"
- "Check status of claim CLM-20260506-ABC123"

This agent uses the same knowledge base as policy_auditor but in conversational mode.
"""

import json
import logging
import os
import re
from typing import Dict, Any, Optional

logger = logging.getLogger("claimflow.chat_agent")

# Import the same KB functions as policy_auditor
try:
    from backend.agents.policy_auditor import _load_kb, _load_kb_config, _query_bedrock_kb
    _KB_CLAUSES = _load_kb()
    _KB_CFG = _load_kb_config()
except ImportError:
    logger.warning("Policy auditor not available - chat will have limited knowledge")
    _KB_CLAUSES = []
    _KB_CFG = {}


def _extract_claim_id(text: str) -> Optional[str]:
    """Extract claim ID from user message if present."""
    # Look for patterns like CLM-20260506-ABC123 or TEST-131551
    match = re.search(r'\b(CLM-\d{8}-[A-Z0-9]{6}|TEST-\d{6})\b', text, re.IGNORECASE)
    return match.group(1) if match else None


def _classify_intent(text: str) -> str:
    """Classify user intent from their message."""
    text_lower = text.lower()
    
    # Claim status check
    if any(word in text_lower for word in ['status', 'check claim', 'claim id', 'clm-', 'test-']):
        return "claim_status"
    
    # Policy coverage questions
    if any(word in text_lower for word in ['covered', 'coverage', 'eligible', 'policy', 'include']):
        return "policy_query"
    
    # Claims process questions
    if any(word in text_lower for word in ['submit', 'file claim', 'documents needed', 'how to']):
        return "process_help"
    
    # Greeting/general
    if any(word in text_lower for word in ['hello', 'hi', 'help', 'what can you']):
        return "greeting"
    
    return "general"


def _search_knowledge_base(query: str) -> list[str]:
    """Search local knowledge base for relevant clauses."""
    query_lower = query.lower()
    relevant_clauses = []
    
    for entry in _KB_CLAUSES:
        text = entry.get("text", "").lower()
        if any(word in text for word in query_lower.split() if len(word) > 3):
            clause_text = f"Clause {entry.get('clause', '?')}: {entry.get('text', '')}"
            relevant_clauses.append(clause_text)
    
    return relevant_clauses[:3]  # Top 3 most relevant


def _generate_policy_response(query: str) -> str:
    """Generate response for policy-related questions."""
    relevant_clauses = _search_knowledge_base(query)
    
    if not relevant_clauses:
        return (
            "I couldn't find specific information about that in your policy. "
            "Please contact your insurance advisor for detailed coverage information."
        )
    
    response = "Based on your policy:\n\n"
    for clause in relevant_clauses:
        response += f"• {clause}\n"
    
    response += "\nFor specific claim eligibility, please submit your documents for assessment."
    return response


def _generate_process_help(query: str) -> str:
    """Generate response for process/how-to questions."""
    query_lower = query.lower()
    
    if "submit" in query_lower or "file" in query_lower:
        return (
            "To submit a claim:\n\n"
            "1. **Online**: Use our web portal to upload photos and fill claim details\n"
            "2. **API**: POST to /api/claims/submit-with-documents with your documents\n"
            "3. **Required info**: Policy number, incident date, description, supporting documents\n\n"
            "**Documents needed**:\n"
            "• Health: Hospital bills, discharge summary, prescriptions\n"
            "• Motor: Repair invoices, photos of damage, police report (if applicable)\n"
            "• Property: FIR copy, damage photos, ownership documents\n"
            "• Crop: Field photos, weather reports, land documents\n\n"
            "Claims are processed within 24-48 hours."
        )
    
    if "document" in query_lower:
        return (
            "**Required documents by claim type**:\n\n"
            "**Health Insurance**:\n"
            "• Hospital bills with patient name and UHID\n"
            "• Discharge summary\n"
            "• Prescriptions and lab reports\n"
            "• ID proof\n\n"
            "**Motor Insurance**:\n"
            "• Repair invoices from authorized workshops\n"
            "• Photos of vehicle damage\n"
            "• Registration certificate (RC)\n"
            "• Driving license\n"
            "• Police FIR (for theft/major accidents)\n\n"
            "**Property Insurance**:\n"
            "• FIR copy from local police station\n"
            "• Photos of damaged property\n"
            "• Ownership documents\n"
            "• Repair estimates\n\n"
            "All documents should be clear, legible photos or scanned copies."
        )
    
    return (
        "I can help you with:\n"
        "• Submitting claims\n"
        "• Required documents\n"
        "• Policy coverage questions\n"
        "• Claim status updates\n\n"
        "What specific information do you need?"
    )


async def handle_chat_query(
    user_message: str,
    user_id: str,
    session_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main chat handler - processes user message and returns appropriate response.
    
    Args:
        user_message: User's text input
        user_id: User identifier for session tracking
        session_context: Previous conversation context (optional)
    
    Returns:
        {
            "response": str,
            "intent": str,
            "claim_id": str | None,
            "requires_pipeline": bool,
            "suggested_actions": list[str]
        }
    """
    intent = _classify_intent(user_message)
    claim_id = _extract_claim_id(user_message)
    
    logger.info(f"[chat] User {user_id}: intent={intent}, claim_id={claim_id}")
    
    # Handle claim status queries
    if intent == "claim_status" and claim_id:
        try:
            # Import here to avoid circular imports
            if os.getenv("USE_MOCK_DB", "false").lower() == "true":
                from backend.database.mock_claims_db import get_claim
            else:
                from backend.database.dynamo_db import get_claim
            
            claim = await get_claim(claim_id)
            if not claim:
                return {
                    "response": f"I couldn't find claim {claim_id}. Please check the claim ID and try again.",
                    "intent": intent,
                    "claim_id": claim_id,
                    "requires_pipeline": False,
                    "suggested_actions": ["Submit a new claim", "Contact support"]
                }
            
            status = claim.get("status", "unknown")
            routing = claim.get("routing_decision", "")
            fraud_score = claim.get("fraud_score")
            estimate = claim.get("damage_estimate")
            
            response = f"**Claim {claim_id} Status**: {status.title()}\n\n"
            
            if status == "approved":
                response += f"✅ Your claim has been approved!\n"
                if estimate:
                    response += f"💰 Settlement amount: ₹{estimate:,.0f}\n"
                response += "Payment will be processed within 2 business days."
            
            elif status == "rejected":
                response += "❌ Your claim could not be approved.\nPlease contact your insurance advisor for details."
            
            elif status == "pending_review" or routing == "human_queue":
                response += "⏳ Your claim is under review by our team.\n"
                if fraud_score is not None:
                    response += f"Current assessment: {fraud_score:.0f}/100 risk score\n"
                response += "We'll notify you within 24 hours."
            
            else:
                response += f"🔄 Processing in progress...\nCurrent stage: {routing or 'Initial review'}"
            
            return {
                "response": response,
                "intent": intent,
                "claim_id": claim_id,
                "requires_pipeline": False,
                "suggested_actions": ["View full report", "Contact support"] if status in ["approved", "rejected"] else ["Wait for update"]
            }
            
        except Exception as e:
            logger.error(f"Error fetching claim {claim_id}: {e}")
            return {
                "response": f"Sorry, I encountered an error checking claim {claim_id}. Please try again later.",
                "intent": intent,
                "claim_id": claim_id,
                "requires_pipeline": False,
                "suggested_actions": ["Try again", "Contact support"]
            }
    
    # Handle policy coverage questions
    elif intent == "policy_query":
        response = _generate_policy_response(user_message)
        return {
            "response": response,
            "intent": intent,
            "claim_id": None,
            "requires_pipeline": False,
            "suggested_actions": ["Submit a claim", "Ask another question", "View policy document"]
        }
    
    # Handle process help
    elif intent == "process_help":
        response = _generate_process_help(user_message)
        return {
            "response": response,
            "intent": intent,
            "claim_id": None,
            "requires_pipeline": False,
            "suggested_actions": ["Submit a claim now", "Upload documents", "Ask about coverage"]
        }
    
    # Handle greetings
    elif intent == "greeting":
        response = (
            "Hello! I'm your ClaimFlow assistant. I can help you with:\n\n"
            "🔍 **Check claim status** - Just mention your claim ID\n"
            "📋 **Policy coverage** - Ask what's covered under your insurance\n"
            "📤 **Submit claims** - Guide you through the claims process\n"
            "📄 **Required documents** - Tell you what documents you need\n\n"
            "What can I help you with today?"
        )
        return {
            "response": response,
            "intent": intent,
            "claim_id": None,
            "requires_pipeline": False,
            "suggested_actions": ["Check claim status", "Ask about coverage", "Submit new claim"]
        }
    
    # General/fallback
    else:
        # Check if this looks like a claim submission (has keywords but no clear intent)
        claim_keywords = ['accident', 'hospital', 'damage', 'bill', 'invoice', 'repair', 'treatment']
        if any(word in user_message.lower() for word in claim_keywords):
            return {
                "response": (
                    "It sounds like you want to submit a claim! To process your claim properly, "
                    "I'll need you to upload supporting documents (photos, bills, reports).\n\n"
                    "You can:\n"
                    "• Use the 'Submit Claim' button to upload documents\n"
                    "• Or ask me about what documents you need for your specific situation\n\n"
                    "What type of claim is this? (Health, Motor, Property, or Crop)"
                ),
                "intent": "claim_submission_prompt",
                "claim_id": None,
                "requires_pipeline": True,
                "suggested_actions": ["Submit claim with documents", "Ask about required documents"]
            }
        
        # True general query
        response = (
            "I can help you with insurance claims and policy questions. Try asking:\n\n"
            "• \"What's covered under health insurance?\"\n"
            "• \"How do I submit a motor claim?\"\n"
            "• \"Check status of claim CLM-20260506-ABC123\"\n"
            "• \"What documents do I need?\"\n\n"
            "Or use the 'Submit Claim' option to file a new claim with documents."
        )
        return {
            "response": response,
            "intent": "general",
            "claim_id": None,
            "requires_pipeline": False,
            "suggested_actions": ["Ask about coverage", "Submit new claim", "Check claim status"]
        }


# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test_chat():
        test_queries = [
            "Hello, what can you help me with?",
            "What's covered under health insurance?",
            "How do I submit a motor claim?",
            "Check status of claim TEST-131551",
            "I had an accident and need to file a claim",
            "What documents do I need for property insurance?"
        ]
        
        for query in test_queries:
            print(f"\n🔵 User: {query}")
            result = await handle_chat_query(query, "test-user", {})
            print(f"🤖 Bot: {result['response']}")
            print(f"   Intent: {result['intent']}")
            if result['suggested_actions']:
                print(f"   Suggestions: {', '.join(result['suggested_actions'])}")
    
    asyncio.run(test_chat())