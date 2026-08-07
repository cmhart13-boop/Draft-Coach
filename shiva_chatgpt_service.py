from __future__ import annotations

import json
from typing import Any

import pandas as pd
from openai import OpenAI

from shiva_query_router import run_shiva_query

MODEL = "gpt-5.6"

SYSTEM_INSTRUCTIONS = """
You are Shiva Intelligence, an expert ESPN Full-PPR fantasy-football analyst embedded inside a draft application.

Your job is to answer the user's question conversationally and directly, like an elite human fantasy analyst.

NON-NEGOTIABLE DATA RULES:
- Treat the VERIFIED EVIDENCE supplied by the application as the source of truth for factual statistics.
- Never invent a statistic, ADP, finish, age, injury fact, or historical result.
- Never substitute a league-wide average for a specifically named player.
- If the evidence does not support a factual claim, say exactly what is missing.
- ESPN Full PPR means 1 point per reception.
- For recommendation questions, make a clear choice when the evidence supports one and explain why.
- If the retrieved evidence appears to reference the wrong player or wrong season compared with the user's wording, do not use it. State that the data match needs correction instead of hallucinating.

STYLE:
- Put the direct answer first.
- Be decisive and conversational.
- Then explain the 2-4 strongest reasons.
- Keep the response useful on a mobile screen.
- Do not talk about internal routing, Pandas, prompts, or implementation details.
"""


def _frame_to_records(frame: pd.DataFrame | None, limit: int = 40) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    safe = frame.head(limit).copy()
    safe = safe.where(pd.notna(safe), None)
    return safe.to_dict(orient="records")


def build_verified_evidence(
    question: str,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    rankings: pd.DataFrame,
    weekly: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Run the local deterministic engine first and serialize only its verified result rows."""
    report = run_shiva_query(question, history, roi, rankings, weekly)
    return {
        "title": report.get("title", ""),
        "answer": report.get("answer", ""),
        "note": report.get("note", ""),
        "takeaway": report.get("takeaway", ""),
        "kind": report.get("kind", ""),
        "structured_query": report.get("structured_query", {}),
        "supporting_rows": _frame_to_records(report.get("table")),
    }


def ask_shiva_via_chatgpt(
    question: str,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    rankings: pd.DataFrame,
    weekly: pd.DataFrame | None,
    api_key: str,
) -> dict[str, Any]:
    """
    Send the user's natural-language question to OpenAI after the app retrieves verified local evidence.
    The model is the conversational analyst; the app data remains the factual source of truth.
    """
    evidence = build_verified_evidence(question, history, roi, rankings, weekly)

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "low"},
        instructions=SYSTEM_INSTRUCTIONS,
        input=(
            "USER QUESTION:\n"
            + question
            + "\n\nVERIFIED EVIDENCE FROM THE SHIVA APP:\n"
            + json.dumps(evidence, ensure_ascii=False, default=str)
            + "\n\nAnswer the user directly. Use only supported factual numbers from the evidence."
        ),
    )

    text = (response.output_text or "").strip()
    if not text:
        text = "I couldn't produce a reliable answer from the verified evidence available for that question."

    return {
        "title": "🧠 ASK SHIVA",
        "answer": text,
        "note": "Powered by ChatGPT reasoning over Shiva's verified app data.",
        "takeaway": "",
        "table": report_table_from_evidence(evidence),
        "kind": "chatgpt",
        "structured_query": evidence.get("structured_query", {}),
    }


def report_table_from_evidence(evidence: dict[str, Any]) -> pd.DataFrame:
    rows = evidence.get("supporting_rows", []) or []
    return pd.DataFrame(rows)
