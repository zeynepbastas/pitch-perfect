import sqlite3

db_path = 'pitch_perfect.db'

# Mapping the Awards to the IDs we just created in the terminal
legend_map = {
    "Lionel Messi": 9001,
    "Cristiano Ronaldo": 9002,
    "Theo Hernandez": 9003,
    "Victor Osimhen": 9004,
    "Mateo Retegui": 9005
}

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Linking award winners to newly created legend IDs...")

for name, p_id in legend_map.items():
    cursor.execute("""
        UPDATE Individual_Award_Wins 
        SET Player_ID = ? 
        WHERE Player = ?
    """, (p_id, name))
    print(f"Fixed Legend: {name} assigned to ID {p_id}")

conn.commit()
conn.close()
print("Done!")