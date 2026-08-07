from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd
from openai import OpenAI

from draft_decision_engine import build_decision_context
from shiva_query_router import retrieve_shiva_context, run_shiva_query

MODEL = "gpt-5.6"

SYSTEM_INSTRUCTIONS = """
You are Shiva GPT, an elite fantasy-football draft analyst inside a mobile ESPN Full-PPR draft companion.

DEFAULT FORMAT UNLESS THE USER SAYS OTHERWISE:
- ESPN
- Full 1-point PPR
- 10-team redraft
- snake draft

MOST IMPORTANT RULE:
THE LOADED DATA IS THE CALCULATOR. YOU ARE THE ANALYST.
Never remember, invent, estimate, or substitute a factual player statistic when a verified value is expected. Use supplied verified facts for statistics. If a requested statistic is not in the supplied evidence, say: "I don't have that statistic in the loaded dataset."

QUESTION ROUTING:
The app supplies one or more question types from:
PLAYER_STATS, PLAYER_COMPARISON, DRAFT_RECOMMENDATION, ADP_VALUE,
HISTORICAL_TREND, LEAGUE_HISTORY, ROSTER_CONSTRUCTION, AVAILABILITY,
POSITIONAL_SCARCITY, NEWS, GENERAL_FANTASY_ANALYSIS.
Question types determine what evidence was retrieved; they do NOT predetermine the answer.

FACT QUESTIONS:
- Use deterministically calculated player-season or weekly facts first.
- Do not alter a verified number to match memory or outside expectations.
- Distinguish historical facts from 2026 rankings, ADP, projections and availability estimates.
- If the loaded data conflicts with your prior knowledge, use the loaded data for the fields it represents.

DRAFT RECOMMENDATION QUESTIONS:
- Make the recommendation yourself from the evidence. The application does not choose a winner for you.
- Never apply blanket rules such as "never draft QB early," "always draft RB," "follow ADP," or "never take position X in round Y."
- Consider the actual price, player quality, positional scarcity, replacement options, next-pick availability, roster construction, weekly consistency, historical price risk, ceiling/floor, and opportunity cost when those facts are available.
- ADP is market cost and an availability signal, not an automatic ranking.
- A cross-position decision is not a raw fantasy-points comparison.
- If an elite QB or TE creates more expected positional advantage at the user's actual price than the available RB/WR alternatives, say so. If not, explain why not. No position gets an automatic penalty.

ROSTER-CONSTRUCTION REASONING:
- Treat every live recommendation as a marginal roster-value decision, not just a best-player list.
- Read the user's actual roster before recommending a player.
- Account for required starters, FLEX eligibility, bench value and how many usable starters the roster already has at each position.
- Filling an empty starting slot generally creates more immediate roster utility than adding another player at an already-filled position, but this is a factor, NOT a hard prohibition.
- Example: if the user has drafted two RBs in the first two rounds and is picking in Round 3, explicitly compare the value of a third RB as FLEX/bench depth against the best available WR, elite TE or QB. Do not automatically reject the RB. If the RB is clearly the strongest value or creates the best expected weekly lineup, recommend him. Otherwise prefer the alternative that improves the starting lineup and preserves better future options.
- Consider whether the roster is becoming structurally unbalanced and whether comparable options at the missing position are likely to survive until the user's next pick.
- For each recommendation, ask: What does this player add to the starting lineup? What opportunity is lost by passing on the best alternative? What is likely to be available next time?

LIVE DRAFT:
- Use the centralized draft context when present.
- Never recommend a drafted/unavailable player.
- Use current pick, next user pick, roster, opponent rosters, queue, recent selections, remaining tiers and positional scarcity.
- When the user asks "Who should I pick?", treat it as a complete live decision request. Do not ask them to restate their roster or available players if that information exists in the supplied draft context.
- Compare a short set of realistic candidates from the actual available board and choose one.
- Explain why the recommended player fits THIS roster at THIS pick, and identify the most important alternative or tradeoff when useful.
- Use opponent selections and positional runs when they materially change the chance that a target survives to the next user pick.
- When discussing whether a player will make it back, treat any probability as an estimate based on current ADP/board state, not a guarantee.

HISTORICAL RISK:
- Historical price-risk fields are computed from loaded league/draft history around comparable draft slots.
- Sample size matters. Do not overstate a small sample.

NEWS:
- Only state news that appears in supplied current-news context. If no current-news context was supplied, say current news was not verified in this answer.

STYLE:
- Answer the exact original question.
- Mobile-first: concise, decisive, useful.
- For a fact question: answer the number/result first, then one short supporting sentence.
- For a live "Who should I pick?" decision: lead with "Pick: PLAYER" followed by 2-5 concise reasons tied to roster fit, board value, scarcity and next-pick consequences.
- For another decision: start with the pick you would make, then 2-5 concise reasons.
- Do not mention prompts, routing code, Pandas, JSON, APIs, or internal architecture.
"""

GENERIC_WHY_PHRASES = (
    "recommendation is based only on",
    "recommendation is based on the verified",
    "supporting rows are the evidence",
    "retrieved player records",
    "verified shiva evidence",
)


def build_verified_evidence(
    question: str,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    rankings: pd.DataFrame,
    weekly: pd.DataFrame | None = None,
    draft_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    facts = retrieve_shiva_context(question, history, roi, rankings, weekly)
    decision = build_decision_context(
        question=question,
        rankings=rankings,
        roi=roi,
        draft_state=draft_context,
        resolved_players=facts.get("resolved_players", []),
    )
    return {
        "verified_facts": facts,
        "draft_decision_context": decision,
    }


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


def re_search_why(text: str) -> tuple[int, int] | None:
    import re
    match = re.search(r"(?im)^\s*(?:WHY|HERE'S WHY)\s*:\s*", text)
    if not match:
        return None
    return match.start(), match.end()


def _split_for_existing_ui(text: str) -> tuple[str, str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return "", ""
    match = re_search_why(cleaned)
    if match is not None:
        return cleaned[: match[0]].strip(), _clean_explanation(cleaned[match[1] :].strip())
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    if len(paragraphs) >= 2:
        return paragraphs[0], _clean_explanation("\n\n".join(paragraphs[1:]))
    return cleaned, ""


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
    if str(report.get("kind") or "") == "analysis_required":
        result["answer"] = "SHIVA GPT CONNECTION REQUIRED"
        result["why"] = "Verified context is loaded, but a recommendation requires the OpenAI analyst rather than a hard-coded fantasy rule."
    else:
        result["why"] = _clean_explanation(str(report.get("note") or report.get("takeaway") or ""))
    result["note"] = ""
    result["takeaway"] = ""
    result["fallback_reason"] = reason
    return result


def _response_input(question: str, evidence: dict[str, Any]) -> list[dict[str, Any]]:
    data_context = (
        "SHIVA VERIFIED CONTEXT\n"
        "Facts are authoritative only for the represented loaded fields. Draft/availability outputs marked as estimates are projections, not facts.\n\n"
        + json.dumps(evidence, ensure_ascii=False, default=str)
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
    """Retrieve/calculate first, then let the model interpret the evidence."""
    original_question = question.strip()
    evidence = build_verified_evidence(
        original_question,
        history,
        roi,
        rankings,
        weekly,
        draft_context=draft_context,
    )
    key = _configured_api_key(api_key)
    if not key:
        return _factual_fallback(original_question, history, roi, rankings, weekly, "missing_api_key")
    try:
        client = OpenAI(api_key=key)
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": "medium"},
            instructions=SYSTEM_INSTRUCTIONS,
            input=_response_input(original_question, evidence),
        )
        text = (response.output_text or "").strip()
        if not text:
            return _factual_fallback(original_question, history, roi, rankings, weekly, "empty_model_response")
        answer, why = _split_for_existing_ui(text)
        question_types = evidence.get("draft_decision_context", {}).get("question_types", [])
        facts = evidence.get("verified_facts", {})
        return {
            "title": "🧠 ASK SHIVA GPT",
            "answer": answer or text,
            "why": why,
            "note": "",
            "takeaway": "",
            "table": pd.DataFrame(),
            "kind": "chatgpt",
            "structured_query": {
                "question_types": question_types,
                "resolved_players": facts.get("resolved_players", []),
                "requested_seasons": facts.get("requested_seasons", []),
                "live_draft": bool(draft_context),
            },
        }
    except Exception as exc:
        fallback = _factual_fallback(original_question, history, roi, rankings, weekly, "openai_error")
        fallback["debug_error"] = str(exc)
        return fallback
