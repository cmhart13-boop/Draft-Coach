import html
import time
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image, UnidentifiedImageError

st.set_page_config(
    page_title="Shiva Intelligence",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

import shiva_app_v3
from consistency_metrics import (
    DEFAULT_MIN_GAMES,
    DEFAULT_POINT_THRESHOLD,
    DEFAULT_PRIOR_SEASON,
    DEFAULT_RATE_THRESHOLD,
    enrich_rankings_with_consistency,
    player_consistency,
    qualified_players,
)
from joel_smyth_ppr import enrich_rankings_with_joel_ppr, render_joel_ppr_panel
from mobile_bottom_nav_fix import apply_mobile_bottom_nav_fix
from mock_draft_players_espn import render_mock_draft_room_v2 as render_espn_players_available
from streamlit_branding_fix import hide_streamlit_branding

# Keep the existing app shell and mock-draft engine. Only replace the
# Players Available presentation layer used by the Draft Coach mock room.
shiva_app_v3.render_mock_draft_room_v2 = render_espn_players_available


def _consistency_settings() -> tuple[float, int, float, int]:
    point_threshold = float(st.session_state.get("consistency_point_threshold", DEFAULT_POINT_THRESHOLD))
    min_games = int(st.session_state.get("consistency_min_games", DEFAULT_MIN_GAMES))
    rate_threshold = float(st.session_state.get("consistency_rate_threshold", DEFAULT_RATE_THRESHOLD))
    season = int(st.session_state.get("consistency_season", DEFAULT_PRIOR_SEASON))
    return point_threshold, min_games, rate_threshold, season


# Inject Joel Smyth's 2026 FULL-PPR information and Shiva's weekly consistency
# metrics into the current rankings dataframe. Because the enriched rankings are
# passed throughout shiva_app_v3, Player Profiles, Ask Shiva, Players, Cheat
# Sheets, Sleepers and Draft Coach all consume the same verified metric fields.
_original_load_rankings = shiva_app_v3.load_rankings


def _load_rankings_with_intelligence():
    rankings = enrich_rankings_with_joel_ppr(_original_load_rankings())
    weekly = shiva_app_v3.load_weekly()
    point_threshold, min_games, rate_threshold, season = _consistency_settings()
    return enrich_rankings_with_consistency(
        rankings,
        weekly,
        season=season,
        point_threshold=point_threshold,
        min_games=min_games,
        rate_threshold=rate_threshold,
    )


shiva_app_v3.load_rankings = _load_rankings_with_intelligence


# Make the consistency stat visible anywhere the common player-ranking rows are
# used. The raw hit count and percentage stay side-by-side so injury-shortened
# seasons are not confused with full-season volume.
_original_player_rows = shiva_app_v3._player_rows


def _player_rows_with_consistency(frame, weekly, limit=100, return_page="Players"):
    if frame is None or frame.empty:
        st.info("No verified players match this view.")
        return
    sort_col = "overall_rank" if "overall_rank" in frame.columns else "adp"
    frame = frame.sort_values([sort_col, "adp"], na_position="last").head(limit)
    point_threshold, min_games, rate_threshold, season = _consistency_settings()

    st.markdown(
        """
        <style>
        .player-row.consistency-row{grid-template-columns:34px minmax(0,1fr) 42px 42px 72px!important}
        .player-consistency{text-align:right;line-height:1.05}
        .player-consistency .hit{font-size:10px;font-weight:1000;color:#dfff00}
        .player-consistency .rate{font-size:8px;color:#aab7c1;margin-top:3px}
        .player-consistency .small{font-size:8px;color:#77838c}
        @media(max-width:390px){.player-row.consistency-row{grid-template-columns:29px minmax(0,1fr) 36px 38px 64px!important}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    for _, row in frame.iterrows():
        name = str(row.get("player_name") or "").strip()
        if not name:
            continue
        pid = shiva_app_v3.canonical_player_id(weekly, name)
        link = shiva_app_v3.player_link_html(pid, name, css_class="player-name", return_page=return_page)
        rank_value = pd.to_numeric(pd.Series([row.get(sort_col)]), errors="coerce").iloc[0]
        rank = int(rank_value) if pd.notna(rank_value) else "—"
        adp = pd.to_numeric(pd.Series([row.get("adp")]), errors="coerce").iloc[0]
        proj = pd.to_numeric(pd.Series([row.get("projected_points")]), errors="coerce").iloc[0]
        team = html.escape(str(row.get("team") or "—"))
        pos = str(row.get("position") or "")
        adp_text = f"{float(adp):.1f}" if pd.notna(adp) else "—"
        proj_text = f"{float(proj):.1f}" if pd.notna(proj) else "—"

        games = pd.to_numeric(pd.Series([row.get("games_played")]), errors="coerce").iloc[0]
        hits = pd.to_numeric(pd.Series([row.get("ppr_threshold_games")]), errors="coerce").iloc[0]
        rate = pd.to_numeric(pd.Series([row.get("ppr_threshold_rate")]), errors="coerce").iloc[0]
        qualified = bool(row.get("consistency_qualified")) if pd.notna(row.get("consistency_qualified")) else False
        if pd.notna(games) and pd.notna(hits) and pd.notna(rate):
            consistency_html = (
                f'<div class="player-consistency"><div class="hit">{int(hits)}/{int(games)}</div>'
                f'<div class="rate">{float(rate):.0%} ≥{point_threshold:g}</div>'
                f'<div class="small">{"QUAL" if qualified else str(season)}</div></div>'
            )
        else:
            consistency_html = '<div class="player-consistency"><div class="hit">—</div><div class="rate">15+ RATE</div></div>'

        st.markdown(
            f'<div class="player-row consistency-row"><div class="player-rank">{rank}</div>'
            f'<div>{link}<div class="player-meta">{team} &nbsp; {shiva_app_v3._pos_badge(pos)}</div></div>'
            f'<div class="player-adp">{adp_text}</div><div class="player-proj">{proj_text}</div>{consistency_html}</div>',
            unsafe_allow_html=True,
        )


shiva_app_v3._player_rows = _player_rows_with_consistency


# Put the same metric directly on every player profile. The selected profile
# season controls the calculation, so historical profiles recalculate from that
# season's weekly game log rather than reusing 2025 numbers.
_original_render_player_profile = shiva_app_v3.render_player_profile


def _render_player_profile_with_consistency(player_name, rankings, weekly, history, births=None, player_id=None, draft_state=None):
    _original_render_player_profile(player_name, rankings, weekly, history, births, player_id, draft_state)
    point_threshold, min_games, rate_threshold, default_season = _consistency_settings()
    selected_raw = st.query_params.get("season")
    try:
        selected_season = int(selected_raw) if selected_raw is not None else default_season
    except (TypeError, ValueError):
        selected_season = default_season

    metric = player_consistency(
        weekly,
        player_name,
        selected_season,
        player_id=player_id,
        point_threshold=point_threshold,
        min_games=min_games,
        rate_threshold=rate_threshold,
    )
    if not metric:
        return

    hits = int(metric["ppr_threshold_games"])
    games = int(metric["games_played"])
    rate = float(metric["ppr_threshold_rate"])
    qualified = bool(metric["consistency_qualified"])
    score = float(metric["shiva_consistency_score"])
    status = "QUALIFIES" if qualified else "BELOW LINE"
    st.markdown(
        f"""
        <div style="margin:12px 0;background:#151b20;border:1px solid #344957;border-radius:14px;padding:14px 16px;color:#fff">
          <div style="font-size:11px;color:#dfff00;font-weight:1000;letter-spacing:.04em">SHIVA CONSISTENCY • {selected_season}</div>
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px;text-align:center">
            <div><div style="font-size:22px;font-weight:1000">{hits}/{games}</div><div style="font-size:9px;color:#9faeba">GAMES ≥ {point_threshold:g} PPR</div></div>
            <div><div style="font-size:22px;font-weight:1000">{rate:.0%}</div><div style="font-size:9px;color:#9faeba">15+ HIT RATE</div></div>
            <div><div style="font-size:22px;font-weight:1000">{score:.0f}</div><div style="font-size:9px;color:#9faeba">SHIVA CONSISTENCY SCORE</div></div>
          </div>
          <div style="margin-top:10px;font-size:10px;color:#c8d2da">{status} • Default elite-consistency line: {min_games}+ games played and ≥{rate_threshold:.0%} of games at {point_threshold:g}+ PPR.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


shiva_app_v3.render_player_profile = _render_player_profile_with_consistency


# Add a dedicated consistency control/leaderboard to Draft Coach while
# preserving the existing value, position, plan and Joel Smyth PPR panels.
_original_draft_coach = shiva_app_v3._draft_coach


def _draft_coach_with_intelligence(rankings, weekly):
    st.markdown('<div class="section-head">SHIVA WEEKLY CONSISTENCY</div>', unsafe_allow_html=True)
    with st.expander("Consistency settings", expanded=False):
        c1, c2, c3 = st.columns(3, gap="small")
        with c1:
            st.number_input(
                "PPR threshold",
                min_value=5.0,
                max_value=40.0,
                step=1.0,
                value=float(st.session_state.get("consistency_point_threshold", DEFAULT_POINT_THRESHOLD)),
                key="consistency_point_threshold",
            )
        with c2:
            st.number_input(
                "Min games",
                min_value=1,
                max_value=18,
                step=1,
                value=int(st.session_state.get("consistency_min_games", DEFAULT_MIN_GAMES)),
                key="consistency_min_games",
            )
        with c3:
            st.slider(
                "Hit rate",
                min_value=0.10,
                max_value=1.00,
                step=0.05,
                value=float(st.session_state.get("consistency_rate_threshold", DEFAULT_RATE_THRESHOLD)),
                key="consistency_rate_threshold",
                format="%.0f%%",
            )
        seasons = sorted(pd.to_numeric(weekly.get("season", pd.Series(dtype=float)), errors="coerce").dropna().astype(int).unique(), reverse=True)
        if seasons:
            current = int(st.session_state.get("consistency_season", DEFAULT_PRIOR_SEASON))
            if current not in seasons:
                current = seasons[0]
            st.selectbox("Consistency season", seasons, index=seasons.index(current), key="consistency_season")

    point_threshold, min_games, rate_threshold, season = _consistency_settings()
    current_metrics = qualified_players(
        weekly,
        season,
        positions=("RB", "WR", "TE"),
        point_threshold=point_threshold,
        min_games=min_games,
        rate_threshold=rate_threshold,
    )
    if not current_metrics.empty:
        counts = current_metrics.groupby("position").size().to_dict()
        st.markdown(
            f'<div class="metric-grid"><div class="metric"><div class="metric-v">{int(counts.get("RB", 0))}</div><div class="metric-l">RB QUALIFIERS</div></div>'
            f'<div class="metric"><div class="metric-v">{int(counts.get("WR", 0))}</div><div class="metric-l">WR QUALIFIERS</div></div>'
            f'<div class="metric"><div class="metric-v">{int(counts.get("TE", 0))}</div><div class="metric-l">TE QUALIFIERS</div></div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("No verified players meet the current consistency settings.")

    _original_draft_coach(rankings, weekly)
    render_joel_ppr_panel(rankings, weekly, shiva_app_v3._player_rows)


shiva_app_v3._draft_coach = _draft_coach_with_intelligence
run = shiva_app_v3.run

hide_streamlit_branding()

APP_ROOT = Path(__file__).resolve().parent
SPLASH_PATH = APP_ROOT / "assets" / "shiva_splash.jpg"


def valid_local_image(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


if not st.session_state.get("_shiva_splash_seen", False):
    st.markdown(
        """
        <style>
        [data-testid="stAppViewBlockContainer"], .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        .stImage img {
            position: fixed !important;
            inset: 0 !important;
            width: 100vw !important;
            height: 100dvh !important;
            object-fit: cover !important;
            z-index: 999999 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if valid_local_image(SPLASH_PATH):
        try:
            st.image(str(SPLASH_PATH), use_container_width=True)
            time.sleep(2.5)
        except (UnidentifiedImageError, OSError, ValueError):
            pass

    st.session_state["_shiva_splash_seen"] = True
    st.session_state["page"] = "Home"
    st.rerun()

_original_set_page_config = st.set_page_config
st.set_page_config = lambda *args, **kwargs: None
try:
    run()
finally:
    st.set_page_config = _original_set_page_config

# Apply last so this targeted mobile override wins over older nav CSS.
apply_mobile_bottom_nav_fix()
hide_streamlit_branding()
