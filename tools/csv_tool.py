"""
CSV search tool
Developer 1: Implement CSV searching logic here
"""

import csv
from typing import List, Dict, Any
from pathlib import Path
from config import CSV_DATA_PATH, MAX_SEARCH_RESULTS
from utils.helpers import log_info, log_error, calculate_similarity


def search_csv(query: str) -> List[Dict[str, Any]]:
    """
    Search through CSV notes/data
    
    Args:
        query: User's search query
    
    Returns:
        List of matching CSV rows
    
    Developer 1 TODO:
        1. Load CSV file (notes.csv)
        2. Search through all columns
        3. Return matching rows with column names
        4. Handle different CSV formats
        5. Consider using pandas for advanced filtering (optional)
    """
    log_info(f"Searching CSV for: {query}")
    
    try:
        # Check if CSV file exists
        if not Path(CSV_DATA_PATH).exists():
            log_error(f"CSV file not found: {CSV_DATA_PATH}")
            return []
        
        results = []
        query_lower = query.lower()
        
        # Read CSV file
        with open(CSV_DATA_PATH, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=1):
                # Calculate relevance score
                score = 0.0
                matching_fields = []
                
                # Search through all fields
                for field, value in row.items():
                    if value and query_lower in str(value).lower():
                        score += 0.5
                        matching_fields.append(field)
                    
                    # Calculate similarity
                    if value:
                        similarity = calculate_similarity(query, str(value))
                        score += similarity * 0.3
                
                if score > 0:
                    results.append({
                        'row_number': row_num,
                        'data': row,
                        'matching_fields': matching_fields,
                        'relevance_score': score,
                        'source': 'CSV Notes'
                    })
        
        # Sort by relevance and return top results
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        top_results = results[:MAX_SEARCH_RESULTS]
        
        log_info(f"Found {len(top_results)} matching CSV rows")
        return top_results
    
    except Exception as e:
        log_error(f"Error searching CSV", e)
        return []


# Alternative implementation using pandas (optional)
def search_csv_pandas(query: str) -> List[Dict[str, Any]]:
    """
    Search CSV using pandas (requires pandas library)
    
    Developer 1: Uncomment and use this if you prefer pandas
    """
    # import pandas as pd
    # 
    # try:
    #     df = pd.read_csv(CSV_DATA_PATH)
    #     
    #     # Search across all columns
    #     mask = df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)
    #     matching_rows = df[mask]
    #     
    #     results = []
    #     for idx, row in matching_rows.iterrows():
    #         results.append({
    #             'row_number': idx + 1,
    #             'data': row.to_dict(),
    #             'source': 'CSV Notes'
    #         })
    #     
    #     return results[:MAX_SEARCH_RESULTS]
    # except Exception as e:
    #     log_error(f"Error searching CSV with pandas", e)
    #     return []
    pass


# Tool specification for OpenAI function calling
CSV_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "search_csv",
        "description": "Search through CSV notes and structured data. Use this when the user asks about notes, records, or tabular information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant CSV data"
                }
            },
            "required": ["query"]
        }
    }
}


if __name__ == "__main__":
    # Test the CSV search tool
    test_query = "meeting"
    results = search_csv(test_query)
    print(f"Search results for '{test_query}':")
    for idx, result in enumerate(results, 1):
        print(f"{idx}. Row {result.get('row_number')}: {result.get('data')}")
