from __future__ import annotations

import re
from typing import Any

import pandas as pd

from shiva_engine import normalize_name, run_shiva_query as run_aggregate_query

MANUAL_ALIASES = {
    "cmc": "Christian McCaffrey",
}

DEFAULT_LEAGUE = {
    "platform": "ESPN",
    "scoring": "Full PPR",
    "reception_points": 1.0,
    "teams": 10,
    "format": "redraft",
    "draft_type": "snake",
    "roster_construction": "standard ESPN",
}

DECISION_WORDS = re.compile(r"\b(?:draft|take|pick|select|choose|rather|would you|should i|round)\b", re.I)
HYPOTHETICAL_WORDS = re.compile(r"\b(?:if i|if we|already drafted|roster|my team|build|start rb|start wr|hypothetical)\b", re.I)
HISTORICAL_WORDS = re.compile(r"\b(?:historical|history|over the last|last \d+|since 20\d{2}|how often|percentage|percent|trend)\b", re.I)
ADP_WORDS = re.compile(r"\b(?:adp|average draft position|draft cost)\b", re.I)
COMPARISON_WORDS = re.compile(r"\b(?:compare|versus|vs\.?| or |more games|higher|better)\b", re.I)


def _report(
    title: str,
    answer: str,
    note: str,
    table: pd.DataFrame | None = None,
    takeaway: str = "",
    kind: str = "facts",
    structured_query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "title": title,
        "answer": answer,
        "note": note,
        "table": table if table is not None else pd.DataFrame(),
        "takeaway": takeaway,
        "kind": kind,
        "structured_query": structured_query or {},
    }


def _season_list(question: str) -> list[int]:
    return sorted({int(x) for x in re.findall(r"\b(20\d{2})\b", question)})


def _all_player_names(history: pd.DataFrame, rankings: pd.DataFrame) -> list[str]:
    names: set[str] = set()
    for frame in (history, rankings):
        if frame is not None and not frame.empty and "player_name" in frame.columns:
            names.update(str(x).strip() for x in frame["player_name"].dropna().unique() if str(x).strip())
    return sorted(names, key=len, reverse=True)


def _player_aliases(names: list[str]) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}
    last_counts: dict[str, int] = {}
    for name in names:
        parts = re.findall(r"[A-Za-z0-9'-]+", name.lower())
        if parts:
            last_counts[parts[-1]] = last_counts.get(parts[-1], 0) + 1

    for name in names:
        parts = re.findall(r"[A-Za-z0-9'-]+", name.lower())
        vals = {name.lower(), normalize_name(name)}
        if len(parts) >= 2:
            vals.add(f"{parts[0][0]}. {parts[-1]}")
            vals.add(f"{parts[0][0]} {parts[-1]}")
            if last_counts.get(parts[-1], 0) == 1:
                vals.add(parts[-1])
        for alias in vals:
            aliases.setdefault(alias, set()).add(name)

    for alias, canonical in MANUAL_ALIASES.items():
        if canonical in names:
            aliases.setdefault(alias, set()).add(canonical)
    return aliases


def resolve_players(question: str, history: pd.DataFrame, rankings: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Resolve named players only. This function never ranks or recommends them."""
    q = question.lower()
    q_norm = normalize_name(question)
    names = _all_player_names(history, rankings)
    aliases = _player_aliases(names)
    found: list[str] = []
    ambiguous: list[str] = []

    for name in names:
        if name.lower() in q:
            found.append(name)

    for alias, matches in aliases.items():
        if len(alias) < 3:
            continue
        if " " in alias or "." in alias:
            matched = alias in q
        else:
            matched = bool(re.search(rf"\b{re.escape(alias)}\b", q)) or alias == q_norm
        if not matched:
            continue
        if len(matches) == 1:
            canonical = next(iter(matches))
            if canonical not in found:
                found.append(canonical)
        elif not any(name in found for name in matches):
            ambiguous.append(alias)

    # Preserve explicit full-name order first, then resolved aliases.
    found = sorted(set(found), key=lambda n: q.find(n.lower()) if n.lower() in q else 10_000)
    return found, sorted(set(ambiguous))


def _metric(question: str) -> str:
    q = question.lower()
    if re.search(r"\b(?:finish|finished|rank|ranking|rb\d+|wr\d+|qb\d+|te\d+)\b", q):
        return "finish"
    if re.search(r"\b(?:receiving stats|receiving line)\b", q):
        return "receiving_stats"
    if re.search(r"\b(?:rushing stats|rushing line)\b", q):
        return "rushing_stats"
    if re.search(r"\b(?:targets?|tgt)\b", q):
        return "targets"
    if re.search(r"\b(?:receptions?|catches)\b", q):
        return "receptions"
    if re.search(r"\breceiving yards?\b", q):
        return "receiving_yards"
    if re.search(r"\breceiving (?:tds?|touchdowns?)\b", q):
        return "receiving_tds"
    if re.search(r"\brushing yards?\b", q):
        return "rushing_yards"
    if re.search(r"\brushing (?:tds?|touchdowns?)\b", q):
        return "rushing_tds"
    if re.search(r"\b(?:ppg|points per game|per-game|per game|weekly scoring)\b", q):
        return "ppg"
    if re.search(r"\b(?:fantasy points|total points|ppr points)\b", q):
        return "points"
    if re.search(r"\b(?:games played|games)\b", q):
        return "games"
    if ADP_WORDS.search(q):
        return "adp"
    return "summary"


def classify_question(question: str, players: list[str] | None = None) -> str:
    """Classification selects data sources only. It must never determine the fantasy answer."""
    players = players or []
    q = question.strip()
    if HYPOTHETICAL_WORDS.search(q):
        return "HYPOTHETICAL"
    if DECISION_WORDS.search(q):
        return "DRAFT_DECISION"
    if ADP_WORDS.search(q):
        return "ADP_QUERY"
    if len(players) > 1 or COMPARISON_WORDS.search(q):
        return "PLAYER_COMPARISON"
    if HISTORICAL_WORDS.search(q):
        return "HISTORICAL_ANALYSIS"
    if players:
        return "STAT_LOOKUP"
    if re.search(r"\b(?:average|top \d+|most|least|how many)\b", q, re.I):
        return "TREND_ANALYSIS"
    return "GENERAL_FANTASY"


def _column(frame: pd.DataFrame | None, *candidates: str) -> str | None:
    if frame is None or frame.empty:
        return None
    lower = {str(c).lower(): c for c in frame.columns}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return None


def _frame_records(frame: pd.DataFrame | None, limit: int = 80) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    safe = frame.head(limit).copy()
    safe = safe.astype(object).where(pd.notna(safe), None)
    return safe.to_dict(orient="records")


def _filter_history(history: pd.DataFrame, players: list[str], seasons: list[int]) -> pd.DataFrame:
    if history is None or history.empty:
        return pd.DataFrame()
    frame = history.copy()
    if players:
        wanted = {normalize_name(p) for p in players}
        frame = frame[frame["player_name"].astype(str).map(normalize_name).isin(wanted)]
    if seasons and "season" in frame.columns:
        frame = frame[pd.to_numeric(frame["season"], errors="coerce").isin(seasons)]
    return frame.copy()


def _filter_rankings(rankings: pd.DataFrame, players: list[str]) -> pd.DataFrame:
    if rankings is None or rankings.empty:
        return pd.DataFrame()
    frame = rankings.copy()
    if players:
        wanted = {normalize_name(p) for p in players}
        frame = frame[frame["player_name"].astype(str).map(normalize_name).isin(wanted)]
    if "adp" in frame.columns:
        frame["adp"] = pd.to_numeric(frame["adp"], errors="coerce")
        frame = frame.sort_values("adp", na_position="last")
    return frame.copy()


def _filter_weekly(weekly: pd.DataFrame | None, players: list[str], seasons: list[int]) -> pd.DataFrame:
    if weekly is None or weekly.empty:
        return pd.DataFrame()
    name_col = _column(weekly, "player_display_name", "player_name", "name", "player")
    season_col = _column(weekly, "season", "year")
    if not name_col:
        return pd.DataFrame()
    frame = weekly.copy()
    if players:
        wanted = {normalize_name(p) for p in players}
        frame = frame[frame[name_col].astype(str).map(normalize_name).isin(wanted)]
    if seasons and season_col:
        frame = frame[pd.to_numeric(frame[season_col], errors="coerce").isin(seasons)]
    return frame.copy()


def _sum_stat(frame: pd.DataFrame, *candidates: str) -> float | None:
    col = _column(frame, *candidates)
    if not col or frame.empty:
        return None
    values = pd.to_numeric(frame[col], errors="coerce")
    if values.notna().sum() == 0:
        return None
    return float(values.sum())


def _exact_player_facts(
    question: str,
    players: list[str],
    seasons: list[int],
    history_rows: pd.DataFrame,
    weekly_rows: pd.DataFrame,
) -> dict[str, Any]:
    """Deterministic calculator only. It returns facts, never a fantasy recommendation."""
    facts: dict[str, Any] = {}
    metric = _metric(question)

    if len(players) == 1 and len(seasons) == 1:
        unique_players = history_rows["player_name"].astype(str).map(normalize_name).nunique() if not history_rows.empty else 0
        unique_seasons = pd.to_numeric(history_rows.get("season"), errors="coerce").dropna().nunique() if not history_rows.empty else 0
        if unique_players > 1 or unique_seasons > 1:
            facts["validation_error"] = "A one-player, one-season lookup broadened beyond the requested entity."
            return facts

        if len(history_rows) == 1:
            row = history_rows.iloc[0]
            facts["player_season"] = {
                "player_name": str(row.get("player_name", players[0])),
                "season": int(row.get("season", seasons[0])),
                "position": row.get("position"),
                "finish": int(row["position_finish_total"]) if pd.notna(row.get("position_finish_total")) else None,
                "fantasy_points_ppr": float(row["fantasy_points_ppr"]) if pd.notna(row.get("fantasy_points_ppr")) else None,
                "points_per_game": float(row["ppg"]) if pd.notna(row.get("ppg")) else None,
                "games_played": int(row["games_played"]) if pd.notna(row.get("games_played")) else None,
                "age": float(row["age"]) if pd.notna(row.get("age")) else None,
            }

    if len(players) == 1 and not weekly_rows.empty:
        player = players[0]
        season = seasons[0] if len(seasons) == 1 else None
        weekly_totals = {
            "player_name": player,
            "season": season,
            "targets": _sum_stat(weekly_rows, "targets", "receiving_targets"),
            "receptions": _sum_stat(weekly_rows, "receptions", "receiving_receptions"),
            "receiving_yards": _sum_stat(weekly_rows, "receiving_yards", "rec_yards"),
            "receiving_tds": _sum_stat(weekly_rows, "receiving_tds", "receiving_touchdowns", "rec_tds"),
            "rushing_yards": _sum_stat(weekly_rows, "rushing_yards", "rush_yards"),
            "rushing_tds": _sum_stat(weekly_rows, "rushing_tds", "rushing_touchdowns", "rush_tds"),
        }
        facts["weekly_totals"] = weekly_totals

    threshold_match = re.search(r"\b(\d+(?:\.\d+)?)\s*\+?\s*(?:ppr\s*)?points?\b", question, re.I)
    if threshold_match and players and not weekly_rows.empty:
        threshold = float(threshold_match.group(1))
        fp_col = _column(weekly_rows, "fantasy_points_ppr")
        name_col = _column(weekly_rows, "player_display_name", "player_name", "name", "player")
        if fp_col and name_col:
            temp = weekly_rows.copy()
            temp["_ppr"] = pd.to_numeric(temp[fp_col], errors="coerce")
            counts: dict[str, int] = {}
            for player in players:
                mask = temp[name_col].astype(str).map(normalize_name).eq(normalize_name(player))
                counts[player] = int(temp.loc[mask, "_ppr"].ge(threshold).sum())
            facts["weekly_threshold"] = {
                "threshold_ppr_points": threshold,
                "counts": counts,
            }

    # Keep the metric label so the model knows what the user asked the calculator to retrieve.
    facts["requested_metric"] = metric
    return facts


def retrieve_shiva_context(
    question: str,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    rankings: pd.DataFrame,
    weekly: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Retrieve relevant verified facts. This function is intentionally verdict-free."""
    original_question = question.strip()
    players, ambiguous = resolve_players(original_question, history, rankings)
    seasons = _season_list(original_question)
    intent = classify_question(original_question, players)

    history_rows = _filter_history(history, players, seasons)
    ranking_rows = _filter_rankings(rankings, players)
    weekly_rows = _filter_weekly(weekly, players, seasons)

    context: dict[str, Any] = {
        "original_question": original_question,
        "intent": intent,
        "league_defaults": dict(DEFAULT_LEAGUE),
        "resolved_players": players,
        "ambiguous_player_aliases": ambiguous,
        "requested_seasons": seasons,
        "needs_clarification": False,
        "missing_information": [],
        "facts": _exact_player_facts(original_question, players, seasons, history_rows, weekly_rows),
        "current_rankings_for_named_players": _frame_records(ranking_rows, 20),
        "historical_player_rows": _frame_records(
            history_rows.sort_values([c for c in ["season", "player_name"] if c in history_rows.columns], ascending=False)
            if not history_rows.empty else history_rows,
            60,
        ),
        "weekly_player_rows": _frame_records(weekly_rows, 80),
    }

    # If the question asks for a player-to-player decision but no players can be resolved,
    # tell the model exactly what is missing. The model still produces the user-facing clarification.
    if intent in {"DRAFT_DECISION", "PLAYER_COMPARISON"} and not players:
        context["needs_clarification"] = True
        context["missing_information"].append("No specific player names were resolved from the question.")

    if ambiguous:
        context["needs_clarification"] = True
        context["missing_information"].append(
            "One or more player aliases are ambiguous: " + ", ".join(ambiguous)
        )

    # Draft/hypothetical questions benefit from a small market snapshot, but the code
    # does not rank a winner or produce a recommendation.
    if intent in {"DRAFT_DECISION", "HYPOTHETICAL", "GENERAL_FANTASY"}:
        market = _filter_rankings(rankings, [])
        context["current_adp_market_sample"] = _frame_records(market, 50)

    # Aggregate/historical engine is permitted only as a calculator for non-decision questions.
    # Its answer is supplied as factual context; it is never used to choose a player.
    if not players and intent in {"HISTORICAL_ANALYSIS", "TREND_ANALYSIS", "ADP_QUERY"}:
        try:
            aggregate = run_aggregate_query(original_question, history, roi, rankings)
            context["aggregate_calculation"] = {
                "title": aggregate.get("title", ""),
                "answer": aggregate.get("answer", ""),
                "note": aggregate.get("note", ""),
                "supporting_rows": _frame_records(aggregate.get("table"), 60),
            }
        except Exception as exc:
            context["aggregate_calculation_error"] = str(exc)

    return context


def run_shiva_query(
    question: str,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    rankings: pd.DataFrame,
    weekly: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Compatibility factual reporter. It never makes draft recommendations."""
    context = retrieve_shiva_context(question, history, roi, rankings, weekly)
    facts = context.get("facts", {})
    intent = context.get("intent", "GENERAL_FANTASY")
    players = context.get("resolved_players", [])
    seasons = context.get("requested_seasons", [])

    if context.get("needs_clarification"):
        return _report(
            "🧠 ASK SHIVA GPT",
            "I NEED A LITTLE MORE CONTEXT",
            " ".join(context.get("missing_information", [])),
            kind="clarify",
            structured_query=context,
        )

    ps = facts.get("player_season") or {}
    metric = facts.get("requested_metric")
    if ps:
        if metric == "ppg" and ps.get("points_per_game") is not None:
            answer = f"{ps['points_per_game']:.2f} PPG"
            note = f"{ps['player_name']} · {ps['season']} · ESPN Full PPR · {ps.get('fantasy_points_ppr', '—')} points · {ps.get('games_played', '—')} games."
        elif metric == "finish" and ps.get("finish") is not None:
            answer = f"{ps.get('position', '')}{ps['finish']}"
            note = f"{ps['player_name']} · {ps['season']}."
        elif metric == "points" and ps.get("fantasy_points_ppr") is not None:
            answer = f"{ps['fantasy_points_ppr']:.1f} PPR POINTS"
            note = f"{ps['player_name']} · {ps['season']}."
        else:
            answer = f"{ps['player_name']} · {ps['season']}"
            note = "Exact verified player-season record retrieved."
        return _report("📊 SHIVA PLAYER LOOKUP", answer, note, kind="fact", structured_query=context)

    totals = facts.get("weekly_totals") or {}
    if totals and len(players) == 1:
        metric_map = {
            "targets": ("targets", "TARGETS"),
            "receptions": ("receptions", "RECEPTIONS"),
            "receiving_yards": ("receiving_yards", "RECEIVING YARDS"),
            "receiving_tds": ("receiving_tds", "RECEIVING TD"),
            "rushing_yards": ("rushing_yards", "RUSHING YARDS"),
            "rushing_tds": ("rushing_tds", "RUSHING TD"),
        }
        if metric == "receiving_stats":
            answer = " · ".join(
                x for x in [
                    f"{int(totals['receptions'])} receptions" if totals.get("receptions") is not None else None,
                    f"{int(totals['receiving_yards'])} receiving yards" if totals.get("receiving_yards") is not None else None,
                    f"{int(totals['receiving_tds'])} receiving TD" if totals.get("receiving_tds") is not None else None,
                ] if x
            )
            return _report("📊 SHIVA PLAYER LOOKUP", answer or "NO VERIFIED RECEIVING TOTALS", f"{players[0]} · {seasons[0] if seasons else 'requested span'}.", kind="fact", structured_query=context)
        if metric in metric_map:
            key, label = metric_map[metric]
            value = totals.get(key)
            answer = f"{int(value)} {label}" if value is not None else f"NO VERIFIED {label}"
            return _report("📊 SHIVA PLAYER LOOKUP", answer, f"{players[0]} · {seasons[0] if seasons else 'requested span'}.", kind="fact", structured_query=context)

    threshold = facts.get("weekly_threshold")
    if threshold:
        details = "; ".join(f"{name}: {count}" for name, count in threshold["counts"].items())
        return _report(
            "📊 SHIVA WEEKLY SCORING",
            details,
            f"Games at or above {threshold['threshold_ppr_points']:.0f} ESPN Full-PPR points.",
            kind="fact",
            structured_query=context,
        )

    if "aggregate_calculation" in context:
        agg = context["aggregate_calculation"]
        return _report(
            agg.get("title") or "📊 SHIVA DATA REPORT",
            agg.get("answer") or "CALCULATION COMPLETE",
            agg.get("note") or "",
            kind="fact",
            structured_query=context,
        )

    # This is deliberate: decision/opinion questions are not answered in code.
    if intent in {"DRAFT_DECISION", "PLAYER_COMPARISON", "HYPOTHETICAL", "GENERAL_FANTASY"}:
        names = ", ".join(players) if players else "the requested scenario"
        return _report(
            "🧠 ASK SHIVA GPT",
            "SHIVA GPT ANALYSIS REQUIRED",
            f"Verified context was retrieved for {names}. The application code intentionally does not choose a winner; the OpenAI analyst must make the recommendation.",
            kind="analysis_required",
            structured_query=context,
        )

    return _report(
        "📊 SHIVA DATA REPORT",
        "NO VERIFIED CALCULATION WAS AVAILABLE",
        "Shiva GPT can still analyze the question, but it must not invent missing statistics.",
        kind="empty",
        structured_query=context,
    )
