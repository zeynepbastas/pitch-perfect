import sqlite3

db_path = 'pitch_perfect.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Fetch all games with a score
cursor.execute("SELECT Game_ID, Score FROM Game WHERE Score IS NOT NULL AND Score != ''")
games = cursor.fetchall()

print(f"Processing {len(games)} game scores...")

updates = []
for game_id, score_str in games:
    try:
        # Split '2-1' into [2, 1]
        parts = score_str.split('-')
        if len(parts) == 2:
            h_score = int(parts[0].strip())
            a_score = int(parts[1].strip())
            updates.append((h_score, a_score, game_id))
    except ValueError:
        # Skips rows where score might be 'Postponed' or malformed
        continue

# 2. Bulk update the new columns
cursor.executemany("UPDATE Game SET Home_Score = ?, Away_Score = ? WHERE Game_ID = ?", updates)

conn.commit()
conn.close()
print(f"Successfully transformed {len(updates)} scores into numeric data!")