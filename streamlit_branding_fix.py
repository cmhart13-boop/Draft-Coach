from __future__ import annotations

import streamlit as st

from mobile_draft_layout_fix import apply_mobile_draft_layout_fix


def _patch_data_loading() -> None:
    """Install one clean rankings loader on every Streamlit rerun.

    app.py is re-executed by Streamlit, while imported modules stay cached. That
    means monkey-patched loaders can otherwise wrap previously patched loaders
    again and again. Always rebuild from the verified base loader instead.
    """
    try:
        import shiva_app_v2
        import shiva_app_v3
        from consistency_metrics import (
            DEFAULT_MIN_GAMES,
            DEFAULT_POINT_THRESHOLD,
            DEFAULT_PRIOR_SEASON,
            DEFAULT_RATE_THRESHOLD,
            enrich_rankings_with_consistency,
        )
        from joel_smyth_ppr import enrich_rankings_with_joel_ppr
    except Exception:
        return

    def _clean_rankings_loader():
        rankings = enrich_rankings_with_joel_ppr(shiva_app_v2.load_rankings())
        weekly = shiva_app_v2.load_weekly()
        point_threshold = float(st.session_state.get("consistency_point_threshold", DEFAULT_POINT_THRESHOLD))
        min_games = int(st.session_state.get("consistency_min_games", DEFAULT_MIN_GAMES))
        rate_threshold = float(st.session_state.get("consistency_rate_threshold", DEFAULT_RATE_THRESHOLD))
        season = int(st.session_state.get("consistency_season", DEFAULT_PRIOR_SEASON))
        return enrich_rankings_with_consistency(
            rankings,
            weekly,
            season=season,
            point_threshold=point_threshold,
            min_games=min_games,
            rate_threshold=rate_threshold,
        )

    shiva_app_v3.load_rankings = _clean_rankings_loader


def _patch_navigation() -> None:
    """Make page and mock-draft navigation survive Streamlit reruns."""
    try:
        import shiva_app_v3
    except Exception:
        shiva_app_v3 = None

    if shiva_app_v3 is not None:
        def _go_persistent(page: str) -> None:
            target = page if page in shiva_app_v3.PAGES else "Home"
            for key in ("player_profile_name", "player_profile_id", "player_profile_return_page"):
                st.session_state.pop(key, None)
            for key in ("player", "player_id", "return_page", "return_q", "season", "profile_tab", "favorite"):
                if key in st.query_params:
                    del st.query_params[key]
            st.session_state["page"] = target
            st.query_params["page"] = target

        shiva_app_v3._go = _go_persistent

    try:
        import mock_draft_ui_v2 as mock_ui
    except Exception:
        mock_ui = None

    if mock_ui is not None:
        def _select_mock_tab(tab_key: str) -> None:
            valid = {key for key, _ in mock_ui.TABS}
            target = str(tab_key).upper()
            if target not in valid:
                target = "PLAYERS_AVAILABLE"
            st.session_state[mock_ui.TAB_KEY] = target
            st.query_params["draft_tab"] = target
            st.session_state["page"] = "Mock Draft"

        def _tab_bar_persistent(current: str) -> str:
            st.markdown('<span class="mock-nav-marker"></span>', unsafe_allow_html=True)
            cols = st.columns(4, gap="small")
            for col, (key, label) in zip(cols, mock_ui.TABS):
                with col:
                    st.button(
                        label,
                        key=f"mock_tab_{key}",
                        use_container_width=True,
                        type="primary" if current == key else "secondary",
                        on_click=_select_mock_tab,
                        args=(key,),
                    )
            return str(st.session_state.get(mock_ui.TAB_KEY, current))

        mock_ui._tab_bar = _tab_bar_persistent

        def _set_page_home_persistent() -> None:
            st.session_state["page"] = "Home"
            st.query_params.clear()
            st.query_params["page"] = "Home"
            st.rerun()

        mock_ui._set_page_home = _set_page_home_persistent


def hide_streamlit_branding() -> None:
    """Remove Streamlit chrome and install rerun-safe app behavior."""
    _patch_data_loading()
    _patch_navigation()
    st.markdown(
        r"""
        <style>
        header,
        footer,
        #MainMenu,
        #stDecoration,
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stToolbarActions"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stStatusWidget"] *,
        [data-testid="stAppDeployButton"],
        [data-testid="stMainMenu"],
        [data-testid="stBaseButton-header"],
        [data-testid="stBaseButton-headerNoPadding"],
        .stAppDeployButton,
        .stDeployButton {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
            width: 0 !important;
            height: 0 !important;
            min-width: 0 !important;
            min-height: 0 !important;
            overflow: hidden !important;
        }

        .viewerBadge_container__1QSob,
        .styles_viewerBadge__1yB5_,
        .viewerBadge_link__1S137,
        .viewerBadge_text__1JaDK,
        [class*="viewerBadge"],
        [class*="ViewerBadge"],
        [class*="hostedWithStreamlit"],
        [class*="HostedWithStreamlit"],
        [aria-label*="Hosted with Streamlit"],
        [aria-label*="Streamlit Community Cloud"],
        [title*="Hosted with Streamlit"],
        [title*="Streamlit Community Cloud"],
        a[href*="streamlit.io/cloud"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        [data-testid="stAppViewContainer"] > header,
        [data-testid="stAppViewContainer"] > footer {
            display: none !important;
            height: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    apply_mobile_draft_layout_fix()
