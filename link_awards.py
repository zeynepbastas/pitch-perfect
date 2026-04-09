import sqlite3
from rapidfuzz import process, utils

db_path = 'pitch_perfect.db'

# 1. Connect to SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 2. Get all players from the database to create a master list
cursor.execute("SELECT Player_ID, Name FROM Player_Plays_For")
players = cursor.fetchall()
player_map = {utils.default_process(name): p_id for p_id, name in players}
player_names_list = list(player_map.keys())

# 3. Get awards that are missing a Player_ID
cursor.execute("SELECT rowid, Player FROM Individual_Award_Wins WHERE Player_ID IS NULL OR Player_ID = ''")
missing_awards = cursor.fetchall()

print(f"Found {len(missing_awards)} awards missing Player_IDs. Matching now...")

updated_count = 0
for rowid, player_name in missing_awards:
    processed_name = utils.default_process(player_name)
    
    # Fuzzy match the award name against our master player list
    match = process.extractOne(processed_name, player_names_list, score_cutoff=80)
    
    if match:
        best_name = match[0]
        matched_id = player_map[best_name]
        
        cursor.execute("""
            UPDATE Individual_Award_Wins 
            SET Player_ID = ? 
            WHERE rowid = ?
        """, (matched_id, rowid))
        updated_count += 1

conn.commit()
conn.close()

print(f"Successfully linked {updated_count} awards to Player IDs!")