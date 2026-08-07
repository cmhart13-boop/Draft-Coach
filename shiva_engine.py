from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def build_history_frame(roi: pd.DataFrame, births: pd.DataFrame) -> pd.DataFrame:
    """Build one verified player-season row from the packaged 2014-2025 history."""
    df = roi.copy()
    for col in ["season", "position_finish_total", "fantasy_points_ppr", "ppg", "games_played", "overall_pick", "round"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = (
        df.sort_values(["season", "position", "position_finish_total", "fantasy_points_ppr"], ascending=[True, True, True, False])
        .drop_duplicates(["season", "player_name", "position"], keep="first")
        .copy()
    )
    df["name_key"] = df["player_name"].map(normalize_name)
    if not births.empty:
        b = births[["name_key", "birth_date"]].drop_duplicates("name_key").copy()
        b["birth_date"] = pd.to_datetime(b["birth_date"], errors="coerce")
        df = df.merge(b, on="name_key", how="left")
        ref = pd.to_datetime(df["season"].astype("Int64").astype(str) + "-09-01", errors="coerce")
        df["age"] = ((ref - df["birth_date"]).dt.days / 365.2425)
    else:
        df["age"] = np.nan
    return df


def _position(query: str) -> str | None:
    aliases = {
        "QB": ["qb", "qbs", "quarterback", "quarterbacks"],
        "RB": ["rb", "rbs", "running back", "running backs"],
        "WR": ["wr", "wrs", "wide receiver", "wide receivers"],
        "TE": ["te", "tes", "tight end", "tight ends"],
    }
    for pos, terms in aliases.items():
        if any(re.search(rf"\b{re.escape(term)}\b", query) for term in terms):
            return pos
    return None


def _top_n(query: str) -> int | None:
    m = re.search(r"\btop\s*[- ]?(\d+)\b", query)
    return int(m.group(1)) if m else None


def _apply_time_filter(pool: pd.DataFrame, query: str) -> pd.DataFrame:
    years = sorted(pd.to_numeric(pool["season"], errors="coerce").dropna().astype(int).unique())
    if not years:
        return pool.iloc[0:0]
    latest = max(years)

    m = re.search(r"\bsince\s+(20\d{2})\b", query)
    if m:
        return pool[pool["season"].ge(int(m.group(1)))]

    m = re.search(r"\b(?:last|past)\s+(\d+)\s+years?\b", query)
    if m:
        n = int(m.group(1))
        return pool[pool["season"].between(latest - n + 1, latest)]

    m = re.search(r"\b(?:in|for|from)\s+(20\d{2})\b", query)
    if m:
        return pool[pool["season"].eq(int(m.group(1)))]

    return pool


def _top_by_finish_each_year(pool: pd.DataFrame, n: int) -> pd.DataFrame:
    return (
        pool.dropna(subset=["position_finish_total"])
        .sort_values(["season", "position_finish_total", "fantasy_points_ppr"], ascending=[False, True, False])
        .groupby("season", group_keys=False)
        .head(n)
    )


def _player_table(pool: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["season", "player_name", "position", "age", "position_finish_total", "fantasy_points_ppr", "ppg", "games_played", "overall_pick"] if c in pool.columns]
    return pool[cols].sort_values(["season", "position_finish_total"], ascending=[False, True])


def _report(title: str, answer: str, note: str, table: pd.DataFrame | None = None, takeaway: str = "", kind: str = "players") -> dict[str, Any]:
    return {
        "title": title,
        "answer": answer,
        "note": note,
        "table": table if table is not None else pd.DataFrame(),
        "takeaway": takeaway,
        "kind": kind,
    }


def _double_rb_report(roi: pd.DataFrame) -> dict[str, Any]:
    picks = roi.copy()
    picks["round"] = pd.to_numeric(picks["round"], errors="coerce")
    picks["position_finish_total"] = pd.to_numeric(picks["position_finish_total"], errors="coerce")
    early = picks[picks["round"].isin([1, 2])].copy()
    grouped = early.groupby(["league_name", "season", "team_id"])
    rows = []
    for (league, season, team_id), g in grouped:
        r1 = g[(g["round"].eq(1)) & (g["position"].eq("RB"))]
        r2 = g[(g["round"].eq(2)) & (g["position"].eq("RB"))]
        if r1.empty or r2.empty:
            continue
        two = pd.concat([r1.head(1), r2.head(1)])
        both_top12 = bool(two["position_finish_total"].notna().all() and two["position_finish_total"].le(12).all())
        rows.append({"league": league, "season": int(season), "team_id": team_id, "rb1": two.iloc[0]["player_name"], "rb2": two.iloc[1]["player_name"], "both_top12": both_top12})
    sample = pd.DataFrame(rows)
    if sample.empty:
        return _report("🚨 DOUBLE-RB START", "NO VERIFIED SAMPLE", "No team-seasons in the league-history database opened RB-RB in Rounds 1 and 2.")
    rate = sample["both_top12"].mean() * 100
    return _report(
        "🚨 DOUBLE-RB START",
        f"{rate:.1f}% BOTH FINISHED TOP-12",
        f"Calculated from {len(sample)} verified RB-RB team-seasons in the actual league-history database.",
        sample.sort_values("season", ascending=False),
        "This is a measured historical result, not a preset verdict. Use it with current 2026 ADP and the players actually available at your picks.",
        "strategy",
    )


def _round1_qb_report(roi: pd.DataFrame) -> dict[str, Any]:
    picks = roi.copy()
    for col in ["round", "position_finish_total", "final_draft_roi", "ppg"]:
        if col in picks.columns:
            picks[col] = pd.to_numeric(picks[col], errors="coerce")
    qbs = picks[(picks["round"].eq(1)) & (picks["position"].eq("QB"))].copy()
    if qbs.empty:
        return _report("📉 ROUND-1 QB", "NO VERIFIED SAMPLE", "No Round-1 QB picks exist in the loaded league-history sample.")
    avg_finish = qbs["position_finish_total"].mean()
    top5_rate = qbs["position_finish_total"].le(5).mean() * 100
    avg_roi = qbs["final_draft_roi"].mean() if "final_draft_roi" in qbs else np.nan
    answer = f"{top5_rate:.1f}% FINISHED TOP-5"
    note = f"{len(qbs)} verified Round-1 QB picks · average positional finish QB{avg_finish:.1f}"
    if pd.notna(avg_roi):
        note += f" · average draft ROI {avg_roi:.1f}"
    return _report("📉 ROUND-1 QB RESULTS", answer, note, _player_table(qbs), "The database can measure what those QB picks returned. It does not invent a roster-depth penalty that is not directly supported by the stored fields.", "strategy")


def _early_te_report(history: pd.DataFrame) -> dict[str, Any]:
    te = history[(history["position"].eq("TE")) & (history["overall_pick"].le(36))].dropna(subset=["position_finish_total"]).copy()
    if te.empty:
        return _report("🪤 EARLY TE", "NO VERIFIED SAMPLE", "No TE seasons with verified top-36 draft capital matched.")
    elite = te["position_finish_total"].le(3)
    rate = elite.mean() * 100
    return _report("🪤 EARLY TE HIT RATE", f"{rate:.1f}% FINISHED TOP-3", f"{int(elite.sum())} of {len(te)} verified early-drafted TE seasons finished top three.", _player_table(te), "This measures actual return on early TE draft capital from the stored history.", "strategy")


def run_shiva_query(question: str, history: pd.DataFrame, roi: pd.DataFrame, rankings: pd.DataFrame) -> dict[str, Any]:
    """Dynamic, data-backed natural-language report engine. No hard-coded fantasy outcomes."""
    query = re.sub(r"\s+", " ", question.lower().strip())
    if not query:
        return _report("📊 SHIVA INTELLIGENCE", "ASK SHIVA A QUESTION", "Enter a historical, scoring, ADP, age, or draft-strategy question.")

    if re.search(r"(?:two|2)\s+(?:running backs|rbs?)", query) and re.search(r"first\s+(?:two|2)\s+rounds|rounds?\s+1\s+(?:and|&)\s+2", query):
        return _double_rb_report(roi)

    if ("quarterback" in query or re.search(r"\bqb\b", query)) and ("round 1" in query or "first round" in query or "1st round" in query):
        return _round1_qb_report(roi)

    if ("tight end" in query or re.search(r"\bte\b", query)) and ("top 3 rounds" in query or "first 3 rounds" in query or "top three rounds" in query):
        return _early_te_report(history)

    if (("qb3" in query and "qb9" in query) or ("tier 1" in query and "tier 2" in query and ("quarterback" in query or "qb" in query))):
        qb = history[history["position"].eq("QB")].copy()
        a = qb[qb["position_finish_total"].eq(3)][["season", "ppg"]].rename(columns={"ppg": "QB3_PPG"})
        b = qb[qb["position_finish_total"].eq(9)][["season", "ppg"]].rename(columns={"ppg": "QB9_PPG"})
        merged = a.merge(b, on="season", how="inner")
        if merged.empty:
            return _report("📉 QB TIER DROP-OFF", "NO VERIFIED SAMPLE", "The stored history does not contain matching QB3 and QB9 seasons.")
        merged["PPG_Gap"] = merged["QB3_PPG"] - merged["QB9_PPG"]
        return _report("📉 QB3 → QB9 DROP-OFF", f"{merged['PPG_Gap'].mean():.2f} PPG", f"Average verified QB3-minus-QB9 gap across {len(merged)} seasons.", merged.sort_values("season", ascending=False), "This is the actual historical weekly scoring premium for the elite-QB tier.", "strategy")

    if ("27" in query and ("running back" in query or re.search(r"\brb\b", query)) and ("top 12" in query or "top-12" in query)):
        rb = history[(history["position"].eq("RB")) & (history["age"].ge(27))].dropna(subset=["position_finish_total"]).copy()
        if rb.empty:
            return _report("⏳ AGE-27 RB TEST", "NO VERIFIED SAMPLE", "No age-27+ RB seasons with verified finishes matched.")
        rate = rb["position_finish_total"].le(12).mean() * 100
        return _report("⏳ AGE-27+ RB TEST", f"{rate:.1f}% FINISHED TOP-12", f"Calculated from {len(rb)} verified age-27+ RB seasons.", _player_table(rb), "Use the observed hit rate as an age-risk input, not as a standalone fade rule.", "strategy")

    if ("tight end" in query or re.search(r"\bte\b", query)) and "outside" in query and "top 50" in query and ("top 3" in query or "top-three" in query):
        te = history[(history["position"].eq("TE")) & (history["overall_pick"].gt(50)) & (history["position_finish_total"].le(3))].copy()
        return _report("🔥 LATE TE UPSIDE", f"{len(te)} VERIFIED SEASONS", "TEs drafted after Pick 50 who still finished top three.", _player_table(te), "This directly measures late-draft access to elite TE finishes.", "strategy")

    pos = _position(query)
    n = _top_n(query)
    pool = history.copy()
    if pos:
        pool = pool[pool["position"].eq(pos)]
    pool = _apply_time_filter(pool, query)
    if n:
        pool = _top_by_finish_each_year(pool, n)

    if pool.empty:
        return _report("📊 SHIVA INTELLIGENCE", "0 VERIFIED MATCHES", "The requested filters returned no rows from the 2014-2025 dataset.")

    asks_average = bool(re.search(r"\baverage\b|\bavg\b|\bmean\b", query))
    if "age" in query:
        valid = pool.dropna(subset=["age"])
        if valid.empty:
            return _report("🚨 AGE REPORT", "NO VERIFIED DOB MATCHES", "Matching player-seasons do not have a verified birth-date match.")
        return _report("🚨 SHIVA AGE REPORT", f"{valid['age'].mean():.1f} YEARS OLD", f"Average across {len(valid)} verified player-seasons.", _player_table(valid), "Age is calculated at September 1 of each season.")

    if "ppg" in query or "points per game" in query:
        valid = pool.dropna(subset=["ppg"])
        return _report("📊 SHIVA PPG REPORT", f"{valid['ppg'].mean():.2f} PPG" if asks_average or n else f"{len(valid)} VERIFIED SEASONS", f"Calculated directly from {len(valid)} matching player-seasons.", _player_table(valid), "The supporting rows are the exact records used in the calculation.")

    if ("points" in query or "fantasy points" in query or "scoring" in query) and asks_average:
        valid = pool.dropna(subset=["fantasy_points_ppr"])
        return _report("📊 SHIVA POINTS REPORT", f"{valid['fantasy_points_ppr'].mean():.1f} PPR POINTS", f"Average across {len(valid)} matching player-seasons.", _player_table(valid))

    if "games" in query and asks_average:
        valid = pool.dropna(subset=["games_played"])
        return _report("📊 SHIVA GAMES REPORT", f"{valid['games_played'].mean():.1f} GAMES", f"Average across {len(valid)} matching player-seasons.", _player_table(valid))

    if "adp" in query and asks_average:
        valid = pool.dropna(subset=["overall_pick"])
        return _report("🎯 HISTORICAL DRAFT POSITION", f"PICK {valid['overall_pick'].mean():.1f}", f"Average draft slot across {len(valid)} matching player-seasons.", _player_table(valid))

    if n or any(term in query for term in ["show me", "list", "who were", "who are", "top"]):
        return _report("📊 SHIVA PLAYER REPORT", f"{len(pool)} VERIFIED PLAYER-SEASONS", "Every row below comes from the loaded historical database.", _player_table(pool))

    return _report(
        "🧠 SHIVA NEEDS A MORE SPECIFIC METRIC",
        "NO NUMBER WAS INVENTED",
        "I found matching historical records, but the question does not identify a calculation Shiva can verify from the currently loaded fields. Ask for PPG, age, points, games, ADP/draft position, a top-N finish group, or one of the supported draft-strategy comparisons.",
        _player_table(pool.head(25)),
        "Unsupported questions return the matching data instead of a fabricated conclusion.",
    )
