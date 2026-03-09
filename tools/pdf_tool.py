"""
PDF search tool
Developer 1: Implement PDF searching logic here
"""

from typing import List, Dict, Any
from pathlib import Path
from config import PDF_DATA_PATH, MAX_SEARCH_RESULTS
from utils.helpers import log_info, log_error, calculate_similarity


def search_pdf(query: str) -> List[Dict[str, Any]]:
    """
    Search through PDF documents
    
    Args:
        query: User's search query
    
    Returns:
        List of matching PDF excerpts
    
    Developer 1 TODO:
        1. Use PyPDF2 or pdfplumber to extract text from PDFs
        2. Split text into chunks (paragraphs or pages)
        3. Search for relevant chunks
        4. Return matches with page numbers and context
        5. Consider using embeddings for better semantic search (optional)
    """
    log_info(f"Searching PDFs for: {query}")
    
    try:
        # Check if PDF file exists
        if not Path(PDF_DATA_PATH).exists():
            log_error(f"PDF file not found: {PDF_DATA_PATH}")
            return []
        
        # TODO: Install PyPDF2 or pdfplumber
        # pip install PyPDF2
        # or
        # pip install pdfplumber
        
        # For now, using a mock implementation
        # Developer 1: Replace this with actual PDF parsing
        
        # Example using PyPDF2 (uncomment when library is installed):
        """
        import PyPDF2
        
        results = []
        with open(PDF_DATA_PATH, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                
                # Search in page text
                if query.lower() in text.lower():
                    # Extract context around the match
                    lines = text.split('\n')
                    matching_lines = [line for line in lines if query.lower() in line.lower()]
                    
                    for line in matching_lines[:MAX_SEARCH_RESULTS]:
                        results.append({
                            'page': page_num + 1,
                            'text': line.strip(),
                            'source': 'PDF Document',
                            'relevance_score': calculate_similarity(query, line)
                        })
        
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:MAX_SEARCH_RESULTS]
        """
        
        # Mock data for testing without PDF library
        mock_results = [
            {
                'page': 1,
                'text': f'Mock PDF result containing "{query}"',
                'source': 'documents.pdf',
                'relevance_score': 0.8
            }
        ]
        
        log_info(f"Found {len(mock_results)} matching PDF excerpts (MOCK DATA)")
        return mock_results
    
    except Exception as e:
        log_error(f"Error searching PDFs", e)
        return []


class PdfTool:
    """
    Class-based PDF/text search tool.
    Reads the PDF placeholder text file and searches line by line.
    """

    def run(self, query: str):
        """
        Search through the PDF text content for a query match.

        Args:
            query: The keyword or phrase to search for.

        Returns:
            List of matching lines, or a 'not found' message.
        """
        results = []

        try:
            with open("sample_data/README_PDF.txt", "r", encoding="utf-8") as file:
                lines = file.readlines()

            print("Searching for:", query)
            for line in lines:
                stripped = line.strip()
                print("Checking:", stripped)
                if stripped and query.lower() in stripped.lower():
                    results.append(stripped)

        except FileNotFoundError:
            return "PDF data file not found"
        except Exception as e:
            return f"Error reading PDF: {e}"

        if not results:
            return "No relevant content found"

        return results


# Tool specification for OpenAI function calling
PDF_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "search_pdf",
        "description": "Search through PDF documents. Use this when the user asks about documents, reports, or written content in PDFs.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant PDF content"
                }
            },
            "required": ["query"]
        }
    }
}


if __name__ == "__main__":
    # Test the PDF search tool
    test_query = "project"
    results = search_pdf(test_query)
    print(f"Search results for '{test_query}':")
    for idx, result in enumerate(results, 1):
        print(f"{idx}. Page {result.get('page')}: {result.get('text')[:100]}...")
