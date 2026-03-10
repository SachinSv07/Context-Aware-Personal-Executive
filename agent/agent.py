"""Agent orchestrator for Context-Aware Personal Executive.

This module keeps the flow simple for hackathon speed:
1) Receive user query
2) Choose the best tool (email/pdf/csv) with LLM routing
3) Execute the selected tool
4) Validate results with LLM before showing to user
5) Return only relevant responses
"""

from __future__ import annotations

import importlib
import json
import os
from urllib import error as url_error
from urllib import request as url_request
from typing import Any, Literal

ToolName = Literal["email", "pdf", "csv", "drive", "calendar"]


def _load_local_env() -> None:
    """Load .env from project root into process environment (non-destructive)."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, ".env")

    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                # Do not override already-exported variables.
                os.environ.setdefault(key, value)
    except OSError:
        # Keep agent resilient in hackathon environments.
        return


# Load .env once on module import so choose_tool() can use os.getenv().
_load_local_env()


def _normalize_tool(raw_output: str) -> ToolName:
    """Normalize model output to exactly one valid tool label.

    Falls back to a keyword heuristic when model output is noisy.
    """
    text = (raw_output or "").strip().lower()

    if text in {"email", "pdf", "csv", "drive", "calendar"}:
        return text  # type: ignore[return-value]

    # Handle longer model output like: "I would choose email"
    for token in ("email", "pdf", "csv", "drive", "calendar"):
        if token in text:
            return token  # type: ignore[return-value]

    # Safe default for ambiguous responses
    return "email"


def _fallback_tool_choice(query: str) -> ToolName:
    """Simple local fallback when API is missing/unavailable."""
    q = query.lower()
    if any(k in q for k in ["email", "mail", "inbox", "sender", "subject"]):
        return "email"
    if any(k in q for k in ["calendar", "meeting", "event", "schedule", "appointment", "invite"]):
        return "calendar"
    if any(k in q for k in ["drive", "google drive", "slides"]):
        return "drive"
    if any(k in q for k in ["pdf", "problem statement", "problem", "question", "assignment", "report", "research", "paper", "chapter", "page", "section"]):
        return "pdf"
    if any(k in q for k in ["csv", "data", "table", "row", "column", "record", "list", "database"]):
        return "csv"
    return "email"


def choose_tool(query: str) -> ToolName:
    """Choose primary tool using KEYWORD-BASED ROUTING ONLY (NO LLM).

    Single-source results: routes to the most specific tool based on query intent.
    No fallback to other tools - returns results only from the detected source.

    Returns one of: email, pdf, csv, drive, calendar
    """
    if not query or not query.strip():
        return "email"

    query_lower = query.lower()

    # === CALENDAR KEYWORDS ===
    # Dates, events, meetings, schedules, personal dates
    if any(k in query_lower for k in [
        "calendar", "meeting", "event", "schedule", "appointment", "invite",
        "upcoming", "birthday", "anniversary", "holiday", "vacation", 
        "conference", "deadline", "reminder", "today", "tomorrow", "week",
        "month", "date", "time", "when is"
    ]):
        return "calendar"

    # === DRIVE KEYWORDS ===
    # Documents, spreadsheets, files, folders in Google Drive
    if any(k in query_lower for k in [
        "drive", "google drive", "file", "document", "docs", "sheet", 
        "spreadsheet", "slides", "folder", "presentation", "google sheets"
    ]):
        return "drive"

    # === PDF KEYWORDS ===
    # Academic work, problem statements, reports, papers, formal documents
    if any(k in query_lower for k in [
        "pdf", "problem statement", "problem", "question", "assignment", 
        "report", "research", "paper", "chapter", "page", "section",
        "resume", "cv", "curriculum vitae", "application", "proposal",
        "contract", "agreement", "manual", "guide", "handbook", "textbook",
        "description", "healthcare", "solution", "answer", "topic", 
        "statement", "definition", "explanation", "details", "content"
    ]):
        return "pdf"

    # === CSV KEYWORDS ===
    # Data tables, records, entries, lists, databases
    if any(k in query_lower for k in [
        "csv", "data", "table", "row", "column", "record", "list", 
        "database", "table header", "field", "entry", "entries",
        "spreadsheet data", "records"
    ]):
        return "csv"

    # === EMAIL KEYWORDS (Default) ===
    # Messages, emails, communications, conversations
    if any(k in query_lower for k in [
        "email", "mail", "inbox", "sender", "subject", "message", 
        "conversation", "from", "to", "reply", "forward"
    ]):
        return "email"

    # Default to email for ambiguous queries
    return "email"


def _validate_results_with_llm(query: str, results: list, tool: ToolName) -> bool:
    """Use Gemini LLM to validate if search results are actually relevant to the query.
    
    Args:
        query: User's original question
        results: Search results from a tool
        tool: Which tool produced these results
        
    Returns:
        True if results are relevant, False otherwise
    """
    if not results or len(results) == 0:
        return False
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        # No Gemini API key - accept results without validation
        return True
    
    try:
        # Create a summary of results for validation
        result_summary = []
        for idx, result in enumerate(results[:3], 1):  # Check first 3 results
            if isinstance(result, dict):
                # Extract key information based on tool type
                if tool == "email":
                    summary = f"Email {idx}: {result.get('subject', 'N/A')} from {result.get('from', 'N/A')}"
                elif tool == "pdf":
                    summary = f"PDF {idx}: {result.get('source', 'N/A')} - {result.get('text', '')[:100]}"
                elif tool == "drive":
                    summary = f"Drive {idx}: {result.get('name', 'N/A')} ({result.get('mime_type', 'N/A')})"
                elif tool == "calendar":
                    summary = f"Calendar {idx}: {result.get('summary', 'N/A')} on {result.get('start', 'N/A')}"
                elif tool == "csv":
                    summary = f"CSV {idx}: Row {result.get('row_number', 'N/A')}"
                else:
                    summary = f"Result {idx}: {str(result)[:100]}"
                result_summary.append(summary)
        
        results_text = "\n".join(result_summary)
        
        # Ask Gemini if results are relevant
        prompt = f"""User asked: "{query}"

Search results found:
{results_text}

Question: Are these search results actually relevant to what the user asked?
Answer ONLY with "YES" if the results answer the user's question, or "NO" if they are irrelevant or don't match the query.

Your answer (YES or NO):"""
        
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.0-flash-exp:generateContent"
            f"?key={gemini_api_key}"
        )
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0},
        }
        
        req = url_request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        with url_request.urlopen(req, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
            llm_response = (
                body.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                .strip()
                .upper()
            )
            
            # Check if Gemini said YES (relevant) or NO (not relevant)
            return "YES" in llm_response
    
    except Exception as e:
        # If validation fails, accept results anyway (fallback)
        return True


def _run_tool(tool: ToolName, query: str, user_email: str | None = None) -> Any:
    """Execute selected tool by importing only what is needed."""
    if tool == "email":
        from tools.gmail_tool import search_gmail
        from tools.email_tool import search_email

        gmail_results = search_gmail(query, user_email=user_email)
        if gmail_results:
            return gmail_results

        # For authenticated users, avoid falling back to local sample email data.
        # This keeps chat results strictly tied to their real Gmail account.
        if user_email:
            return []

        return search_email(query)

    if tool == "pdf":
        from tools.pdf_tool import search_pdf

        return search_pdf(query)

    if tool == "drive":
        from tools.drive_tool import search_drive

        return search_drive(query, user_email=user_email)

    if tool == "calendar":
        from tools.calendar_tool import search_calendar

        return search_calendar(query, user_email=user_email)

    from tools.csv_tool import search_csv

    return search_csv(query)


def _is_non_empty_result(result: Any) -> bool:
    return isinstance(result, list) and len(result) > 0


def _shorten(text: Any, limit: int = 140) -> str:
    value = str(text or "").strip().replace("\n", " ")
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def _wrap_paragraph(text: str, width: int = 65) -> list[str]:
    """
    Wrap text into paragraph format with word boundaries.
    Returns list of lines that fit within the specified width.
    """
    if not text:
        return []
    
    lines = []
    paragraphs = text.split('\n')
    
    for para in paragraphs:
        if not para.strip():
            lines.append("")  # Preserve empty lines between paragraphs
            continue
        
        words = para.split()
        current_line = ""
        
        for word in words:
            # If adding this word would exceed width
            if current_line and len(current_line) + len(word) + 1 > width:
                lines.append(current_line)
                current_line = word
            else:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
        
        # Add the last line of this paragraph
        if current_line:
            lines.append(current_line)
    
    return lines


def _format_structured_result(tool: ToolName, query: str, result: Any) -> str:
    source_map = {
        "email": "Gmail/Email",
        "drive": "Google Drive",
        "calendar": "Google Calendar",
        "pdf": "PDF",
        "csv": "CSV",
    }
    
    # Header
    lines = []
    lines.append("=" * 70)
    lines.append(f"SOURCE: {source_map.get(tool, tool)}")
    lines.append(f"QUERY: {query}")
    lines.append("=" * 70)

    if not isinstance(result, list) or not result:
        lines.append("\nMatches: 0")
        lines.append("\nNo relevant information found.")
        return "\n".join(lines)

    lines.append(f"\nMatches: {len(result)} found\n")

    # Format each result as a clean block
    for idx, item in enumerate(result, start=1):
        if not isinstance(item, dict):
            lines.append(f"[{idx}] {_shorten(item)}\n")
            continue

        # EMAIL FORMAT
        if tool == "email":
            source_label = item.get("source") or "Gmail/Email"
            lines.append(f"Result {idx}")
            lines.append(f"source: {source_label}")
            lines.append(f"subject: {_shorten(item.get('subject', 'N/A'), 180)}")
            lines.append(f"from: {_shorten(item.get('from', 'N/A'), 180)}")
            if item.get("to"):
                lines.append(f"to: {_shorten(item.get('to', ''), 180)}")
            if item.get("date"):
                lines.append(f"date: {_shorten(item.get('date'), 180)}")

            summary_text = item.get("snippet") or ""
            if summary_text:
                lines.append(f"summary: {_shorten(summary_text, 260)}")

            content_text = item.get("matched_content") or item.get("content") or ""
            if content_text:
                lines.append("content:")
                wrapped_lines = _wrap_paragraph(content_text, 90)
                for wrapped_line in wrapped_lines[:10]:
                    lines.append(wrapped_line)

            lines.append("-" * 70)
            continue

        # DRIVE FORMAT
        if tool == "drive":
            lines.append(f"+--- RESULT {idx} " + "-" * 53 + "+")
            
            name = _shorten(item.get('name', 'N/A'), 58)
            lines.append(f"| FILE:     {name:<58} |")
            
            if item.get("mime_type"):
                mime = _shorten(item.get('mime_type'), 58)
                lines.append(f"| TYPE:     {mime:<58} |")
            
            if item.get("owner"):
                owner = _shorten(item.get('owner'), 58)
                lines.append(f"| OWNER:    {owner:<58} |")
            
            if item.get("modified"):
                modified = _shorten(item.get('modified'), 58)
                lines.append(f"| MODIFIED: {modified:<58} |")
            
            lines.append("|" + "-" * 68 + "|")
            
            # Show FULL description in paragraph format
            if item.get("description"):
                desc = item.get('description', '')
                lines.append(f"| DESCRIPTION:")
                lines.append("|")
                wrapped_lines = _wrap_paragraph(desc, 64)
                for wrapped_line in wrapped_lines:
                    lines.append(f"| {wrapped_line:<64} |")
            
            # Show FULL content in paragraph format (extracted from file)
            if item.get("content"):
                content = item.get('content', '')
                lines.append("|")
                lines.append(f"| FULL CONTENT:")
                lines.append("|")
                wrapped_lines = _wrap_paragraph(content, 64)
                for wrapped_line in wrapped_lines:
                    lines.append(f"| {wrapped_line:<64} |")
            
            if item.get("link"):
                lines.append("|")
                link = _shorten(item.get('link'), 65)
                lines.append(f"| LINK:")
                lines.append(f"| {link:<65} |")
            
            lines.append("+" + "-" * 68 + "+\n")
            continue

        # CALENDAR FORMAT
        if tool == "calendar":
            lines.append(f"+--- RESULT {idx} " + "-" * 53 + "+")
            
            summary = _shorten(item.get('summary', 'N/A'), 58)
            lines.append(f"| EVENT:    {summary:<58} |")
            
            if item.get("start"):
                start = _shorten(item.get('start'), 58)
                lines.append(f"| START:    {start:<58} |")
            
            if item.get("end"):
                end = _shorten(item.get('end'), 58)
                lines.append(f"| END:      {end:<58} |")
            
            if item.get("location"):
                location = _shorten(item.get('location'), 58)
                lines.append(f"| LOCATION: {location:<58} |")
            
            lines.append("|" + "-" * 68 + "|")
            
            # Show FULL description in paragraph format
            if item.get("description"):
                desc = item.get('description', '')
                lines.append(f"| DESCRIPTION:")
                lines.append("|")
                wrapped_lines = _wrap_paragraph(desc, 64)
                for wrapped_line in wrapped_lines:
                    lines.append(f"| {wrapped_line:<64} |")
            
            attendees = item.get("attendees") or []
            if attendees:
                attendees_str = _shorten(', '.join(str(a) for a in attendees), 65)
                lines.append(f"| ATTENDEES:")
                lines.append(f"| {attendees_str:<65} |")
            
            if item.get("link"):
                lines.append("|")
                link = _shorten(item.get('link'), 65)
                lines.append(f"| LINK: {link:<59} |")
            
            lines.append("+" + "-" * 68 + "+\n")
            continue

        # PDF FORMAT
        if tool == "pdf":
            lines.append(f"+--- RESULT {idx} " + "-" * 53 + "+")
            
            if item.get("source"):
                source = _shorten(item.get('source'), 58)
                lines.append(f"| FILE:     {source:<58} |")
            
            page = item.get('page', 'N/A')
            lines.append(f"| PAGE:     {str(page):<58} |")
            
            lines.append("|" + "-" * 68 + "|")
            
            # Show FULL content in paragraph format (all text)
            text = item.get('text', '')
            lines.append(f"| FULL CONTENT:")
            lines.append("|")
            wrapped_lines = _wrap_paragraph(text, 64)
            for wrapped_line in wrapped_lines:
                lines.append(f"| {wrapped_line:<64} |")
            
            lines.append("+" + "-" * 68 + "+\n")
            continue

        # CSV/DEFAULT FORMAT
        row_number = item.get("row_number", "N/A")
        lines.append(f"+--- RESULT {idx} " + "-" * 53 + "+")
        lines.append(f"| ROW:      {str(row_number):<58} |")
        
        matching_fields = item.get("matching_fields") or []
        if matching_fields:
            lines.append("|" + "-" * 68 + "|")
            lines.append(f"| MATCHING FIELDS:")
            for field_val in matching_fields[:5]:
                field_str = _shorten(str(field_val), 62)
                lines.append(f"|   - {field_str:<62} |")
        
        lines.append("+" + "-" * 68 + "+\n")

    lines.append("=" * 70)
    return "\n".join(lines)


def process_query(query: str, user_email: str | None = None) -> str:
    """Main orchestrator entry point with smart multi-tool fallback and LLM validation.

    Flow:
    1. Choose primary tool based on keyword matching (no LLM)
    2. Search primary tool first
    3. Validate results with LLM - are they relevant to the query?
    4. If relevant, return results; if not, try other tools
    5. Only show "not found" if ALL tools were searched or no relevant results

    Usage:
        from agent.agent import process_query
        response = process_query(user_query)
    """
    if not query or not query.strip():
        return "No relevant information found."

    primary_tool = choose_tool(query)

    try:
        # Step 1: Search primary tool first
        result = _run_tool(primary_tool, query, user_email=user_email)
        
        if _is_non_empty_result(result):
            # Validate with LLM - are these results actually relevant?
            if _validate_results_with_llm(query, result, primary_tool):
                # Results are relevant - return immediately
                return _format_structured_result(primary_tool, query, result)
            # Results not relevant - continue searching other tools
        
        # Step 2: Primary tool found nothing or results were irrelevant - try other tools
        # Define search order for fallback (related tools first)
        tool_fallback_order = {
            "email": ["drive", "pdf", "csv", "calendar"],
            "pdf": ["drive", "csv", "email"],
            "csv": ["drive", "pdf", "email"],
            "drive": ["pdf", "csv", "email"],
            "calendar": ["email", "drive"],
        }
        
        fallback_tools = tool_fallback_order.get(primary_tool, ["email", "pdf", "csv", "drive", "calendar"])
        
        # Try each fallback tool in order
        for fallback_tool in fallback_tools:
            if fallback_tool == primary_tool:
                continue  # Skip primary tool (already searched)
            
            fallback_result = _run_tool(fallback_tool, query, user_email=user_email)
            
            if _is_non_empty_result(fallback_result):
                # Validate with LLM before returning
                if _validate_results_with_llm(query, fallback_result, fallback_tool):
                    # Found relevant results in fallback tool - return immediately
                    return _format_structured_result(fallback_tool, query, fallback_result)
                # Results not relevant - continue to next tool
        
        # Step 3: Nothing relevant found in any tool - show comprehensive "not found" message
        searched_tools = [primary_tool] + [t for t in fallback_tools if t != primary_tool]
        tool_names = ", ".join([
            {"email": "Gmail", "pdf": "PDFs", "csv": "CSV", "drive": "Google Drive", "calendar": "Calendar"}
            .get(t, t) for t in searched_tools
        ])
        
        return (
            f"======================================================================\n"
            f"SEARCH QUERY: {query}\n"
            f"======================================================================\n\n"
            f"Searched in: {tool_names}\n\n"
            f"No relevant information found in any source.\n\n"
            f"Your question might require:\n"
            f"- Real-time data (stock prices, current news, weather)\n"
            f"- Information not yet uploaded to your sources\n"
            f"- Different keywords or phrasing\n\n"
            f"Tip: Upload relevant files or connect more data sources for better results.\n"
            f"======================================================================"
        )
    
    except Exception as e:
        return f"Error processing query: {str(e)}"
