from __future__ import annotations

import re
from typing import Any

import pandas as pd
import streamlit as st

# Joel Smyth's 2026 FULL-PPR board only. Half-PPR, dynasty, kicker and DST
# material from the source guide is intentionally excluded from this module.
PPR_BIG_BOARD = [
    "Jahmyr Gibbs", "Bijan Robinson", "Ja'Marr Chase", "Puka Nacua", "Christian McCaffrey",
    "Amon-Ra St. Brown", "Jaxon Smith-Njigba", "Jonathan Taylor", "James Cook III", "CeeDee Lamb",
    "Omarion Hampton", "Ashton Jeanty", "Justin Jefferson", "Chase Brown", "Kenneth Walker III",
    "Saquon Barkley", "Drake London", "De'Von Achane", "Brock Bowers", "A.J. Brown",
    "George Pickens", "Rashee Rice", "Nico Collins", "Derrick Henry", "Trey McBride",
    "Jeremiyah Love", "DeVonta Smith", "Malik Nabers", "Josh Allen", "Chris Olave",
    "Josh Jacobs", "Tee Higgins", "Breece Hall", "Jaylen Waddle", "Zay Flowers",
    "Kyren Williams", "Tetairoa McMillan", "Emeka Egbuka", "Luther Burden III", "Colston Loveland",
    "Javonte Williams", "Garrett Wilson", "Ladd McConkey", "DJ Moore", "Cam Skattebo",
    "Bucky Irving", "Travis Etienne Jr.", "Tyler Warren", "Terry McLaurin", "Lamar Jackson",
    "Rome Odunze", "Davante Adams", "David Montgomery", "Christian Watson", "Bhayshul Tuten",
    "D'Andre Swift", "TreVeyon Henderson", "Quinshon Judkins", "Drake Maye", "Jayden Daniels",
    "Mike Evans", "Parker Washington", "Joe Burrow", "Jalen Hurts", "Jameson Williams",
    "Carnell Tate", "Brian Thomas Jr.", "Chuba Hubbard", "Jadarian Price", "Sam LaPorta",
    "Harold Fannin Jr.", "Marvin Harrison Jr.", "Jordyn Tyson", "Alec Pierce", "Rhamondre Stevenson",
    "Tucker Kraft", "Caleb Williams", "Justin Herbert", "Trevor Lawrence", "Jaylen Warren",
    "Rico Dowdle", "RJ Harvey", "Kyle Pitts Sr.", "Makai Lemon", "Michael Wilson",
    "Jaxson Dart", "Brock Purdy", "Dak Prescott", "Chris Godwin Jr.", "Tony Pollard",
    "Jonathon Brooks", "Blake Corum", "DK Metcalf", "George Kittle", "Josh Downs",
    "Stefon Diggs", "Courtland Sutton", "Kyle Monangai", "Rachaad White", "J.K. Dobbins",
    "Dalton Kincaid", "Bo Nix", "Patrick Mahomes II", "Matthew Stafford", "Kyler Murray",
    "Jared Goff", "Deebo Samuel Sr.", "Quentin Johnston", "Jordan Addison", "Malik Willis",
    "Jakobi Meyers", "Michael Pittman Jr.", "Kenny Gainwell", "Jordan Mason", "Jacory Croskey-Merritt",
    "Dallas Goedert", "Mark Andrews", "Tyler Shough", "Zach Charbonnet", "Chris Rodriguez Jr.",
    "Jayden Reed", "Romeo Doubs", "Isaiah Likely", "Matthew Golden", "Aaron Jones Sr.",
    "Baker Mayfield", "Jake Ferguson", "Jordan Love", "Keaton Mitchell", "Travis Kelce",
    "Isiah Pacheco", "Cam Ward", "Tank Bigsby", "Tyler Allgeier", "De'Zhaun Stribling",
    "Wan'Dale Robinson", "Xavier Worthy", "Oronde Gadsden II", "Alvin Kamara", "Ray Davis",
    "Chig Okonkwo", "Tyrone Tracy Jr.", "Sam Darnold", "Woody Marks", "Jayden Higgins",
    "KC Concepcion", "Travis Hunter", "Tre Tucker", "Tyjae Spears", "Bryce Young",
]

PPR_POSITION_RANKS: dict[str, dict[str, int]] = {
    "RB": {name: i + 1 for i, name in enumerate([
        "Jahmyr Gibbs", "Bijan Robinson", "Christian McCaffrey", "Jonathan Taylor", "James Cook III",
        "Omarion Hampton", "Ashton Jeanty", "Chase Brown", "Kenneth Walker III", "Saquon Barkley",
        "De'Von Achane", "Derrick Henry", "Jeremiyah Love", "Josh Jacobs", "Breece Hall", "Kyren Williams",
        "Javonte Williams", "Cam Skattebo", "Bucky Irving", "Travis Etienne Jr.", "David Montgomery",
        "Bhayshul Tuten", "D'Andre Swift", "TreVeyon Henderson", "Quinshon Judkins", "Chuba Hubbard",
        "Jadarian Price", "Rhamondre Stevenson", "Jaylen Warren", "Rico Dowdle", "RJ Harvey", "Tony Pollard",
        "Jonathon Brooks", "Blake Corum", "Kyle Monangai", "Rachaad White", "J.K. Dobbins", "Kenny Gainwell",
        "Jordan Mason", "Jacory Croskey-Merritt", "Zach Charbonnet", "Chris Rodriguez Jr.", "Aaron Jones Sr.",
        "Keaton Mitchell", "Isiah Pacheco", "Tank Bigsby", "Tyler Allgeier", "Alvin Kamara", "Ray Davis",
        "Tyrone Tracy Jr.", "Woody Marks", "Tyjae Spears", "Jonah Coleman", "Brian Robinson Jr.", "Emmett Johnson",
        "Dylan Sampson", "Mike Washington Jr.", "Jaydon Blue", "Isaiah Davis", "Ollie Gordon II",
    ])},
    "WR": {name: i + 1 for i, name in enumerate([
        "Ja'Marr Chase", "Puka Nacua", "Amon-Ra St. Brown", "Jaxon Smith-Njigba", "CeeDee Lamb", "Justin Jefferson",
        "Drake London", "A.J. Brown", "George Pickens", "Rashee Rice", "Nico Collins", "DeVonta Smith", "Malik Nabers",
        "Chris Olave", "Tee Higgins", "Jaylen Waddle", "Zay Flowers", "Tetairoa McMillan", "Emeka Egbuka",
        "Luther Burden III", "Garrett Wilson", "Ladd McConkey", "DJ Moore", "Terry McLaurin", "Rome Odunze",
        "Davante Adams", "Christian Watson", "Mike Evans", "Parker Washington", "Jameson Williams", "Carnell Tate",
        "Brian Thomas Jr.", "Marvin Harrison Jr.", "Jordyn Tyson", "Alec Pierce", "Makai Lemon", "Michael Wilson",
        "Chris Godwin Jr.", "DK Metcalf", "Josh Downs", "Stefon Diggs", "Courtland Sutton", "Deebo Samuel Sr.",
        "Quentin Johnston", "Jordan Addison", "Jakobi Meyers", "Michael Pittman Jr.", "Jayden Reed", "Romeo Doubs",
        "Matthew Golden", "De'Zhaun Stribling", "Wan'Dale Robinson", "Xavier Worthy", "Jayden Higgins", "KC Concepcion",
        "Travis Hunter", "Tre Tucker", "Jalen Coker", "Rashid Shaheed", "Khalil Shakir",
    ])},
    "QB": {name: i + 1 for i, name in enumerate([
        "Josh Allen", "Lamar Jackson", "Drake Maye", "Jayden Daniels", "Joe Burrow", "Jalen Hurts", "Caleb Williams",
        "Justin Herbert", "Trevor Lawrence", "Jaxson Dart", "Brock Purdy", "Dak Prescott", "Bo Nix", "Patrick Mahomes II",
        "Matthew Stafford", "Kyler Murray", "Jared Goff", "Malik Willis", "Tyler Shough", "Baker Mayfield", "Jordan Love",
        "Cam Ward", "Sam Darnold", "Bryce Young", "Daniel Jones", "Fernando Mendoza", "C.J. Stroud", "Jacoby Brissett",
        "Michael Penix Jr.", "Aaron Rodgers", "Geno Smith", "Shedeur Sanders",
    ])},
    "TE": {name: i + 1 for i, name in enumerate([
        "Brock Bowers", "Trey McBride", "Colston Loveland", "Tyler Warren", "Sam LaPorta", "Harold Fannin Jr.",
        "Tucker Kraft", "Kyle Pitts Sr.", "George Kittle", "Dalton Kincaid", "Dallas Goedert", "Mark Andrews",
        "Isaiah Likely", "Jake Ferguson", "Travis Kelce", "Oronde Gadsden II", "Chig Okonkwo", "T.J. Hockenson",
        "Kenyon Sadiq", "Greg Dulcich", "Terrance Ferguson", "Juwan Johnson", "Brenton Strange", "Hunter Henry",
        "AJ Barner", "Dalton Schultz", "Colby Parkinson", "Cade Otton", "Eli Stowers", "Gunnar Helm", "Pat Freiermuth",
        "Darnell Washington",
    ])},
}

# Context-adjusted 2025 PPR PPG from the guide. These are analyst-adjusted values,
# not raw season averages, and must remain labeled that way in the UI.
ADJUSTED_PPR_PPG = {
    "QB": {
        "Josh Allen": 23.2, "Matthew Stafford": 20.6, "Patrick Mahomes II": 20.4, "Jaxson Dart": 20.1,
        "Trevor Lawrence": 19.9, "Drake Maye": 19.8, "Dak Prescott": 19.6, "Jacoby Brissett": 18.9,
        "Daniel Jones": 18.8, "Caleb Williams": 18.7, "Jalen Hurts": 18.3, "Bo Nix": 18.3,
        "Joe Burrow": 18.2, "Brock Purdy": 18.1, "Jared Goff": 17.6, "Jayden Daniels": 17.6,
        "Justin Herbert": 17.5, "Lamar Jackson": 17.5, "Jordan Love": 17.4, "Tyler Shough": 17.1,
        "Baker Mayfield": 16.8, "Kyler Murray": 15.5, "C.J. Stroud": 14.5, "Sam Darnold": 14.2,
        "Bryce Young": 14.1, "Aaron Rodgers": 13.7, "Michael Penix Jr.": 13.3, "Shedeur Sanders": 12.0,
        "Geno Smith": 11.6, "Cam Ward": 11.1,
    },
    "RB": {
        "Christian McCaffrey": 24.8, "Jahmyr Gibbs": 24.6, "Jonathan Taylor": 23.8, "Bijan Robinson": 22.0,
        "Chase Brown": 21.0, "De'Von Achane": 20.4, "Cam Skattebo": 19.1, "Josh Jacobs": 18.0,
        "James Cook III": 17.9, "Derrick Henry": 16.9, "Javonte Williams": 16.2, "Omarion Hampton": 16.2,
        "Travis Etienne Jr.": 15.4, "Kyren Williams": 14.7, "Saquon Barkley": 14.6, "Ashton Jeanty": 14.5,
        "Bucky Irving": 14.0, "Rhamondre Stevenson": 13.5, "Jaylen Warren": 13.4, "Kenneth Walker III": 13.3,
        "Breece Hall": 13.1, "D'Andre Swift": 12.9, "Quinshon Judkins": 12.5, "Rico Dowdle": 11.7,
        "J.K. Dobbins": 11.6, "Rachaad White": 11.6, "Zach Charbonnet": 11.3, "Tony Pollard": 10.8,
        "Chuba Hubbard": 10.8, "Woody Marks": 10.7, "Kenny Gainwell": 10.6, "RJ Harvey": 10.0,
        "Aaron Jones Sr.": 10.0, "David Montgomery": 9.9, "Alvin Kamara": 9.7, "TreVeyon Henderson": 9.5,
        "Kyle Monangai": 9.5, "Tyjae Spears": 9.2, "Blake Corum": 8.8, "Jacory Croskey-Merritt": 8.4,
        "Tyler Allgeier": 7.2, "Isiah Pacheco": 6.7, "Tyrone Tracy Jr.": 6.5, "Jordan Mason": 6.3,
    },
    "WR": {
        "Puka Nacua": 23.7, "Jaxon Smith-Njigba": 20.4, "Amon-Ra St. Brown": 20.3, "Ja'Marr Chase": 20.1,
        "Drake London": 19.7, "Rashee Rice": 18.8, "Chris Olave": 18.8, "CeeDee Lamb": 16.6,
        "George Pickens": 16.1, "Rome Odunze": 15.5, "Davante Adams": 15.3, "Tee Higgins": 15.2,
        "Nico Collins": 15.0, "Zay Flowers": 15.0, "A.J. Brown": 14.1, "Michael Pittman Jr.": 14.1,
        "Wan'Dale Robinson": 13.6, "Emeka Egbuka": 13.1, "Michael Wilson": 13.0, "Jaylen Waddle": 12.9,
        "Courtland Sutton": 12.7, "Tetairoa McMillan": 12.5, "Deebo Samuel Sr.": 12.3, "Christian Watson": 12.3,
        "Marvin Harrison Jr.": 12.3, "Parker Washington": 12.3, "Jameson Williams": 12.1, "DK Metcalf": 12.1,
        "DeVonta Smith": 12.1, "Mike Evans": 12.1, "Justin Jefferson": 11.9, "Quentin Johnston": 11.8,
        "Stefon Diggs": 11.5, "Alec Pierce": 11.5, "Terry McLaurin": 11.4, "Jakobi Meyers": 11.4,
        "Romeo Doubs": 11.4, "Ladd McConkey": 11.0, "DJ Moore": 10.8, "Luther Burden III": 10.3,
        "Chris Godwin Jr.": 10.0, "Brian Thomas Jr.": 9.9, "Jordan Addison": 9.7, "Tre Tucker": 9.5,
    },
    "TE": {
        "Trey McBride": 18.6, "Brock Bowers": 16.4, "Tucker Kraft": 16.2, "George Kittle": 15.4,
        "Tyler Warren": 13.1, "Dalton Kincaid": 12.9, "Colston Loveland": 12.9, "Travis Kelce": 12.8,
        "Dallas Goedert": 12.3, "Juwan Johnson": 12.0, "Sam LaPorta": 11.9, "Harold Fannin Jr.": 11.7,
        "Dalton Schultz": 10.5, "Kyle Pitts Sr.": 10.0, "Hunter Henry": 9.8, "Brenton Strange": 9.8,
        "Jake Ferguson": 9.5, "Oronde Gadsden II": 9.4, "AJ Barner": 8.7, "Mark Andrews": 8.2,
        "T.J. Hockenson": 7.5, "Chig Okonkwo": 7.3, "Isaiah Likely": 4.4,
    },
}

DRAFT_STRATEGY = [
    "Rounds 1-2: RB/RB is a strong default; elite league-winning RBs are usually found in the first two rounds.",
    "Target three RBs from roughly the top 25-30 rather than living in the RB30-40 range.",
    "Round 3 and Round 5 are preferred WR zones; late WR is the preferred place to hunt upside.",
    "QB target zone: roughly QB7-QB11, often with 2-3 preferred options still available around Round 8; take QB3-QB6 if one falls far enough.",
    "TE can be best-player-available: TE2-TE4 when RB/WR value is weak, a mid-round TE around Rounds 7-8, or punt the position strategically.",
    "Use rankings with ADP. Do not draft a player at his ranking if the market says he can be taken materially later.",
    "Do not optimize for merely beating ADP by one spot; favor players with real ceiling and league-winning upside.",
    "Late-round process: rookie WRs, rushing QBs, talent on top offenses, and clear RB2/handcuff roles.",
    "Balance risk across the roster instead of stacking too many fragile/injury-risk bets.",
]

PPR_INSIGHTS = [
    "Since 2019, the PPR PPG gap between a top-8 first-round pick and picks 9-12 is only 0.5 PPG; reaching a few spots for your preferred elite player can be rational.",
    "Christian McCaffrey owns four of the five best PPR seasons since entering the NFL, illustrating his unique ceiling.",
    "Puka Nacua has a 36.8% target-per-route rate since 2024; no other qualified player is over 30%.",
    "Ja'Marr Chase has 200 targets in his last 17 games with Joe Burrow.",
    "Chase Brown benefits from a Cincinnati offense whose top three QBs in 2025 all ranked at the top in checkdown rate.",
    "Jaylen Warren was top-two among RBs in targets per route, yards per route and missed tackles per reception in 2025; Pittsburgh also has major vacated RB targets.",
    "De'Von Achane has averaged 11.4 receiving PPG with Tua Tagovailoa versus 3.4 without him.",
    "Josh Allen has finished top-two among fantasy QBs in each of the last six seasons.",
    "Rushing QBs drafted in Rounds 2-5 since 2015 have hit at a much higher rate than passing-first QBs in Joel's study.",
    "Only 2 of 33 RBs drafted in the first four fantasy rounds who reached 20+ PPG came from Rounds 3-4; elite RB ceilings have overwhelmingly come earlier.",
    "Ladd McConkey's yards per route increased sharply with motion, which matters in a Mike McDaniel offense built around motion.",
    "CeeDee Lamb was Joel's unluckiest player of 2025, estimated at roughly 2.7 PPG of bad-luck drag.",
    "Jahmyr Gibbs ranked near the top of the league in gap-scheme efficiency but far lower in zone efficiency, making 2026 scheme usage meaningful.",
    "Fourteen RBs have been selected top-25 in the NFL Draft since 2015; the first 11 all produced an RB1 fantasy season by Year 2.",
]


def _norm(value: Any) -> str:
    text = str(value or "").lower()
    text = text.replace("iii", "3").replace("ii", "2").replace("jr.", "jr").replace("sr.", "sr")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _lookup_map(data: dict[str, Any]) -> dict[str, Any]:
    return {_norm(k): v for k, v in data.items()}


def enrich_rankings_with_joel_ppr(rankings: pd.DataFrame) -> pd.DataFrame:
    if rankings is None or rankings.empty or "player_name" not in rankings.columns:
        return rankings
    frame = rankings.copy()
    overall = {_norm(name): rank for rank, name in enumerate(PPR_BIG_BOARD, start=1)}
    pos_maps = {pos: _lookup_map(values) for pos, values in PPR_POSITION_RANKS.items()}
    ppg_maps = {pos: _lookup_map(values) for pos, values in ADJUSTED_PPR_PPG.items()}

    keys = frame["player_name"].astype(str).map(_norm)
    positions = frame.get("position", pd.Series("", index=frame.index)).astype(str).str.upper()
    frame["joel_ppr_rank"] = keys.map(overall)
    frame["joel_ppr_pos_rank"] = [pos_maps.get(pos, {}).get(key) for pos, key in zip(positions, keys)]
    frame["joel_adjusted_2025_ppr_ppg"] = [ppg_maps.get(pos, {}).get(key) for pos, key in zip(positions, keys)]
    if "adp" in frame.columns:
        adp = pd.to_numeric(frame["adp"], errors="coerce")
        frame["joel_ppr_adp_value"] = adp - pd.to_numeric(frame["joel_ppr_rank"], errors="coerce")
    frame["joel_ppr_source"] = "Joel Smyth 2026 Draft Guide - Full PPR"
    return frame


def render_joel_ppr_panel(rankings: pd.DataFrame, weekly: pd.DataFrame, player_rows_fn) -> None:
    st.markdown('<div class="section-head">JOEL SMYTH • 2026 FULL PPR</div>', unsafe_allow_html=True)
    st.caption("Full-PPR material only. Half-PPR, dynasty, kicker and DST material from the guide are intentionally excluded.")

    tabs = st.tabs(["BIG BOARD", "ADP VALUE", "ADJ PPG", "STRATEGY", "INTEL"])

    with tabs[0]:
        frame = rankings.dropna(subset=["joel_ppr_rank"]).copy() if "joel_ppr_rank" in rankings.columns else pd.DataFrame()
        if not frame.empty:
            frame["_joel_sort"] = pd.to_numeric(frame["joel_ppr_rank"], errors="coerce")
            frame["overall_rank"] = frame["_joel_sort"]
            player_rows_fn(frame.sort_values("_joel_sort"), weekly, 150, "Draft Coach")
        else:
            st.info("Joel PPR rankings could not be matched to the current player file.")

    with tabs[1]:
        frame = rankings.dropna(subset=["joel_ppr_rank"]).copy() if "joel_ppr_rank" in rankings.columns else pd.DataFrame()
        if not frame.empty and "adp" in frame.columns:
            frame["_value"] = pd.to_numeric(frame["adp"], errors="coerce") - pd.to_numeric(frame["joel_ppr_rank"], errors="coerce")
            frame = frame.dropna(subset=["_value"]).sort_values(["_value", "adp"], ascending=[False, True])
            for _, row in frame.head(30).iterrows():
                value = float(row["_value"])
                st.markdown(
                    f'<div class="iq-card"><div style="display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px">'
                    f'<div><div class="iq-name">{row.get("player_name", "")}</div>'
                    f'<div class="iq-meta">{row.get("position", "")} • ADP {float(row.get("adp")):.1f} • Joel PPR #{int(row.get("joel_ppr_rank"))}</div></div>'
                    f'<div class="iq-value">{value:+.0f}</div></div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("ADP value requires current ADP plus a matched Joel PPR rank.")

    with tabs[2]:
        pos = st.selectbox("Position", ["RB", "WR", "QB", "TE"], key="joel_adj_ppg_pos")
        data = ADJUSTED_PPR_PPG[pos]
        for rank, (name, ppg) in enumerate(data.items(), start=1):
            st.markdown(
                f'<div class="iq-card"><div style="display:grid;grid-template-columns:32px minmax(0,1fr) auto;gap:8px;align-items:center">'
                f'<div class="player-rank">{rank}</div><div class="iq-name">{name}</div><div class="iq-value">{ppg:.1f}</div></div></div>',
                unsafe_allow_html=True,
            )
        st.caption("Joel's context-adjusted 2025 PPR PPG — not raw season PPG.")

    with tabs[3]:
        for item in DRAFT_STRATEGY:
            st.markdown(f'<div class="iq-card"><div class="iq-meta" style="font-size:11px;color:#dce5eb">• {item}</div></div>', unsafe_allow_html=True)

    with tabs[4]:
        for item in PPR_INSIGHTS:
            st.markdown(f'<div class="iq-card"><div class="iq-meta" style="font-size:11px;color:#dce5eb">• {item}</div></div>', unsafe_allow_html=True)
