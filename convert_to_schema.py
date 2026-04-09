"""
Pitch Perfect: Full clean conversion — seasons 2020-21 to 2024-25 only
Run: python3.11 convert_to_schema.py
Place all CSV files in the same folder as this script.
"""

import pandas as pd
import os
import glob

OUTPUT_DIR = "soccer_schema_csvs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

LEAGUE_MAP = {
    "Premier_League": {"Name": "Premier League", "Country": "England",  "Number_Of_Teams": 20},
    "La_Liga":        {"Name": "La Liga",         "Country": "Spain",    "Number_Of_Teams": 20},
    "Serie_A":        {"Name": "Serie A",         "Country": "Italy",    "Number_Of_Teams": 20},
    "Bundesliga":     {"Name": "Bundesliga",      "Country": "Germany",  "Number_Of_Teams": 18},
    "Ligue_1":        {"Name": "Ligue 1",         "Country": "France",   "Number_Of_Teams": 20},
}

TM_LEAGUE_MAP = {
    "GB1": "Premier League",
    "ES1": "La Liga",
    "IT1": "Serie A",
    "L1":  "Bundesliga",
    "FR1": "Ligue 1",
}

VALID_END_YY = {21, 22, 23, 24, 25}  # 20/21 through 24/25

def get_league_key(filename):
    base = os.path.basename(filename).replace(".csv", "")
    for key in LEAGUE_MAP:
        if base.startswith(key):
            return key
    return None

def get_season_year(filename):
    base = os.path.basename(filename).replace(".csv", "")
    parts = base.split("_")
    try:
        end_yy = int(parts[-1])
        return end_yy, 2000 + end_yy
    except:
        return None, None

# ── Load match CSVs — only 20/21 to 24/25 ───────────────────────────────
all_files = glob.glob("*.csv")
match_files = [f for f in all_files
               if get_league_key(f) is not None
               and get_season_year(f)[0] in VALID_END_YY]

print(f"Loading {len(match_files)} match CSV files...\n")
all_games = []

for filepath in sorted(match_files):
    league_key = get_league_key(filepath)
    end_yy, season_year = get_season_year(filepath)
    try:
        df = pd.read_csv(filepath, encoding="latin1")
        rows = [{"_league_key": league_key,
                 "_season_year": season_year,
                 "_league_name": LEAGUE_MAP[league_key]["Name"],
                 **r} for r in df.to_dict("records")]
        all_games.append(pd.DataFrame(rows))
        print(f"  ✓ {filepath} — {len(df)} matches")
    except Exception as e:
        print(f"  ✗ {filepath}: {e}")

print()
matches = pd.concat(all_games, ignore_index=True)
print(f"Total matches: {len(matches)}\n")

# ── 1. LEAGUE ────────────────────────────────────────────────────────────
league_df = pd.DataFrame([
    {"Name": v["Name"], "Country": v["Country"], "Number_Of_Teams": v["Number_Of_Teams"]}
    for v in LEAGUE_MAP.values()
])
league_df.to_csv(f"{OUTPUT_DIR}/league.csv", index=False)
print(f"✓ league.csv — {len(league_df)} rows")

# ── 2. GAME ──────────────────────────────────────────────────────────────
matches = matches.reset_index(drop=True)
matches["Game_ID"] = matches.index + 1

def make_score(row):
    try:
        return f"{int(row['FTHG'])}-{int(row['FTAG'])}"
    except:
        return None

def make_winner(row):
    ftr = str(row.get("FTR", "")).strip()
    if ftr == "H":   return row.get("HomeTeam")
    elif ftr == "A": return row.get("AwayTeam")
    elif ftr == "D": return "Draw"
    return None

matches["Score"]        = matches.apply(make_score, axis=1)
matches["Winning_team"] = matches.apply(make_winner, axis=1)
time_col = "Time" if "Time" in matches.columns else None
matches["Start_Time"] = (
    matches["Date"].astype(str) + " " + matches[time_col].astype(str)
    if time_col else matches["Date"].astype(str)
)

game_df = matches[["Game_ID","HomeTeam","AwayTeam","Start_Time","Score","Winning_team"]].copy()
game_df.columns = ["Game_ID","Home_Team","Away_Team","Start_Time","Score","Winning_team"]
game_df["Location"] = None
game_df = game_df[["Game_ID","Home_Team","Away_Team","Start_Time","Location","Score","Winning_team"]]
game_df.to_csv(f"{OUTPUT_DIR}/game.csv", index=False)
print(f"✓ game.csv — {len(game_df)} rows")

# ── 3. PLAYS ─────────────────────────────────────────────────────────────
plays_home = matches[["Game_ID","HomeTeam"]].rename(columns={"HomeTeam":"Club_Name"})
plays_away = matches[["Game_ID","AwayTeam"]].rename(columns={"AwayTeam":"Club_Name"})
plays_df = pd.concat([plays_home, plays_away], ignore_index=True).sort_values("Game_ID")
plays_df.to_csv(f"{OUTPUT_DIR}/plays.csv", index=False)
print(f"✓ plays.csv — {len(plays_df)} rows")

# ── 4. CLUB_TEAMS_BELONGS_TO ─────────────────────────────────────────────
clubs_tm = pd.read_csv("clubs.csv")
stadium_lookup = dict(zip(clubs_tm["name"].str.strip(), clubs_tm["stadium_name"].fillna("")))

club_rows = []
seen = set()
for _, row in matches.iterrows():
    for team_col in ["HomeTeam","AwayTeam"]:
        club  = row[team_col]
        league = row["_league_name"]
        key = (club, league)
        if key not in seen:
            seen.add(key)
            home_wins = len(matches[(matches["HomeTeam"]==club) & (matches["FTR"]=="H")])
            away_wins = len(matches[(matches["AwayTeam"]==club) & (matches["FTR"]=="A")])
            club_rows.append({
                "Name":           club,
                "Location":       stadium_lookup.get(club, ""),
                "Number_Players": None,
                "Number_Of_Wins": home_wins + away_wins,
                "League_Name":    league
            })

clubs_df = pd.DataFrame(club_rows)
clubs_df.to_csv(f"{OUTPUT_DIR}/club_teams_belongs_to.csv", index=False)
print(f"✓ club_teams_belongs_to.csv — {len(clubs_df)} rows")

# ── 5. LEAGUE_TOURNAMENT_HAS ─────────────────────────────────────────────
tournament_rows = []
for (league_key, season_year), group in matches.groupby(["_league_key","_season_year"]):
    league_name = LEAGUE_MAP[league_key]["Name"]
    home_w = group[group["FTR"]=="H"].groupby("HomeTeam").size()
    away_w = group[group["FTR"]=="A"].groupby("AwayTeam").size()
    all_teams = set(group["HomeTeam"]).union(set(group["AwayTeam"]))
    win_counts = {t: home_w.get(t,0) + away_w.get(t,0) for t in all_teams}
    winner = max(win_counts, key=win_counts.get)
    tournament_rows.append({
        "Name":        f"{league_name} {season_year}",
        "Year":        season_year,
        "League_Name": league_name,
        "Winner":      winner
    })

tournament_df = pd.DataFrame(tournament_rows).sort_values(["League_Name","Year"])
tournament_df.to_csv(f"{OUTPUT_DIR}/league_tournament_has.csv", index=False)
print(f"✓ league_tournament_has.csv — {len(tournament_df)} rows")

# ── 6. PLAYER_PLAYS_FOR ──────────────────────────────────────────────────
players_tm = pd.read_csv("players.csv")
goals_df   = pd.read_csv("player_goals_summary.csv")

big5_ids = list(TM_LEAGUE_MAP.keys())
players_big5 = players_tm[
    players_tm["current_club_domestic_competition_id"].isin(big5_ids) &
    players_tm["last_season"].between(2020, 2025)
].copy().reset_index(drop=True)

players_big5["Player_ID"] = players_big5.index + 1
players_big5["DOB"] = pd.to_datetime(
    players_big5["date_of_birth"], errors="coerce"
).dt.strftime("%Y-%m-%d")

# Merge goals
players_big5 = players_big5.merge(goals_df, on="player_id", how="left")
players_big5["goals"] = players_big5["goals"].fillna(0).astype(int)

player_plays_df = players_big5[["Player_ID","name","DOB","current_club_name","goals"]].copy()
player_plays_df.columns = ["Player_ID","Name","DOB","Club_Name","Goals"]
player_plays_df["Salary"] = None
player_plays_df = player_plays_df[["Player_ID","Name","DOB","Salary","Goals","Club_Name"]]
player_plays_df.to_csv(f"{OUTPUT_DIR}/player_plays_for.csv", index=False)
print(f"✓ player_plays_for.csv — {len(player_plays_df)} rows")

# ── 7. PLAYER_POSITION ───────────────────────────────────────────────────
position_rows = []
for _, row in players_big5.iterrows():
    positions = []
    if pd.notna(row.get("position")):
        positions.append(str(row["position"]).strip())
    if pd.notna(row.get("sub_position")) and row["sub_position"] != row["position"]:
        positions.append(str(row["sub_position"]).strip())
    for pos in positions:
        position_rows.append({"Player_ID": row["Player_ID"], "position": pos})

position_df = pd.DataFrame(position_rows)
position_df.to_csv(f"{OUTPUT_DIR}/player_position.csv", index=False)
print(f"✓ player_position.csv — {len(position_df)} rows")

# ── Done ─────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"All CSVs saved to: ./{OUTPUT_DIR}/")
print(f"{'='*50}")
print("""
STILL NEEDED (manual):
  - Manager_Manages table
  - Individual_Award table
  - Salary in player_plays_for.csv (not publicly available)
  - Location gaps in club_teams_belongs_to.csv
""")
