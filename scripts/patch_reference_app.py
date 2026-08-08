from pathlib import Path
import re

path = Path("app.py")
text = path.read_text()

# Imports
if "from player_profile import" not in text:
    text = text.replace(
        "from mock_draft_ui import render_mock_draft_room\n",
        "from mock_draft_ui import render_mock_draft_room\nfrom player_profile import open_player_profile, render_player_directory, render_player_profile\nfrom shiva_mobile_home import apply_mobile_shell_css, render_bottom_navigation, render_home, render_mobile_header\n",
        1,
    )

# Opponent/team context for weekly game-log profile rows.
old = '"season", "week", "season_type", "player_id", "player_display_name",\n        "player_name", "name", "position", "recent_team", "team",'
new = '"season", "week", "season_type", "player_id", "player_display_name",\n        "player_name", "name", "position", "recent_team", "team", "opponent_team", "opponent", "game_id",'
text = text.replace(old, new)

# Replace old global top-tool navigation with the mobile home / bottom-nav routing contract.
nav_start = "st.markdown('<div class=\"app-title\">SHIVA DRAFT INTELLIGENCE</div>', unsafe_allow_html=True)"
nav_end = "# Global command bar. Every page reads the same canonical draft_state.\ndraft_state = render_command_bar(rankings)"
if nav_start in text and nav_end in text:
    before, rest = text.split(nav_start, 1)
    _, after = rest.split(nav_end, 1)
    replacement = '''apply_mobile_shell_css()

# Query-parameter profile links remain supported, while in-app buttons use session state.
query_player = st.query_params.get("player") if "player" in st.query_params else None
if query_player:
    st.session_state["player_profile_name"] = str(query_player)
    st.session_state.setdefault("player_profile_return_page", "Player Profiles")
    st.session_state.page = "Player Profile"

if "page" not in st.session_state:
    st.session_state.page = "Home"
if st.session_state.page in {"Live Draft", "Grade Draft"}:
    st.session_state.page = "Mock Draft" if st.session_state.page == "Live Draft" else "Shiva Intelligence"
page = st.session_state.page

# The old always-visible command strip is intentionally hidden on the reference Home,
# Mock Draft and Player Profile screens. Existing intelligence/coach/history logic still
# reads the same centralized draft state when those tools are open.
draft_state = {}
if page in {"Shiva Intelligence", "Draft Coach", "Shiva League History"}:
    draft_state = render_command_bar(rankings)
'''
    text = before + replacement + after

# Convert main branch to include Home / Player Profiles / Player Profile.
text = text.replace('if page == "Shiva Intelligence":\n', '''if page == "Home":
    render_home(rankings, draft_state)

elif page == "Player Profiles":
    render_mobile_header("PLAYER PROFILES", "Stats & Trends", back_page="Home")
    render_player_directory(rankings, load_weekly(), history, births)

elif page == "Player Profile":
    player_name = str(st.session_state.get("player_profile_name") or "").strip()
    if not player_name:
        st.session_state.page = "Player Profiles"
        st.rerun()
    render_player_profile(player_name, rankings, load_weekly(), history, births)

elif page == "Shiva Intelligence":
    render_mobile_header("ASK SHIVA GPT", "Fantasy Intelligence", back_page="Home")
''', 1)

# Add matching headers to other top-level pages.
text = text.replace('elif page == "Draft Coach":\n    st.markdown', 'elif page == "Draft Coach":\n    render_mobile_header("MY TEAM HQ", "Draft Coach & Plan", back_page="Home")\n    st.markdown', 1)
text = text.replace('else:\n    st.markdown(\'<div class="hero"><div class="kicker">🏛️ Shiva League History', 'else:\n    render_mobile_header("LEAGUE HISTORY", "Shiva Champion League", back_page="Home")\n    st.markdown(\'<div class="hero"><div class="kicker">🏛️ Shiva League History', 1)

# Add clickable player chips below Ask Shiva whenever current ranked players are named.
old_report = '''    report = st.session_state.get("shiva_report_dynamic")
    if report:
        render_report(report)
'''
new_report = '''    report = st.session_state.get("shiva_report_dynamic")
    if report:
        render_report(report)
        report_blob = f"{report.get('answer', '')} {report.get('why', '')}".casefold()
        mentioned = [str(n) for n in rankings["player_name"].dropna().unique() if str(n).casefold() in report_blob][:8]
        if mentioned:
            st.caption("PLAYER PROFILES")
            link_cols = st.columns(min(4, len(mentioned)))
            for i, name in enumerate(mentioned):
                with link_cols[i % len(link_cols)]:
                    if st.button(name, key=f"shiva_mentioned_{i}_{name}", use_container_width=True):
                        open_player_profile(name, "Shiva Intelligence"); st.rerun()
'''
text = text.replace(old_report, new_report, 1)

# Make Draft Coach Player Fit primary names clickable while preserving the exact data/meta.
pattern = re.compile(r'''            for _, player in fits.iterrows\(\):\n                st\.markdown\(f'<div class="player-card"><div class="pos">\{player\["position"\]\}</div><div><div class="player">\{escape\(str\(player\["player_name"\]\)\)\}</div><div class="meta">ESPN ADP \{player\["adp"\]:\.1f\} · \{player\["availability"\]\}</div></div><div class="tag">\{player\["fit"\]\}</div></div>', unsafe_allow_html=True\)''')
replacement = '''            for idx, (_, player) in enumerate(fits.iterrows()):
                cols = st.columns([.7, 3.2, 1.3])
                with cols[0]:
                    st.markdown(f'<div class="pos" style="padding-top:13px">{player["position"]}</div>', unsafe_allow_html=True)
                with cols[1]:
                    if st.button(str(player["player_name"]), key=f"fit_profile_{idx}_{player['player_name']}", use_container_width=True):
                        open_player_profile(str(player["player_name"]), "Draft Coach"); st.rerun()
                    st.caption(f"ESPN ADP {player['adp']:.1f} · {player['availability']}")
                with cols[2]:
                    st.markdown(f'<div class="tag" style="padding-top:13px">{player["fit"]}</div>', unsafe_allow_html=True)'''
text = pattern.sub(replacement, text, count=1)

# Make Draft Plan selected players clickable.
pattern2 = re.compile(r'''        for _, pick in build_plan\(int\(slot\), int\(teams\), 16\)\.iterrows\(\):\n            st\.markdown\(f'<div class="player-card"><div class="pos">R\{int\(pick\["Round"\]\)\}</div><div><div class="player">\{escape\(str\(pick\["Player"\]\)\)\} \(\{pick\["Pos"\]\}\)</div><div class="meta">Pick \{int\(pick\["Pick"\]\)\} · Alternatives: \{escape\(str\(pick\["Alternatives"\] or "—"\)\)\}</div></div><div class="tag">ADP \{pick\["ADP"\]:\.1f\}</div></div>', unsafe_allow_html=True\)''')
replacement2 = '''        for idx, (_, pick) in enumerate(build_plan(int(slot), int(teams), 16).iterrows()):
            cols = st.columns([.7, 3.3, 1.2])
            with cols[0]: st.markdown(f'<div class="pos" style="padding-top:13px">R{int(pick["Round"])}</div>', unsafe_allow_html=True)
            with cols[1]:
                if st.button(f"{pick['Player']} ({pick['Pos']})", key=f"plan_profile_{idx}_{pick['Player']}", use_container_width=True):
                    open_player_profile(str(pick["Player"]), "Draft Coach"); st.rerun()
                st.caption(f"Pick {int(pick['Pick'])} · Alternatives: {pick['Alternatives'] or '—'}")
            with cols[2]: st.markdown(f'<div class="tag" style="padding-top:13px">ADP {pick["ADP"]:.1f}</div>', unsafe_allow_html=True)'''
text = pattern2.sub(replacement2, text, count=1)

# Make League History player names clickable.
old_history = '''    for _, pick in result.sort_values(["season", "round", "overall_pick"], ascending=[False, True, True]).head(200).iterrows():
        ppg = f"{float(pick['ppg']):.1f} PPG" if pd.notna(pick.get("ppg")) else "—"
        finish = pick.get("position_finish_total")
        finish_text = int(finish) if pd.notna(finish) else "—"
        st.markdown(f'<div class="player-card"><div class="pos">R{int(pick["round"])}</div><div><div class="player">{escape(str(pick["player_name"]))} ({pick["position"]})</div><div class="meta">{int(pick["season"])} · {escape(str(pick["league_name"]))} · Pick {int(pick["overall_pick"])} · Final {finish_text}</div></div><div class="tag">{ppg}</div></div>', unsafe_allow_html=True)
'''
new_history = '''    for idx, (_, pick) in enumerate(result.sort_values(["season", "round", "overall_pick"], ascending=[False, True, True]).head(200).iterrows()):
        ppg = f"{float(pick['ppg']):.1f} PPG" if pd.notna(pick.get("ppg")) else "—"
        finish = pick.get("position_finish_total")
        finish_text = int(finish) if pd.notna(finish) else "—"
        cols = st.columns([.7, 3.3, 1.2])
        with cols[0]: st.markdown(f'<div class="pos" style="padding-top:13px">R{int(pick["round"])}</div>', unsafe_allow_html=True)
        with cols[1]:
            if st.button(f"{pick['player_name']} ({pick['position']})", key=f"history_player_{idx}_{pick['player_name']}", use_container_width=True):
                open_player_profile(str(pick["player_name"]), "Shiva League History"); st.rerun()
            st.caption(f"{int(pick['season'])} · {pick['league_name']} · Pick {int(pick['overall_pick'])} · Final {finish_text}")
        with cols[2]: st.markdown(f'<div class="tag" style="padding-top:13px">{ppg}</div>', unsafe_allow_html=True)
'''
text = text.replace(old_history, new_history, 1)

# Keep ESPN news on Intelligence where it belongs instead of appending it under every screen.
news_marker = "# Preserve the existing ESPN news service and last-good cache."
if news_marker in text and "if page == \"Shiva Intelligence\":\n    # Preserve the existing ESPN news service" not in text:
    before, news = text.split(news_marker, 1)
    news_block = news_marker + news
    indented = "\n".join(("    " + line) if line.strip() else line for line in news_block.splitlines())
    text = before.rstrip() + '\n\nif page == "Shiva Intelligence":\n' + indented + '\n\nrender_bottom_navigation(page)\n'
elif "render_bottom_navigation(page)" not in text:
    text += "\n\nrender_bottom_navigation(page)\n"

path.write_text(text)
print("Reference home/navigation/player-profile integration applied.")
