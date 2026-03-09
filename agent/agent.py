"""Agent orchestrator for Context-Aware Personal Executive.

This module keeps the flow simple for hackathon speed:
1) Receive user query
2) Choose the best tool (email/pdf/csv) with LLM routing
3) Execute the selected tool
4) Return a readable response with decision trace
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
    if any(k in q for k in ["drive", "google drive", "document", "docs", "spreadsheet", "sheet", "slides", "file"]):
        return "drive"
    if any(k in q for k in ["calendar", "meeting", "event", "schedule", "appointment", "invite"]):
        return "calendar"
    if any(k in q for k in ["pdf", "document", "report", "paper", "page"]):
        return "pdf"
    if any(k in q for k in ["csv", "table", "sheet", "row", "column", "note", "notes"]):
        return "csv"
    return "email"


def choose_tool(query: str) -> ToolName:
    """Choose which data source to search: email, drive, calendar, pdf, or csv.

    Prompt format used:
        A user asked: {query}

        Which data source should be searched?

        Options:
        email
        pdf
        csv
        drive
        calendar

        Return only the tool name.
    """
    if not query or not query.strip():
        return "email"

    gemini_api_key = os.getenv("GEMINI_API_KEY")

    prompt = (
        f"A user asked: {query}\n\n"
        "Which data source should be searched?\n\n"
        "Options:\n"
        "email\n"
        "pdf\n"
        "csv\n"
        "drive\n"
        "calendar\n\n"
        "Return only the tool name."
    )

    # Preferred path: Gemini 2.0 Flash
    if gemini_api_key:
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                "gemini-2.0-flash:generateContent"
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

            with url_request.urlopen(req, timeout=20) as response:
                body = json.loads(response.read().decode("utf-8"))
                raw = (
                    body.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                if raw:
                    return _normalize_tool(raw)
                # If Gemini returns empty, fall back
                return _fallback_tool_choice(query)
        except (url_error.URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError) as e:
            # Silently fall back if API fails
            return _fallback_tool_choice(query)

    # Optional compatibility path: OpenAI if GEMINI_API_KEY is not set.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_tool_choice(query)

    try:
        openai_module = importlib.import_module("openai")
        OpenAI = getattr(openai_module, "OpenAI")
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a routing assistant. Return only one word: email, drive, calendar, pdf, or csv.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        raw = response.choices[0].message.content or ""
        return _normalize_tool(raw)

    except Exception:
        return _fallback_tool_choice(query)


def _run_tool(tool: ToolName, query: str) -> Any:
    """Execute selected tool by importing only what is needed."""
    if tool == "email":
        from tools.gmail_tool import search_gmail
        from tools.email_tool import search_email

        gmail_results = search_gmail(query)
        if gmail_results:
            return gmail_results

        return search_email(query)

    if tool == "pdf":
        from tools.pdf_tool import search_pdf

        return search_pdf(query)

    if tool == "drive":
        from tools.drive_tool import search_drive

        return search_drive(query)

    if tool == "calendar":
        from tools.calendar_tool import search_calendar

        return search_calendar(query)

    from tools.csv_tool import search_csv

    return search_csv(query)


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
            lines.append(f"+--- RESULT {idx} " + "-" * 53 + "+")
            
            subject = _shorten(item.get('subject', 'N/A'), 60)
            lines.append(f"| SUBJECT:  {subject:<58} |")
            
            sender = _shorten(item.get('from', 'N/A'), 58)
            lines.append(f"| FROM:     {sender:<58} |")
            
            if item.get("date"):
                date_str = _shorten(item.get('date'), 58)
                lines.append(f"| DATE:     {date_str:<58} |")
            
            lines.append("|" + "-" * 68 + "|")
            
            # Show snippet or summary
            if item.get("snippet"):
                snippet = _shorten(item.get('snippet'), 65)
                lines.append(f"| SUMMARY:")
                lines.append(f"| {snippet:<65} |")
            
            # Show FULL content in paragraph format
            content = item.get("content", "")
            if content:
                lines.append("|")
                lines.append(f"| FULL CONTENT:")
                lines.append("|")
                # Wrap content as paragraphs
                wrapped_lines = _wrap_paragraph(content, 64)
                for wrapped_line in wrapped_lines:
                    lines.append(f"| {wrapped_line:<64} |")
            
            lines.append("+" + "-" * 68 + "+\n")
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


def process_query(query: str) -> str:
    """Main orchestrator entry point.

    Usage:
        from agent.agent import process_query
        response = process_query(user_query)
    """
    if not query or not query.strip():
        return "No relevant information found."

    tool = choose_tool(query)

    try:
        result = _run_tool(tool, query)
        return _format_structured_result(tool, query, result)
    except Exception:
        return "No relevant information found."
