from __future__ import annotations

import json
import math
import re
import sqlite3
import time
import uuid
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_ROSTER = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1,
    "FLEX": 1,
    "D/ST": 1,
    "K": 1,
    "BENCH": 7,
}

STARTER_POSITIONS = {"QB", "RB", "WR", "TE", "D/ST", "K"}
FLEX_POSITIONS = {"RB", "WR", "TE"}


def normalize_name(value: str) -> str:
    value = str(value or "").lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_position(value: str) -> str:
    pos = str(value or "").upper().strip()
    aliases = {"DST": "D/ST", "DEF": "D/ST", "D": "D/ST", "PK": "K"}
    return aliases.get(pos, pos)


def build_player_pool(rankings: pd.DataFrame, weekly: pd.DataFrame | None = None) -> list[dict[str, Any]]:
    """Build the live draft pool exclusively from the app's verified 2026 rankings.

    No player rows are invented. Canonical IDs use the historical weekly player_id when
    available; otherwise a deterministic rankings-scoped ID keeps the same player stable
    across draft state, profiles and Shiva context.
    """
    if rankings is None or rankings.empty:
        return []

    id_map: dict[str, str] = {}
    if weekly is not None and not weekly.empty and "player_id" in weekly.columns:
        name_col = next((c for c in ["player_display_name", "player_name"] if c in weekly.columns), None)
        if name_col:
            matched = weekly[[name_col, "player_id"]].dropna().drop_duplicates(name_col, keep="last")
            id_map = {normalize_name(r[name_col]): str(r["player_id"]) for _, r in matched.iterrows()}

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for _, row in rankings.iterrows():
        name = str(row.get("player_name") or "").strip()
        pos = normalize_position(row.get("position"))
        adp = pd.to_numeric(pd.Series([row.get("adp")]), errors="coerce").iloc[0]
        if not name or pos not in STARTER_POSITIONS or pd.isna(adp):
            continue
        key = normalize_name(name)
        if key in seen:
            continue
        seen.add(key)
        player_id = id_map.get(key) or f"rankings::{key.replace(' ', '-')}"
        overall_rank = pd.to_numeric(pd.Series([row.get("overall_rank")]), errors="coerce").iloc[0]
        position_rank = pd.to_numeric(pd.Series([row.get("position_rank")]), errors="coerce").iloc[0]
        bye = pd.to_numeric(pd.Series([row.get("bye")]), errors="coerce").iloc[0]
        projection = pd.to_numeric(pd.Series([row.get("projected_points")]), errors="coerce").iloc[0] if "projected_points" in rankings.columns else np.nan
        rows.append({
            "id": player_id,
            "name": name,
            "position": pos,
            "team": str(row.get("team") or "").strip(),
            "bye": None if pd.isna(bye) else int(bye),
            "adp": float(adp),
            "rank": int(overall_rank) if pd.notna(overall_rank) else int(round(float(adp))),
            "position_rank": int(position_rank) if pd.notna(position_rank) else None,
            "projected_points": None if pd.isna(projection) else float(projection),
            "isAvailable": True,
        })
    return sorted(rows, key=lambda p: (p["rank"], p["adp"], p["name"]))


def snake_team_for_pick(overall_pick: int, teams_count: int) -> int:
    round_number = (overall_pick - 1) // teams_count + 1
    pick_in_round = (overall_pick - 1) % teams_count
    return teams_count - pick_in_round if round_number % 2 == 0 else pick_in_round + 1


def round_for_pick(overall_pick: int, teams_count: int) -> int:
    return (overall_pick - 1) // teams_count + 1


def slot_pick_number(round_number: int, slot: int, teams_count: int) -> int:
    return (round_number - 1) * teams_count + (slot if round_number % 2 else teams_count - slot + 1)


def default_team(team_number: int, user_team_id: str) -> dict[str, Any]:
    team_id = f"t{team_number}"
    return {
        "id": team_id,
        "name": "My Team" if team_id == user_team_id else f"Team {team_number}",
        "draftSlot": team_number,
        "isUser": team_id == user_team_id,
        "roster": [],
    }


def initialize_draft(
    players: list[dict[str, Any]],
    teams_count: int = 10,
    draft_position: int = 1,
    scoring: str = "PPR",
    roster_settings: dict[str, int] | None = None,
    rounds: int | None = None,
    seconds_per_pick: int = 60,
) -> dict[str, Any]:
    if teams_count not in {8, 10, 12}:
        raise ValueError("teams_count must be 8, 10 or 12")
    if not 1 <= draft_position <= teams_count:
        raise ValueError("draft_position outside league size")
    roster = dict(roster_settings or DEFAULT_ROSTER)
    default_rounds = sum(int(v) for v in roster.values())
    rounds = int(rounds or default_rounds)
    user_team_id = f"t{draft_position}"
    clean_players = deepcopy(players)
    ids = [p["id"] for p in clean_players]
    if len(ids) != len(set(ids)):
        raise ValueError("player IDs must be unique")
    now = time.time()
    return {
        "draftId": str(uuid.uuid4()),
        "status": "ready",
        "settings": {
            "season": 2026,
            "teamsCount": teams_count,
            "scoring": scoring,
            "draftFormat": "snake",
            "rounds": rounds,
            "secondsPerPick": int(seconds_per_pick),
            "roster": roster,
        },
        "teams": [default_team(i, user_team_id) for i in range(1, teams_count + 1)],
        "picks": [],
        "availablePlayers": clean_players,
        "currentOverallPick": 1,
        "currentRound": 1,
        "currentTeam": "t1",
        "userTeamId": user_team_id,
        "queue": [],
        "timer": {"remaining": int(seconds_per_pick), "startedAt": now},
        "paused": False,
        "createdAt": now,
        "completedAt": None,
    }


def start_draft(state: dict[str, Any]) -> dict[str, Any]:
    state["status"] = "active"
    reset_timer(state)
    return state


def pause_draft(state: dict[str, Any]) -> dict[str, Any]:
    if state["status"] == "active":
        state["timer"]["remaining"] = timer_remaining(state)
        state["paused"] = True
    return state


def resume_draft(state: dict[str, Any]) -> dict[str, Any]:
    if state["status"] == "active":
        state["paused"] = False
        state["timer"]["startedAt"] = time.time()
    return state


def reset_timer(state: dict[str, Any]) -> None:
    state["timer"] = {
        "remaining": int(state["settings"]["secondsPerPick"]),
        "startedAt": time.time(),
    }


def timer_remaining(state: dict[str, Any], now: float | None = None) -> int:
    if state.get("paused"):
        return int(state["timer"].get("remaining", 0))
    if state.get("status") != "active":
        return 0
    now = now or time.time()
    base = int(state["timer"].get("remaining", state["settings"]["secondsPerPick"]))
    elapsed = max(0, int(now - float(state["timer"].get("startedAt", now))))
    return max(0, base - elapsed)


def team_by_id(state: dict[str, Any], team_id: str) -> dict[str, Any]:
    return next(t for t in state["teams"] if t["id"] == team_id)


def get_player(state: dict[str, Any], player_id: str) -> dict[str, Any] | None:
    return next((p for p in state["availablePlayers"] if p["id"] == player_id), None)


def roster_needs(state: dict[str, Any], team_id: str) -> dict[str, int]:
    required = dict(state["settings"]["roster"])
    roster = team_by_id(state, team_id)["roster"]
    counts: dict[str, int] = {}
    for player in roster:
        pos = normalize_position(player["position"])
        counts[pos] = counts.get(pos, 0) + 1

    needs = {k: max(0, int(v)) for k, v in required.items() if k != "BENCH"}
    for pos in ["QB", "RB", "WR", "TE", "D/ST", "K"]:
        use = min(needs.get(pos, 0), counts.get(pos, 0))
        needs[pos] = max(0, needs.get(pos, 0) - use)
        counts[pos] = max(0, counts.get(pos, 0) - use)

    flex_need = needs.get("FLEX", 0)
    flex_available = sum(counts.get(p, 0) for p in FLEX_POSITIONS)
    needs["FLEX"] = max(0, flex_need - flex_available)
    starters = sum(int(v) for k, v in required.items() if k != "BENCH")
    needs["BENCH"] = max(0, sum(required.values()) - max(starters, len(roster)))
    return needs


def roster_slots(state: dict[str, Any], team_id: str) -> list[tuple[str, dict[str, Any] | None]]:
    """Assign roster players into starting slots then bench; FLEX accepts RB/WR/TE."""
    roster = deepcopy(team_by_id(state, team_id)["roster"])
    slots: list[tuple[str, dict[str, Any] | None]] = []
    used: set[str] = set()
    requirements = state["settings"]["roster"]
    for pos in ["QB", "RB", "WR", "TE", "D/ST", "K"]:
        for _ in range(int(requirements.get(pos, 0))):
            player = next((p for p in roster if p["id"] not in used and normalize_position(p["position"]) == pos), None)
            slots.append((pos, player))
            if player:
                used.add(player["id"])
    for _ in range(int(requirements.get("FLEX", 0))):
        player = next((p for p in roster if p["id"] not in used and normalize_position(p["position"]) in FLEX_POSITIONS), None)
        slots.append(("FLEX", player))
        if player:
            used.add(player["id"])
    bench = [p for p in roster if p["id"] not in used]
    for i in range(int(requirements.get("BENCH", 0))):
        slots.append((f"BN{i + 1}", bench[i] if i < len(bench) else None))
    return slots


def _positional_baseline(players: list[dict[str, Any]], position: str) -> float:
    pos = sorted((p for p in players if p["position"] == position), key=lambda p: p["adp"])
    if not pos:
        return 999.0
    idx = min(len(pos) - 1, 8 if position in {"RB", "WR"} else 4)
    return float(pos[idx]["adp"])


def player_value_score(state: dict[str, Any], player: dict[str, Any], team_id: str) -> float:
    """Competent draft-value score: ADP/rank + roster need + positional scarcity.

    Projection is intentionally only a small within-position tiebreaker; raw cross-position
    projected points never drive CPU decisions.
    """
    overall = int(state["currentOverallPick"])
    rnd = int(state["currentRound"])
    pos = player["position"]
    adp = float(player["adp"])
    rank = float(player.get("rank") or adp)
    needs = roster_needs(state, team_id)
    roster = team_by_id(state, team_id)["roster"]
    pos_count = sum(1 for p in roster if p["position"] == pos)

    market = 120.0 - abs(adp - overall) * 2.4 - max(0.0, rank - overall) * 0.6
    value_vs_adp = max(-20.0, min(24.0, overall - adp)) * 1.6
    baseline = _positional_baseline(state["availablePlayers"], pos)
    scarcity = max(-10.0, min(20.0, baseline - adp)) * 0.9

    need = 0.0
    if needs.get(pos, 0) > 0:
        need += 20.0
    if pos in FLEX_POSITIONS and needs.get("FLEX", 0) > 0:
        need += 8.0

    # Realistic positional timing. Elite QB/TE can win tiebreakers, but early rounds
    # are not a raw-points contest and normally prioritize scarce RB/WR capital.
    timing = 0.0
    if rnd <= 2:
        if pos in {"RB", "WR"}: timing += 14.0
        if pos == "QB": timing -= 22.0
        if pos == "TE": timing -= 10.0
        if pos in {"D/ST", "K"}: timing -= 80.0
    elif rnd <= 5:
        if pos in {"RB", "WR"}: timing += 8.0
        if pos == "QB" and pos_count == 0: timing += 2.0
        if pos in {"D/ST", "K"}: timing -= 60.0
    elif rnd <= 9:
        if pos == "QB" and pos_count == 0: timing += 12.0
        if pos == "TE" and pos_count == 0: timing += 8.0
        if pos in {"D/ST", "K"}: timing -= 30.0
    else:
        if pos in {"D/ST", "K"} and needs.get(pos, 0) > 0: timing += 10.0

    duplication = 0.0
    if pos == "QB" and pos_count >= 1 and rnd < 10: duplication -= 25.0
    if pos == "TE" and pos_count >= 1 and rnd < 9: duplication -= 15.0
    if pos in {"D/ST", "K"} and pos_count >= 1: duplication -= 100.0

    projection_tiebreak = 0.0
    if player.get("projected_points") is not None:
        same_pos = [p for p in state["availablePlayers"] if p["position"] == pos and p.get("projected_points") is not None]
        if same_pos:
            vals = [float(p["projected_points"]) for p in same_pos]
            lo, hi = min(vals), max(vals)
            if hi > lo:
                projection_tiebreak = (float(player["projected_points"]) - lo) / (hi - lo) * 4.0

    return market + value_vs_adp + scarcity + need + timing + duplication + projection_tiebreak


def recommendation_groups(state: dict[str, Any], team_id: str | None = None) -> dict[str, list[dict[str, Any]]]:
    team_id = team_id or state["userTeamId"]
    available = state["availablePlayers"]
    scored = [(player_value_score(state, p, team_id), p) for p in available]
    scored.sort(key=lambda x: (-x[0], x[1]["adp"]))
    best = [p for _, p in scored[:8]]
    best_rb = [p for _, p in scored if p["position"] == "RB"][:5]
    best_wr = [p for _, p in scored if p["position"] == "WR"][:5]
    value = sorted(available, key=lambda p: (p["adp"] - state["currentOverallPick"], p["adp"]))[:8]
    needs = roster_needs(state, team_id)
    fit = [p for _, p in scored if needs.get(p["position"], 0) > 0 or (p["position"] in FLEX_POSITIONS and needs.get("FLEX", 0) > 0)][:8]
    return {"BEST AVAILABLE": best, "BEST RB": best_rb, "BEST WR": best_wr, "BEST VALUE": value, "ROSTER FIT": fit or best}


def cpu_select_player(state: dict[str, Any], team_id: str | None = None) -> dict[str, Any] | None:
    if not state["availablePlayers"]:
        return None
    team_id = team_id or state["currentTeam"]
    scored = sorted(
        ((player_value_score(state, p, team_id), p) for p in state["availablePlayers"]),
        key=lambda x: (-x[0], x[1]["adp"], x[1]["rank"]),
    )
    return scored[0][1] if scored else None


def make_pick(state: dict[str, Any], player_id: str, source: str = "user") -> dict[str, Any]:
    if state["status"] not in {"active", "ready"}:
        raise ValueError("draft is not active")
    player = get_player(state, player_id)
    if player is None:
        raise ValueError("player is unavailable or already drafted")
    teams_count = int(state["settings"]["teamsCount"])
    overall = int(state["currentOverallPick"])
    team_num = snake_team_for_pick(overall, teams_count)
    team_id = f"t{team_num}"
    if team_id != state["currentTeam"]:
        state["currentTeam"] = team_id

    picked = deepcopy(player)
    pick = {
        "pickNumber": overall,
        "round": round_for_pick(overall, teams_count),
        "teamId": team_id,
        "playerId": picked["id"],
        "playerName": picked["name"],
        "position": picked["position"],
        "nflTeam": picked["team"],
        "source": source,
        "timestamp": time.time(),
    }
    state["picks"].append(pick)
    team_by_id(state, team_id)["roster"].append(picked)
    state["availablePlayers"] = [p for p in state["availablePlayers"] if p["id"] != player_id]
    state["queue"] = [pid for pid in state["queue"] if pid != player_id]

    total_picks = teams_count * int(state["settings"]["rounds"])
    if overall >= total_picks:
        state["status"] = "complete"
        state["completedAt"] = time.time()
        state["currentOverallPick"] = total_picks
        state["currentRound"] = int(state["settings"]["rounds"])
        state["timer"]["remaining"] = 0
        return state

    state["currentOverallPick"] = overall + 1
    state["currentRound"] = round_for_pick(overall + 1, teams_count)
    state["currentTeam"] = f"t{snake_team_for_pick(overall + 1, teams_count)}"
    reset_timer(state)
    return state


def undo_last_pick(state: dict[str, Any]) -> dict[str, Any]:
    if not state["picks"]:
        return state
    pick = state["picks"].pop()
    team = team_by_id(state, pick["teamId"])
    restored = next((p for p in team["roster"] if p["id"] == pick["playerId"]), None)
    team["roster"] = [p for p in team["roster"] if p["id"] != pick["playerId"]]
    if restored and all(p["id"] != restored["id"] for p in state["availablePlayers"]):
        restored["isAvailable"] = True
        state["availablePlayers"].append(restored)
        state["availablePlayers"].sort(key=lambda p: (p["rank"], p["adp"], p["name"]))
    state["status"] = "active"
    state["completedAt"] = None
    state["currentOverallPick"] = int(pick["pickNumber"])
    state["currentRound"] = int(pick["round"])
    state["currentTeam"] = str(pick["teamId"])
    reset_timer(state)
    return state


def restart_draft(state: dict[str, Any], original_players: list[dict[str, Any]]) -> dict[str, Any]:
    settings = state["settings"]
    slot = int(state["userTeamId"].lstrip("t"))
    return initialize_draft(
        original_players,
        teams_count=int(settings["teamsCount"]),
        draft_position=slot,
        scoring=str(settings["scoring"]),
        roster_settings=dict(settings["roster"]),
        rounds=int(settings["rounds"]),
        seconds_per_pick=int(settings["secondsPerPick"]),
    )


def queue_add(state: dict[str, Any], player_id: str) -> None:
    if get_player(state, player_id) and player_id not in state["queue"]:
        state["queue"].append(player_id)


def queue_remove(state: dict[str, Any], player_id: str) -> None:
    state["queue"] = [pid for pid in state["queue"] if pid != player_id]


def queue_move(state: dict[str, Any], player_id: str, delta: int) -> None:
    if player_id not in state["queue"]:
        return
    i = state["queue"].index(player_id)
    j = max(0, min(len(state["queue"]) - 1, i + delta))
    if i != j:
        state["queue"][i], state["queue"][j] = state["queue"][j], state["queue"][i]


def auto_pick_user(state: dict[str, Any]) -> dict[str, Any]:
    if state["currentTeam"] != state["userTeamId"]:
        return state
    queued = next((get_player(state, pid) for pid in state["queue"] if get_player(state, pid)), None)
    selected = queued or cpu_select_player(state, state["userTeamId"])
    if selected:
        make_pick(state, selected["id"], source="autopick")
    return state


def advance_cpu_until_user(state: dict[str, Any], max_picks: int = 50) -> dict[str, Any]:
    count = 0
    while state["status"] == "active" and not state["paused"] and state["currentTeam"] != state["userTeamId"] and count < max_picks:
        selected = cpu_select_player(state, state["currentTeam"])
        if selected is None:
            break
        make_pick(state, selected["id"], source="cpu")
        count += 1
    return state


def full_draft_context(state: dict[str, Any], recommendation_limit: int = 20) -> dict[str, Any]:
    recs = recommendation_groups(state, state["userTeamId"])
    return {
        "season": 2026,
        "scoring": state["settings"]["scoring"],
        "teamsCount": state["settings"]["teamsCount"],
        "currentRound": state["currentRound"],
        "currentOverallPick": state["currentOverallPick"],
        "currentTeam": state["currentTeam"],
        "userTeamId": state["userTeamId"],
        "myDraftPosition": int(state["userTeamId"].lstrip("t")),
        "myRoster": team_by_id(state, state["userTeamId"])["roster"],
        "opponentRosters": {t["id"]: t["roster"] for t in state["teams"] if not t["isUser"]},
        "draftedPlayers": state["picks"],
        "availablePlayers": state["availablePlayers"][:80],
        "queue": [p for pid in state["queue"] if (p := get_player(state, pid))],
        "rosterRequirements": state["settings"]["roster"],
        "rosterNeeds": roster_needs(state, state["userTeamId"]),
        "recentSelections": state["picks"][-10:],
        "recommendations": {k: v[:recommendation_limit] for k, v in recs.items()},
    }


def ensure_mock_draft_table(db_path: str | Path) -> None:
    with sqlite3.connect(db_path) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS mock_drafts (
                draft_id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                completed_at REAL,
                season INTEGER NOT NULL,
                scoring TEXT NOT NULL,
                teams_count INTEGER NOT NULL,
                draft_position INTEGER NOT NULL,
                settings_json TEXT NOT NULL,
                picks_json TEXT NOT NULL,
                roster_json TEXT NOT NULL,
                state_json TEXT NOT NULL
            )
        """)
        con.commit()


def save_completed_draft(state: dict[str, Any], db_path: str | Path) -> str:
    if state.get("status") != "complete":
        raise ValueError("only completed drafts can be saved")
    ensure_mock_draft_table(db_path)
    user_roster = team_by_id(state, state["userTeamId"])["roster"]
    with sqlite3.connect(db_path) as con:
        con.execute(
            """INSERT OR REPLACE INTO mock_drafts
               (draft_id, created_at, completed_at, season, scoring, teams_count, draft_position,
                settings_json, picks_json, roster_json, state_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                state["draftId"], state["createdAt"], state.get("completedAt"), 2026,
                state["settings"]["scoring"], state["settings"]["teamsCount"],
                int(state["userTeamId"].lstrip("t")), json.dumps(state["settings"]),
                json.dumps(state["picks"]), json.dumps(user_roster), json.dumps(state),
            ),
        )
        con.commit()
    return state["draftId"]


def list_saved_drafts(db_path: str | Path) -> list[dict[str, Any]]:
    ensure_mock_draft_table(db_path)
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT draft_id, created_at, completed_at, season, scoring, teams_count, draft_position FROM mock_drafts ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def load_saved_draft(db_path: str | Path, draft_id: str) -> dict[str, Any] | None:
    ensure_mock_draft_table(db_path)
    with sqlite3.connect(db_path) as con:
        row = con.execute("SELECT state_json FROM mock_drafts WHERE draft_id = ?", (draft_id,)).fetchone()
    return json.loads(row[0]) if row else None
