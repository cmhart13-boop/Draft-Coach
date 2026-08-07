from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd
from openai import OpenAI

from shiva_query_router import run_shiva_query, resolve_players

MODEL = "gpt-5.6"

SYSTEM_INSTRUCTIONS = """
You are Shiva GPT, an expert ESPN Full-PPR fantasy-football analyst embedded inside a draft application.

You must answer like a knowledgeable human fantasy analyst, not a spreadsheet and not a generic disclaimer generator.

NON-NEGOTIABLE DATA RULES:
- VERIFIED EVIDENCE supplied by the app is the source of truth for every factual statistic, ADP, finish, age, injury fact, or current-season claim.
- Never invent a number.
- Never substitute league-wide averages for a named-player question.
- For a DRAFT DECISION between named players, do NOT simply pick the player with the higher historical PPG. Prioritize current ESPN ADP, expected availability, positional opportunity cost, roster construction, and then use historical production as supporting context.
- In early rounds, explicitly consider the opportunity cost of taking QB/TE over elite RB/WR when the verified current ADP supports that distinction.
- If evidence is incomplete, say exactly what is missing, but still give the strongest football analysis supported by what is present.
- ESPN Full PPR means one point per reception.
- If evidence references the wrong player or season, ignore it.

OUTPUT FORMAT — FOLLOW EXACTLY:
FINAL ANSWER: <one clear, concise answer to the user's question>
WHY:
<2-4 specific reasons explaining the actual football decision. Cite the verified evidence naturally. Do not write a generic sentence about “based on the data.”>

STYLE:
- FINAL ANSWER must be decisive and short.
- WHY must contain the actual reasoning the user came for.
- If the user asks who to draft, say who and explain why.
- Mobile-friendly.
- Do not mention Pandas, routing, prompts, evidence objects, databases, APIs, or internal systems.
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
    """Retrieve verified local evidence before asking the model to analyze it."""
    report = run_shiva_query(question, history, roi, rankings, weekly)
    players, _ = resolve_players(question, history, rankings)
    current_rows = pd.DataFrame()
    if players and rankings is not None and not rankings.empty:
        wanted = {p.lower() for p in players}
        current_rows = rankings[rankings["player_name"].astype(str).str.lower().isin(wanted)].copy()

    evidence = {
        "title": report.get("title", ""),
        "answer": report.get("answer", ""),
        "note": report.get("note", ""),
        "takeaway": report.get("takeaway", ""),
        "kind": report.get("kind", ""),
        "structured_query": report.get("structured_query", {}),
        "current_rankings_for_named_players": _frame_to_records(current_rows, limit=10),
        "supporting_rows": _frame_to_records(report.get("table")),
    }
    return evidence, report


def _configured_api_key(explicit_key: str | None = None) -> str:
    return (explicit_key or os.getenv("OPENAI_API_KEY") or "").strip()


def _local_fallback(report: dict[str, Any], reason: str = "") -> dict[str, Any]:
    """Keep Ask Shiva GPT usable if the external model connection is unavailable."""
    result = dict(report)
    result["title"] = "🧠 ASK SHIVA GPT"
    result.setdefault("answer", "")
    result.setdefault("note", "")
    result.setdefault("takeaway", "")
    result.setdefault("table", pd.DataFrame())
    result.setdefault("kind", "local_verified")
    result.setdefault("structured_query", {})
    why = str(result.get("takeaway") or result.get("note") or "").strip()
    if not why and reason:
        why = "This answer was generated from Shiva's verified local fantasy data because the live GPT connection was unavailable."
    result["why"] = why
    return result


def _split_model_response(text: str) -> tuple[str, str]:
    """Split ChatGPT's FINAL ANSWER / WHY response into UI-ready fields."""
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
    """GPT analyst grounded in deterministic verified Shiva evidence."""
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
                + "\n\nReturn exactly two sections: FINAL ANSWER and WHY. Use factual numbers only when supported by the verified evidence."
            ),
        )
        text = (response.output_text or "").strip()
        if not text:
            return _local_fallback(local_report, "empty_model_response")

        answer, why = _split_model_response(text)
        if not answer:
            return _local_fallback(local_report, "empty_model_answer")

        return {
            "title": "🧠 ASK SHIVA GPT",
            "answer": answer,
            "why": why or "The recommendation is based on the verified Shiva evidence retrieved for this specific question.",
            "note": "",
            "takeaway": "",
            "table": pd.DataFrame(),
            "kind": "chatgpt",
            "structured_query": evidence.get("structured_query", {}),
        }
    except Exception:
        return _local_fallback(local_report, "openai_error")
