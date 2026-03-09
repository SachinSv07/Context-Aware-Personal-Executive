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

ToolName = Literal["email", "pdf", "csv"]


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

    if text in {"email", "pdf", "csv"}:
        return text  # type: ignore[return-value]

    # Handle longer model output like: "I would choose email"
    for token in ("email", "pdf", "csv"):
        if token in text:
            return token  # type: ignore[return-value]

    # Safe default for ambiguous responses
    return "email"


def _fallback_tool_choice(query: str) -> ToolName:
    """Simple local fallback when API is missing/unavailable."""
    q = query.lower()
    if any(k in q for k in ["email", "mail", "inbox", "sender", "subject"]):
        return "email"
    if any(k in q for k in ["pdf", "document", "report", "paper", "page"]):
        return "pdf"
    if any(k in q for k in ["csv", "table", "sheet", "row", "column", "note", "notes"]):
        return "csv"
    return "email"


def choose_tool(query: str) -> ToolName:
    """Choose which data source to search: email, pdf, or csv.

    Prompt format used:
        A user asked: {query}

        Which data source should be searched?

        Options:
        email
        pdf
        csv

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
        "csv\n\n"
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
                    "content": "You are a routing assistant. Return only one word: email, pdf, or csv.",
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

    from tools.csv_tool import search_csv

    return search_csv(query)


def _shorten(text: Any, limit: int = 140) -> str:
    value = str(text or "").strip().replace("\n", " ")
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def _format_structured_result(tool: ToolName, query: str, result: Any) -> str:
    source_map = {"email": "Gmail/Email", "pdf": "PDF", "csv": "CSV"}
    lines = [
        f"Source: {source_map.get(tool, tool)}",
        f"Query: {query}",
    ]

    if not isinstance(result, list) or not result:
        lines.append("Matches: 0")
        lines.append("")
        lines.append("No relevant information found.")
        return "\n".join(lines)

    lines.append(f"Matches: {len(result)}")
    lines.append("")
    lines.append("Top Results:")

    for idx, item in enumerate(result, start=1):
        if not isinstance(item, dict):
            lines.append(f"{idx}. {_shorten(item)}")
            continue

        if tool == "email":
            lines.append(f"{idx}. Subject: {_shorten(item.get('subject', 'N/A'), 100)}")
            lines.append(f"   From: {_shorten(item.get('from', 'N/A'), 90)}")
            if item.get("date"):
                lines.append(f"   Date: {_shorten(item.get('date'), 60)}")
            if item.get("snippet"):
                lines.append(f"   Snippet: {_shorten(item.get('snippet'), 160)}")
            content = item.get("content")
            if content:
                lines.append(f"   Content: {_shorten(content, 700)}")
            if item.get("relevance_score") is not None:
                try:
                    lines.append(f"   Relevance: {float(item.get('relevance_score')):.2f}")
                except (TypeError, ValueError):
                    pass
            continue

        if tool == "pdf":
            lines.append(f"{idx}. Page: {item.get('page', 'N/A')}")
            lines.append(f"   Text: {_shorten(item.get('text', ''), 180)}")
            if item.get("source"):
                lines.append(f"   File: {_shorten(item.get('source'), 80)}")
            continue

        row_number = item.get("row_number", "N/A")
        lines.append(f"{idx}. Row: {row_number}")
        matching_fields = item.get("matching_fields") or []
        if matching_fields:
            lines.append(f"   Matching fields: {', '.join(str(field) for field in matching_fields)}")
        data = item.get("data") or {}
        if isinstance(data, dict) and data:
            preview_pairs = []
            for key, value in list(data.items())[:3]:
                preview_pairs.append(f"{key}={_shorten(value, 40)}")
            lines.append(f"   Data: {' | '.join(preview_pairs)}")

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
