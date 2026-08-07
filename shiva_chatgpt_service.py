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
- If evidence is incomplete, say what is missing, then still give the best football analysis that can be supported by the evidence that IS present.
- ESPN Full PPR means one point per reception.
- Recommendation questions require a clear choice when the supplied evidence supports one.
- If evidence references the wrong player or season, do not use it.

STYLE:
- Direct answer first.
- Then 2-4 strongest reasons.
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
    if reason:
        existing = str(result.get("note") or "").strip()
        result["note"] = existing if existing else "Answer calculated from Shiva's verified local data."
    return result


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

    # Never break Ask Shiva because a deployment secret is missing.
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
                + "\n\nGive the direct fantasy-football answer first. Use factual numbers only when supported by the evidence."
            ),
        )
        text = (response.output_text or "").strip()
        if not text:
            return _local_fallback(local_report, "empty_model_response")

        return {
            "title": "🧠 ASK SHIVA",
            "answer": text,
            "note": "ChatGPT analysis grounded in Shiva's verified data.",
            "takeaway": "",
            "table": report_table_from_evidence(evidence),
            "kind": "chatgpt",
            "structured_query": evidence.get("structured_query", {}),
        }
    except Exception:
        # Production UI must remain useful even if OpenAI is temporarily unavailable.
        return _local_fallback(local_report, "openai_error")


def report_table_from_evidence(evidence: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(evidence.get("supporting_rows", []) or [])
