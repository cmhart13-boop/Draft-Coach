from pathlib import Path

path = Path('app.py')
text = path.read_text()
old = '''@st.cache_data(show_spinner=False)
def load_weekly() -> pd.DataFrame:
    if not WEEKLY_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(WEEKLY_PATH, low_memory=False, compression="gzip")
'''
new = '''@st.cache_resource(show_spinner=False)
def load_weekly() -> pd.DataFrame:
    """Load only weekly columns used by Shiva/Mock Draft and share one in-memory frame.

    The full compressed master expands dramatically in RAM. Streamlit cache_data also
    serializes/copies the dataframe per session, which can push Community Cloud over its
    memory limit. cache_resource keeps one shared read-only dataframe and usecols avoids
    loading dozens of unused NFL stat columns.
    """
    if not WEEKLY_PATH.exists():
        return pd.DataFrame()
    header = pd.read_csv(WEEKLY_PATH, compression="gzip", nrows=0).columns.tolist()
    wanted = [
        "season", "week", "season_type", "player_id", "player_display_name",
        "player_name", "name", "position", "recent_team", "team",
        "fantasy_points_ppr", "fantasy_points", "targets", "receptions",
        "receiving_yards", "receiving_tds", "carries", "rushing_yards",
        "rushing_tds", "target_share", "red_zone_touches", "attempts",
        "passing_yards", "passing_tds", "interceptions"
    ]
    usecols = [c for c in wanted if c in header]
    return pd.read_csv(
        WEEKLY_PATH,
        compression="gzip",
        usecols=usecols or None,
        low_memory=False,
    )
'''
if old not in text:
    raise SystemExit('load_weekly block not found; refusing unsafe patch')
text = text.replace(old, new, 1)
path.write_text(text)
print('Optimized weekly master loading for Streamlit memory limits.')
