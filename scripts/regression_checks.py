from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shiva_engine import build_history_frame, normalize_name
from shiva_query_router import retrieve_shiva_context, run_shiva_query
import shiva_chatgpt_service as service


def load_data():
    with sqlite3.connect(ROOT / "shiva_draft_roi.sqlite") as con:
        roi = pd.read_sql_query("SELECT * FROM draft_roi_scores", con)
    rankings = pd.read_csv(ROOT / "current_rankings.csv")
    births = pd.read_csv(ROOT / "player_birth_dates.csv")
    births["birth_date"] = pd.to_datetime(births["birth_date"], errors="coerce")
    weekly = pd.read_csv(ROOT / "player_weekly_master_2014_2025.csv.gz", low_memory=False, compression="gzip")
    for col in ["season", "round", "overall_pick", "position_draft_rank", "position_finish_total", "fantasy_points_ppr", "ppg", "games_played", "final_draft_roi"]:
        if col in roi.columns:
            roi[col] = pd.to_numeric(roi[col], errors="coerce")
    history = build_history_frame(roi, births)
    return history, roi, rankings, weekly


def _serialized(context) -> str:
    return json.dumps(context, default=str, ensure_ascii=False).lower()


def _assert_no_code_verdict(context, label: str):
    blob = _serialized(context)
    banned = ["i'd take", "winner", "recommendation_score", "comparison_score", "pickplayer", "chooseplayer", "presetrecommendation"]
    found = [x for x in banned if x in blob]
    if found:
        raise AssertionError(f"{label}: data context contains forbidden verdict material: {found}")


def _named_rankings(context) -> dict[str, dict]:
    return {str(r.get("player_name")): r for r in context.get("current_rankings_for_named_players", [])}


class _FakeResponse:
    def __init__(self, text: str):
        self.output_text = text


class _FakeResponses:
    def __init__(self, text: str, capture: dict):
        self.text = text
        self.capture = capture

    def create(self, **kwargs):
        self.capture.update(kwargs)
        return _FakeResponse(self.text)


class _FakeClient:
    def __init__(self, text: str, capture: dict):
        self.responses = _FakeResponses(text, capture)


def _run_endpoint_with_fake_model(question, fake_text, history, roi, rankings, weekly):
    capture = {}
    old_openai = service.OpenAI
    try:
        service.OpenAI = lambda api_key=None: _FakeClient(fake_text, capture)
        result = service.ask_shiva_via_chatgpt(
            question=question,
            history=history,
            roi=roi,
            rankings=rankings,
            weekly=weekly,
            api_key="test-key",
        )
    finally:
        service.OpenAI = old_openai
    return result, capture


def test_1_cross_position_model_decides(history, roi, rankings, weekly):
    question = "Would you draft CeeDee Lamb or Josh Allen in the first round?"
    context = retrieve_shiva_context(question, history, roi, rankings, weekly)
    if context["intent"] != "DRAFT_DECISION":
        raise AssertionError(f"TEST 1 wrong intent: {context['intent']}")
    names = set(context["resolved_players"])
    if names != {"CeeDee Lamb", "Josh Allen"}:
        raise AssertionError(f"TEST 1 wrong players: {names}")
    ranks = _named_rankings(context)
    if set(ranks) != names:
        raise AssertionError(f"TEST 1 missing current ranking rows: {set(ranks)}")
    if str(ranks["CeeDee Lamb"].get("position")) != "WR" or str(ranks["Josh Allen"].get("position")) != "QB":
        raise AssertionError("TEST 1 expected WR/QB positional context")
    _assert_no_code_verdict(context, "TEST 1")

    fake = "I'd take CeeDee Lamb in the first round.\n\nWHY:\nIn a 10-team full-PPR league, elite WR opportunity cost matters more here. Lamb's current ADP places him in the first-round market while Allen's ADP is later, so taking Allen here gives up a scarcer early WR tier for a QB position with useful later alternatives."
    result, capture = _run_endpoint_with_fake_model(question, fake, history, roi, rankings, weekly)
    if "CeeDee Lamb" not in result.get("answer", ""):
        raise AssertionError(f"TEST 1 endpoint did not preserve model choice: {result}")
    input_messages = capture.get("input", [])
    if not input_messages or input_messages[-1].get("role") != "user" or input_messages[-1].get("content") != question:
        raise AssertionError("TEST 1 original question was not passed untouched as the user message")
    developer_blob = json.dumps(input_messages[0], default=str).lower()
    if "i'd take" in developer_blob:
        raise AssertionError("TEST 1 developer/data context contains a preselected winner")
    print("TEST 1 PASS: cross-position draft question reaches the model with WR/QB + ADP context and no code-selected winner")


def test_2_same_position_comparison(history, roi, rankings, weekly):
    question = "Who would you draft, Justin Jefferson or Ja'Marr Chase?"
    context = retrieve_shiva_context(question, history, roi, rankings, weekly)
    if context["intent"] != "DRAFT_DECISION":
        raise AssertionError(f"TEST 2 wrong intent: {context['intent']}")
    if set(context["resolved_players"]) != {"Justin Jefferson", "Ja'Marr Chase"}:
        raise AssertionError(f"TEST 2 wrong resolved players: {context['resolved_players']}")
    _assert_no_code_verdict(context, "TEST 2")
    fake = "I'd take Ja'Marr Chase by a small margin.\n\nWHY:\nBoth are elite first-round WRs, so this is a tier-level decision rather than a raw PPG sort. I would weigh current ADP, target ceiling, weekly spike potential and team context before breaking the tie."
    result, _ = _run_endpoint_with_fake_model(question, fake, history, roi, rankings, weekly)
    if "Ja'Marr Chase" not in result.get("answer", ""):
        raise AssertionError(f"TEST 2 model response parsing failed: {result}")
    print("TEST 2 PASS: same-position draft comparison is model-decided, not highest historical PPG")


def test_3_cmc_ppg(history, roi, rankings, weekly):
    question = "How many PPR points per game did Christian McCaffrey average in 2025?"
    context = retrieve_shiva_context(question, history, roi, rankings, weekly)
    ps = context.get("facts", {}).get("player_season") or {}
    if ps.get("player_name") != "Christian McCaffrey" or ps.get("season") != 2025:
        raise AssertionError(f"TEST 3 wrong exact player-season: {ps}")
    ppg = float(ps.get("points_per_game"))
    points = float(ps.get("fantasy_points_ppr"))
    games = int(ps.get("games_played"))
    if abs(ppg - (points / games)) > 0.02 or not (24.0 <= ppg <= 25.0):
        raise AssertionError(f"TEST 3 incorrect deterministic PPG: points={points} games={games} ppg={ppg}")
    report = run_shiva_query(question, history, roi, rankings, weekly)
    if "24." not in report.get("answer", ""):
        raise AssertionError(f"TEST 3 factual reporter mismatch: {report}")
    print(f"TEST 3 PASS: CMC 2025 = {points:.1f} points / {games} games = {ppg:.2f} PPG")


def test_4_weekly_threshold(history, roi, rankings, weekly):
    question = "Who had more games with 15+ PPR points in 2025, Christian McCaffrey or Bijan Robinson?"
    context = retrieve_shiva_context(question, history, roi, rankings, weekly)
    threshold = context.get("facts", {}).get("weekly_threshold") or {}
    counts = threshold.get("counts", {})
    expected_names = {"Christian McCaffrey", "Bijan Robinson"}
    if set(counts) != expected_names:
        raise AssertionError(f"TEST 4 missing weekly threshold counts: {counts}")

    # Independent check directly against weekly source rows.
    w = weekly[pd.to_numeric(weekly["season"], errors="coerce").eq(2025)].copy()
    w["_ppr"] = pd.to_numeric(w["fantasy_points_ppr"], errors="coerce")
    independent = {}
    for player in expected_names:
        mask = w["player_display_name"].astype(str).map(normalize_name).eq(normalize_name(player))
        independent[player] = int(w.loc[mask, "_ppr"].ge(15.0).sum())
    if counts != independent:
        raise AssertionError(f"TEST 4 deterministic weekly count mismatch: context={counts} direct={independent}")
    _assert_no_code_verdict(context, "TEST 4")
    print(f"TEST 4 PASS: verified 2025 15+ PPR game counts = {counts}; code calculates counts but does not choose the fantasy winner")


def test_5_roster_hypothetical(history, roi, rankings, weekly):
    question = "If I already drafted two RBs, would you take another RB or an elite WR here?"
    context = retrieve_shiva_context(question, history, roi, rankings, weekly)
    if context["intent"] != "HYPOTHETICAL":
        raise AssertionError(f"TEST 5 expected HYPOTHETICAL, got {context['intent']}")
    if not context.get("current_adp_market_sample"):
        raise AssertionError("TEST 5 expected current ADP market context")
    if context.get("league_defaults", {}).get("teams") != 10 or context.get("league_defaults", {}).get("scoring") != "Full PPR":
        raise AssertionError(f"TEST 5 league defaults missing: {context.get('league_defaults')}")
    _assert_no_code_verdict(context, "TEST 5")
    fake = "I'd lean elite WR.\n\nWHY:\nWith two RBs already rostered, a third RB has to clear a much higher value bar. In a 10-team full-PPR build, adding an elite WR usually improves starting-lineup balance and protects you from falling behind at a position where multiple starters are required."
    result, _ = _run_endpoint_with_fake_model(question, fake, history, roi, rankings, weekly)
    if "elite WR" not in result.get("answer", ""):
        raise AssertionError(f"TEST 5 hypothetical model response failed: {result}")
    print("TEST 5 PASS: roster-construction hypothetical reaches the analyst with league defaults and current market context")


def test_6_missing_players(history, roi, rankings, weekly):
    question = "Who would you rather draft?"
    context = retrieve_shiva_context(question, history, roi, rankings, weekly)
    if context["intent"] != "DRAFT_DECISION" or not context.get("needs_clarification"):
        raise AssertionError(f"TEST 6 expected missing-player clarification context: {context}")
    _assert_no_code_verdict(context, "TEST 6")
    fake = "Which two players are you deciding between?"
    result, _ = _run_endpoint_with_fake_model(question, fake, history, roi, rankings, weekly)
    if "which" not in result.get("answer", "").lower() or "players" not in result.get("answer", "").lower():
        raise AssertionError(f"TEST 6 expected clarification question: {result}")
    print("TEST 6 PASS: missing-player draft question asks for the players instead of fabricating a verdict")


def maybe_run_live_model_smoke(history, roi, rankings, weekly):
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        print("LIVE MODEL SMOKE SKIPPED: GitHub Actions OPENAI_API_KEY secret is not configured.")
        return
    question = "Would you draft CeeDee Lamb or Josh Allen in the first round?"
    result = service.ask_shiva_via_chatgpt(question, history, roi, rankings, weekly, api_key=key)
    if result.get("kind") != "chatgpt":
        raise AssertionError(f"LIVE MODEL SMOKE failed to reach OpenAI: {result}")
    if not result.get("answer"):
        raise AssertionError("LIVE MODEL SMOKE returned an empty answer")
    print("LIVE MODEL SMOKE PASS:", result.get("answer"), "| WHY:", result.get("why", "")[:300])


def main():
    history, roi, rankings, weekly = load_data()
    test_1_cross_position_model_decides(history, roi, rankings, weekly)
    test_2_same_position_comparison(history, roi, rankings, weekly)
    test_3_cmc_ppg(history, roi, rankings, weekly)
    test_4_weekly_threshold(history, roi, rankings, weekly)
    test_5_roster_hypothetical(history, roi, rankings, weekly)
    test_6_missing_players(history, roi, rankings, weekly)
    maybe_run_live_model_smoke(history, roi, rankings, weekly)


if __name__ == "__main__":
    main()
