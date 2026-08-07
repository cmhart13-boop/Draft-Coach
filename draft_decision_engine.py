from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd

QUESTION_TYPES = (
    "PLAYER_STATS",
    "PLAYER_COMPARISON",
    "DRAFT_RECOMMENDATION",
    "ADP_VALUE",
    "HISTORICAL_TREND",
    "LEAGUE_HISTORY",
    "ROSTER_CONSTRUCTION",
    "AVAILABILITY",
    "POSITIONAL_SCARCITY",
    "NEWS",
    "GENERAL_FANTASY_ANALYSIS",
)


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def classify_question_types(question: str, resolved_players: list[str] | None = None) -> list[str]:
    """Multi-label routing. Classification selects evidence; it never selects the answer."""
    q = question.lower().strip()
    players = resolved_players or []
    types: list[str] = []

    if players and re.search(r"\b(ppg|points per game|fantasy points|games|targets?|receptions?|yards?|touchdowns?|finish|rank|stats?)\b", q):
        types.append("PLAYER_STATS")
    if len(players) >= 2 or re.search(r"\b(vs\.?|versus|compare|rather| or )\b", q):
        types.append("PLAYER_COMPARISON")
    if re.search(r"\b(should i|would you|who should|draft|take|pick|select|best choice|best player)\b", q):
        types.append("DRAFT_RECOMMENDATION")
    if re.search(r"\b(adp|average draft position|value|overdraft|reach|price|cost)\b", q):
        types.append("ADP_VALUE")
    if re.search(r"\b(since 20\d{2}|histor|trend|how often|bust|hit rate|last \d+ years?|round \d+)\b", q):
        types.append("HISTORICAL_TREND")
    if re.search(r"\b(my league|our league|championship|manager|who did i|shiva 2\.0|league history)\b", q):
        types.append("LEAGUE_HISTORY")
    if re.search(r"\b(my roster|my team|roster|construction|already have|need a|rb\d|wr\d|qb\d|te\d|flex)\b", q):
        types.append("ROSTER_CONSTRUCTION")
    if re.search(r"\b(make it back|available at|available when|next pick|survive|still be there|availability)\b", q):
        types.append("AVAILABILITY")
    if re.search(r"\b(scarcity|tier|dry up|drop.?off|remaining|run on|position.*left)\b", q):
        types.append("POSITIONAL_SCARCITY")
    if re.search(r"\b(news|injur|out for|practice|suspension|depth chart|trade|signed|released)\b", q):
        types.append("NEWS")

    return list(dict.fromkeys(types)) or ["GENERAL_FANTASY_ANALYSIS"]


def snake_team_for_pick(overall_pick: int, teams: int) -> int:
    round_no = (overall_pick - 1) // teams + 1
    in_round = (overall_pick - 1) % teams
    return teams - in_round if round_no % 2 == 0 else in_round + 1


def next_pick_for_slot(current_pick: int, draft_position: int, teams: int, rounds: int = 16) -> int | None:
    for overall in range(max(1, current_pick + 1), teams * rounds + 1):
        if snake_team_for_pick(overall, teams) == draft_position:
            return overall
    return None


def round_pick_label(overall_pick: int | None, teams: int) -> str:
    if not overall_pick:
        return "—"
    rnd = (int(overall_pick) - 1) // teams + 1
    slot = (int(overall_pick) - 1) % teams + 1
    return f"{rnd}.{slot:02d}"


def roster_counts(roster: list[dict[str, Any]] | None) -> dict[str, int]:
    counts = Counter(str(p.get("position") or "").upper() for p in (roster or []))
    return {p: int(counts.get(p, 0)) for p in ("RB", "WR", "QB", "TE", "D/ST", "K")}


def canonical_draft_state(raw: dict[str, Any] | None, rankings: pd.DataFrame | None = None) -> dict[str, Any]:
    """Normalize legacy mock state into one shared app-facing state shape."""
    raw = raw or {}
    settings = raw.get("settings", {}) if isinstance(raw, dict) else {}
    teams = int(settings.get("teamsCount") or raw.get("teams") or 10)
    draft_position = int(str(raw.get("userTeamId") or f"t{raw.get('draft_position', 4)}").lstrip("t") or 4)
    rounds = int(settings.get("rounds") or raw.get("rounds") or 16)
    current_pick = int(raw.get("currentOverallPick") or raw.get("current_pick") or 1)
    current_round = int(raw.get("currentRound") or raw.get("current_round") or ((current_pick - 1) // teams + 1))
    current_team_raw = raw.get("currentTeam") or raw.get("current_team") or f"t{snake_team_for_pick(current_pick, teams)}"
    current_team = int(str(current_team_raw).lstrip("t")) if str(current_team_raw).lstrip("t").isdigit() else snake_team_for_pick(current_pick, teams)

    team_rows = raw.get("teams") if isinstance(raw.get("teams"), list) else []
    team_rosters: dict[str, list[dict[str, Any]]] = {}
    for team in team_rows:
        team_rosters[str(team.get("id") or team.get("draftSlot"))] = list(team.get("roster") or [])
    user_roster = team_rosters.get(str(raw.get("userTeamId")), raw.get("user_roster") or [])

    available = raw.get("availablePlayers") or raw.get("available_players") or []
    if not available and rankings is not None and not rankings.empty:
        available = [
            {
                "name": str(r.get("player_name")),
                "position": str(r.get("position")),
                "team": str(r.get("team") or ""),
                "adp": float(r.get("adp")) if pd.notna(r.get("adp")) else None,
                "rank": int(r.get("overall_rank")) if pd.notna(r.get("overall_rank")) else None,
            }
            for _, r in rankings.iterrows()
            if pd.notna(r.get("player_name"))
        ]

    next_pick = next_pick_for_slot(current_pick - 1, draft_position, teams, rounds)
    return {
        "teams": teams,
        "draft_position": draft_position,
        "rounds": rounds,
        "scoring": str(settings.get("scoring") or raw.get("scoring") or "PPR"),
        "seconds_per_pick": int(settings.get("secondsPerPick") or raw.get("seconds_per_pick") or 60),
        "current_pick": current_pick,
        "current_round": current_round,
        "current_team": current_team,
        "current_pick_label": round_pick_label(current_pick, teams),
        "next_user_pick": next_pick,
        "next_user_pick_label": round_pick_label(next_pick, teams),
        "drafted_players": list(raw.get("picks") or raw.get("drafted_players") or []),
        "available_players": list(available),
        "user_roster": list(user_roster),
        "team_rosters": team_rosters or dict(raw.get("team_rosters") or {}),
        "queue": list(raw.get("queue") or []),
        "watchlist": list(raw.get("watchlist") or []),
        "avoid_list": list(raw.get("avoid_list") or []),
        "player_notes": dict(raw.get("player_notes") or {}),
        "draft_log": list(raw.get("draft_log") or raw.get("picks") or []),
        "timer_remaining": int(raw.get("timer_remaining") or (raw.get("timer") or {}).get("remaining") or 60),
        "roster_counts": roster_counts(user_roster),
        "status": raw.get("status") or "ready",
    }


def availability_probability(adp: float | None, next_pick: int | None, spread: float = 5.5) -> float | None:
    """ADP-based availability estimate, explicitly a projection rather than a historical fact."""
    if adp is None or next_pick is None or pd.isna(adp):
        return None
    z = (float(adp) - float(next_pick)) / max(1.0, float(spread))
    return float(1.0 / (1.0 + math.exp(-z)))


def _available_frame(state: dict[str, Any], rankings: pd.DataFrame) -> pd.DataFrame:
    available = state.get("available_players") or []
    if available:
        names = {_norm(p.get("name") or p.get("player_name")) for p in available}
        frame = rankings[rankings["player_name"].astype(str).map(_norm).isin(names)].copy()
        if not frame.empty:
            return frame
    return rankings.copy()


def positional_scarcity(rankings: pd.DataFrame, state: dict[str, Any], lookahead: int = 24) -> dict[str, Any]:
    frame = _available_frame(state, rankings)
    if frame.empty:
        return {}
    current_pick = int(state.get("current_pick") or 1)
    next_pick = state.get("next_user_pick")
    result: dict[str, Any] = {}
    for pos in ("RB", "WR", "QB", "TE"):
        p = frame[frame["position"].astype(str).str.upper().eq(pos)].copy()
        if p.empty:
            continue
        p["adp"] = pd.to_numeric(p["adp"], errors="coerce")
        p = p.dropna(subset=["adp"]).sort_values("adp")
        if p.empty:
            continue
        before_next = int((p["adp"] <= float(next_pick or current_pick + lookahead)).sum())
        top_now = p.head(1).iloc[0]
        next_tier_gap = None
        if len(p) >= 2:
            next_tier_gap = float(p.iloc[1]["adp"] - p.iloc[0]["adp"])
        result[pos] = {
            "remaining": int(len(p)),
            "expected_to_go_before_next_pick": before_next,
            "best_available": str(top_now["player_name"]),
            "best_available_adp": float(top_now["adp"]),
            "next_player_adp_gap": next_tier_gap,
        }
    return result


def historical_price_risk(roi: pd.DataFrame, current_adp: float, position: str, window: int = 6) -> dict[str, Any]:
    """Summarize historical outcomes around a comparable draft price; never fabricates missing rows."""
    if roi is None or roi.empty or "overall_pick" not in roi.columns:
        return {}
    frame = roi.copy()
    frame["overall_pick"] = pd.to_numeric(frame["overall_pick"], errors="coerce")
    frame = frame.dropna(subset=["overall_pick"])
    if "position" in frame.columns:
        frame = frame[frame["position"].astype(str).str.upper().eq(str(position).upper())]
    frame = frame[frame["overall_pick"].between(max(1, current_adp - window), current_adp + window)]
    if frame.empty:
        return {}
    out: dict[str, Any] = {"sample_size": int(len(frame))}
    if {"position_draft_rank", "position_finish_total"}.issubset(frame.columns):
        draft_rank = pd.to_numeric(frame["position_draft_rank"], errors="coerce")
        finish = pd.to_numeric(frame["position_finish_total"], errors="coerce")
        delta = finish - draft_rank
        valid = delta.dropna()
        if not valid.empty:
            out["median_finish_minus_draft_rank"] = float(valid.median())
            out["bust_rate_10_plus_spots"] = float((valid >= 10).mean())
            out["beat_price_rate"] = float((valid < 0).mean())
    if "final_draft_roi" in frame.columns:
        vals = pd.to_numeric(frame["final_draft_roi"], errors="coerce").dropna()
        if not vals.empty:
            out["median_draft_roi"] = float(vals.median())
    return out


def player_signal_rows(rankings: pd.DataFrame, roi: pd.DataFrame, state: dict[str, Any], limit: int = 18) -> list[dict[str, Any]]:
    frame = _available_frame(state, rankings).copy()
    if frame.empty:
        return []
    for col in ("adp", "overall_rank", "consensus_adp"):
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=["adp"])
    frame["shiva_rank"] = frame.get("overall_rank", frame["adp"])
    frame["shiva_rank"] = pd.to_numeric(frame["shiva_rank"], errors="coerce").fillna(frame["adp"])
    frame["pick_value"] = frame["adp"] - frame["shiva_rank"]
    next_pick = state.get("next_user_pick")
    rows: list[dict[str, Any]] = []
    for _, r in frame.sort_values(["shiva_rank", "adp"]).head(max(limit * 2, 30)).iterrows():
        risk = historical_price_risk(roi, float(r["adp"]), str(r["position"]))
        rows.append({
            "player_name": str(r["player_name"]),
            "position": str(r["position"]),
            "team": str(r.get("team") or ""),
            "adp": float(r["adp"]),
            "shiva_rank": float(r["shiva_rank"]),
            "pick_value": float(r["pick_value"]),
            "availability_next_pick": availability_probability(float(r["adp"]), next_pick),
            "historical_price_risk": risk,
        })
    return rows[:limit]


def build_today_edge(rankings: pd.DataFrame, roi: pd.DataFrame, state: dict[str, Any], max_cards: int = 6) -> list[dict[str, Any]]:
    """Generate deterministic draft-edge cards from loaded data and current draft state."""
    signals = player_signal_rows(rankings, roi, state, limit=30)
    scarcity = positional_scarcity(rankings, state)
    cards: list[dict[str, Any]] = []

    value = [s for s in signals if s["pick_value"] >= 3]
    if value:
        s = max(value, key=lambda x: x["pick_value"])
        cards.append({"kind": "RISING VALUE", "icon": "🔥", "tone": "green", "title": s["player_name"], "text": f"ADP {s['adp']:.0f} → Shiva rank {s['shiva_rank']:.0f}. {s['pick_value']:+.0f} picks of board value."})

    risk_rows = [s for s in signals if (s.get("historical_price_risk") or {}).get("bust_rate_10_plus_spots") is not None]
    if risk_rows:
        s = max(risk_rows, key=lambda x: x["historical_price_risk"]["bust_rate_10_plus_spots"])
        risk = s["historical_price_risk"]
        cards.append({"kind": "PRICE RISK", "icon": "📉", "tone": "red", "title": s["player_name"], "text": f"ADP {s['adp']:.0f}. Comparable {s['position']} prices busted by 10+ positional spots {risk['bust_rate_10_plus_spots']:.0%} of the time (n={risk['sample_size']})."})

    if scarcity:
        pos, info = max(scarcity.items(), key=lambda kv: kv[1].get("expected_to_go_before_next_pick", 0))
        cards.append({"kind": "TIER ALERT", "icon": "⚠️", "tone": "orange", "title": pos, "text": f"{info['expected_to_go_before_next_pick']} {pos}s carry ADPs before your next pick. Best available: {info['best_available']} (ADP {info['best_available_adp']:.0f})."})

    avail = [s for s in signals if s.get("availability_next_pick") is not None]
    if avail:
        plausible = [s for s in avail if 0.55 <= s["availability_next_pick"] <= 0.9]
        if plausible:
            s = max(plausible, key=lambda x: x["shiva_rank"] * -1)
            cards.append({"kind": "NEXT-PICK VALUE", "icon": "💎", "tone": "blue", "title": s["player_name"], "text": f"ADP-based estimate: {s['availability_next_pick']:.0%} chance to still be available at {state.get('next_user_pick_label', 'your next pick')}."})

    return cards[:max_cards]


def build_decision_context(
    question: str,
    rankings: pd.DataFrame,
    roi: pd.DataFrame,
    draft_state: dict[str, Any] | None = None,
    resolved_players: list[str] | None = None,
) -> dict[str, Any]:
    state = canonical_draft_state(draft_state, rankings)
    types = classify_question_types(question, resolved_players)
    signals = player_signal_rows(rankings, roi, state, limit=24)
    if resolved_players:
        wanted = {_norm(x) for x in resolved_players}
        named = [s for s in signals if _norm(s["player_name"]) in wanted]
    else:
        named = []
    return {
        "question_types": types,
        "league": {
            "teams": state["teams"],
            "scoring": state["scoring"],
            "draft_position": state["draft_position"],
        },
        "draft": {
            "current_round": state["current_round"],
            "current_pick": state["current_pick"],
            "current_pick_label": state["current_pick_label"],
            "next_user_pick": state["next_user_pick"],
            "next_user_pick_label": state["next_user_pick_label"],
            "on_clock_team": state["current_team"],
            "user_roster": state["user_roster"],
            "roster_counts": state["roster_counts"],
            "queue": state["queue"],
        },
        "named_player_signals": named,
        "board_signals": signals,
        "positional_scarcity": positional_scarcity(rankings, state),
        "today_edge": build_today_edge(rankings, roi, state, max_cards=6),
        "method_notes": {
            "availability": "Model estimate derived from current ADP distance to the next user pick; it is not a guaranteed fact.",
            "historical_price_risk": "Calculated only from loaded historical draft/finish rows around comparable pick prices.",
        },
    }
