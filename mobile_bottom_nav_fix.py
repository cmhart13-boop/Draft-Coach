from __future__ import annotations

import streamlit as st


def apply_mobile_bottom_nav_fix() -> None:
    """Apply the reference-driven mobile shell without replacing any existing callbacks or state."""
    st.markdown(
        r"""
<style>
/* ============================================================
   SHIVA MOBILE SHELL
   Presentation-only override. Existing state, callbacks and pages stay intact.
   ============================================================ */

html, body, .stApp {
    background: #02070b !important;
    overflow-x: hidden !important;
}

[data-testid="stAppViewBlockContainer"],
.block-container {
    width: 100% !important;
    max-width: 520px !important;
    margin: 0 auto !important;
    padding: 16px 14px 112px !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

/* ---------- HOME HEADER ---------- */
.app-head {
    display: flex !important;
    align-items: flex-end !important;
    justify-content: space-between !important;
    min-height: 96px !important;
    padding: 18px 4px 14px !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}

.app-head::after {
    content: "☰  ♧";
    color: #f3f5f7;
    font-size: 27px;
    line-height: 1;
    letter-spacing: 5px;
    padding-bottom: 4px;
    white-space: nowrap;
}

.app-head .brand {
    color: #dfff00 !important;
    font-size: 22px !important;
    line-height: 1.05 !important;
    font-weight: 1000 !important;
    font-style: italic !important;
    letter-spacing: .095em !important;
    white-space: nowrap !important;
}

.app-head .brand-sub {
    color: #e2e5e8 !important;
    font-size: 13px !important;
    line-height: 1.2 !important;
    margin-top: 8px !important;
}

/* ============================================================
   HOME ACTIONS
   Flatten the existing two Streamlit columns into the exact 3/2/1 mobile grid.
   No callbacks are replaced: these are still the same st.button controls.
   ============================================================ */

@media (max-width: 520px) {
    div[data-testid="stHorizontalBlock"]:has(.st-key-home_draft):has(.st-key-home_players) {
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        grid-template-rows: 136px 136px 82px !important;
        gap: 10px !important;
        width: 100% !important;
        margin: 4px 0 18px !important;
        align-items: stretch !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.st-key-home_draft):has(.st-key-home_players) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(.st-key-home_draft):has(.st-key-home_players) > div[data-testid="stColumn"] > div,
    div[data-testid="stHorizontalBlock"]:has(.st-key-home_draft):has(.st-key-home_players) > div[data-testid="stColumn"] [data-testid="stVerticalBlock"] {
        display: contents !important;
    }

    .st-key-home_draft   { grid-column: 1 !important; grid-row: 1 !important; }
    .st-key-home_players { grid-column: 2 !important; grid-row: 1 !important; }
    .st-key-home_team    { grid-column: 3 !important; grid-row: 1 !important; }
    .st-key-home_sleepers{ grid-column: 1 !important; grid-row: 2 !important; }
    .st-key-home_cheats  { grid-column: 2 !important; grid-row: 2 !important; }
    .st-key-home_shiva   { grid-column: 1 / -1 !important; grid-row: 3 !important; }

    .st-key-home_draft,
    .st-key-home_players,
    .st-key-home_team,
    .st-key-home_sleepers,
    .st-key-home_cheats,
    .st-key-home_shiva,
    .st-key-home_draft [data-testid="stButton"],
    .st-key-home_players [data-testid="stButton"],
    .st-key-home_team [data-testid="stButton"],
    .st-key-home_sleepers [data-testid="stButton"],
    .st-key-home_cheats [data-testid="stButton"],
    .st-key-home_shiva [data-testid="stButton"] {
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .st-key-home_draft button,
    .st-key-home_players button,
    .st-key-home_team button,
    .st-key-home_sleepers button,
    .st-key-home_cheats button {
        width: 100% !important;
        height: 136px !important;
        min-height: 136px !important;
        padding: 14px 7px 12px !important;
        border-radius: 15px !important;
        border-width: 2px !important;
        border-style: solid !important;
        box-shadow: none !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
        touch-action: manipulation !important;
        -webkit-tap-highlight-color: transparent !important;
        overflow: hidden !important;
    }

    .st-key-home_draft button   { background: #171206 !important; border-color: #f39a18 !important; }
    .st-key-home_players button { background: #071821 !important; border-color: #39b5de !important; }
    .st-key-home_team button    { background: #0b1b0b !important; border-color: #58cc35 !important; }
    .st-key-home_sleepers button{ background: #171206 !important; border-color: #f39a18 !important; }
    .st-key-home_cheats button  { background: #1b0b14 !important; border-color: #e64d88 !important; }

    .st-key-home_draft button p,
    .st-key-home_players button p,
    .st-key-home_team button p,
    .st-key-home_sleepers button p,
    .st-key-home_cheats button p {
        font-size: 0 !important;
        line-height: 1 !important;
        margin: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .st-key-home_draft button p::before,
    .st-key-home_players button p::before,
    .st-key-home_team button p::before,
    .st-key-home_sleepers button p::before,
    .st-key-home_cheats button p::before {
        display: block !important;
        font-family: "Apple Color Emoji", "Segoe UI Emoji", sans-serif !important;
        font-size: 38px !important;
        line-height: 42px !important;
        font-weight: 400 !important;
        margin-bottom: 8px !important;
    }

    .st-key-home_draft button p::after,
    .st-key-home_players button p::after,
    .st-key-home_team button p::after,
    .st-key-home_sleepers button p::after,
    .st-key-home_cheats button p::after {
        display: block !important;
        color: #f7f7f7 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif !important;
        font-size: 13px !important;
        line-height: 17px !important;
        font-weight: 950 !important;
        text-align: center !important;
        white-space: pre-line !important;
    }

    .st-key-home_draft button p::before { content: "🏆"; }
    .st-key-home_draft button p::after { content: "DRAFT BOARD\A Mock Drafts • 2026 Rankings"; }
    .st-key-home_players button p::before { content: "👤"; }
    .st-key-home_players button p::after { content: "PLAYER PROFILES\A Stats & Trends"; }
    .st-key-home_team button p::before { content: "⭐"; }
    .st-key-home_team button p::after { content: "MY TEAM IQ\A League • Manager • Year"; }
    .st-key-home_sleepers button p::before { content: "🥷"; }
    .st-key-home_sleepers button p::after { content: "SLEEPERS\A Hidden Gems"; }
    .st-key-home_cheats button p::before { content: "📋"; }
    .st-key-home_cheats button p::after { content: "CHEAT SHEETS\A Key Rankings"; }

    /* Wide Ask Shiva card */
    .st-key-home_shiva button {
        width: 100% !important;
        height: 82px !important;
        min-height: 82px !important;
        border-radius: 14px !important;
        border: 1.5px solid #1976a7 !important;
        background: #061c2b !important;
        box-shadow: none !important;
        padding: 8px 18px !important;
        touch-action: manipulation !important;
        -webkit-tap-highlight-color: transparent !important;
    }

    .st-key-home_shiva button p {
        position: relative !important;
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        padding: 0 30px 0 50px !important;
        box-sizing: border-box !important;
        font-size: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }

    .st-key-home_shiva button p::before {
        content: "🤖";
        position: absolute !important;
        left: 0 !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        font-size: 31px !important;
        line-height: 1 !important;
    }

    .st-key-home_shiva button p::after {
        content: "ASK SHIVA GPT\A Ask questions, get advice, win your league.   ›";
        white-space: pre-line !important;
        color: #f7f7f7 !important;
        font-size: 14px !important;
        line-height: 22px !important;
        font-weight: 900 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif !important;
    }
}

/* ---------- HOME LEAGUE + NEWS ---------- */
.section-head {
    color: #dfff00 !important;
    font-size: 16px !important;
    line-height: 1.2 !important;
    font-weight: 1000 !important;
    margin: 27px 4px 11px !important;
}

.iq-card {
    background: #071722 !important;
    border: 1px solid #27445a !important;
    border-radius: 13px !important;
    box-shadow: none !important;
    padding: 18px !important;
}

.iq-name { font-size: 17px !important; font-weight: 950 !important; }
.iq-meta { font-size: 11px !important; color: #b7c0c8 !important; margin-top: 8px !important; }

.news-link {
    background: #071722 !important;
    border: 1px solid #27445a !important;
    border-radius: 12px !important;
    padding: 13px 14px !important;
    margin: 8px 0 !important;
    box-shadow: none !important;
}
.news-title { font-size: 13px !important; line-height: 1.3 !important; }
.news-desc { font-size: 10.5px !important; line-height: 1.45 !important; }
.news-open { color: #55a8ff !important; }

/* ============================================================
   FIXED BOTTOM NAV — 5 across, large mobile touch targets
   ============================================================ */
.st-key-app_bottom_nav {
    position: fixed !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    transform: none !important;
    width: 100vw !important;
    max-width: none !important;
    min-height: 88px !important;
    z-index: 2147483000 !important;
    background: #03080c !important;
    border-top: 1px solid #1d3446 !important;
    padding: 6px 5px max(8px, env(safe-area-inset-bottom)) !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}

.st-key-app_bottom_nav > div,
.st-key-app_bottom_nav [data-testid="stVerticalBlock"] {
    width: 100% !important;
    max-width: none !important;
    padding: 0 !important;
    margin: 0 !important;
    gap: 0 !important;
}

.st-key-app_bottom_nav div[data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    align-items: stretch !important;
    gap: 2px !important;
    width: 100% !important;
    min-width: 0 !important;
    flex-wrap: nowrap !important;
}

.st-key-app_bottom_nav div[data-testid="stColumn"] {
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    flex: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

.st-key-app_bottom_nav [data-testid="stButton"] { width: 100% !important; }

.st-key-app_bottom_nav button {
    width: 100% !important;
    min-width: 0 !important;
    height: 68px !important;
    min-height: 68px !important;
    padding: 2px 1px !important;
    margin: 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    color: #aeb5bc !important;
    overflow: hidden !important;
    touch-action: manipulation !important;
    -webkit-tap-highlight-color: transparent !important;
}

.st-key-app_bottom_nav button[kind="primary"] { background: transparent !important; }

.st-key-app_bottom_nav button p {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 4px !important;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    font-size: 0 !important;
    line-height: 1 !important;
    white-space: nowrap !important;
}

.st-key-app_bottom_nav button p::before {
    display: block !important;
    color: #b7bec5 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI Symbol", "Segoe UI", sans-serif !important;
    font-size: 28px !important;
    line-height: 29px !important;
    font-weight: 500 !important;
}

.st-key-app_bottom_nav button p::after {
    display: block !important;
    color: #b7bec5 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif !important;
    font-size: 10.5px !important;
    line-height: 13px !important;
    font-weight: 750 !important;
}

.st-key-bottom_Home button p::before { content: "⌂"; }
.st-key-bottom_Home button p::after { content: "Home"; }
.st-key-bottom_Mock_Draft button p::before { content: "⊙"; }
.st-key-bottom_Mock_Draft button p::after { content: "Draft"; }
.st-key-bottom_Players button p::before { content: "♙"; }
.st-key-bottom_Players button p::after { content: "Players"; }
.st-key-bottom_League_History button p::before { content: "♧"; }
.st-key-bottom_League_History button p::after { content: "Team IQ"; }
.st-key-bottom_Draft_Coach button p::before { content: "•••"; font-size: 26px !important; letter-spacing: 2px !important; }
.st-key-bottom_Draft_Coach button p::after { content: "Coach"; }

.st-key-app_bottom_nav button[kind="primary"] p::before,
.st-key-app_bottom_nav button[kind="primary"] p::after {
    color: #dfff00 !important;
}

@media (max-width: 390px) {
    [data-testid="stAppViewBlockContainer"], .block-container {
        padding-left: 10px !important;
        padding-right: 10px !important;
    }
    .app-head .brand { font-size: 19px !important; }
    .app-head .brand-sub { font-size: 11.5px !important; }
    div[data-testid="stHorizontalBlock"]:has(.st-key-home_draft):has(.st-key-home_players) {
        grid-template-rows: 126px 126px 78px !important;
        gap: 8px !important;
    }
    .st-key-home_draft button,
    .st-key-home_players button,
    .st-key-home_team button,
    .st-key-home_sleepers button,
    .st-key-home_cheats button { height: 126px !important; min-height: 126px !important; }
    .st-key-home_shiva button { height: 78px !important; min-height: 78px !important; }
    .st-key-home_draft button p::after,
    .st-key-home_players button p::after,
    .st-key-home_team button p::after,
    .st-key-home_sleepers button p::after,
    .st-key-home_cheats button p::after { font-size: 11.5px !important; line-height: 15px !important; }
    .st-key-app_bottom_nav button p::before { font-size: 26px !important; }
    .st-key-app_bottom_nav button p::after { font-size: 10px !important; }
}
</style>
""",
        unsafe_allow_html=True,
    )
