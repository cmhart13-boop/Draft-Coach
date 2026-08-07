from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from shiva_engine import normalize_name, run_shiva_query as run_aggregate_query

MANUAL_ALIASES = {
    "cmc": "Christian McCaffrey",
}


def _report(title: str, answer: str, note: str, table: pd.DataFrame | None = None, takeaway: str = "", kind: str = "players", structured_query: dict[str, Any] | None = None) -> dict[str, Any]:
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
    q = question.lower()
    q_norm = normalize_name(question)
    names = _all_player_names(history, rankings)
    aliases = _player_aliases(names)
    found: list[str] = []
    ambiguous: list[str] = []

    # Full-name matches take priority.
    for name in names:
        if name.lower() in q:
            found.append(name)

    # Then aliases such as CMC, surname, or first-initial + surname.
    for alias, matches in aliases.items():
        if len(alias) < 3:
            continue
        matched = False
        if " " in alias or "." in alias:
            matched = alias in q
        else:
            matched = bool(re.search(rf"\b{re.escape(alias)}\b", q)) or alias == q_norm
        if not matched:
            continue
        if len(matches) == 1:
            name = next(iter(matches))
            if name not in found:
                found.append(name)
        elif not any(name in found for name in matches):
            ambiguous.append(alias)

    # Preserve order of appearance where possible.
    found = sorted(set(found), key=lambda n: q.find(n.lower()) if n.lower() in q else 10_000)
    return found, ambiguous


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
    if re.search(r"\b(?:adp|draft cost|average draft position)\b", q):
        return "adp"
    return "summary"


def _column(frame: pd.DataFrame, *candidates: str) -> str | None:
    lower = {str(c).lower(): c for c in frame.columns}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return None


def _weekly_player_season(weekly: pd.DataFrame | None, player: str, season: int | None) -> pd.DataFrame:
    if weekly is None or weekly.empty:
        return pd.DataFrame()
    name_col = _column(weekly, "player_display_name", "player_name", "name", "player")
    season_col = _column(weekly, "season", "year")
    if not name_col:
        return pd.DataFrame()
    w = weekly.copy()
    keys = w[name_col].astype(str).map(normalize_name)
    w = w[keys.eq(normalize_name(player))]
    if season is not None and season_col:
        years = pd.to_numeric(w[season_col], errors="coerce")
        w = w[years.eq(season)]
    return w


def _sum_stat(frame: pd.DataFrame, *candidates: str) -> float | None:
    col = _column(frame, *candidates)
    if not col or frame.empty:
        return None
    values = pd.to_numeric(frame[col], errors="coerce")
    if values.notna().sum() == 0:
        return None
    return float(values.sum())


def _direct_player_report(question: str, players: list[str], history: pd.DataFrame, rankings: pd.DataFrame, weekly: pd.DataFrame | None) -> dict[str, Any]:
    seasons = _season_list(question)
    metric = _metric(question)
    asks_average = bool(re.search(r"\b(?:average|avg|mean|over the last|last \d+ seasons?)\b", question.lower()))
    structured = {
        "intent": "player_comparison" if len(players) > 1 else "player_stat",
        "players": players,
        "seasons": seasons,
        "metric": metric,
        "aggregation": "mean" if asks_average else "exact",
        "scoring_format": "ESPN_FULL_PPR",
    }

    pool = history.copy()
    pool["name_key"] = pool["player_name"].astype(str).map(normalize_name)
    player_keys = {normalize_name(p) for p in players}
    pool = pool[pool["name_key"].isin(player_keys)].copy()
    if seasons:
        pool = pool[pd.to_numeric(pool["season"], errors="coerce").isin(seasons)]

    # Guardrail: a specific one-player/one-season query must never broaden to other players/seasons.
    if len(players) == 1 and len(seasons) == 1:
        unique_players = pool["name_key"].nunique()
        unique_seasons = pd.to_numeric(pool["season"], errors="coerce").dropna().nunique()
        if unique_players > 1 or unique_seasons > 1:
            return _report(
                "🚨 SHIVA QUERY VALIDATION",
                "I STOPPED AN INVALID BROAD QUERY",
                "A one-player, one-season request returned more than one player or season. Shiva refused to average unrelated records.",
                kind="error",
                structured_query=structured,
            )

    if pool.empty and metric not in {"receiving_stats", "rushing_stats", "targets", "receptions", "receiving_yards", "receiving_tds", "rushing_yards", "rushing_tds"}:
        return _report(
            "📊 SHIVA PLAYER LOOKUP",
            "NO MATCHING PLAYER-SEASON FOUND",
            f"I resolved the player as {players[0] if len(players)==1 else ', '.join(players)}, but the requested season record is not present in the verified history.",
            kind="empty",
            structured_query=structured,
        )

    if len(players) > 1:
        table = pool.sort_values(["season", "player_name"], ascending=[False, True])
        q_lower = question.lower()
        is_draft_decision = bool(re.search(r"\b(?:draft|take|pick|select|round)\b", q_lower))

        # Draft decisions are NOT historical-PPG contests. Use current ESPN ADP
        # for the exact named players first, then let the analyst explain positional value.
        if is_draft_decision:
            current = rankings.copy()
            current["name_key"] = current["player_name"].astype(str).map(normalize_name)
            current = current[current["name_key"].isin(player_keys)].copy()
            current["adp"] = pd.to_numeric(current.get("adp"), errors="coerce")
            current = current.dropna(subset=["adp"]).sort_values("adp")

            structured["intent"] = "draft_decision"
            structured["current_adp_players"] = current["player_name"].astype(str).tolist()

            if current["name_key"].nunique() == len(player_keys):
                pick_row = current.iloc[0]
                pick = str(pick_row["player_name"])
                pick_adp = float(pick_row["adp"])
                other_rows = current[current["player_name"].ne(pick)]
                comparisons = []
                for _, r in current.iterrows():
                    comparisons.append(f"{r['player_name']} ({r.get('position', '—')}) — ESPN ADP {float(r['adp']):.1f}")
                why = (
                    f"Current ESPN ADP has {pick} at {pick_adp:.1f}, ahead of the other option(s): "
                    + "; ".join(comparisons)
                    + ". For an early-round draft decision, Shiva should follow current draft cost and positional opportunity cost rather than simply choosing whichever position historically scores more raw PPG."
                )
                combined = pd.concat([current, table], ignore_index=True, sort=False) if not table.empty else current
                return _report(
                    "⚖️ SHIVA DRAFT DECISION",
                    f"I'D TAKE {pick.upper()}",
                    why,
                    combined,
                    why,
                    "draft_decision",
                    structured,
                )

            missing = [p for p in players if normalize_name(p) not in set(current["name_key"].astype(str))]
            why = "I can compare these players historically, but I do not have verified current ESPN ADP for " + ", ".join(missing) + ". I will not fake a current draft recommendation without it."
            return _report("⚖️ SHIVA DRAFT DECISION", "CURRENT ADP DATA IS INCOMPLETE", why, table, why, "draft_decision", structured)

        if table.empty:
            return _report("⚖️ SHIVA COMPARISON", "NO MATCHING COMPARISON ROWS", "The requested players could not be matched to the selected season(s).", structured_query=structured)

        latest = table if not seasons else table[pd.to_numeric(table["season"], errors="coerce").isin(seasons)]
        scored = latest.dropna(subset=["ppg"]).copy()
        if not scored.empty:
            by_player = scored.groupby("player_name", as_index=False)["ppg"].mean().sort_values("ppg", ascending=False)
            pick = str(by_player.iloc[0]["player_name"])
            answer = f"{pick.upper()} HAD THE HIGHER VERIFIED PPG"
            detail = "; ".join(f"{r['player_name']} {float(r['ppg']):.1f} PPG" for _, r in by_player.iterrows())
            note = f"Across the exact matching player-season rows: {detail}."
        else:
            answer = "HERE'S THE HEAD-TO-HEAD DATA"
            note = "The comparison is limited to the verified fields available for those players."
        return _report("⚖️ SHIVA PLAYER COMPARISON", answer, note, table, note, "comparison", structured)

    player = players[0]
    season = seasons[0] if seasons else None

    # Weekly-detail stats are aggregated only for the exact resolved player/season.
    if metric in {"receiving_stats", "rushing_stats", "targets", "receptions", "receiving_yards", "receiving_tds", "rushing_yards", "rushing_tds"}:
        w = _weekly_player_season(weekly, player, season)
        if w.empty:
            return _report("📊 SHIVA PLAYER LOOKUP", "DETAILED WEEKLY STATS ARE NOT AVAILABLE FOR THAT MATCH", f"I found the player identity, but the weekly dataset did not contain a matching {season or ''} row set for {player}.", pool, structured_query=structured)
        stats = {
            "targets": _sum_stat(w, "targets", "receiving_targets"),
            "receptions": _sum_stat(w, "receptions", "receiving_receptions"),
            "receiving_yards": _sum_stat(w, "receiving_yards", "rec_yards"),
            "receiving_tds": _sum_stat(w, "receiving_tds", "receiving_touchdowns", "rec_tds"),
            "rushing_yards": _sum_stat(w, "rushing_yards", "rush_yards"),
            "rushing_tds": _sum_stat(w, "rushing_tds", "rushing_touchdowns", "rush_tds"),
        }
        if metric == "receiving_stats":
            parts = [
                f"{int(stats['receptions'])} receptions" if stats['receptions'] is not None else None,
                f"{int(stats['receiving_yards'])} receiving yards" if stats['receiving_yards'] is not None else None,
                f"{int(stats['receiving_tds'])} receiving TD" if stats['receiving_tds'] is not None else None,
            ]
            answer = " · ".join(x for x in parts if x) or "NO VERIFIED RECEIVING TOTALS"
        elif metric == "rushing_stats":
            parts = [
                f"{int(stats['rushing_yards'])} rushing yards" if stats['rushing_yards'] is not None else None,
                f"{int(stats['rushing_tds'])} rushing TD" if stats['rushing_tds'] is not None else None,
            ]
            answer = " · ".join(x for x in parts if x) or "NO VERIFIED RUSHING TOTALS"
        else:
            value = stats.get(metric)
            answer = f"{int(value)} {metric.replace('_', ' ').upper()}" if value is not None else f"NO VERIFIED {metric.replace('_', ' ').upper()}"
        return _report("📊 SHIVA PLAYER LOOKUP", answer, f"{player}{f' · {season}' if season else ''}. Totals come from only that player's matching weekly rows.", pool, "Exact player routing was applied before any aggregation.", "player", structured)

    valid = pool.copy()
    if len(valid) == 1 and not asks_average:
        row = valid.iloc[0]
        finish = row.get("position_finish_total")
        pos = str(row.get("position", ""))
        if metric == "finish" and pd.notna(finish):
            answer = f"{pos}{int(finish)}"
            note = f"{player} finished as {pos}{int(finish)} in {int(row['season'])}."
        elif metric == "ppg" and pd.notna(row.get("ppg")):
            answer = f"{float(row['ppg']):.2f} PPG"
            note = f"{player} · {int(row['season'])} · ESPN Full PPR · {int(row['games_played']) if pd.notna(row.get('games_played')) else '—'} games."
        elif metric == "points" and pd.notna(row.get("fantasy_points_ppr")):
            answer = f"{float(row['fantasy_points_ppr']):.1f} PPR POINTS"
            note = f"{player} · {int(row['season'])}."
        elif metric == "games" and pd.notna(row.get("games_played")):
            answer = f"{int(row['games_played'])} GAMES"
            note = f"{player} · {int(row['season'])}."
        elif metric == "adp" and pd.notna(row.get("overall_pick")):
            answer = f"PICK {float(row['overall_pick']):.1f}"
            note = f"Historical draft cost for {player} in {int(row['season'])}."
        else:
            answer = f"{player.upper()} · {int(row['season'])}"
            note = "Exact player-season record retrieved."
        return _report("📊 SHIVA PLAYER LOOKUP", answer, note, valid, "This result is from one canonical player-season record, not a league-wide average.", "player", structured)

    if metric == "ppg" and not valid.dropna(subset=["ppg"]).empty:
        answer = f"{valid['ppg'].mean():.2f} PPG"
    elif metric == "points" and not valid.dropna(subset=["fantasy_points_ppr"]).empty:
        answer = f"{valid['fantasy_points_ppr'].mean():.1f} PPR POINTS"
    elif metric == "games" and not valid.dropna(subset=["games_played"]).empty:
        answer = f"{valid['games_played'].mean():.1f} GAMES"
    else:
        answer = f"{len(valid)} MATCHING {player.upper()} SEASONS"
    return _report("📊 SHIVA PLAYER REPORT", answer, f"Only {player}'s matching player-season rows were used.", valid, "Ask for a specific season to get a single-season result, or ask for an average to intentionally combine seasons.", "player", structured)


def run_shiva_query(question: str, history: pd.DataFrame, roi: pd.DataFrame, rankings: pd.DataFrame, weekly: pd.DataFrame | None = None) -> dict[str, Any]:
    """Entity-first query router. Specific players are resolved before any aggregate intent."""
    q = re.sub(r"\s+", " ", question.strip())
    players, ambiguous = resolve_players(q, history, rankings)
    if ambiguous and not players:
        return _report(
            "📊 SHIVA PLAYER LOOKUP",
            "WHICH PLAYER DID YOU MEAN?",
            "That name could match more than one player in the database. Use the full player name so Shiva does not merge different players.",
            kind="clarify",
        )
    if players:
        return _direct_player_report(q, players, history, rankings, weekly)
    return run_aggregate_query(q, history, roi, rankings)
