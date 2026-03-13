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
import logging as _logging
import os
import re
from urllib import error as url_error
from urllib import request as url_request
from typing import Any, Literal

try:
    from google import genai as _genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

_synth_log = _logging.getLogger(__name__)

ToolName = Literal["email", "pdf", "csv", "drive", "calendar"]

TOOL_SOURCE_LABELS: dict[ToolName, str] = {
    "email": "Gmail/Email",
    "drive": "Google Drive",
    "calendar": "Google Calendar",
    "pdf": "PDF",
    "csv": "CSV/Notes",
}


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
    if any(k in q for k in ["birthday", "birth", "dob", "date of birth", "anniversary"]):
        return "calendar"
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


def _tool_intent_scores(query: str) -> dict[ToolName, float]:
    q = (query or "").strip().lower()
    scores: dict[ToolName, float] = {
        "email": 0.1,
        "pdf": 0.1,
        "csv": 0.1,
        "drive": 0.1,
        "calendar": 0.1,
    }

    keyword_weights: dict[ToolName, list[str]] = {
        "email": ["email", "mail", "inbox", "sender", "subject", "thread", "message"],
        "calendar": ["calendar", "meeting", "event", "schedule", "appointment", "birthday", "anniversary", "dob", "date of birth"],
        "drive": ["drive", "folder", "google drive", "docs", "sheets", "slides", "shared file"],
        "pdf": ["pdf", "report", "paper", "page", "document"],
        "csv": ["csv", "sheet", "table", "row", "column", "notes", "records", "contact list"],
    }

    for tool, keywords in keyword_weights.items():
        for keyword in keywords:
            if keyword in q:
                scores[tool] += 1.0

    if "when is" in q and any(token in q for token in ["birthday", "dob", "birth", "anniversary"]):
        scores["calendar"] += 1.5
        scores["csv"] += 1.0
        scores["email"] -= 0.4

    return scores


def rank_tools(query: str) -> list[ToolName]:
    """Return tools ordered by likely relevance to the user prompt."""
    scores = _tool_intent_scores(query)
    llm_choice = choose_tool(query)
    scores[llm_choice] += 0.75

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [tool for tool, _ in ranked]


def _build_routing_reason(query: str, selected_tool: ToolName, searched_tools: list[ToolName]) -> str:
    q = (query or "").lower()
    if any(token in q for token in ["birthday", "dob", "date of birth", "anniversary"]):
        return (
            f"The query indicates a personal date/event intent, so {TOOL_SOURCE_LABELS[selected_tool]} was prioritized "
            f"before email and validated across {', '.join(TOOL_SOURCE_LABELS[t] for t in searched_tools)}."
        )
    return (
        f"Intent-based routing selected {TOOL_SOURCE_LABELS[selected_tool]} as the best match for this question "
        f"after checking {', '.join(TOOL_SOURCE_LABELS[t] for t in searched_tools)}."
    )


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

    # Preferred path: Gemini Flash Latest
    if gemini_api_key:
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                "gemini-flash-latest:generateContent"
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
    if not isinstance(result, list) or len(result) == 0:
        return False

    scored_items = [
        item.get("relevance_score")
        for item in result
        if isinstance(item, dict) and isinstance(item.get("relevance_score"), (int, float))
    ]

    if scored_items:
        return any(score >= 0.2 for score in scored_items)

    return True


def _extract_person_for_birthday_query(query: str) -> str:
    q = (query or "").strip().lower()
    match = re.search(r"when\s+is\s+(.+?)\s+(?:birthday|dob|date\s+of\s+birth)", q)
    if not match:
        return ""
    name = match.group(1).strip()
    return re.sub(r"\s+", " ", name)


def _filter_results_for_query(tool: ToolName, query: str, result: Any) -> Any:
    if not isinstance(result, list) or not result:
        return result

    q = (query or "").lower()
    if tool == "calendar" and any(token in q for token in ["birthday", "dob", "date of birth"]):
        person = _extract_person_for_birthday_query(query)
        if person:
            filtered = []
            for item in result:
                if not isinstance(item, dict):
                    continue
                haystack = " ".join([
                    str(item.get("summary", "")),
                    str(item.get("description", "")),
                ]).lower()
                if person in haystack:
                    filtered.append(item)
            if filtered:
                return filtered

    return result


def _wants_brief_answer(query: str) -> bool:
    q = (query or "").strip().lower()
    asks_details = any(
        token in q
        for token in ["details", "detail", "list", "show all", "full", "explain", "why", "summarize"]
    )
    direct_question = any(
        q.startswith(prefix)
        for prefix in ["when", "what", "who", "where", "which", "how many", "is ", "does ", "did "]
    )
    return direct_question and not asks_details


def _format_fallback_answer(tool: ToolName, query: str, result: Any) -> str:
    if not isinstance(result, list) or not result:
        return "I couldn't find relevant information for that question."

    q = (query or "").lower()
    if tool == "calendar" and any(token in q for token in ["birthday", "dob", "date of birth", "when is"]):
        person = _extract_person_for_birthday_query(query)
        top = result[0] if isinstance(result[0], dict) else {}
        summary = str(top.get("summary", "")).strip()
        start = str(top.get("start", "")).strip()
        date_only = start.split("T")[0] if start else start
        if person and date_only:
            return f"{person.title()}'s birthday is on {date_only}."
        if summary and date_only:
            return f"{summary} is on {date_only}."

    first = result[0]
    if isinstance(first, dict):
        if first.get("summary"):
            return str(first.get("summary"))
        if first.get("subject"):
            return str(first.get("subject"))
        if first.get("name"):
            return str(first.get("name"))

    return _shorten(first, 220)


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


def _truncate_results_for_prompt(result: Any, max_chars: int = 8000) -> str:
    """Serialise results to JSON and trim to stay within Gemini's input limits."""
    try:
        raw = json.dumps(result, default=str, indent=2)
    except Exception:
        raw = str(result)
    if len(raw) > max_chars:
        raw = raw[:max_chars] + "\n... (truncated for brevity)"
    return raw


def _synthesize_response(tool: ToolName, query: str, result: Any) -> str:
    """Pass raw tool results through Gemini to produce a clean natural-language answer.

    Falls back to _format_structured_result if Gemini is unavailable or fails.
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        _synth_log.warning("[SYNTHESIZE] GEMINI_API_KEY not found — using concise fallback")
        return _format_fallback_answer(tool, query, result)

    raw_data = _truncate_results_for_prompt(result)
    source_label = TOOL_SOURCE_LABELS.get(tool, tool)
    num_results = len(result) if isinstance(result, list) else 1
    brief_answer = _wants_brief_answer(query)

    response_style = (
        "Answer in exactly 1-2 sentences with only the direct fact requested. "
        "Do not include bullets, headings, lists, source breakdown, or extra commentary."
        if brief_answer
        else "Answer clearly in short markdown with only relevant details."
    )

    prompt = (
        "You are a helpful personal executive assistant.\n\n"
        f'The user asked: "{query}"\n\n'
        f"Selected source: {source_label}. Matching result count: {num_results}.\n\n"
        f"{raw_data}\n\n"
        f"{response_style}\n\n"
        "Hard rules:\n"
        "- Use only information supported by the provided results\n"
        "- Prefer the single best match to the user question\n"
        "- Ignore near matches that refer to other people/items\n"
        "- If results are insufficient, say that briefly and ask one short clarifying question\n"
    )

    _synth_log.info("[SYNTHESIZE] Calling Gemini to synthesize %s result(s) for query: %s",
                    num_results, query)

    # Preferred path: use google-genai SDK (avoids urllib 403 on large payloads)
    if _GENAI_AVAILABLE:
        try:
            client = _genai.Client(api_key=gemini_api_key)
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config={"temperature": 0.3},
            )
            synthesized = response.text or ""
            if synthesized:
                _synth_log.info("[SYNTHESIZE] Gemini SDK synthesis successful")
                return synthesized.strip()
            _synth_log.warning("[SYNTHESIZE] Gemini SDK returned empty text — using structured fallback")
        except Exception as exc:
            _synth_log.error("[SYNTHESIZE] Gemini SDK call failed (%s: %s) — using structured fallback",
                             type(exc).__name__, exc)
        return _format_fallback_answer(tool, query, result)

    # urllib fallback (only if SDK not installed)
    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-flash-latest:generateContent"
            f"?key={gemini_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3},
        }
        req = url_request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with url_request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            synthesized = (
                body.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            if synthesized:
                _synth_log.info("[SYNTHESIZE] Gemini urllib synthesis successful")
                return synthesized.strip()
            _synth_log.warning("[SYNTHESIZE] Gemini returned empty text — using structured fallback")
    except Exception as exc:
        _synth_log.error("[SYNTHESIZE] Gemini urllib call failed (%s: %s) — using structured fallback",
                         type(exc).__name__, exc)

    return _format_fallback_answer(tool, query, result)


def process_query_structured(query: str, user_email: str | None = None) -> dict[str, Any]:
    """Main orchestrator returning both answer text and routing metadata."""
    if not query or not query.strip():
        return {
            "answer": "No relevant information found.",
            "selected_source": None,
            "searched_sources": [],
            "results_count": 0,
            "routing_reason": "Query was empty.",
        }

    candidate_tools = rank_tools(query)
    searched_sources: list[ToolName] = []

    try:
        for candidate in candidate_tools:
            searched_sources.append(candidate)
            candidate_result = _run_tool(candidate, query, user_email=user_email)
            candidate_result = _filter_results_for_query(candidate, query, candidate_result)
            if _is_non_empty_result(candidate_result):
                answer = _synthesize_response(candidate, query, candidate_result)
                return {
                    "answer": answer,
                    "selected_source": candidate,
                    "searched_sources": searched_sources,
                    "results_count": len(candidate_result) if isinstance(candidate_result, list) else 0,
                    "routing_reason": _build_routing_reason(query, candidate, searched_sources),
                }

        return {
            "answer": "I couldn't find any relevant information for your query. Please try rephrasing or check that your data sources are connected.",
            "selected_source": None,
            "searched_sources": searched_sources,
            "results_count": 0,
            "routing_reason": "No relevant matches were found in the searched data sources.",
        }
    except Exception:
        return {
            "answer": "No relevant information found.",
            "selected_source": None,
            "searched_sources": searched_sources,
            "results_count": 0,
            "routing_reason": "An internal error occurred during routing or search.",
        }


def process_query(query: str, user_email: str | None = None) -> str:
    """Backward-compatible string response entry point."""
    return process_query_structured(query, user_email=user_email).get("answer", "No relevant information found.")
