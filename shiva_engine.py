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
    for col in [
        "season",
        "position_finish_total",
        "fantasy_points_ppr",
        "ppg",
        "games_played",
        "overall_pick",
        "round",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = (
        df.sort_values(
            ["season", "position", "position_finish_total", "fantasy_points_ppr"],
            ascending=[True, True, True, False],
        )
        .drop_duplicates(["season", "player_name", "position"], keep="first")
        .copy()
    )

    df["name_key"] = df["player_name"].map(normalize_name)
    if not births.empty:
        b = births[["name_key", "birth_date"]].drop_duplicates("name_key").copy()
        b["birth_date"] = pd.to_datetime(b["birth_date"], errors="coerce")
        df = df.merge(b, on="name_key", how="left")
        ref = pd.to_datetime(
            df["season"].astype("Int64").astype(str) + "-09-01",
            errors="coerce",
        )
        df["age"] = (ref - df["birth_date"]).dt.days / 365.2425
    else:
        df["age"] = np.nan

    return df


def _position(query: str) -> str | None:
    aliases = {
        "QB": ["qb", "qbs", "quarterback", "quarterbacks", "passer"],
        "RB": ["rb", "rbs", "running back", "running backs", "back", "backs"],
        "WR": ["wr", "wrs", "wide receiver", "wide receivers", "receiver", "receivers"],
        "TE": ["te", "tes", "tight end", "tight ends"],
    }
    for pos, terms in aliases.items():
        if any(re.search(rf"\b{re.escape(term)}\b", query) for term in terms):
            return pos
    return None


def _top_n(query: str) -> int | None:
    patterns = [
        r"\btop\s*[- ]?(\d+)\b",
        r"\bbest\s*[- ]?(\d+)\b",
        r"\bfirst\s+(\d+)\s+(?:players?|backs?|receivers?|quarterbacks?|tight ends?)\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, query)
        if m:
            return int(m.group(1))
    return None


def _apply_time_filter(pool: pd.DataFrame, query: str) -> pd.DataFrame:
    years = sorted(
        pd.to_numeric(pool["season"], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
    )
    if not years:
        return pool.iloc[0:0]

    latest = max(years)

    m = re.search(r"\bsince\s+(20\d{2})\b", query)
    if m:
        return pool[pool["season"].ge(int(m.group(1)))]

    m = re.search(r"\b(?:last|past|previous|recent)\s+(\d+)\s+(?:seasons?|years?)\b", query)
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
        .sort_values(
            ["season", "position_finish_total", "fantasy_points_ppr"],
            ascending=[False, True, False],
        )
        .groupby("season", group_keys=False)
        .head(n)
    )


def _player_table(pool: pd.DataFrame) -> pd.DataFrame:
    cols = [
        c
        for c in [
            "season",
            "player_name",
            "position",
            "age",
            "position_finish_total",
            "fantasy_points_ppr",
            "ppg",
            "games_played",
            "overall_pick",
        ]
        if c in pool.columns
    ]
    if pool.empty:
        return pool[cols] if cols else pd.DataFrame()
    sort_cols = [c for c in ["season", "position_finish_total"] if c in pool.columns]
    if sort_cols:
        ascending = [False, True][: len(sort_cols)]
        return pool[cols].sort_values(sort_cols, ascending=ascending)
    return pool[cols]


def _report(
    title: str,
    answer: str,
    note: str,
    table: pd.DataFrame | None = None,
    takeaway: str = "",
    kind: str = "players",
) -> dict[str, Any]:
    return {
        "title": title,
        "answer": answer,
        "note": note,
        "table": table if table is not None else pd.DataFrame(),
        "takeaway": takeaway,
        "kind": kind,
    }


def _has_round(query: str, round_number: int) -> bool:
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
    word = words.get(round_number, str(round_number))
    patterns = [
        rf"\bround\s*{round_number}\b",
        rf"\bround\s*{word}\b",
        rf"\b{round_number}(?:st|nd|rd|th)\s*round\b",
        rf"\b{word}\w*\s*round\b",
    ]
    return any(re.search(pattern, query) for pattern in patterns)


def _double_rb_intent(query: str) -> bool:
    has_rb = bool(re.search(r"\b(?:rb|rbs|running back|running backs|backs)\b", query))
    first_two = bool(
        re.search(r"\bfirst\s+(?:two|2)\s+rounds\b", query)
        or (_has_round(query, 1) and _has_round(query, 2))
        or re.search(r"\brounds?\s*1\s*(?:and|&|then|plus)\s*2\b", query)
    )
    strategy_language = bool(
        re.search(
            r"\b(?:should|would|can|could|take|draft|start|open|go|strategy|plan|build)\b",
            query,
        )
    )
    return has_rb and first_two and strategy_language


def _double_rb_report(roi: pd.DataFrame, rankings: pd.DataFrame) -> dict[str, Any]:
    picks = roi.copy()
    picks["round"] = pd.to_numeric(picks["round"], errors="coerce")
    picks["position_finish_total"] = pd.to_numeric(
        picks["position_finish_total"], errors="coerce"
    )

    early = picks[picks["round"].isin([1, 2])].copy()
    rows: list[dict[str, Any]] = []
    for (league, season, team_id), g in early.groupby(
        ["league_name", "season", "team_id"]
    ):
        r1 = g[(g["round"].eq(1)) & (g["position"].eq("RB"))]
        r2 = g[(g["round"].eq(2)) & (g["position"].eq("RB"))]
        if r1.empty or r2.empty:
            continue
        two = pd.concat([r1.head(1), r2.head(1)])
        finishes = pd.to_numeric(two["position_finish_total"], errors="coerce")
        rows.append(
            {
                "league": league,
                "season": int(season),
                "team_id": team_id,
                "round_1_rb": str(two.iloc[0]["player_name"]),
                "round_2_rb": str(two.iloc[1]["player_name"]),
                "both_top12": bool(finishes.notna().all() and finishes.le(12).all()),
                "at_least_one_top12": bool(finishes.le(12).any()),
            }
        )

    sample = pd.DataFrame(rows)
    current_top24 = rankings[
        rankings["position"].eq("RB") & rankings["adp"].le(24)
    ].sort_values("adp")

    if sample.empty:
        current_note = (
            f" Current 2026 ESPN ADP has {len(current_top24)} RBs inside the first 24 picks."
            if not current_top24.empty
            else ""
        )
        return _report(
            "🚨 SHIVA STRATEGY: RB-RB START",
            "THE HISTORY SAMPLE IS TOO SMALL TO CALL IT AUTOMATIC",
            "I understood this as: draft an RB in Round 1 and another RB in Round 2. "
            "The stored league history does not contain enough verified RB-RB openings to calculate a reliable hit rate."
            + current_note,
            current_top24[["player_name", "position", "adp"]]
            if not current_top24.empty
            else pd.DataFrame(),
            "Football answer: do not force the position. If both picks remain inside the best available RB/WR tier, RB-RB is viable; if Round 2 requires reaching past a clearly better player, take the value instead.",
            "strategy",
        )

    both_rate = sample["both_top12"].mean() * 100
    one_rate = sample["at_least_one_top12"].mean() * 100
    current_note = (
        f" Current 2026 ESPN ADP has {len(current_top24)} RBs inside the first 24 picks."
        if not current_top24.empty
        else ""
    )

    if both_rate >= 50:
        verdict = "YES — THE HISTORICAL SAMPLE SUPPORTS THE BUILD"
        takeaway = (
            "RB-RB has produced enough two-hit outcomes in your actual league history to be a legitimate opening, "
            "but the 2026 decision still depends on which players reach your exact picks."
        )
    elif one_rate >= 70:
        verdict = "VIABLE — BUT EXPECT ONE OF THE TWO PICKS TO CARRY THE BUILD"
        takeaway = (
            "The history supports getting at least one strong RB result, but it does not justify blindly forcing a second RB over superior value."
        )
    else:
        verdict = "DO NOT FORCE RB-RB"
        takeaway = (
            "Your actual historical sample does not show enough two-player payoff to justify passing a clearly better WR or other elite value just to stay RB-RB."
        )

    return _report(
        "🚨 SHIVA STRATEGY: RB IN ROUND 1 + ROUND 2",
        verdict,
        f"Across {len(sample)} verified RB-RB team-seasons, {both_rate:.1f}% had both backs finish top-12 and {one_rate:.1f}% produced at least one top-12 back."
        + current_note,
        sample.sort_values("season", ascending=False),
        takeaway,
        "strategy",
    )


def _round1_qb_report(roi: pd.DataFrame) -> dict[str, Any]:
    picks = roi.copy()
    for col in ["round", "position_finish_total", "final_draft_roi", "ppg"]:
        if col in picks.columns:
            picks[col] = pd.to_numeric(picks[col], errors="coerce")

    qbs = picks[(picks["round"].eq(1)) & (picks["position"].eq("QB"))].copy()
    if qbs.empty:
        return _report(
            "📉 ROUND-1 QB",
            "I WOULD TREAT IT AS A PREMIUM-COST BET",
            "There are no verified Round-1 QB picks in the loaded league-history sample, so Shiva cannot claim a historical hit rate from this database.",
            takeaway="Football logic: a Round-1 QB must create enough weekly edge over later QB options to offset passing on an elite RB or WR. Without that edge, the opportunity cost is too high.",
            kind="strategy",
        )

    avg_finish = qbs["position_finish_total"].mean()
    top5_rate = qbs["position_finish_total"].le(5).mean() * 100
    avg_roi = qbs["final_draft_roi"].mean() if "final_draft_roi" in qbs else np.nan
    note = (
        f"{len(qbs)} verified Round-1 QB picks · {top5_rate:.1f}% finished top-5 · average positional finish QB{avg_finish:.1f}."
    )
    if pd.notna(avg_roi):
        note += f" Average draft ROI: {avg_roi:.1f}."

    return _report(
        "📉 SHIVA STRATEGY: ROUND-1 QB",
        "ONLY PAY THE PRICE FOR A REAL WEEKLY EDGE",
        note,
        _player_table(qbs),
        "A first-round QB is not automatically wrong, but the burden of proof is higher because you are giving up scarce elite RB/WR draft capital. Use the verified return history above as the evidence, not a canned rule.",
        "strategy",
    )


def _early_te_report(history: pd.DataFrame) -> dict[str, Any]:
    te = history[
        history["position"].eq("TE") & history["overall_pick"].le(36)
    ].dropna(subset=["position_finish_total"]).copy()
    if te.empty:
        return _report(
            "🪤 EARLY TE",
            "TREAT IT AS A PLAYER-SPECIFIC BET",
            "The loaded history does not contain enough verified top-36 TE seasons to calculate a reliable hit rate.",
            takeaway="Do not draft the position because it is TE. Draft an early TE only when the individual player's projected edge over replacement justifies the premium pick.",
            kind="strategy",
        )

    elite = te["position_finish_total"].le(3)
    rate = elite.mean() * 100
    return _report(
        "🪤 EARLY TE HIT RATE",
        f"{rate:.1f}% FINISHED TOP-3",
        f"{int(elite.sum())} of {len(te)} verified early-drafted TE seasons finished top three.",
        _player_table(te),
        "This is the actual return rate on premium TE draft capital in the stored history. Use it to judge whether the specific 2026 TE price is worth paying.",
        "strategy",
    )


def _infer_metric(query: str) -> str:
    """Infer what a human is actually asking about instead of requiring magic keywords."""
    if re.search(r"\b(?:old|older|young|younger|age|ages|prime)\b", query):
        return "age"
    if re.search(
        r"\b(?:weekly|per game|ppg|score|scores|scoring|produce|production|productive|points each week|fantasy output)\b",
        query,
    ):
        return "ppg"
    if re.search(r"\b(?:total points|season points|fantasy points)\b", query):
        return "points"
    if re.search(r"\b(?:games played|availability|durable|durability|healthy|health)\b", query):
        return "games"
    if re.search(r"\b(?:adp|drafted|draft position|draft cost|cost|price|where.*go|how early|how late)\b", query):
        return "adp"
    return "summary"


def _conversational_summary(query: str, pool: pd.DataFrame, pos: str | None, n: int | None) -> dict[str, Any]:
    """Data-backed football answer when the user asks naturally instead of naming a metric."""
    valid_finish = pool.dropna(subset=["position_finish_total"])
    valid_ppg = pool.dropna(subset=["ppg"])
    valid_points = pool.dropna(subset=["fantasy_points_ppr"])

    if pool.empty:
        return _report(
            "🧠 SHIVA INTELLIGENCE",
            "I COULDN'T FIND A MATCHING HISTORICAL SAMPLE",
            "I understood the football question, but the requested slice of the 2014-2025 data has no verified records.",
            takeaway="Try changing the timeframe, position, finish tier, or draft range and Shiva will rerun the comparison.",
        )

    ppg = valid_ppg["ppg"].mean() if not valid_ppg.empty else np.nan
    avg_finish = valid_finish["position_finish_total"].mean() if not valid_finish.empty else np.nan
    top12_rate = valid_finish["position_finish_total"].le(12).mean() * 100 if not valid_finish.empty else np.nan
    avg_points = valid_points["fantasy_points_ppr"].mean() if not valid_points.empty else np.nan

    subject = pos or "PLAYER"
    tier = f"TOP-{n} " if n else ""
    headline = f"HERE'S WHAT THE {tier}{subject} HISTORY ACTUALLY SAYS"

    pieces = []
    if pd.notna(ppg):
        pieces.append(f"{ppg:.2f} average PPG")
    if pd.notna(avg_finish):
        pieces.append(f"average positional finish {avg_finish:.1f}")
    if pd.notna(top12_rate):
        pieces.append(f"{top12_rate:.1f}% top-12 finish rate")
    if pd.notna(avg_points):
        pieces.append(f"{avg_points:.1f} average season PPR points")

    note = (
        f"Shiva matched {len(pool)} verified player-seasons. " + " · ".join(pieces)
        if pieces
        else f"Shiva matched {len(pool)} verified player-seasons from the historical database."
    )

    if pd.notna(ppg) and pd.notna(top12_rate):
        if top12_rate >= 60:
            takeaway = "This profile has historically converted into usable fantasy starters at a strong rate. The next question is whether the 2026 draft price gives you enough value."
        elif top12_rate >= 35:
            takeaway = "This profile is viable but not automatic. Treat current role, workload and ADP as the tiebreakers rather than drafting the archetype blindly."
        else:
            takeaway = "The historical hit rate is weak enough that Shiva would require a meaningful 2026 discount or a clear role change before paying full price."
    else:
        takeaway = "The supporting rows below are the actual sample. Shiva is giving you the strongest football read the stored data can support without inventing a statistic."

    return _report(
        "🧠 SHIVA FOOTBALL READ",
        headline,
        note,
        _player_table(pool.head(100)),
        takeaway,
        "players",
    )


def run_shiva_query(
    question: str,
    history: pd.DataFrame,
    roi: pd.DataFrame,
    rankings: pd.DataFrame,
) -> dict[str, Any]:
    """Conversational, data-backed Shiva Intelligence engine."""
    query = re.sub(r"\s+", " ", question.lower().strip())
    if not query:
        return _report(
            "📊 SHIVA INTELLIGENCE",
            "ASK SHIVA ANY FOOTBALL QUESTION",
            "You can phrase it naturally. Shiva will infer the football intent, map it to the verified data, and show the evidence behind the answer.",
        )

    # Strategy intents are recognized semantically; users do not need exact phrasing.
    if _double_rb_intent(query):
        return _double_rb_report(roi, rankings)

    if (
        _position(query) == "QB"
        and _has_round(query, 1)
        and re.search(r"\b(?:should|take|draft|worth|good|bad|happen|strategy|idea|go)\b", query)
    ):
        return _round1_qb_report(roi)

    if (
        _position(query) == "TE"
        and (
            re.search(r"\b(?:top|first)\s+(?:3|three)\s+rounds\b", query)
            or any(_has_round(query, r) for r in [1, 2, 3])
        )
        and re.search(r"\b(?:should|take|draft|trap|worth|strategy|good|bad)\b", query)
    ):
        return _early_te_report(history)

    if (
        ("qb3" in query and "qb9" in query)
        or (
            "tier 1" in query
            and "tier 2" in query
            and _position(query) == "QB"
        )
    ):
        qb = history[history["position"].eq("QB")].copy()
        a = qb[qb["position_finish_total"].eq(3)][["season", "ppg"]].rename(
            columns={"ppg": "QB3_PPG"}
        )
        b = qb[qb["position_finish_total"].eq(9)][["season", "ppg"]].rename(
            columns={"ppg": "QB9_PPG"}
        )
        merged = a.merge(b, on="season", how="inner")
        if merged.empty:
            return _report(
                "📉 QB TIER DROP-OFF",
                "I CAN'T CALCULATE THAT GAP FROM THIS SAMPLE",
                "The stored history does not contain matching QB3 and QB9 records for the same seasons.",
                takeaway="That does not make the strategy question invalid; it means Shiva needs the matching season records before attaching a number to the gap.",
                kind="strategy",
            )
        merged["PPG_Gap"] = merged["QB3_PPG"] - merged["QB9_PPG"]
        return _report(
            "📉 QB3 → QB9 DROP-OFF",
            f"{merged['PPG_Gap'].mean():.2f} PPG",
            f"Average verified QB3-minus-QB9 gap across {len(merged)} seasons.",
            merged.sort_values("season", ascending=False),
            "This is the actual historical weekly scoring premium for the elite-QB tier.",
            "strategy",
        )

    if (
        "27" in query
        and _position(query) == "RB"
        and re.search(r"\b(?:top\s*12|top-12|rb1|starter)\b", query)
    ):
        rb = history[
            history["position"].eq("RB") & history["age"].ge(27)
        ].dropna(subset=["position_finish_total"]).copy()
        if rb.empty:
            return _report(
                "⏳ AGE-27 RB TEST",
                "THERE ISN'T A VERIFIED SAMPLE TO SCORE",
                "No age-27+ RB seasons with verified finishes matched the loaded data.",
                takeaway="The football question is valid; Shiva simply will not manufacture a hit rate when the matching sample is absent.",
                kind="strategy",
            )
        rate = rb["position_finish_total"].le(12).mean() * 100
        return _report(
            "⏳ AGE-27+ RB TEST",
            f"{rate:.1f}% FINISHED TOP-12",
            f"Calculated from {len(rb)} verified age-27+ RB seasons.",
            _player_table(rb),
            "Use the observed hit rate as an age-risk input, not as a standalone fade rule.",
            "strategy",
        )

    if (
        _position(query) == "TE"
        and "outside" in query
        and re.search(r"\b(?:top\s*50|first\s*50|pick\s*50)\b", query)
        and re.search(r"\b(?:top\s*3|top-three|te1|te2|te3)\b", query)
    ):
        te = history[
            history["position"].eq("TE")
            & history["overall_pick"].gt(50)
            & history["position_finish_total"].le(3)
        ].copy()
        return _report(
            "🔥 LATE TE UPSIDE",
            f"{len(te)} VERIFIED SEASONS",
            "TEs drafted after Pick 50 who still finished top three.",
            _player_table(te),
            "This directly measures late-draft access to elite TE finishes.",
            "strategy",
        )

    # Natural-language historical analysis.
    pos = _position(query)
    n = _top_n(query)
    pool = history.copy()
    if pos:
        pool = pool[pool["position"].eq(pos)]
    pool = _apply_time_filter(pool, query)
    if n:
        pool = _top_by_finish_each_year(pool, n)

    if pool.empty:
        return _report(
            "🧠 SHIVA INTELLIGENCE",
            "I UNDERSTAND THE QUESTION — THAT SLICE HAS NO VERIFIED MATCHES",
            "The filters implied by your question returned no rows from the 2014-2025 dataset.",
            takeaway="Change the timeframe or player tier and Shiva can rerun it. The question itself is not being rejected for wording.",
        )

    metric = _infer_metric(query)
    asks_average = bool(
        re.search(r"\b(?:average|avg|mean|typically|usually|normally|on average)\b", query)
    )

    if metric == "age":
        valid = pool.dropna(subset=["age"])
        if not valid.empty:
            return _report(
                "🚨 SHIVA AGE REPORT",
                f"{valid['age'].mean():.1f} YEARS OLD",
                f"Average across {len(valid)} verified player-seasons.",
                _player_table(valid),
                "Age is calculated at September 1 of each season. Use it as context alongside role, workload and draft cost.",
            )

    if metric == "ppg":
        valid = pool.dropna(subset=["ppg"])
        if not valid.empty:
            return _report(
                "📊 SHIVA SCORING REPORT",
                f"{valid['ppg'].mean():.2f} PPG",
                f"Shiva inferred that you were asking about weekly fantasy production and calculated it from {len(valid)} matching player-seasons.",
                _player_table(valid),
                "The number comes directly from the matching Full-PPR player-seasons; the supporting rows are the evidence.",
            )

    if metric == "points":
        valid = pool.dropna(subset=["fantasy_points_ppr"])
        if not valid.empty:
            return _report(
                "📊 SHIVA SEASON SCORING REPORT",
                f"{valid['fantasy_points_ppr'].mean():.1f} PPR POINTS",
                f"Average across {len(valid)} matching player-seasons.",
                _player_table(valid),
                "This is season-long Full-PPR scoring from the verified historical sample.",
            )

    if metric == "games":
        valid = pool.dropna(subset=["games_played"])
        if not valid.empty:
            return _report(
                "📊 SHIVA AVAILABILITY REPORT",
                f"{valid['games_played'].mean():.1f} GAMES",
                f"Average games played across {len(valid)} matching player-seasons.",
                _player_table(valid),
                "Shiva interpreted the question as an availability/durability comparison rather than requiring you to say 'games played'.",
            )

    if metric == "adp":
        valid = pool.dropna(subset=["overall_pick"])
        if not valid.empty:
            return _report(
                "🎯 SHIVA DRAFT-COST REPORT",
                f"AVERAGE PICK {valid['overall_pick'].mean():.1f}",
                f"Historical draft cost across {len(valid)} matching player-seasons.",
                _player_table(valid),
                "Shiva inferred draft cost from your wording; you do not need to explicitly type 'ADP'.",
            )

    # The key behavioral change: natural football questions never hit a rigid validator wall.
    return _conversational_summary(query, pool, pos, n)
