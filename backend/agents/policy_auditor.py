import os
import sys
import json

# Ensure we can import from backend root when running directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.inclusion_agent import InclusionAgent
from guardrails.config import apply_guardrail, financial_guardrail

class PolicyAuditor:
    def __init__(self):
        self.inclusion_agent = InclusionAgent()

    def audit(self, claim: dict) -> dict:
        claim_id = claim.get("claim_id")
        claim_type = claim.get("claim_type")
        claim_amount = claim.get("claim_amount", 0.0)
        description = claim.get("description", "")
        
        # Step 1 - PII check on description field
        guardrail_resp = apply_guardrail(description)
        if guardrail_resp.get("is_blocked") or guardrail_resp.get("action") == "BLOCKED":
            return {
                "claim_id": claim_id,
                "audit_status": "BLOCKED",
                "note": "Blocked by PII guardrail"
            }
            
        pii_check = "clean"
        if guardrail_resp.get("action") == "ANONYMIZED" or guardrail_resp.get("filtered_text") != description:
            pii_check = "redacted"

        # Step 2 - Financial check
        fin_resp = financial_guardrail(claim_amount)
        requires_human = fin_resp.get("requires_human", False)
        financial_compliance = fin_resp.get("compliance", "ok")

        # Step 3 - Inclusion check
        inclusion_resp = self.inclusion_agent.check(claim_type, claim_amount)
        included = inclusion_resp.get("included")

        # Step 4 - Build audit result
        if requires_human:
            audit_status = "ESCALATED"
        elif included is False:
            audit_status = "REJECTED"
        elif included is None:
            audit_status = "UNCERTAIN"
        else: # included is True and requires_human is False
            audit_status = "APPROVED"

        return {
            "claim_id": claim_id,
            "claim_type": claim_type,
            "included": included,
            "financial_compliance": financial_compliance,
            "requires_human": requires_human,
            "pii_check": pii_check,
            "answer": inclusion_resp.get("answer"),
            "source": inclusion_resp.get("source"),
            "confidence": inclusion_resp.get("confidence"),
            "audit_status": audit_status,
            "note": "Audited by PolicyAuditor"
        }

if __name__ == "__main__":
    auditor = PolicyAuditor()
    
    test_cases = [
        {
            "claim_id": "CLM-001", "claim_type": "surgery", 
            "claim_amount": 150000, "claimant_name": "John Doe",
            "description": "Emergency surgery at Apollo Hospital"
        },
        {
            "claim_id": "CLM-002", "claim_type": "gym membership",
            "claim_amount": 5000, "claimant_name": "Jane Smith",
            "description": "Monthly gym fees"
        },
        {
            "claim_id": "CLM-003", "claim_type": "hospitalization",
            "claim_amount": 500000, "claimant_name": "Bob Kumar",
            "description": "ICU admission for 5 days"
        },
        {
            "claim_id": "CLM-004", "claim_type": "surgery",
            "claim_amount": 80000, "claimant_name": "My Aadhaar is 123456789012",
            "description": "Knee surgery"
        }
    ]
    
    results = []
    for test in test_cases:
        res = auditor.audit(test)
        results.append(res)
        
    print(json.dumps(results, indent=2))
