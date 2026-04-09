import sqlite3

db_path = 'pitch_perfect.db'

# Add EVERY mismatch you find here. 
# Key = The 'wrong' name in your data, Value = The 'correct' name in your DB
aliases = {
    'Club': {
        'Man Utd': 'Manchester United',
        'Man City': 'Manchester City',
        'FC Bayern': 'Bayern Munich',
        'Spurs': 'Tottenham Hotspur'
    },
    'Player': {
        'K. De Bruyne': 'Kevin De Bruyne',
        'Son': 'Son Heung-min',
        'Leo Messi': 'Lionel Messi'
    }
}

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def update_all_occurrences(old_name, new_name):
    # This list defines which columns in which tables need checking
    targets = [
        ('Game', 'Home_Team'),
        ('Game', 'Away_Team'),
        ('Game', 'Winning_team'),
        ('Individual_Award_Wins', 'Player'),
        ('Player_Plays_For', 'Club_Name'),
        ('Manager_Manages', 'Club_Name')
    ]
    
    for table, column in targets:
        cursor.execute(f"UPDATE {table} SET {column} = ? WHERE {column} = ?", (new_name, old_name))
        if cursor.rowcount > 0:
            print(f"Updated {cursor.rowcount} rows in {table}.{column}: {old_name} -> {new_name}")

# Run the standardization
for category, mapping in aliases.items():
    for alias, standard in mapping.items():
        update_all_occurrences(alias, standard)

conn.commit()
conn.close()
print("Global standardization complete.")
