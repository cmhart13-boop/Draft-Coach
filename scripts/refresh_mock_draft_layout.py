from pathlib import Path
import re

PATH = Path('mock_draft_ui.py')
text = PATH.read_text()

new_css = r'''def _css() -> None:
    st.markdown(
        """
<style>
.mock-shell{width:100%;max-width:100%;overflow-x:hidden}
.mock-topbar{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin:8px 0}
.mock-chip{background:#18191d;border:1px solid #30323a;border-radius:10px;padding:8px;min-width:0}
.mock-chip-label{color:#858790;font-size:8px;font-weight:1000;text-transform:uppercase;letter-spacing:.08em}
.mock-chip-value{color:#fff;font-size:15px;font-weight:1000;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mock-chip-value.you{color:#31f22f}
.mock-section-title{font-size:12px;font-weight:1000;color:#fff;margin:12px 0 6px}
.mock-subtle{font-size:10px;color:#929399;line-height:1.35}
.mock-list-head{display:grid;grid-template-columns:35px minmax(0,1fr) 48px 54px;gap:6px;align-items:center;padding:6px 8px;background:#15161a;border:1px solid #30323a;border-bottom:0;border-radius:12px 12px 0 0;color:#7f828b;font-size:8px;font-weight:1000;letter-spacing:.06em;text-transform:uppercase}
.mock-rank{font-size:11px;color:#a2a4ab;font-weight:900;text-align:center}
.mock-player-name{font-size:12px;color:#fff;font-weight:1000;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mock-player-meta{font-size:9px;color:#929399;line-height:1.25;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mock-pos{font-size:9px;font-weight:1000;border-radius:7px;padding:4px 5px;text-align:center;min-width:32px;display:inline-block}
.pos-qb{background:#5a2529;color:#ff9aa0}.pos-rb{background:#17472e;color:#65ff9e}.pos-wr{background:#283d78;color:#9bb2ff}.pos-te{background:#604515;color:#ffd16b}.pos-dst{background:#3b3d44;color:#e5e5e8}.pos-k{background:#4a2b5e;color:#e2afff}
.mock-rec{display:flex;gap:7px;overflow-x:auto;padding:2px 0 7px;scrollbar-width:none}.mock-rec::-webkit-scrollbar{display:none}
.mock-rec-card{flex:0 0 128px;background:#1b1c20;border:1px solid #333640;border-radius:11px;padding:8px}
.mock-board-wrap{width:100%;overflow-x:auto;overflow-y:hidden;border:1px solid #3a3c45;border-radius:14px;background:#0f1013;-webkit-overflow-scrolling:touch;box-shadow:0 8px 28px rgba(0,0,0,.22)}
.mock-board{display:grid;min-width:900px;gap:4px;padding:7px;background:linear-gradient(180deg,#111217,#0d0e11)}
.mock-board-head,.mock-board-cell{border:1px solid #30333b;border-radius:7px;min-height:68px;padding:6px;background:#181a1f}
.mock-board-head{min-height:38px;font-size:9px;font-weight:1000;text-align:center;display:flex;align-items:center;justify-content:center;background:#202229;color:#d5d6da}
.mock-board-head.mine{border-color:#31f22f;color:#31f22f;background:#152218;box-shadow:0 0 10px rgba(49,242,47,.15)}
.mock-board-cell.mine{outline:1px solid rgba(49,242,47,.45);outline-offset:-1px}
.mock-board-cell.current{box-shadow:inset 0 0 0 2px #31f22f,0 0 12px rgba(49,242,47,.32);animation:mockPulse 1.4s ease-in-out infinite}
.mock-board-cell.pos-qb{background:linear-gradient(145deg,#422126,#26171a);border-color:#6b3037}
.mock-board-cell.pos-rb{background:linear-gradient(145deg,#16442e,#11291f);border-color:#276544}
.mock-board-cell.pos-wr{background:linear-gradient(145deg,#263d76,#17244a);border-color:#3f5da4}
.mock-board-cell.pos-te{background:linear-gradient(145deg,#5a421a,#302510);border-color:#806026}
.mock-board-cell.pos-dst{background:linear-gradient(145deg,#383b43,#22242a);border-color:#51545e}
.mock-board-cell.pos-k{background:linear-gradient(145deg,#4b2d5c,#281a31);border-color:#6b427f}
.mock-pick-no{font-size:8px;color:#9a9ca4}.mock-pick-player{font-size:9px;color:#fff;font-weight:1000;line-height:1.12;margin-top:4px}.mock-pick-meta{font-size:8px;color:#c0c2c8;margin-top:3px}
.mock-board-legend{display:flex;gap:6px;flex-wrap:wrap;margin:7px 0 8px}.mock-legend-item{font-size:8px;font-weight:900;padding:4px 7px;border-radius:7px}
.mock-roster-row{display:grid;grid-template-columns:34px minmax(0,1fr);gap:7px;padding:6px 0;border-bottom:1px solid #252529}.mock-roster-slot{font-size:8px;color:#31f22f;font-weight:1000}.mock-roster-name{font-size:10px;color:#fff;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.mock-queue-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px;align-items:center}.mock-complete{background:linear-gradient(145deg,#173317,#121712);border:1px solid #31f22f;border-radius:18px;padding:18px;text-align:center;margin:12px 0}.mock-complete h2{color:#31f22f!important;margin:0}.mock-history{font-size:10px;padding:6px 0;border-bottom:1px solid #28282c;color:#ddd}.mock-controls [data-testid="stHorizontalBlock"]{gap:5px!important}.mock-view-toggle [data-testid="stHorizontalBlock"]{gap:5px!important}
@keyframes mockPulse{0%,100%{filter:brightness(1)}50%{filter:brightness(1.18)}}
button[kind="secondary"]{transition:all .12s ease}
@media(min-width:800px){.block-container{max-width:1180px!important}.mock-player-name{font-size:13px}.mock-board{min-width:980px}}
@media(max-width:430px){html,body,.stApp,.block-container{max-width:100vw!important;overflow-x:hidden!important}.mock-topbar{grid-template-columns:repeat(3,minmax(0,1fr))}.mock-chip{padding:7px 5px}.mock-chip-value{font-size:13px}.mock-list-head{grid-template-columns:30px minmax(0,1fr) 42px 48px;padding-left:6px;padding-right:6px}.mock-player-name{font-size:11px}.mock-player-meta{font-size:8px}.mock-board-wrap{max-width:calc(100vw - 24px)}}
</style>
""",
        unsafe_allow_html=True,
    )'''

text = re.sub(r'def _css\(\) -> None:.*?\n\ndef _state_key', lambda _: new_css + '\n\n\ndef _state_key', text, flags=re.S)

new_available = r'''def _render_available(state: dict[str, Any], history: pd.DataFrame, weekly: pd.DataFrame) -> None:
    st.markdown('<div class="mock-section-title">AVAILABLE PLAYERS</div>', unsafe_allow_html=True)
    st.caption('Players are stacked by 2026 rank / ADP. Tap a player name for analytics, or use Queue / Draft.')

    search = st.text_input("Search", placeholder='Search player', key='mock_search', label_visibility='collapsed')
    pos = st.segmented_control(
        "Position", ["ALL", "QB", "RB", "WR", "TE", "D/ST", "K"],
        default='ALL', key='mock_position_filter', label_visibility='collapsed'
    ) or 'ALL'

    pool = list(state['availablePlayers'])
    if search.strip():
        pool = [p for p in pool if search.lower().strip() in p['name'].lower()]
    if pos != 'ALL':
        pool = [p for p in pool if p['position'] == pos]
    pool = sorted(pool, key=lambda p: (p.get('rank', 9999), p.get('adp', 9999), p['name']))[:80]

    st.markdown(
        '<div class="mock-list-head"><div>RK</div><div>PLAYER</div><div>POS</div><div>ADP</div></div>',
        unsafe_allow_html=True,
    )

    for p in pool:
        can_draft = state['status'] == 'active' and not state['paused'] and state['currentTeam'] == state['userTeamId']
        row = st.columns([0.45, 3.65, 0.78, 0.82, 1.0, 1.0], gap='small')
        with row[0]:
            st.markdown(f'<div style="padding-top:10px;text-align:center;color:#a2a4ab;font-size:11px;font-weight:900">{p["rank"]}</div>', unsafe_allow_html=True)
        with row[1]:
            label = f"{p['name']}\n{p['team'] or '—'}" + (f" · Bye {p['bye']}" if p.get('bye') else '')
            if st.button(label, key=f"detail_{p['id']}", use_container_width=True):
                st.session_state['mock_detail_player'] = p['id']
        with row[2]:
            pos_cls = POSITION_CLASS.get(p['position'], '')
            st.markdown(f'<div style="padding-top:9px"><span class="mock-pos {pos_cls}">{html.escape(p["position"])}</span></div>', unsafe_allow_html=True)
        with row[3]:
            st.markdown(f'<div style="padding-top:11px;color:#fff;font-size:10px;font-weight:900;text-align:center">{p["adp"]:.1f}</div>', unsafe_allow_html=True)
        with row[4]:
            if st.button('＋', key=f"queue_{p['id']}", help='Add to queue', use_container_width=True):
                queue_add(state, p['id']); st.rerun()
        with row[5]:
            if st.button('DRAFT', key=f"draft_{p['id']}", use_container_width=True, disabled=not can_draft):
                make_pick(state, p['id'], source='user'); advance_cpu_until_user(state); st.rerun()

    detail_id = st.session_state.get('mock_detail_player')
    detail = get_player(state, detail_id) if detail_id else None
    if detail:
        with st.expander('Player Details', expanded=True):
            _render_player_details(detail, history, weekly)'''

text = re.sub(r'def _render_available\(.*?\n\ndef _render_queue', lambda _: new_available + '\n\n\ndef _render_queue', text, flags=re.S)

new_board = r'''def _render_board(state: dict[str, Any]) -> None:
    teams = int(state['settings']['teamsCount'])
    rounds = int(state['settings']['rounds'])
    cols_css = f"54px repeat({teams}, 96px)"

    st.markdown(
        '<div class="mock-board-legend">'
        '<span class="mock-legend-item pos-qb">QB</span>'
        '<span class="mock-legend-item pos-rb">RB</span>'
        '<span class="mock-legend-item pos-wr">WR</span>'
        '<span class="mock-legend-item pos-te">TE</span>'
        '<span class="mock-legend-item pos-dst">D/ST</span>'
        '<span class="mock-legend-item pos-k">K</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    parts = [f'<div class="mock-board" style="grid-template-columns:{cols_css}">', '<div class="mock-board-head">ROUND</div>']
    for t in state['teams']:
        parts.append(f'<div class="mock-board-head {"mine" if t["isUser"] else ""}">{html.escape(t["name"])}</div>')

    pick_map = {int(p['pickNumber']): p for p in state['picks']}
    for rnd in range(1, rounds + 1):
        parts.append(f'<div class="mock-board-head">R{rnd}</div>')
        for team_number in range(1, teams + 1):
            overall = (rnd - 1) * teams + (team_number if rnd % 2 else teams - team_number + 1)
            pick = pick_map.get(overall)
            team_id = f't{team_number}'
            mine = team_id == state['userTeamId']
            current = overall == state['currentOverallPick'] and state['status'] == 'active'
            pos_cls = POSITION_CLASS.get(pick['position'], '') if pick else ''
            cls = f'mock-board-cell {pos_cls} {"mine" if mine else ""} {"current" if current else ""}'
            if pick:
                body = (
                    f'<div class="mock-pick-no">#{overall}</div>'
                    f'<div class="mock-pick-player">{html.escape(pick["playerName"])}</div>'
                    f'<div class="mock-pick-meta">{html.escape(pick["position"])} · {html.escape(pick["nflTeam"] or "—")}</div>'
                )
            else:
                body = f'<div class="mock-pick-no">#{overall}</div>'
            parts.append(f'<div class="{cls}">{body}</div>')
    parts.append('</div>')
    st.markdown('<div class="mock-board-wrap">' + ''.join(parts) + '</div>', unsafe_allow_html=True)'''

text = re.sub(r'def _render_board\(.*?\n\ndef _render_ask_shiva', lambda _: new_board + '\n\n\ndef _render_ask_shiva', text, flags=re.S)

PATH.write_text(text)
print('Mock Draft layout refreshed: compact traditional player list + color draft board.')
