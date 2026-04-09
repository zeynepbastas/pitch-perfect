import sqlite3
import pandas as pd
from rapidfuzz import process, utils

db_path = 'pitch_perfect.db'
clubs_csv_path = 'soccer_schema_csvs/clubs.csv'

# 1. Load the club-to-stadium mapping
clubs_df = pd.read_csv(clubs_csv_path)
# Standardize names for better matching
stadium_map = {utils.default_process(row['name']): row['stadium_name'] for _, row in clubs_df.iterrows()}
club_names_list = list(stadium_map.keys())

# 2. Connect to SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Running Fuzzy Match on game locations... (this might take a minute)")

cursor.execute("SELECT DISTINCT Home_Team FROM Game")
home_teams = cursor.fetchall()

updated_count = 0
not_found = 0

for (team_name,) in home_teams:
    processed_name = utils.default_process(team_name)
    
    # Find the best match in our clubs list
    # score_cutoff=60 ensures we don't match "Arsenal" with "Barcelona" by accident
    match = process.extractOne(processed_name, club_names_list, score_cutoff=60)
    
    if match:
        best_match_name = match[0]
        stadium = stadium_map[best_match_name]
        
        if stadium and str(stadium) != 'nan':
            cursor.execute("""
                UPDATE Game 
                SET Location = ? 
                WHERE Home_Team = ?
            """, (stadium, team_name))
            updated_count += cursor.rowcount
        else:
            not_found += 1
    else:
        not_found += 1

conn.commit()
conn.close()

print(f"Success! Updated {updated_count} rows using fuzzy matching.")
print(f"Teams still missing stadiums: {not_found}")