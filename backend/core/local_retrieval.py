import string
import re

def local_retrieve(original_query, kb):
    stopwords = {"is", "the", "can", "i", "a", "an", "what", "if", "for", "to"}
    
    synonyms_map = {
        "surgery": ["operation", "treatment"],
        "claim": ["coverage", "reimbursement"],
        "limit": ["maximum", "cap"],
        "gym": ["fitness", "workout"],
        "pre-authorize": ["approval", "authorization", "pre-authorization"],
        "pre-authorization": ["approval", "authorization", "pre-authorize"]
    }
    
    domain_keywords = {"surgery", "claim", "insurance", "hospital", "damage", "vehicle", "pre-authorize", "pre-authorization"}
    invalid_keywords = {"gym", "fitness", "workout"}
    
    query = original_query.lower()
    
    # Check for rejection queries before replacing anything
    rejection_query_words = ["not", "fail", "don't", "don’t", "without"]
    has_rejection_query = any(word in query for word in rejection_query_words)
    
    # 1. Normalize query
    query = re.sub(r"don['’]t\s+pre-?authorize", "pre-authorization", query)
    query = re.sub(r"do\s+not\s+pre-?authorize", "pre-authorization", query)
    query = re.sub(r"no\s+pre-?authorization", "pre-authorization", query)
    
    # Replace don't -> not
    query = query.replace("don’t", "not")
    query = query.replace("don't", "not")
    
    # Remove punctuation except hyphen
    for p in string.punctuation:
        if p != '-':
            query = query.replace(p, " ")
            
    # Standardize words and remove stopwords
    raw_words = query.split()
    keywords = set()
    for word in raw_words:
        if word and word not in stopwords:
            keywords.add(word)
            
    # Check for invalid keywords
    if any(kw in invalid_keywords for kw in keywords):
        return []
        
    # Check domain-specific condition: at least one domain keyword must be present
    if not any(kw in domain_keywords for kw in keywords):
        return []
            
    scored_entries = []
    
    # Process each KB entry
    for entry in kb:
        text_lower = entry.get("text", "").lower()
        score = 0
        
        # Rejection boosting logic
        if has_rejection_query:
            rejection_entry_words = ["reject", "pre-authorization", "failure"]
            if any(word in text_lower for word in rejection_entry_words):
                score += 3
        
        # Standard scoring logic
        for kw in keywords:
            if kw in text_lower:
                score += 2
            elif kw in synonyms_map:
                # Check for synonym match
                for syn in synonyms_map[kw]:
                    if syn in text_lower:
                        score += 1
                        break
                        
        # Only keep results where score >= 2
        if score >= 2:
            scored_entries.append((score, entry))
            
    # Sort results by score (descending)
    scored_entries.sort(key=lambda x: x[0], reverse=True)
    
    # If no valid results, returns []
    return [entry for score, entry in scored_entries[:3]]
