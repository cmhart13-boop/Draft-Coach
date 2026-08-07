from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd
from openai import OpenAI

from shiva_query_router import retrieve_shiva_context, run_shiva_query

MODEL = "gpt-5.6"

SYSTEM_INSTRUCTIONS = """
You are Shiva GPT, an elite fantasy-football analyst.

You answer fantasy-football questions using analytical reasoning rather than preset verdicts.

DEFAULT LEAGUE FORMAT UNLESS THE USER SAYS OTHERWISE:
- ESPN scoring
- Full 1-point PPR
- 10-team redraft
- standard ESPN roster construction
- snake draft

YOU CAN ANSWER:
- player statistical questions
- historical questions
- averages and PPG
- weekly consistency
- ADP questions
- player comparisons
- draft decisions
- roster construction questions
- hypothetical scenarios
- breakout/bust questions
- positional trends
- historical trend analysis
- live draft-board decisions when LIVE DRAFT CONTEXT is supplied

CORE ARCHITECTURE RULE:
THE DATABASE IS THE CALCULATOR. YOU ARE THE ANALYST.
The application may supply verified statistical calculations, player-season rows, weekly rows, ADP rows, historical aggregates, and live draft state. Treat supplied facts as authoritative for the fields represented by those datasets. The application code does NOT choose a fantasy winner for you.

FACTUAL QUESTIONS:
- Report the requested statistic from the verified context.
- Do not invent a number that is not supplied or deterministically calculated.
- If a required factual value is unavailable, say exactly what is missing.

DECISION / OPINION QUESTIONS:
- You make the recommendation yourself after analyzing the original user question and supplied evidence.
- Never select a player merely because he has more raw fantasy points than a player at another position.
- For cross-position comparisons, evaluate positional scarcity, value over replacement, ADP, opportunity cost, expected positional advantage, roster construction, league size, starting requirements, replacement-level options available later, weekly consistency, ceiling, floor, historical performance, and current player/team context when those facts are available.
- Current ADP is evidence of draft cost/availability, not an automatic winner rule.
- Historical PPG is evidence of production, not an automatic winner rule.
- Give a direct answer when the user asks who you would pick, then explain the actual fantasy-football reasoning.

LIVE DRAFT RULES:
- When LIVE DRAFT CONTEXT is supplied, answer from the actual current board, not a generic hypothetical.
- Respect drafted players: never recommend a player who is absent from availablePlayers.
- Use current round, overall pick, team count, scoring, user's roster, roster needs, queue, opponent rosters, recent selections and remaining player pool.
- Consider whether a target is likely to survive to the user's next pick.
- If asked “RB or WR?” or “best fit?”, analyze the user's actual roster construction and available tiers.

CONVERSATION RULES:
- Use the EXACT ORIGINAL USER QUESTION as the request you answer.
- Do not mention Pandas, routing, prompts, JSON, APIs, databases, evidence objects, or internal systems.
- Never use generic filler such as "the recommendation is based on retrieved player records" or "the supporting rows are the evidence."
- If the user asks "Who would you rather draft?" and no players/context can be inferred from the supplied context, ask them which players they mean.
- If the user supplies a hypothetical roster situation, reason about roster construction rather than demanding a historical exact match.
- Keep answers useful and mobile-friendly.

RESPONSE STYLE:
For a simple factual question, answer naturally in one or two concise paragraphs.
For a player comparison or draft decision, start with a direct choice and then explain why.
For a deeper question, you may use concise sections such as VERDICT, KEY DATA, WHY, RISK / COUNTERARGUMENT, and BOTTOM LINE when helpful.
Do not force every answer into the same template.
"""

GENERIC_WHY_PHRASES = (
    "recommendation is based only on",
    "recommendation is based on the verified",
    "supporting rows are the evidence",
    "retrieved player records",
    "no unrelated league-wide average",
    "verified shiva evidence",
)


def build_verified_evidence(
    question: str,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    rankings: pd.DataFrame,
    weekly: pd.DataFrame | None = None,
) -> dict[str, Any]:
    return retrieve_shiva_context(question, history, roi, rankings, weekly)


def _configured_api_key(explicit_key: str | None = None) -> str:
    return (explicit_key or os.getenv("OPENAI_API_KEY") or "").strip()


def _clean_explanation(text: str) -> str:
    value = (text or "").strip()
    lower = value.lower()
    if not value:
        return ""
    if any(phrase in lower for phrase in GENERIC_WHY_PHRASES):
        return ""
    return value


def _split_for_existing_ui(text: str) -> tuple[str, str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return "", ""
    match = re_search_why(cleaned)
    if match is not None:
        answer = cleaned[: match[0]].strip()
        why = cleaned[match[1] :].strip()
        return answer, _clean_explanation(why)
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    if len(paragraphs) >= 2:
        return paragraphs[0], _clean_explanation("\n\n".join(paragraphs[1:]))
    return cleaned, ""


def re_search_why(text: str) -> tuple[int, int] | None:
    import re
    match = re.search(r"(?im)^\s*(?:WHY|HERE'S WHY)\s*:\s*", text)
    if not match:
        return None
    return match.start(), match.end()


def _factual_fallback(
    question: str,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    rankings: pd.DataFrame,
    weekly: pd.DataFrame | None,
    reason: str,
) -> dict[str, Any]:
    report = run_shiva_query(question, history, roi, rankings, weekly)
    result = dict(report)
    result["title"] = "🧠 ASK SHIVA GPT"
    result["table"] = pd.DataFrame()
    kind = str(report.get("kind") or "")
    if kind == "analysis_required":
        result["answer"] = "SHIVA GPT CONNECTION REQUIRED FOR THIS RECOMMENDATION"
        result["why"] = "The verified fantasy context is available, but the application code intentionally does not choose a winner. Reconnect Shiva GPT so the AI analyst can evaluate the decision."
    else:
        result["why"] = _clean_explanation(str(report.get("note") or report.get("takeaway") or ""))
    result["note"] = ""
    result["takeaway"] = ""
    result["fallback_reason"] = reason
    return result


def _response_input(question: str, evidence: dict[str, Any], draft_context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data_context = (
        "VERIFIED SHIVA DATA CONTEXT\n"
        "Use this as factual evidence only. It contains no preselected fantasy winner.\n\n"
        + json.dumps(evidence, ensure_ascii=False, default=str)
    )
    if draft_context:
        data_context += (
            "\n\nLIVE DRAFT CONTEXT\n"
            "This is the current centralized draft state. Use it when the question concerns the live mock draft.\n\n"
            + json.dumps(draft_context, ensure_ascii=False, default=str)
        )
    return [
        {"role": "developer", "content": data_context},
        {"role": "user", "content": question},
    ]


def ask_shiva_via_chatgpt(
    question: str,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    rankings: pd.DataFrame,
    weekly: pd.DataFrame | None,
    api_key: str | None = None,
    draft_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Production Ask Shiva endpoint: retrieve facts, then let the OpenAI model analyze them."""
    original_question = question.strip()
    evidence = build_verified_evidence(original_question, history, roi, rankings, weekly)
    key = _configured_api_key(api_key)
    if not key:
        return _factual_fallback(original_question, history, roi, rankings, weekly, "missing_api_key")
    try:
        client = OpenAI(api_key=key)
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": "medium"},
            instructions=SYSTEM_INSTRUCTIONS,
            input=_response_input(original_question, evidence, draft_context=draft_context),
        )
        text = (response.output_text or "").strip()
        if not text:
            return _factual_fallback(original_question, history, roi, rankings, weekly, "empty_model_response")
        answer, why = _split_for_existing_ui(text)
        if not answer:
            answer = text
        return {
            "title": "🧠 ASK SHIVA GPT",
            "answer": answer,
            "why": why,
            "note": "",
            "takeaway": "",
            "table": pd.DataFrame(),
            "kind": "chatgpt",
            "structured_query": {
                "intent": evidence.get("intent"),
                "resolved_players": evidence.get("resolved_players", []),
                "requested_seasons": evidence.get("requested_seasons", []),
                "live_draft": bool(draft_context),
            },
        }
    except Exception as exc:
        fallback = _factual_fallback(original_question, history, roi, rankings, weekly, "openai_error")
        fallback["debug_error"] = str(exc)
        return fallback
