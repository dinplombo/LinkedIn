"""
Job Parser - Extract job details and required years from job descriptions
"""
import re


def extract_required_years(description):
    """
    Extract required years of experience from job description text.
    
    Returns a string like "3+ years", "2-5 years", or "Not specified"
    """
    if not description:
        return "Not specified"
    
    description_lower = description.lower()
    
    # Patterns to match various experience requirements
    patterns = [
        # "5+ years", "5 + years", "5+ yrs"
        r'(\d+)\s*\+\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)?',
        
        # "3-5 years", "3 - 5 years", "3 to 5 years"
        r'(\d+)\s*[-–—to]+\s*(\d+)\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)?',
        
        # "minimum 3 years", "at least 5 years"
        r'(?:minimum|at\s+least|min\.?)\s*(\d+)\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)?',
        
        # "5 years of experience", "5 years experience"
        r'(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)',
        
        # "experience: 5 years", "experience - 5 years"
        r'(?:experience|exp)[\s:–—-]+(\d+)\s*(?:years?|yrs?)',
        
        # "5 years' experience"
        r"(\d+)\s*(?:years?'?|yrs?'?)\s+experience",
        
        # General pattern for X years
        r'(\d+)\s*(?:years?|yrs?)\b',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, description_lower)
        if matches:
            match = matches[0]
            if isinstance(match, tuple):
                # Range match (e.g., "3-5 years")
                if len(match) == 2 and match[1]:
                    return f"{match[0]}-{match[1]} years"
                else:
                    return f"{match[0]}+ years"
            else:
                # Check if original context suggests "plus" years
                if re.search(rf'{match}\s*\+', description_lower):
                    return f"{match}+ years"
                return f"{match} years"
    
    return "Not specified"


# Test the parser
if __name__ == "__main__":
    # Test cases for extract_required_years
    test_descriptions = [
        "Looking for a developer with 5+ years of experience in Python",
        "Requirements: 3-5 years of software development experience",
        "Minimum 2 years of experience required",
        "We need someone with at least 7 years experience",
        "5 years of experience in web development",
        "Experience: 3 years in similar role",
        "No experience mentioned in this description",
        "Bachelor's degree required, 4+ yrs of relevant experience",
        "Looking for a senior developer with 8 to 10 years of experience",
    ]
    
    print("Testing extract_required_years function:")
    print("-" * 60)
    
    for desc in test_descriptions:
        result = extract_required_years(desc)
        print(f"Description: {desc[:50]}...")
        print(f"Extracted: {result}")
        print("-" * 60)

