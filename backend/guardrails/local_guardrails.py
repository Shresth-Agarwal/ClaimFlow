# This will be enhanced by Amazon Bedrock Guardrails
import boto3

def apply_bedrock_guardrail(text, guardrail_id, guardrail_version):
    client = boto3.client('bedrock-runtime')
    response = client.apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion=guardrail_version,
        source='INPUT',
        content=[{'text': {'text': text}}]
    )
    if response.get('action') == 'GUARDRAIL_INTERVENED':
        for output in response.get('outputs', []):
            return output.get('text', text)
    return text

import re

def validate(response):
    if response is None:
        return {
            "answer": "I don't know based on the provided policy.",
            "source": None,
            "confidence": "low"
        }
    return response

def pii_mask(response):
    if response is None or "answer" not in response:
        return response
        
    text = str(response["answer"])
    
    # Mask Aadhaar numbers (12 digits)
    text = re.sub(r'\b\d{4}[ -]?\d{4}[ -]?\d{4}\b', '[REDACTED]', text)
    
    # Mask Phone numbers (10 digits)
    text = re.sub(r'\b\d{10}\b', '[REDACTED]', text)
    
    response["answer"] = text
    return response

def financial_check(response, query):
    if response is None:
        return response
        
    LIMIT = 200000
    
    # 1. Detect lakh format
    lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*lakh', query, re.IGNORECASE)
    if lakh_match:
        extracted_amount = int(float(lakh_match.group(1)) * 100000)
    else:
        # 2. Detect numeric sequences like ₹5,00,000 or 500000
        matches = re.findall(r'\d+(?:,\d+)*', query)
        extracted_amount = 0
        if matches:
            extracted_amount = max(int(m.replace(',', '')) for m in matches)
            
    if extracted_amount > LIMIT:
        response["compliance"] = "escalated"
    else:
        response["compliance"] = "ok"
        
    return response
