from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SERVICE = ROOT / "shiva_chatgpt_service.py"
ROUTER = ROOT / "shiva_query_router.py"

# ============================================================
# APP LAYOUT
# ============================================================
text = APP.read_text(encoding="utf-8")

for old_label in ["Run Report", "Ask ChatGPT", "ASK CHATGPT", "Ask Shiva GPT"]:
    text = text.replace(
        f'submitted = st.form_submit_button("{old_label}", use_container_width=True)',
        'submitted = st.form_submit_button("ASK SHIVA GPT", use_container_width=True)',
    )

new_renderer = '''def render_report(report: dict) -> None:
    title = str(report.get("title") or "🧠 ASK SHIVA GPT").strip()
    answer = str(report.get("answer") or "").strip()
    why = str(
        report.get("why")
        or report.get("takeaway")
        or report.get("note")
        or ""
    ).strip()

    st.markdown(
        f"""
        <div style="background:linear-gradient(145deg,#17181c,#111214);border:1px solid #34363d;border-left:8px solid #31f22f;border-radius:20px;padding:24px 22px;margin:18px 0 14px;box-shadow:0 8px 28px rgba(0,0,0,.25);">
            <div style="color:#d8d8dc;font-size:13px;font-weight:900;letter-spacing:.06em;text-transform:uppercase;margin-bottom:14px;">{title}</div>
            <div style="color:#31f22f;font-size:clamp(30px,8vw,46px);line-height:1.08;font-weight:1000;letter-spacing:-.02em;white-space:pre-wrap;">{answer}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if why:
        st.markdown(
            f"""
            <div style="background:linear-gradient(145deg,#1a1d1a,#121412);border:1px solid #324232;border-radius:20px;padding:22px;margin:14px 0 22px;">
                <div style="color:#31f22f;font-size:13px;font-weight:1000;letter-spacing:.10em;text-transform:uppercase;margin-bottom:13px;">WHY</div>
                <div style="color:#f5f5f6;font-size:17px;line-height:1.55;font-weight:600;white-space:pre-wrap;">{why}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

'''

pattern = re.compile(
    r'def render_supporting_data\(report: dict\) -> None:.*?(?=st\.markdown\(\'<div class="app-title">)',
    re.DOTALL,
)
if pattern.search(text):
    text = pattern.sub(new_renderer, text, count=1)
else:
    render_only = re.compile(
        r'def render_report\(report: dict\) -> None:.*?(?=st\.markdown\(\'<div class="app-title">)',
        re.DOTALL,
    )
    if render_only.search(text):
        text = render_only.sub(new_renderer, text, count=1)

text = text.replace('<div class="hero-title">Ask Shiva</div>', '<div class="hero-title">Ask Shiva GPT</div>')
text = text.replace("ChatGPT connected for this session.", "Shiva GPT connected for this session.")
text = text.replace("Shiva is asking ChatGPT and checking the verified data...", "Shiva GPT is analyzing the verified data...")
APP.write_text(text, encoding="utf-8")

# ============================================================
# QUERY ROUTER — DRAFT COMPARISONS MUST USE CURRENT ADP FIRST
# ============================================================
router = ROUTER.read_text(encoding="utf-8")

old_comparison = '''    if len(players) > 1:
        table = pool.sort_values(["season", "player_name"], ascending=[False, True])
        if table.empty:
            return _report("⚖️ SHIVA COMPARISON", "NO MATCHING COMPARISON ROWS", "The requested players could not be matched to the selected season(s).", structured_query=structured)
        latest = table if not seasons else table[pd.to_numeric(table["season"], errors="coerce").isin(seasons)]
        scored = latest.dropna(subset=["ppg"]).copy()
        if not scored.empty:
            by_player = scored.groupby("player_name", as_index=False)["ppg"].mean().sort_values("ppg", ascending=False)
            pick = str(by_player.iloc[0]["player_name"])
            answer = f"I'D TAKE {pick.upper()}"
            note = "Among the exact players requested, Shiva compared the matching Full-PPR player-season rows."
        else:
            answer = "HERE'S THE HEAD-TO-HEAD DATA"
            note = "The comparison is limited to the verified fields available for those players."
        return _report("⚖️ SHIVA PLAYER COMPARISON", answer, note, table, "The recommendation is based only on the retrieved player records; no unrelated league-wide average was substituted.", "comparison", structured)
'''

new_comparison = '''    if len(players) > 1:
        table = pool.sort_values(["season", "player_name"], ascending=[False, True])
        q_lower = question.lower()
        is_draft_decision = bool(re.search(r"\\b(?:draft|take|pick|select|round)\\b", q_lower))

        # Draft decisions are NOT historical-PPG contests. Use current ESPN ADP
        # for the exact named players first, then let the analyst explain positional value.
        if is_draft_decision:
            current = rankings.copy()
            current["name_key"] = current["player_name"].astype(str).map(normalize_name)
            current = current[current["name_key"].isin(player_keys)].copy()
            current["adp"] = pd.to_numeric(current.get("adp"), errors="coerce")
            current = current.dropna(subset=["adp"]).sort_values("adp")

            structured["intent"] = "draft_decision"
            structured["current_adp_players"] = current["player_name"].astype(str).tolist()

            if current["name_key"].nunique() == len(player_keys):
                pick_row = current.iloc[0]
                pick = str(pick_row["player_name"])
                pick_adp = float(pick_row["adp"])
                other_rows = current[current["player_name"].ne(pick)]
                comparisons = []
                for _, r in current.iterrows():
                    comparisons.append(f"{r['player_name']} ({r.get('position', '—')}) — ESPN ADP {float(r['adp']):.1f}")
                why = (
                    f"Current ESPN ADP has {pick} at {pick_adp:.1f}, ahead of the other option(s): "
                    + "; ".join(comparisons)
                    + ". For an early-round draft decision, Shiva should follow current draft cost and positional opportunity cost rather than simply choosing whichever position historically scores more raw PPG."
                )
                combined = pd.concat([current, table], ignore_index=True, sort=False) if not table.empty else current
                return _report(
                    "⚖️ SHIVA DRAFT DECISION",
                    f"I'D TAKE {pick.upper()}",
                    why,
                    combined,
                    why,
                    "draft_decision",
                    structured,
                )

            missing = [p for p in players if normalize_name(p) not in set(current["name_key"].astype(str))]
            why = "I can compare these players historically, but I do not have verified current ESPN ADP for " + ", ".join(missing) + ". I will not fake a current draft recommendation without it."
            return _report("⚖️ SHIVA DRAFT DECISION", "CURRENT ADP DATA IS INCOMPLETE", why, table, why, "draft_decision", structured)

        if table.empty:
            return _report("⚖️ SHIVA COMPARISON", "NO MATCHING COMPARISON ROWS", "The requested players could not be matched to the selected season(s).", structured_query=structured)

        latest = table if not seasons else table[pd.to_numeric(table["season"], errors="coerce").isin(seasons)]
        scored = latest.dropna(subset=["ppg"]).copy()
        if not scored.empty:
            by_player = scored.groupby("player_name", as_index=False)["ppg"].mean().sort_values("ppg", ascending=False)
            pick = str(by_player.iloc[0]["player_name"])
            answer = f"{pick.upper()} HAD THE HIGHER VERIFIED PPG"
            detail = "; ".join(f"{r['player_name']} {float(r['ppg']):.1f} PPG" for _, r in by_player.iterrows())
            note = f"Across the exact matching player-season rows: {detail}."
        else:
            answer = "HERE'S THE HEAD-TO-HEAD DATA"
            note = "The comparison is limited to the verified fields available for those players."
        return _report("⚖️ SHIVA PLAYER COMPARISON", answer, note, table, note, "comparison", structured)
'''

if old_comparison not in router:
    raise RuntimeError("Could not locate the old comparison block in shiva_query_router.py")
router = router.replace(old_comparison, new_comparison)
ROUTER.write_text(router, encoding="utf-8")

# ============================================================
# CHATGPT SERVICE — REAL WHY, CURRENT ADP CONTEXT, NO GENERIC COPY
# ============================================================
service = SERVICE.read_text(encoding="utf-8")
service = service.replace(
    'from shiva_query_router import run_shiva_query',
    'from shiva_query_router import run_shiva_query, resolve_players',
)

service = re.sub(
    r'SYSTEM_INSTRUCTIONS = """.*?"""',
    '''SYSTEM_INSTRUCTIONS = """
You are Shiva GPT, an expert ESPN Full-PPR fantasy-football analyst embedded inside a draft application.

You must answer like a knowledgeable human fantasy analyst, not a spreadsheet and not a generic disclaimer generator.

NON-NEGOTIABLE DATA RULES:
- VERIFIED EVIDENCE supplied by the app is the source of truth for every factual statistic, ADP, finish, age, injury fact, or current-season claim.
- Never invent a number.
- Never substitute league-wide averages for a named-player question.
- For a DRAFT DECISION between named players, do NOT simply pick the player with the higher historical PPG. Prioritize current ESPN ADP, expected availability, positional opportunity cost, roster construction, and then use historical production as supporting context.
- In early rounds, explicitly consider the opportunity cost of taking QB/TE over elite RB/WR when the verified current ADP supports that distinction.
- If evidence is incomplete, say exactly what is missing, but still give the strongest football analysis supported by what is present.
- ESPN Full PPR means one point per reception.
- If evidence references the wrong player or season, ignore it.

OUTPUT FORMAT — FOLLOW EXACTLY:
FINAL ANSWER: <one clear, concise answer to the user's question>
WHY:
<2-4 specific reasons explaining the actual football decision. Cite the verified evidence naturally. Do not write a generic sentence about “based on the data.”>

STYLE:
- FINAL ANSWER must be decisive and short.
- WHY must contain the actual reasoning the user came for.
- If the user asks who to draft, say who and explain why.
- Mobile-friendly.
- Do not mention Pandas, routing, prompts, evidence objects, databases, APIs, or internal systems.
"""''',
    service,
    count=1,
    flags=re.DOTALL,
)

# Add exact current ranking rows for named players into ChatGPT evidence.
old_evidence_tail = '''    evidence = {
        "title": report.get("title", ""),
        "answer": report.get("answer", ""),
        "note": report.get("note", ""),
        "takeaway": report.get("takeaway", ""),
        "kind": report.get("kind", ""),
        "structured_query": report.get("structured_query", {}),
        "supporting_rows": _frame_to_records(report.get("table")),
    }
    return evidence, report
'''
new_evidence_tail = '''    players, _ = resolve_players(question, history, rankings)
    current_rows = pd.DataFrame()
    if players and rankings is not None and not rankings.empty:
        wanted = {p.lower() for p in players}
        current_rows = rankings[rankings["player_name"].astype(str).str.lower().isin(wanted)].copy()

    evidence = {
        "title": report.get("title", ""),
        "answer": report.get("answer", ""),
        "note": report.get("note", ""),
        "takeaway": report.get("takeaway", ""),
        "kind": report.get("kind", ""),
        "structured_query": report.get("structured_query", {}),
        "current_rankings_for_named_players": _frame_to_records(current_rows, limit=10),
        "supporting_rows": _frame_to_records(report.get("table")),
    }
    return evidence, report
'''
if old_evidence_tail in service:
    service = service.replace(old_evidence_tail, new_evidence_tail)

# Never replace a missing WHY with the generic sentence the user explicitly rejected.
service = service.replace(
    '"why": why or "This recommendation is based on the verified Shiva evidence retrieved for your question.",',
    '"why": why or str(local_report.get("takeaway") or local_report.get("note") or "").strip(),',
)
SERVICE.write_text(service, encoding="utf-8")

print("Ask Shiva GPT fixed: current-ADP draft decisions, real WHY reasoning, no generic recommendation filler.")
