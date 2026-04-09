import sqlite3

db_path = 'pitch_perfect.db'

# Define the "Visual Polish" mapping
# Format: "Old Name": "New Professional Name"
polish_map = {
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Tottenham": "Tottenham Hotspur",
    "Ein Frankfurt": "Eintracht Frankfurt",
    "FC Koln": "FC Köln",
    "Bayern Munich": "Bayern München"
}

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Applying visual polish to club names...")

# Tables and columns that need updating
targets = [
    ('Manager_Manages', 'Club_Name'),
    ('Manager_Years_Started', 'Club_Name'),
    ('Player_Plays_For', 'Club_Name'),
    ('Game', 'Home_Team'),
    ('Game', 'Away_Team'),
    ('Game', 'Winning_team'),
    ('Plays', 'Club_Name'),
    ('League_Tournament_Has', 'Winner'),
    ('Club_Teams_Belongs_To', 'Name')
]

for old_name, new_name in polish_map.items():
    for table, column in targets:
        cursor.execute(f"UPDATE {table} SET {column} = ? WHERE {column} = ?", (new_name, old_name))
    print(f"✨ Polished: {old_name} -> {new_name}")

conn.commit()
conn.close()
print("\nDatabase is now visually consistent!")