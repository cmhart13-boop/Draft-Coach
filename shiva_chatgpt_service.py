from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd
from openai import OpenAI

from shiva_query_router import resolve_players, run_shiva_query

MODEL = "gpt-5.6"

SYSTEM_INSTRUCTIONS = """
You are Shiva GPT, an expert ESPN Full-PPR fantasy-football analyst embedded inside a draft application.

You must answer like a knowledgeable human fantasy analyst, not a spreadsheet and not a generic disclaimer generator.

NON-NEGOTIABLE DATA RULES:
- VERIFIED EVIDENCE supplied by the app is the source of truth for every factual statistic, ADP, finish, age, injury fact, or current-season claim.
- Never invent a number.
- Never substitute league-wide averages for a named-player question.
- If the verified evidence contains a deterministic draft recommendation, you MUST NOT contradict it. Your job is to explain it clearly.
- For a DRAFT DECISION between named players, do NOT simply pick the player with the higher historical PPG. Prioritize current ESPN ADP, expected availability, positional opportunity cost, roster construction, and then use historical production as supporting context.
- In early rounds, explicitly consider the opportunity cost of taking QB/TE over elite RB/WR when the verified current ADP supports that distinction.
- If evidence is incomplete, say exactly what is missing. Do not fake certainty.
- ESPN Full PPR means one point per reception.
- If evidence references the wrong player or season, ignore it.

OUTPUT FORMAT — FOLLOW EXACTLY:
FINAL ANSWER: <one clear, concise answer to the user's question>
WHY:
<2-4 specific reasons explaining the actual football decision. Cite the verified evidence naturally. Do not write a generic sentence about being based on data or retrieved records.>

STYLE:
- FINAL ANSWER must be decisive and short.
- WHY must contain the actual football reasoning the user came for.
- If the user asks who to draft, say who and explain why.
- For early-round RB/WR versus QB decisions, explain positional opportunity cost and current ADP when those facts are present.
- Mobile-friendly.
- Do not mention Pandas, routing, prompts, evidence objects, databases, APIs, or internal systems.
"""

GENERIC_WHY_PHRASES = (
    "recommendation is based only on",
    "recommendation is based on the verified",
    "supporting rows are the evidence",
    "retrieved player records",
    "no unrelated league-wide average",
    "verified shiva evidence",
)


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
    report = run_shiva_query(question, history, roi, rankings, weekly)
    players, _ = resolve_players(question, history, rankings)

    current_rows = pd.DataFrame()
    if players and rankings is not None and not rankings.empty:
        wanted = {p.lower() for p in players}
        current_rows = rankings[
            rankings["player_name"].astype(str).str.lower().isin(wanted)
        ].copy()

    evidence = {
        "title": report.get("title", ""),
        "deterministic_answer": report.get("answer", ""),
        "deterministic_reasoning": report.get("takeaway") or report.get("note") or "",
        "kind": report.get("kind", ""),
        "structured_query": report.get("structured_query", {}),
        "current_rankings_for_named_players": _frame_to_records(current_rows, limit=10),
        "supporting_rows": _frame_to_records(report.get("table")),
    }
    return evidence, report


def _configured_api_key(explicit_key: str | None = None) -> str:
    return (explicit_key or os.getenv("OPENAI_API_KEY") or "").strip()


def _clean_why(text: str) -> str:
    why = (text or "").strip()
    lower = why.lower()
    if not why:
        return ""
    if any(phrase in lower for phrase in GENERIC_WHY_PHRASES):
        return ""
    return why


def _local_fallback(report: dict[str, Any], reason: str = "") -> dict[str, Any]:
    result = dict(report)
    result["title"] = "🧠 ASK SHIVA GPT"
    result.setdefault("answer", "")
    result.setdefault("note", "")
    result.setdefault("takeaway", "")
    result.setdefault("table", pd.DataFrame())
    result.setdefault("kind", "local_verified")
    result.setdefault("structured_query", {})

    why = _clean_why(str(result.get("takeaway") or result.get("note") or ""))
    if not why and reason:
        why = "I could not reach the live GPT analyst, so I am showing the verified local recommendation without inventing extra reasoning."
    result["why"] = why
    return result


def _split_model_response(text: str) -> tuple[str, str]:
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


def _enforce_deterministic_draft_answer(
    local_report: dict[str, Any],
    model_answer: str,
    model_why: str,
) -> tuple[str, str]:
    """Draft recommendations may be explained by GPT, but not contradicted by it."""
    kind = str(local_report.get("kind") or "")
    local_answer = str(local_report.get("answer") or "").strip()
    local_why = str(local_report.get("takeaway") or local_report.get("note") or "").strip()

    if kind == "draft_decision" and local_answer.upper().startswith("I'D TAKE"):
        answer = local_answer
        why = _clean_why(model_why) or _clean_why(local_why)
        return answer, why

    return model_answer, _clean_why(model_why)


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
                + "\n\nIMPORTANT: If deterministic_answer contains an explicit draft recommendation, preserve that recommendation exactly and use WHY to explain the football logic. Return exactly two sections: FINAL ANSWER and WHY."
            ),
        )

        text = (response.output_text or "").strip()
        if not text:
            return _local_fallback(local_report, "empty_model_response")

        answer, why = _split_model_response(text)
        if not answer:
            return _local_fallback(local_report, "empty_model_answer")

        answer, why = _enforce_deterministic_draft_answer(local_report, answer, why)

        if not why:
            why = _clean_why(
                str(local_report.get("takeaway") or local_report.get("note") or "")
            )

        return {
            "title": "🧠 ASK SHIVA GPT",
            "answer": answer,
            "why": why,
            "note": "",
            "takeaway": "",
            "table": pd.DataFrame(),
            "kind": "chatgpt",
            "structured_query": evidence.get("structured_query", {}),
        }
    except Exception:
        return _local_fallback(local_report, "openai_error")
