from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

DEFAULT_POINT_THRESHOLD = 15.0
DEFAULT_MIN_GAMES = 10
DEFAULT_RATE_THRESHOLD = 0.50
DEFAULT_PRIOR_SEASON = 2025


@dataclass(frozen=True)
class ConsistencyConfig:
    point_threshold: float = DEFAULT_POINT_THRESHOLD
    min_games: int = DEFAULT_MIN_GAMES
    rate_threshold: float = DEFAULT_RATE_THRESHOLD
    season: int = DEFAULT_PRIOR_SEASON


def _name_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def _name_col(df: pd.DataFrame) -> str | None:
    for col in ("player_display_name", "player_name", "display_name", "name"):
        if col in df.columns:
            return col
    return None


def _ppr_points(frame: pd.DataFrame) -> pd.Series:
    """Return ESPN full-PPR fantasy points without inventing missing data."""
    if frame is None or frame.empty:
        return pd.Series(dtype=float)
    if "fantasy_points_ppr" in frame.columns:
        stored = pd.to_numeric(frame["fantasy_points_ppr"], errors="coerce")
        if stored.notna().any():
            return stored

    scoring = {
        "passing_yards": 0.04,
        "passing_tds": 4.0,
        "interceptions": -2.0,
        "rushing_yards": 0.1,
        "rushing_tds": 6.0,
        "receptions": 1.0,
        "receiving_yards": 0.1,
        "receiving_tds": 6.0,
        "fumbles_lost": -2.0,
        "passing_two_point_conversions": 2.0,
        "rushing_two_point_conversions": 2.0,
        "receiving_two_point_conversions": 2.0,
    }
    available = [c for c in scoring if c in frame.columns]
    if not available:
        return pd.Series(index=frame.index, dtype=float)

    points = pd.Series(0.0, index=frame.index)
    has_any = pd.Series(False, index=frame.index)
    for col in available:
        values = pd.to_numeric(frame[col], errors="coerce")
        has_any |= values.notna()
        points = points.add(values.fillna(0.0) * scoring[col], fill_value=0.0)
    return points.where(has_any)


def regular_season_weekly(weekly: pd.DataFrame, season: int | None = None) -> pd.DataFrame:
    if weekly is None or weekly.empty:
        return pd.DataFrame()
    out = weekly.copy()
    if season is not None and "season" in out.columns:
        out = out.loc[pd.to_numeric(out["season"], errors="coerce").eq(int(season))].copy()
    if "season_type" in out.columns and not out.empty:
        regular = out["season_type"].astype(str).str.upper().isin(["REG", "REGULAR", "REGULAR SEASON"])
        if regular.any():
            out = out.loc[regular].copy()
    if "week" in out.columns and not out.empty:
        weeks = pd.to_numeric(out["week"], errors="coerce")
        out = out.loc[weeks.between(1, 18)].copy()
    return out


def season_consistency(
    weekly: pd.DataFrame,
    season: int,
    *,
    point_threshold: float = DEFAULT_POINT_THRESHOLD,
    min_games: int = DEFAULT_MIN_GAMES,
    rate_threshold: float = DEFAULT_RATE_THRESHOLD,
) -> pd.DataFrame:
    """One row per player for a season, based on verified weekly PPR rows."""
    frame = regular_season_weekly(weekly, season)
    name_col = _name_col(frame)
    if frame.empty or not name_col:
        return pd.DataFrame(
            columns=[
                "player_name", "season", "position", "games_played", "ppr_threshold",
                "ppr_threshold_games", "ppr_threshold_rate", "consistency_qualified",
                "shiva_consistency_score",
            ]
        )

    frame = frame.copy()
    frame["_player_name"] = frame[name_col].astype(str).str.strip()
    frame["_name_key"] = frame["_player_name"].map(_name_key)
    frame["_ppr_points"] = _ppr_points(frame)
    frame = frame.loc[frame["_name_key"].ne("") & frame["_ppr_points"].notna()].copy()
    if frame.empty:
        return pd.DataFrame()

    position_col = "position" if "position" in frame.columns else None
    rows: list[dict[str, object]] = []
    for _, group in frame.groupby("_name_key", sort=False):
        games = int(group["_ppr_points"].count())
        hits = int(group["_ppr_points"].ge(float(point_threshold)).sum())
        rate = float(hits / games) if games else 0.0
        pos = ""
        if position_col:
            vals = group[position_col].dropna().astype(str).str.upper()
            if not vals.empty:
                pos = vals.iloc[-1]
        rows.append(
            {
                "player_name": group["_player_name"].iloc[-1],
                "_name_key": group["_name_key"].iloc[-1],
                "season": int(season),
                "position": pos,
                "games_played": games,
                "ppr_threshold": float(point_threshold),
                "ppr_threshold_games": hits,
                "ppr_threshold_rate": rate,
                "consistency_qualified": bool(games >= int(min_games) and rate >= float(rate_threshold)),
                "shiva_consistency_score": round(rate * 100.0, 1),
            }
        )
    return pd.DataFrame(rows)


def enrich_rankings_with_consistency(
    rankings: pd.DataFrame,
    weekly: pd.DataFrame,
    *,
    season: int = DEFAULT_PRIOR_SEASON,
    point_threshold: float = DEFAULT_POINT_THRESHOLD,
    min_games: int = DEFAULT_MIN_GAMES,
    rate_threshold: float = DEFAULT_RATE_THRESHOLD,
) -> pd.DataFrame:
    """Attach consistency columns safely, even if Streamlit reruns enrichment."""
    if rankings is None:
        return pd.DataFrame()
    out = rankings.copy()
    if out.empty or "player_name" not in out.columns:
        return out

    metrics = season_consistency(
        weekly,
        season,
        point_threshold=point_threshold,
        min_games=min_games,
        rate_threshold=rate_threshold,
    )
    if metrics.empty:
        return out

    metric_cols = [
        "consistency_season", "games_played", "ppr_threshold", "ppr_threshold_games",
        "ppr_threshold_rate", "consistency_qualified", "shiva_consistency_score",
    ]
    # Streamlit reruns app.py. The app may therefore call this function on a
    # dataframe that was already enriched during an earlier wrapper call. Drop
    # those derived fields before merging so pandas never creates _x/_y suffix
    # collisions or raises MergeError.
    out.drop(columns=[c for c in metric_cols if c in out.columns], inplace=True, errors="ignore")
    out.drop(columns=["_name_key"], inplace=True, errors="ignore")
    out["_name_key"] = out["player_name"].map(_name_key)

    cols = [
        "_name_key", "season", "games_played", "ppr_threshold", "ppr_threshold_games",
        "ppr_threshold_rate", "consistency_qualified", "shiva_consistency_score",
    ]
    metrics = metrics[cols].rename(columns={"season": "consistency_season"})
    metrics = metrics.drop_duplicates(subset=["_name_key"], keep="last")
    out = out.merge(metrics, on="_name_key", how="left", validate="m:1")
    out.drop(columns=["_name_key"], inplace=True, errors="ignore")
    return out


def player_consistency(
    weekly: pd.DataFrame,
    player_name: str,
    season: int,
    *,
    player_id: str | None = None,
    point_threshold: float = DEFAULT_POINT_THRESHOLD,
    min_games: int = DEFAULT_MIN_GAMES,
    rate_threshold: float = DEFAULT_RATE_THRESHOLD,
) -> dict[str, object]:
    frame = regular_season_weekly(weekly, season)
    if frame.empty:
        return {}

    selected = pd.DataFrame()
    if player_id and "player_id" in frame.columns and not str(player_id).startswith("name::"):
        selected = frame.loc[frame["player_id"].astype(str).eq(str(player_id))].copy()
    if selected.empty:
        name_col = _name_col(frame)
        if name_col:
            selected = frame.loc[frame[name_col].map(_name_key).eq(_name_key(player_name))].copy()
    if selected.empty:
        return {}

    points = _ppr_points(selected).dropna()
    games = int(points.count())
    hits = int(points.ge(float(point_threshold)).sum())
    rate = float(hits / games) if games else 0.0
    return {
        "season": int(season),
        "games_played": games,
        "ppr_threshold": float(point_threshold),
        "ppr_threshold_games": hits,
        "ppr_threshold_rate": rate,
        "consistency_qualified": bool(games >= int(min_games) and rate >= float(rate_threshold)),
        "shiva_consistency_score": round(rate * 100.0, 1),
    }


def qualified_players(
    weekly: pd.DataFrame,
    season: int,
    *,
    positions: tuple[str, ...] = ("RB", "WR", "TE"),
    point_threshold: float = DEFAULT_POINT_THRESHOLD,
    min_games: int = DEFAULT_MIN_GAMES,
    rate_threshold: float = DEFAULT_RATE_THRESHOLD,
) -> pd.DataFrame:
    metrics = season_consistency(
        weekly,
        season,
        point_threshold=point_threshold,
        min_games=min_games,
        rate_threshold=rate_threshold,
    )
    if metrics.empty:
        return metrics
    wanted = {str(p).upper() for p in positions}
    out = metrics.loc[
        metrics["position"].astype(str).str.upper().isin(wanted)
        & metrics["consistency_qualified"].fillna(False)
    ].copy()
    return out.sort_values(
        ["position", "ppr_threshold_rate", "ppr_threshold_games", "games_played"],
        ascending=[True, False, False, False],
    )