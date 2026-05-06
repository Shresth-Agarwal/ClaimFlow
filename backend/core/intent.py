def detect_intent(query):
    query_lower = query.lower()
    
    coverage_keywords = ["surgery", "treatment", "covered"]
    if any(word in query_lower for word in coverage_keywords):
        return "coverage"
        
    limit_keywords = ["limit", "maximum", "how much"]
    if any(word in query_lower for word in limit_keywords):
        return "limit"
        
    rejection_keywords = ["not", "fail", "reject", "pre-authorize"]
    if any(word in query_lower for word in rejection_keywords):
        return "rejection"
        
    return "unknown"
