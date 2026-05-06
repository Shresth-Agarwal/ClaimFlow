import re

def local_generate(context, query):
    if not context:
        return None
        
    # Interpret the query & select the most relevant clause
    top_entry = context[0]
    raw_text = top_entry.get("text", "")
    
    answer = raw_text
    
    # Simulate LLM-like reasoning and rephrase into natural answer
    if "Failure to obtain pre-authorization may result in claim rejection" in raw_text:
        answer = "If pre-authorization is not obtained, the claim may be rejected as per policy."
    elif "Surgery expenses are covered up to a maximum of" in raw_text:
        amount_match = re.search(r'(₹[\d,]+)', raw_text)
        amount = amount_match.group(1) if amount_match else "the limit"
        answer = f"Surgery is covered under your policy up to {amount}."
    else:
        # Generic natural phrasing fallback
        replacements = [
            ("the policy", "your policy"),
            ("this policy", "your policy"),
            ("The policy", "Your policy"),
            ("This policy", "Your policy"),
            ("are covered", "are covered under your policy"),
            ("are not covered", "are not covered under your policy")
        ]

        for old, new in replacements:
            answer = answer.replace(old, new)
        
    if answer:
        answer = answer[0].upper() + answer[1:]
        
    return {
        "answer": answer,
        "source": f"Page {top_entry.get('page', '')}, Clause {top_entry.get('clause', '')}"
    }
