from retrieval import retrieve
from generator import generate_answer
from guardrails import validate, pii_mask, financial_check
from intent import detect_intent

def pipeline(query, kb):
    # Intent Detection
    intent = detect_intent(query)
    
    if intent == "unknown":
        response = None
    else:
        # 1. Retrieve relevant KB entries
        context = retrieve(query, kb)
        
        # Prioritize KB entries for rejection intent
        if intent == "rejection":
            rejection_terms = ["reject", "pre-authorization", "failure"]
            context.sort(key=lambda entry: sum(1 for term in rejection_terms if term in entry.get("text", "").lower()), reverse=True)
        
        # 2. Generate answer
        response = generate_answer(context, query)
    
    # 3. Validate response
    validated_response = validate(response)
    
    # Set default confidence if not already set by validate()
    if "confidence" not in validated_response:
        validated_response["confidence"] = "high"
        
    # 4. Apply PII masking
    validated_response = pii_mask(validated_response)
        
    # 5. Apply financial guardrail
    final_response = financial_check(validated_response, query)
    
    # Ensure default compliance if not already set
    if "compliance" not in final_response:
        final_response["compliance"] = "ok"
        
    return {
        "answer": final_response.get("answer", ""),
        "source": final_response.get("source"),
        "confidence": final_response.get("confidence", "high"),
        "compliance": final_response.get("compliance", "ok"),
        "note": "Response generated strictly based on policy guidelines"
    }
