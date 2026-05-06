import sys
import os
import json

# Ensure we can import from backend root when running directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.policy_auditor import PolicyAuditor

def generate_synthetic_claims():
    claims = [
        {
            "claim_id": "CLM-SYN-001",
            "claim_type": "surgery",
            "claim_amount": 120000.0,
            "claimant_name": "Rajesh Sharma",
            "description": "Appendectomy surgery performed at Fortis Escorts Hospital."
        },
        {
            "claim_id": "CLM-SYN-002",
            "claim_type": "hospitalization",
            "claim_amount": 250000.0,  # Edge case: > 2,00,000
            "claimant_name": "Priya Patel",
            "description": "Admitted to ICU for 4 days due to severe dengue fever."
        },
        {
            "claim_id": "CLM-SYN-003",
            "claim_type": "dental",
            "claim_amount": 15000.0,
            "claimant_name": "Amit Kumar",
            "description": "Root canal treatment and dental crown installation."
        },
        {
            "claim_id": "CLM-SYN-004",
            "claim_type": "gym membership",  # Edge case: out of scope
            "claim_amount": 18000.0,
            "claimant_name": "Sneha Iyer",
            "description": "Annual gym membership fee for fitness and wellness."
        },
        {
            "claim_id": "CLM-SYN-005",
            "claim_type": "maternity",
            "claim_amount": 80000.0,
            "claimant_name": "Neha Gupta",
            "description": "Normal delivery and post-natal care at Cloudnine Hospital."
        },
        {
            "claim_id": "CLM-SYN-006",
            "claim_type": "fracture",
            "claim_amount": 300000.0,  # Edge case: > 2,00,000
            "claimant_name": "Vikram Singh",
            "description": "Surgery and hospitalization for compound fracture in right femur."
        },
        {
            "claim_id": "CLM-SYN-007",
            "claim_type": "outpatient",
            "claim_amount": 5500.0,
            "claimant_name": "Anjali Desai",
            "description": "Outpatient consultation and diagnostic tests for persistent cough. Aadhaar provided: 9876 5432 1098." # Edge case: Aadhaar in description
        },
        {
            "claim_id": "CLM-SYN-008",
            "claim_type": "pharmacy",
            "claim_amount": 8500.0,
            "claimant_name": "Rahul Verma",
            "description": "Prescription medicines for hypertension and diabetes."
        },
        {
            "claim_id": "CLM-SYN-009",
            "claim_type": "hospitalization",
            "claim_amount": 45000.0,
            "claimant_name": "Kavita Rao",
            "description": "Hospitalization for food poisoning and intravenous fluids."
        },
        {
            "claim_id": "CLM-SYN-010",
            "claim_type": "surgery",
            "claim_amount": 175000.0,
            "claimant_name": "Suresh Nair",
            "description": "Cataract surgery with premium intraocular lens implant."
        }
    ]
    return claims

if __name__ == "__main__":
    auditor = PolicyAuditor()
    claims = generate_synthetic_claims()
    
    results = []
    for claim in claims:
        print(f"Auditing claim {claim['claim_id']}...")
        result = auditor.audit(claim)
        results.append(result)
        
    print("\n--- Final Audit Results ---")
    print(json.dumps(results, indent=2))
