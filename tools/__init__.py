"""
Tools package for searching different data sources
Developer 1 works primarily in this folder
"""

from .email_tool import search_email
from .pdf_tool import search_pdf
from .csv_tool import search_csv

# Tool registry for the agent
AVAILABLE_TOOLS = {
    "search_email": search_email,
    "search_pdf": search_pdf,
    "search_csv": search_csv
}

__all__ = ['search_email', 'search_pdf', 'search_csv', 'AVAILABLE_TOOLS']
