from pathlib import Path
import re

path = Path('app.py')
text = path.read_text()

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

# Replace any existing load_weekly implementation, regardless of previous optimization wording.
pattern = re.compile(
    r'@st\.cache_(?:data|resource)\(show_spinner=False\)\ndef load_weekly\(\) -> pd\.DataFrame:\n.*?(?=\nroi = load_roi\(\))',
    re.S,
)
text, count = pattern.subn(optimized_loader.rstrip(), text, count=1)
if count != 1:
    raise SystemExit('load_weekly block not found; refusing unsafe patch')

# Do NOT expand the large weekly dataset on every app page load.
text = text.replace('weekly = load_weekly()\nfor col in [', 'weekly = None\nfor col in [', 1)

# Shiva Intelligence loads weekly data only when a question is actually submitted.
text = text.replace(
    '                        weekly=weekly,\n                        api_key=configured_api_key,\n',
    '                        weekly=load_weekly(),\n                        api_key=configured_api_key,\n',
    1,
)

# Mock Draft loads the optimized shared weekly frame only when that page is opened.
text = text.replace(
    '        weekly=weekly,\n        history=history,\n        roi=roi,\n        db_path=DB_PATH,\n',
    '        weekly=load_weekly(),\n        history=history,\n        roi=roi,\n        db_path=DB_PATH,\n',
    1,
)

path.write_text(text)
print('Optimized Streamlit memory: selective shared weekly data + lazy page loading.')
