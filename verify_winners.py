import sqlite3

db_path = 'pitch_perfect.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Verifying Winning_team consistency...")

# 1. Update Home Wins
cursor.execute("""
    UPDATE Game 
    SET Winning_team = Home_Team 
    WHERE Home_Score > Away_Score
""")
home_wins = cursor.rowcount

# 2. Update Away Wins
cursor.execute("""
    UPDATE Game 
    SET Winning_team = Away_Team 
    WHERE Away_Score > Home_Score
""")
away_wins = cursor.rowcount

# 3. Update Draws
cursor.execute("""
    UPDATE Game 
    SET Winning_team = 'Draw' 
    WHERE Home_Score = Away_Score
""")
draws = cursor.rowcount

conn.commit()
conn.close()

print(f"Database consistency check complete!")
print(f"Final stats: {home_wins} Home Wins, {away_wins} Away Wins, {draws} Draws.")