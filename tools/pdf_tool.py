"""
PDF search tool - searches uploaded PDF files
"""

from typing import List, Dict, Any
from pathlib import Path
from config import PDF_DATA_PATH, MAX_SEARCH_RESULTS
from utils.helpers import log_info, log_error, calculate_similarity


def search_pdf(query: str) -> List[Dict[str, Any]]:
    """
    Search through uploaded PDF documents using keyword-based matching.
    
    Args:
        query: User's search query
    
    Returns:
        List of matching PDF excerpts with page numbers and context
    """
    log_info(f"Searching PDFs for: {query}")
    
    if not query or not query.strip():
        return []
    
    try:
        # Search in the uploads directory where user PDFs are stored
        uploads_dir = Path(__file__).parent.parent / "uploads"
        results = []
        
        if not uploads_dir.exists():
            log_info(f"Uploads directory not found: {uploads_dir}")
            return []
        
        # Find all PDF files in uploads directory
        pdf_files = list(uploads_dir.glob("**/*.pdf"))
        
        if not pdf_files:
            log_info(f"No PDF files found in {uploads_dir}")
            return []
        
        log_info(f"Found {len(pdf_files)} PDF file(s) to search")
        
        # Extract keywords from query (remove common stop words)
        stop_words = {'the', 'is', 'it', 'what', 'in', 'a', 'an', 'and', 'or', 'of', 'to', 'for', 'on', 'at'}
        query_keywords = [
            word.lower() for word in query.split() 
            if word.lower() not in stop_words and len(word) > 1
        ]
        
        if not query_keywords:
            # If all words were stop words, use original query
            query_keywords = [query.lower()]
        
        log_info(f"Search keywords: {query_keywords}")
        
        # Try using pdfplumber for advanced extraction
        try:
            import pdfplumber
            
            for pdf_file in pdf_files:
                try:
                    with pdfplumber.open(pdf_file) as pdf:
                        for page_num, page in enumerate(pdf.pages, 1):
                            text = page.extract_text() or ""
                            text_lower = text.lower()
                            
                            # Check if ANY keyword matches in this page
                            matched_keywords = [kw for kw in query_keywords if kw in text_lower]
                            
                            if matched_keywords:
                                # Split into lines and find lines with matches
                                lines = text.split('\n')
                                for line_idx, line in enumerate(lines):
                                    line_lower = line.lower()
                                    
                                    # Count how many keywords this line contains
                                    line_matches = [kw for kw in query_keywords if kw in line_lower]
                                    
                                    if line_matches:
                                        # Get context lines around the match
                                        context_start = max(0, line_idx - 2)
                                        context_end = min(len(lines), line_idx + 3)
                                        context_lines = lines[context_start:context_end]
                                        context = '\n'.join(context_lines)
                                        
                                        # Calculate relevance: more keywords matched = higher score
                                        relevance = len(line_matches) / len(query_keywords)
                                        
                                        results.append({
                                            'page': page_num,
                                            'text': context.strip(),
                                            'source': pdf_file.name,
                                            'relevance_score': relevance,
                                            'matched_keywords': line_matches
                                        })
                except Exception as e:
                    log_error(f"Error reading PDF file {pdf_file.name}: {str(e)}")
                    continue
        
        except ImportError:
            # Fallback: try PyPDF2
            try:
                import PyPDF2
                
                for pdf_file in pdf_files:
                    try:
                        with open(pdf_file, 'rb') as f:
                            pdf_reader = PyPDF2.PdfReader(f)
                            
                            for page_num, page in enumerate(pdf_reader.pages, 1):
                                text = page.extract_text() or ""
                                text_lower = text.lower()
                                
                                matched_keywords = [kw for kw in query_keywords if kw in text_lower]
                                
                                if matched_keywords:
                                    lines = text.split('\n')
                                    for line_idx, line in enumerate(lines):
                                        line_lower = line.lower()
                                        line_matches = [kw for kw in query_keywords if kw in line_lower]
                                        
                                        if line_matches:
                                            context_start = max(0, line_idx - 2)
                                            context_end = min(len(lines), line_idx + 3)
                                            context = '\n'.join(lines[context_start:context_end])
                                            
                                            relevance = len(line_matches) / len(query_keywords)
                                            
                                            results.append({
                                                'page': page_num,
                                                'text': context.strip(),
                                                'source': pdf_file.name,
                                                'relevance_score': relevance,
                                                'matched_keywords': line_matches
                                            })
                    except Exception as e:
                        log_error(f"Error reading PDF file {pdf_file.name}: {str(e)}")
                        continue
            
            except ImportError:
                log_error("Neither pdfplumber nor PyPDF2 is installed. Cannot extract PDF text.")
                return []
        
        # Remove duplicates based on page + similar text content
        seen = set()
        unique_results = []
        for result in results:
            key = (result['source'], result['page'], result['text'][:100])
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        # Sort by relevance and limit results
        unique_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        unique_results = unique_results[:MAX_SEARCH_RESULTS]
        
        log_info(f"Found {len(unique_results)} matching PDF results")
        return unique_results
    
    except Exception as e:
        log_error(f"Error searching PDFs: {str(e)}")
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
