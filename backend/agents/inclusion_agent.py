import os
import sys
import json
import boto3

# Ensure we can import from core when running directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def query_bedrock_kb(query: str) -> dict:
    try:
        # Read KB ID from kb_config.json
        config_path = os.path.join(os.path.dirname(__file__), '..', 'kb_config.json')
        with open(config_path) as f:
            kb_config = json.load(f)
        
        kb_id = kb_config["knowledge_base_id"]
        
        bedrock = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
        
        response = bedrock.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kb_id,
                    "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
                }
            }
        )
        
        answer = response["output"]["text"]
        citations = response.get("citations", [])
        
        source = "Policy Document"
        if citations:
            refs = citations[0].get("retrievedReferences", [])
            if refs:
                metadata = refs[0].get("metadata", {})
                page = metadata.get("page", "N/A")
                clause = metadata.get("clause", "N/A")
                source = f"Page {page}, Clause {clause}"
        
        return {
            "answer": answer,
            "source": source,
            "confidence": "low" if "don't know" in answer.lower() else "high"
        }
    
    except Exception as e:
        # Fallback to local retrieval if Bedrock fails
        from core.local_retrieval import local_retrieve
        from core.local_generator import local_generate
        kb_path = os.path.join(os.path.dirname(__file__), '..', 'insurance_kb.json')
        try:
            with open(kb_path, 'r', encoding='utf-8') as f:
                kb = json.load(f)
        except Exception:
            kb = []
            
        context = local_retrieve(query, kb)
        if not context:
            return {
                "answer": "I don't know based on the provided policy.",
                "source": None,
                "confidence": "low"
            }
            
        result = local_generate(context, query)
        return {
            "answer": result.get("answer", "I don't know based on the provided policy."),
            "source": result.get("source", None),
            "confidence": "low"
        }

class InclusionAgent:
    def check(self, claim_type: str, claim_amount: float = None) -> dict:
        query = f"Is {claim_type} covered under this insurance policy?"
        
        rag_response = query_bedrock_kb(query)
        
        answer = rag_response.get("answer", "")
        if not isinstance(answer, str):
            answer = str(answer)
            
        answer_lower = answer.lower()
        
        included = None
        if "not covered" in answer_lower or "excluded" in answer_lower:
            included = False
        elif "covered" in answer_lower or "eligible" in answer_lower:
            included = True
        elif "i don't know" in answer_lower:
            included = None
            
        return {
            "claim_type": claim_type,
            "included": included,
            "answer": answer,
            "source": rag_response.get("source"),
            "confidence": rag_response.get("confidence", "high" if included is not None else "low"),
            "compliance": rag_response.get("compliance", "ok"),
            "note": "Checked by InclusionAgent"
        }

if __name__ == "__main__":
    agent = InclusionAgent()
    
    test_cases = [
        ("surgery", None),
        ("gym membership", None),
        ("hospitalization", 150000.0),
        ("dental treatment", None)
    ]
    
    results = []
    for claim_type, amount in test_cases:
        res = agent.check(claim_type=claim_type, claim_amount=amount)
        results.append(res)
        
    print(json.dumps(results, indent=2))
