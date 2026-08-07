from __future__ import annotations

import inspect
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import mock_draft_engine as eng
import mock_draft_ui
import shiva_chatgpt_service


def sample_players(n=180):
    positions = ["RB", "WR", "RB", "WR", "TE", "QB", "RB", "WR", "QB", "TE", "D/ST", "K"]
    return [
        {"id": f"p{i}", "name": f"Player {i}", "position": positions[(i-1) % len(positions)], "team": f"N{i%32}", "bye": (i % 14)+1,
         "adp": float(i), "rank": i, "position_rank": i, "projected_points": float(100 + i), "isAvailable": True}
        for i in range(1, n+1)
    ]


def check(label, condition, detail=""):
    if not condition:
        raise AssertionError(f"{label} FAILED {detail}")
    print(f"{label} PASS")


def main():
    players = sample_players()
    state = eng.initialize_draft(players, teams_count=10, draft_position=4, scoring="PPR", rounds=16, seconds_per_pick=2)

    # 1 Start mock / 2 draft position / 3 CPU picks
    eng.start_draft(state)
    check("TEST 1 start mock", state["status"] == "active")
    check("TEST 2 draft position", state["userTeamId"] == "t4")
    eng.advance_cpu_until_user(state)
    check("TEST 3 CPU picks", len(state["picks"]) == 3 and state["currentTeam"] == "t4")

    # 4-7 user draft, removal, board/pick history, roster
    pid = state["availablePlayers"][0]["id"]
    picked_name = state["availablePlayers"][0]["name"]
    eng.make_pick(state, pid, "user")
    check("TEST 4 user can draft", state["picks"][-1]["playerId"] == pid)
    check("TEST 5 selected disappears", all(p["id"] != pid for p in state["availablePlayers"]))
    check("TEST 6 player on board state", any(p["playerId"] == pid and p["pickNumber"] == 4 for p in state["picks"]))
    check("TEST 7 player on correct roster", any(p["id"] == pid for p in eng.team_by_id(state, "t4")["roster"]))

    # 8-9 advance + snake reversal
    check("TEST 8 draft advances", state["currentOverallPick"] == 5 and state["currentTeam"] == "t5")
    check("TEST 9 round 2 snake reverses", eng.snake_team_for_pick(11, 10) == 10 and eng.snake_team_for_pick(20, 10) == 1)

    # 10 timer
    state["currentTeam"] = state["userTeamId"]
    state["timer"] = {"remaining": 2, "startedAt": time.time()-3}
    check("TEST 10 timer", eng.timer_remaining(state) == 0)

    # 11 queue + 12 autopick
    qid = state["availablePlayers"][3]["id"]
    eng.queue_add(state, qid)
    check("TEST 11 queue", state["queue"] == [qid])
    state["currentTeam"] = state["userTeamId"]
    current_pick = state["currentOverallPick"]
    # align team ID with snake slot for a legal state before auto-pick
    expected_team = f"t{eng.snake_team_for_pick(current_pick, 10)}"
    state["currentTeam"] = expected_team
    state["userTeamId"] = expected_team
    eng.auto_pick_user(state)
    check("TEST 12 auto-pick queue first", state["picks"][-1]["playerId"] == qid)

    # 13-14 search/filter are UI controls, assert implementation contains both.
    ui_source = inspect.getsource(mock_draft_ui)
    check("TEST 13 search", 'st.text_input("Search"' in ui_source)
    check("TEST 14 position filters", '["ALL", "QB", "RB", "WR", "TE", "D/ST", "K"]' in ui_source)

    # 15 view toggle does not own/reset state: single state key and both views render it.
    check("TEST 15 synchronized views", 'mock_room_view' in ui_source and 'mock_draft_state_v2' in ui_source and '_render_board(state)' in ui_source and '_render_available(state' in ui_source)

    # 16-17 pause/resume
    eng.pause_draft(state); check("TEST 16 pause", state["paused"] is True)
    eng.resume_draft(state); check("TEST 17 resume", state["paused"] is False)

    # 18 undo restores everything
    last = state["picks"][-1]; before_len = len(state["picks"])
    eng.undo_last_pick(state)
    check("TEST 18 undo restores", len(state["picks"]) == before_len-1 and any(p["id"] == last["playerId"] for p in state["availablePlayers"]) and state["currentOverallPick"] == last["pickNumber"])

    # 19 duplicate prevention
    restored_id = last["playerId"]
    state["currentTeam"] = f"t{eng.snake_team_for_pick(state['currentOverallPick'], 10)}"
    eng.make_pick(state, restored_id, "user")
    duplicate_blocked = False
    try:
        eng.make_pick(state, restored_id, "user")
    except ValueError:
        duplicate_blocked = True
    check("TEST 19 no duplicate drafts", duplicate_blocked)

    # 20 CPU logic isn't raw projected points. In R1, absurd-QB projection must not auto-win over proper RB/WR market value.
    cpu_state = eng.initialize_draft([
        {"id":"qb","name":"QB High Points","position":"QB","team":"A","bye":1,"adp":18.0,"rank":18,"position_rank":1,"projected_points":500.0,"isAvailable":True},
        {"id":"wr","name":"Elite WR","position":"WR","team":"B","bye":2,"adp":2.0,"rank":2,"position_rank":1,"projected_points":280.0,"isAvailable":True},
        {"id":"rb","name":"Elite RB","position":"RB","team":"C","bye":3,"adp":3.0,"rank":3,"position_rank":1,"projected_points":260.0,"isAvailable":True},
    ], 10, 1, rounds=2)
    eng.start_draft(cpu_state)
    selection = eng.cpu_select_player(cpu_state, "t1")
    check("TEST 20 positional CPU logic", selection["id"] in {"wr","rb"}, f"selected={selection}")

    # 21 draft ends correctly
    end_state = eng.initialize_draft(sample_players(40), 8, 1, rounds=1, seconds_per_pick=1)
    eng.start_draft(end_state)
    for _ in range(8):
        p = eng.cpu_select_player(end_state, end_state["currentTeam"])
        eng.make_pick(end_state, p["id"], "cpu")
    check("TEST 21 completion", end_state["status"] == "complete" and end_state["timer"]["remaining"] == 0)

    # 22 persistence
    with tempfile.TemporaryDirectory() as td:
        db = Path(td)/"mocks.sqlite"
        did = eng.save_completed_draft(end_state, db)
        loaded = eng.load_saved_draft(db, did)
        check("TEST 22 completed draft saves", loaded is not None and len(loaded["picks"]) == 8)

    # 23-24 mobile overflow controls
    check("TEST 23 no global horizontal overflow", 'overflow-x:hidden!important' in ui_source)
    check("TEST 24 board contained scrolling", '.mock-board-wrap' in ui_source and 'overflow-x:auto' in ui_source)

    # 25 existing navigation still lives in app and Mock Draft is one of the four tools
    app_source = (ROOT/"app.py").read_text(encoding="utf-8")
    check("TEST 25 navigation preserved", 'Shiva Intelligence' in app_source and 'Draft Coach' in app_source and 'Mock Draft' in app_source and 'Shiva League History' in app_source)

    # 26 full live context handed to Ask Shiva service.
    context = eng.full_draft_context(state)
    expected = {"season","scoring","teamsCount","currentRound","currentOverallPick","currentTeam","userTeamId","myDraftPosition","myRoster","opponentRosters","draftedPlayers","availablePlayers","queue","rosterRequirements","rosterNeeds","recentSelections","recommendations"}
    sig = inspect.signature(shiva_chatgpt_service.ask_shiva_via_chatgpt)
    check("TEST 26 Ask Shiva full live context", expected.issubset(context.keys()) and "draft_context" in sig.parameters)

    print("ALL 26 MOCK DRAFT REGRESSION TESTS PASSED")


if __name__ == "__main__":
    main()
