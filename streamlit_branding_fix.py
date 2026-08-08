from __future__ import annotations

import streamlit as st


def _patch_navigation() -> None:
    """Make page and mock-draft navigation survive Streamlit reruns.

    The mobile layout intentionally uses native Streamlit buttons.  Navigation
    must therefore be stored in both session state and a one-shot query param so
    a rerun cannot drop the destination and fall back to the previous screen.
    """
    try:
        import shiva_app_v3
    except Exception:
        shiva_app_v3 = None

    if shiva_app_v3 is not None:
        def _go_persistent(page: str) -> None:
            target = page if page in shiva_app_v3.PAGES else "Home"
            # Clear only player-profile routing state.  Do not clear mock-draft
            # state; switching views must keep the live draft intact.
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
            # One-shot route marker. render_mock_draft_room_v2 consumes and
            # removes it on the next render while preserving the draft state.
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

        mock_ui._set_page_home = _set_page_home_persistent


def hide_streamlit_branding() -> None:
    """Remove Streamlit chrome and install rerun-safe navigation."""
    _patch_navigation()
    st.markdown(
        r"""
        <style>
        /* Native Streamlit toolbar / status / deploy controls */
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

        /* Community Cloud viewer / Hosted-with-Streamlit badge.
           Streamlit has changed these generated class names across releases,
           so target both known names and stable substring patterns. */
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

        /* Prevent any hidden Streamlit chrome from reserving mobile space. */
        [data-testid="stAppViewContainer"] > header,
        [data-testid="stAppViewContainer"] > footer {
            display: none !important;
            height: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )