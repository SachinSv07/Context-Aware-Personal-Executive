"""
Email search tool
Developer 1: Implement email searching logic here
"""

import json
from typing import List, Dict, Any
from pathlib import Path
from config import EMAIL_DATA_PATH, MAX_SEARCH_RESULTS
from utils.helpers import log_info, log_error, calculate_similarity


def search_email(query: str) -> List[Dict[str, Any]]:
    """
    Search through email data
    
    Args:
        query: User's search query
    
    Returns:
        List of matching emails
    
    Developer 1 TODO:
        1. Load emails from EMAIL_DATA_PATH (JSON file)
        2. Search through subject, from, to, and body fields
        3. Rank results by relevance
        4. Return top MAX_SEARCH_RESULTS results
        5. Handle errors gracefully
    """
    log_info(f"Searching emails for: {query}")
    
    try:
        # Load email data
        if not Path(EMAIL_DATA_PATH).exists():
            log_error(f"Email data file not found: {EMAIL_DATA_PATH}")
            return []
        
        with open(EMAIL_DATA_PATH, 'r', encoding='utf-8') as f:
            emails = json.load(f)
        
        # Search logic
        results = []
        query_lower = query.lower()
        
        for email in emails:
            # Calculate relevance score
            score = 0.0
            
            # Check subject
            if query_lower in email.get('subject', '').lower():
                score += 0.4
            
            # Check body
            if query_lower in email.get('body', '').lower():
                score += 0.3
            
            # Check sender
            if query_lower in email.get('from', '').lower():
                score += 0.2
            
            # Use similarity for better matching
            subject_sim = calculate_similarity(query, email.get('subject', ''))
            body_sim = calculate_similarity(query, email.get('body', ''))
            score += (subject_sim * 0.5 + body_sim * 0.5) * 0.3
            
            if score > 0:
                results.append({
                    **email,
                    'relevance_score': score,
                    'source': 'Sample Email Data'
                })
        
        # Sort by relevance and return top results
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        top_results = results[:MAX_SEARCH_RESULTS]
        
        log_info(f"Found {len(top_results)} matching emails")
        return top_results
    
    except Exception as e:
        log_error(f"Error searching emails", e)
        return []


class EmailTool:
    """
    Class-based email search tool.
    Searches email bodies for a given query string.
    """

    def run(self, query: str):
        """
        Search through emails for a query match in the body.

        Args:
            query: The keyword or phrase to search for.

        Returns:
            List of matching email bodies, or a 'not found' message.
        """
        results = []

        try:
            with open("sample_data/emails.json", "r", encoding="utf-8") as file:
                emails = json.load(file)

            print("Searching for:", query)
            for email in emails:
                content = email.get("body", "")
                print("Checking:", content)
                if query.lower() in content.lower():
                    results.append(content)

        except FileNotFoundError:
            return "Email data file not found"
        except Exception as e:
            return f"Error reading emails: {e}"

        if not results:
            return "No relevant email found"

        return results


# Tool specification for OpenAI function calling
EMAIL_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "search_email",
        "description": "Search through emails by subject, sender, or content. Use this when the user asks about emails, messages, or correspondence.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant emails"
                }
            },
            "required": ["query"]
        }
    }
}


if __name__ == "__main__":
    # Test the function-based search
    test_query = "meeting"
    results = search_email(test_query)
    print(f"Search results for '{test_query}':")
    for idx, result in enumerate(results, 1):
        print(f"{idx}. {result.get('subject')} (Score: {result.get('relevance_score', 0):.2f})")

    # Test the class-based EmailTool
    print("\n--- EmailTool class ---")
    tool = EmailTool()
    class_results = tool.run(test_query)
    if isinstance(class_results, list):
        for idx, body in enumerate(class_results, 1):
            print(f"{idx}. {body[:80]}...")
    else:
        print(class_results)
