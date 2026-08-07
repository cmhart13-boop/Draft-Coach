from pathlib import Path

path = Path('app.py')
text = path.read_text()

old_loader = '''@st.cache_data(show_spinner=False)
def load_weekly() -> pd.DataFrame:
    if not WEEKLY_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(WEEKLY_PATH, low_memory=False, compression="gzip")
'''
optimized_loader = '''@st.cache_resource(show_spinner=False)
def load_weekly() -> pd.DataFrame:
    """Load only weekly columns actually used by Shiva/Mock Draft.

    The compressed weekly master expands dramatically in memory. cache_resource keeps
    one shared read-only frame instead of serializing/copying it per Streamlit session.
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

if old_loader in text:
    text = text.replace(old_loader, optimized_loader, 1)
elif optimized_loader not in text:
    raise SystemExit('weekly loader shape changed; refusing unsafe patch')

# Do NOT expand the large weekly dataset on every page load.
text = text.replace('weekly = load_weekly()\nfor col in [', 'weekly = None\nfor col in [', 1)

# Shiva Intelligence loads weekly data only when a question is actually submitted.
shiva_old = '''                        weekly=weekly,
                        api_key=configured_api_key,
'''
shiva_new = '''                        weekly=load_weekly(),
                        api_key=configured_api_key,
'''
if shiva_old in text:
    text = text.replace(shiva_old, shiva_new, 1)

# Mock Draft needs only the optimized shared weekly frame when that page is opened.
mock_old = '''        weekly=weekly,
        history=history,
        roi=roi,
        db_path=DB_PATH,
'''
mock_new = '''        weekly=load_weekly(),
        history=history,
        roi=roi,
        db_path=DB_PATH,
'''
if mock_old in text:
    text = text.replace(mock_old, mock_new, 1)

path.write_text(text)
print('Optimized Streamlit memory: selective shared weekly data + lazy page loading.')
