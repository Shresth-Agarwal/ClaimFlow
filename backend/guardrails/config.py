import os
import json
import boto3
from botocore.exceptions import ClientError
from .local_guardrails import pii_mask

def get_guardrail_config():
    guardrail_id = os.environ.get("GUARDRAIL_ID")
    guardrail_version = os.environ.get("GUARDRAIL_VERSION")
    
    if not guardrail_id or not guardrail_version:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'guardrail_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                guardrail_id = guardrail_id or config.get("guardrail_id")
                guardrail_version = guardrail_version or config.get("guardrail_version")
        except FileNotFoundError:
            pass
            
    return {
        "guardrailId": guardrail_id,
        "guardrailVersion": guardrail_version
    }

def apply_guardrail(text: str) -> dict:
    config = get_guardrail_config()
    guardrail_id = config.get("guardrailId")
    guardrail_version = config.get("guardrailVersion")
    
    def fallback_local(t):
        masked_resp = pii_mask({"answer": t})
        return {
            "filtered_text": masked_resp.get("answer", t),
            "action": "NONE",
            "is_blocked": False
        }

    if not guardrail_id or not guardrail_version:
        return fallback_local(text)
        
    try:
        client = boto3.client('bedrock-runtime')
        response = client.apply_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            source='INPUT',
            content=[{'text': {'text': text}}]
        )
        
        bedrock_action = response.get('action', 'NONE')
        
        if bedrock_action == 'GUARDRAIL_INTERVENED':
            is_blocked = False
            
            # Check if any assessment resulted in a BLOCKED action
            for assessment in response.get('assessments', []):
                for key, val in assessment.items():
                    if isinstance(val, dict):
                        if val.get('action') == 'BLOCKED':
                            is_blocked = True
                    elif isinstance(val, list):
                        for item in val:
                            if isinstance(item, dict) and item.get('action') == 'BLOCKED':
                                is_blocked = True
            
            if is_blocked:
                return {
                    "filtered_text": "I cannot process this request. Please ask questions related to your insurance policy.",
                    "action": "BLOCKED",
                    "is_blocked": True
                }
            else:
                # If not blocked, it was likely anonymized/masked
                filtered_text = text
                if response.get('outputs') and len(response['outputs']) > 0:
                    filtered_text = response['outputs'][0].get('text', text)
                    
                return {
                    "filtered_text": filtered_text,
                    "action": "ANONYMIZED",
                    "is_blocked": False
                }
        else:
            return {
                "filtered_text": text,
                "action": "NONE",
                "is_blocked": False
            }
            
    except Exception as e:
        print(f"Error calling Bedrock Guardrails: {e}. Falling back to local guardrails.")
        return fallback_local(text)

def financial_guardrail(claim_amount: float) -> dict:
    if claim_amount > 200000:
        return {
            "compliance": "escalated",
            "reason": "Claim exceeds Rs 2,00,000 auto-approval limit",
            "requires_human": True
        }
    else:
        return {
            "compliance": "ok",
            "requires_human": False
        }
