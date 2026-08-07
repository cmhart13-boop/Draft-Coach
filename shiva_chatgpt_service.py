from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd
from openai import OpenAI

from shiva_query_router import run_shiva_query

MODEL = "gpt-5.6"

SYSTEM_INSTRUCTIONS = """
You are Shiva Intelligence, an expert ESPN Full-PPR fantasy-football analyst embedded inside a draft application.

Answer naturally, decisively, and conversationally like an elite fantasy-football analyst.

NON-NEGOTIABLE DATA RULES:
- VERIFIED EVIDENCE supplied by the app is the source of truth for factual statistics.
- Never invent a statistic, ADP, finish, age, injury fact, historical result, or current-season claim.
- Never substitute league-wide averages for a named-player question.
- If evidence is incomplete, say what is missing, then still give the best football analysis supported by the evidence that IS present.
- ESPN Full PPR means one point per reception.
- Recommendation questions require a clear choice when the supplied evidence supports one.
- If evidence references the wrong player or season, do not use it.

OUTPUT FORMAT — FOLLOW EXACTLY:
FINAL ANSWER: <one clear, concise answer to the user's question>
WHY:
<2-4 concise paragraphs or bullets explaining the reasoning, context, and strongest verified evidence>

STYLE:
- Make FINAL ANSWER decisive and short enough to be the visual headline.
- Put all explanation and context under WHY.
- Mobile-friendly.
- No implementation jargon.
- Do not mention Pandas, routing, prompts, or internal systems.
"""


def _frame_to_records(frame: pd.DataFrame | None, limit: int = 60) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    safe = frame.head(limit).copy()
    safe = safe.astype(object).where(pd.notna(safe), None)
    return safe.to_dict(orient="records")


def build_verified_evidence(
    question: str,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    rankings: pd.DataFrame,
    weekly: pd.DataFrame | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Retrieve verified local evidence first; return both serialized evidence and original report."""
    report = run_shiva_query(question, history, roi, rankings, weekly)
    evidence = {
        "title": report.get("title", ""),
        "answer": report.get("answer", ""),
        "note": report.get("note", ""),
        "takeaway": report.get("takeaway", ""),
        "kind": report.get("kind", ""),
        "structured_query": report.get("structured_query", {}),
        "supporting_rows": _frame_to_records(report.get("table")),
    }
    return evidence, report


def _configured_api_key(explicit_key: str | None = None) -> str:
    return (explicit_key or os.getenv("OPENAI_API_KEY") or "").strip()


def _local_fallback(report: dict[str, Any], reason: str = "") -> dict[str, Any]:
    """Keep Ask Shiva functional even if the external model connection is unavailable."""
    result = dict(report)
    result.setdefault("title", "🧠 ASK SHIVA")
    result.setdefault("answer", "")
    result.setdefault("note", "")
    result.setdefault("takeaway", "")
    result.setdefault("table", pd.DataFrame())
    result.setdefault("kind", "local_verified")
    result.setdefault("structured_query", {})
    why = str(result.get("takeaway") or result.get("note") or "").strip()
    if not why and reason:
        why = "Answer calculated from Shiva's verified local data."
    result["why"] = why
    return result


def _split_model_response(text: str) -> tuple[str, str]:
    """Split ChatGPT's required FINAL ANSWER / WHY format into two UI-ready fields."""
    cleaned = (text or "").strip()
    if not cleaned:
        return "", ""

    upper = cleaned.upper()
    answer_marker = "FINAL ANSWER:"
    why_marker = "WHY:"

    if answer_marker in upper:
        start = upper.index(answer_marker) + len(answer_marker)
        remainder = cleaned[start:].strip()
        remainder_upper = remainder.upper()
        if why_marker in remainder_upper:
            split_at = remainder_upper.index(why_marker)
            answer = remainder[:split_at].strip()
            why = remainder[split_at + len(why_marker):].strip()
            return answer, why
        return remainder, ""

    if why_marker in upper:
        split_at = upper.index(why_marker)
        return cleaned[:split_at].strip(), cleaned[split_at + len(why_marker):].strip()

    parts = [part.strip() for part in cleaned.split("\n\n") if part.strip()]
    if len(parts) >= 2:
        return parts[0], "\n\n".join(parts[1:])
    return cleaned, ""


def ask_shiva_via_chatgpt(
    question: str,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    rankings: pd.DataFrame,
    weekly: pd.DataFrame | None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """ChatGPT-first analyst with deterministic verified-data fallback."""
    evidence, local_report = build_verified_evidence(question, history, roi, rankings, weekly)
    key = _configured_api_key(api_key)

    if not key:
        return _local_fallback(local_report, "missing_api_key")

    try:
        client = OpenAI(api_key=key)
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": "low"},
            instructions=SYSTEM_INSTRUCTIONS,
            input=(
                "USER QUESTION:\n"
                + question
                + "\n\nVERIFIED EVIDENCE FROM SHIVA:\n"
                + json.dumps(evidence, ensure_ascii=False, default=str)
                + "\n\nReturn exactly two sections: FINAL ANSWER and WHY. Use factual numbers only when supported by the evidence."
            ),
        )
        text = (response.output_text or "").strip()
        if not text:
            return _local_fallback(local_report, "empty_model_response")

        answer, why = _split_model_response(text)
        if not answer:
            return _local_fallback(local_report, "empty_model_answer")

        return {
            "title": "🧠 ASK SHIVA",
            "answer": answer,
            "why": why or "This recommendation is based on the verified Shiva evidence retrieved for your question.",
            "note": "",
            "takeaway": "",
            "table": report_table_from_evidence(evidence),
            "kind": "chatgpt",
            "structured_query": evidence.get("structured_query", {}),
        }
    except Exception:
        return _local_fallback(local_report, "openai_error")


def report_table_from_evidence(evidence: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(evidence.get("supporting_rows", []) or [])
