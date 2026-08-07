from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import espn_news_service as news
from shiva_engine import build_history_frame
from shiva_query_router import run_shiva_query


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


def assert_contains(report, needle: str, label: str):
    text = " ".join(str(report.get(k, "")) for k in ["title", "answer", "note", "takeaway"])
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: expected {needle!r} in report, got: {text}")


def main():
    history, roi, rankings, weekly = load_data()
    print("WEEKLY COLUMNS:", list(weekly.columns))

    r1 = run_shiva_query("What was Christian McCaffrey's PPG in 2025?", history, roi, rankings, weekly)
    table1 = r1.get("table", pd.DataFrame())
    if len(table1) != 1 or table1["player_name"].nunique() != 1 or int(table1.iloc[0]["season"]) != 2025:
        raise AssertionError(f"TEST 1 invalid result shape: rows={len(table1)} players={table1.get('player_name', pd.Series(dtype=str)).nunique()}")
    ppg = float(table1.iloc[0]["ppg"])
    if not (24.0 <= ppg <= 25.0):
        raise AssertionError(f"TEST 1 expected CMC 2025 PPG around 24.5, got {ppg}")
    print(f"TEST 1 PASS: Christian McCaffrey 2025 = {ppg:.2f} PPG; exactly one player-season")

    r2 = run_shiva_query("What were Christian McCaffrey's receiving stats in 2025?", history, roi, rankings, weekly)
    for expected in ["102 receptions", "924 receiving yards", "7 receiving TD"]:
        assert_contains(r2, expected, "TEST 2")
    print(f"TEST 2 PASS: {r2['answer']}")

    r3 = run_shiva_query("Compare Christian McCaffrey and Bijan Robinson in 2025.", history, roi, rankings, weekly)
    table3 = r3.get("table", pd.DataFrame())
    names3 = set(table3["player_name"].astype(str)) if not table3.empty else set()
    if names3 != {"Christian McCaffrey", "Bijan Robinson"}:
        raise AssertionError(f"TEST 3 expected only CMC/Bijan, got {names3}")
    print(f"TEST 3 PASS: exactly {sorted(names3)}")

    r4 = run_shiva_query("Who would you draft, Christian McCaffrey or Bijan Robinson?", history, roi, rankings, weekly)
    if "I'D TAKE" not in str(r4.get("answer", "")):
        raise AssertionError(f"TEST 4 expected clear recommendation, got {r4.get('answer')}")
    names4 = set(r4.get("table", pd.DataFrame()).get("player_name", pd.Series(dtype=str)).astype(str))
    if not names4.issubset({"Christian McCaffrey", "Bijan Robinson"}) or len(names4) != 2:
        raise AssertionError(f"TEST 4 supporting data contains unexpected players: {names4}")
    print(f"TEST 4 PASS: {r4['answer']}")

    stories = news.fetch_espn_news(limit=4)
    if not stories or not all(s.get("title") and s.get("link") for s in stories):
        raise AssertionError("TEST 5 ESPN backend did not return valid normalized stories")
    print(f"TEST 5 PASS: ESPN backend returned {len(stories)} stories")

    source = (ROOT / "espn_news_service.py").read_text(encoding="utf-8")
    if "window.fetch" in source:
        raise AssertionError("TEST 6 found client-side fetch dependency")
    print("TEST 6 PASS: ESPN retrieval is server-side Python, not browser/client fetch")

    old_cache = news.CACHE_PATH
    old_request = news._request
    try:
        with tempfile.TemporaryDirectory() as td:
            news.CACHE_PATH = Path(td) / "espn_news_cache.json"
            news.CACHE_PATH.write_text(json.dumps({"stories": stories}), encoding="utf-8")
            def fail(*args, **kwargs):
                raise RuntimeError("simulated ESPN outage")
            news._request = fail
            cached = news.fetch_espn_news(limit=4)
            if not cached or cached[0]["title"] != stories[0]["title"]:
                raise AssertionError("TEST 7 cache fallback failed")
    finally:
        news.CACHE_PATH = old_cache
        news._request = old_request
    print("TEST 7 PASS: simulated ESPN outage served last-good cached headlines")


if __name__ == "__main__":
    main()
