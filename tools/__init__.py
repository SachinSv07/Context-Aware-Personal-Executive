"""
Tools package for searching different data sources
Developer 1 works primarily in this folder
"""

from .email_tool import search_email
from .pdf_tool import search_pdf
from .csv_tool import search_csv
from .gmail_tool import search_gmail
from .drive_tool import search_drive
from .calendar_tool import search_calendar

# Tool registry for the agent
AVAILABLE_TOOLS = {
    "search_email":    search_email,
    "search_pdf":      search_pdf,
    "search_csv":      search_csv,
    "search_gmail":    search_gmail,
    "search_drive":    search_drive,
    "search_calendar": search_calendar,
}

__all__ = [
    'search_email', 'search_pdf', 'search_csv',
    'search_gmail', 'search_drive', 'search_calendar',
    'AVAILABLE_TOOLS',
]
