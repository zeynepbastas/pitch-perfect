"""
Pitch Perfect: Load all CSVs into a SQLite database
Run: python3.11 load_to_sqlite.py

Place this script in the same folder as your soccer_schema_csvs/ folder.
Creates: pitch_perfect.db
"""

import sqlite3
import pandas as pd
import os

DB_NAME = "pitch_perfect.db"
CSV_DIR = "."

if os.path.exists(DB_NAME):
    os.remove(DB_NAME)

conn = sqlite3.connect(DB_NAME)
cur  = conn.cursor()
cur.execute("PRAGMA foreign_keys = ON")

print("Creating tables...\n")

cur.executescript("""
CREATE TABLE League (
    Name             TEXT PRIMARY KEY,
    Country          TEXT NOT NULL,
    Number_Of_Teams  INTEGER
);

CREATE TABLE League_Tournament_Has (
    Name        TEXT,
    Year        INTEGER,
    League_Name TEXT NOT NULL,
    Winner      TEXT,
    PRIMARY KEY (Name, Year),
    FOREIGN KEY (League_Name) REFERENCES League(Name)
);

CREATE TABLE Club_Teams_Belongs_To (
    Name            TEXT PRIMARY KEY,
    Location        TEXT,
    Number_Players  INTEGER,
    Number_Of_Wins  INTEGER,
    League_Name     TEXT NOT NULL,
    FOREIGN KEY (League_Name) REFERENCES League(Name)
);

CREATE TABLE Manager_Manages (
    Manager_ID    INTEGER,
    Club_Name     TEXT NOT NULL,
    Name          TEXT NOT NULL,
    Years_Managed INTEGER,
    PRIMARY KEY (Manager_ID, Club_Name),
    FOREIGN KEY (Club_Name) REFERENCES Club_Teams_Belongs_To(Name)
);

CREATE TABLE Manager_Years_Started (
    Manager_ID INTEGER,
    Club_Name  TEXT NOT NULL,
    Years      INTEGER,
    PRIMARY KEY (Manager_ID, Club_Name, Years),
    FOREIGN KEY (Manager_ID, Club_Name) REFERENCES Manager_Manages(Manager_ID, Club_Name)
);

CREATE TABLE Game (
    Game_ID      INTEGER PRIMARY KEY,
    Home_Team    TEXT NOT NULL,
    Away_Team    TEXT NOT NULL,
    Start_Time   TEXT,
    Location     TEXT,
    Score        TEXT,
    Winning_team TEXT
);

CREATE TABLE Plays (
    Game_ID   INTEGER,
    Club_Name TEXT NOT NULL,
    PRIMARY KEY (Game_ID, Club_Name),
    FOREIGN KEY (Game_ID)   REFERENCES Game(Game_ID),
    FOREIGN KEY (Club_Name) REFERENCES Club_Teams_Belongs_To(Name)
);

CREATE TABLE Player_Plays_For (
    Player_ID INTEGER PRIMARY KEY,
    Name      TEXT NOT NULL,
    DOB       TEXT,
    Market_Value REAL,
    Goals     INTEGER,
    Club_Name TEXT,
    FOREIGN KEY (Club_Name) REFERENCES Club_Teams_Belongs_To(Name)
);

CREATE TABLE Player_Position (
    Player_ID INTEGER,
    position  TEXT,
    PRIMARY KEY (Player_ID, position),
    FOREIGN KEY (Player_ID) REFERENCES Player_Plays_For(Player_ID)
);

CREATE TABLE Individual_Award_Wins (
    Name      TEXT,
    Year      INTEGER,
    League    TEXT,
    Player    TEXT,
    Player_ID INTEGER,
    PRIMARY KEY (Name, Year, League),
    FOREIGN KEY (Player_ID) REFERENCES Player_Plays_For(Player_ID)
);
""")

print("✓ All tables created\n")

def load(table, filename, transform=None):
    path = os.path.join(CSV_DIR, filename)
    df = pd.read_csv(path)
    if transform:
        df = transform(df)
    df = df.where(pd.notna(df), None)
    df.to_sql(table, conn, if_exists="append", index=False)
    print(f"  ✓ {table:<30} {len(df)} rows loaded")

print("Loading data...\n")

load("League",                "league.csv")
load("League_Tournament_Has", "league_tournament_has.csv")
load("Club_Teams_Belongs_To", "club_teams_belongs_to.csv")
load("Manager_Manages",       "manager_manages.csv")
load("Manager_Years_Started", "manager_years_started.csv")
load("Game",                  "game.csv")

# Plays: only rows where Club_Name exists in Club_Teams
plays_df  = pd.read_csv(os.path.join(CSV_DIR, "plays.csv"))
clubs_set = set(pd.read_csv(os.path.join(CSV_DIR, "club_teams_belongs_to.csv"))["Name"])
plays_df  = plays_df[plays_df["Club_Name"].isin(clubs_set)]
plays_df  = plays_df.where(pd.notna(plays_df), None)
plays_df.to_sql("Plays", conn, if_exists="append", index=False)
print(f"  ✓ {'Plays':<30} {len(plays_df)} rows loaded")

# Player_Plays_For: null out unknown club names
players_df = pd.read_csv(os.path.join(CSV_DIR, "player_plays_for.csv"))
players_df["Club_Name"] = players_df["Club_Name"].apply(
    lambda x: x if x in clubs_set else None
)
players_df = players_df.where(pd.notna(players_df), None)
players_df.to_sql("Player_Plays_For", conn, if_exists="append", index=False)
print(f"  ✓ {'Player_Plays_For':<30} {len(players_df)} rows loaded")

load("Player_Position",       "player_position.csv")
load("Individual_Award_Wins", "individual_award_wins.csv")

conn.commit()

# ── SUMMARY ──────────────────────────────────────────────────────────────
print("\n" + "="*55)
print("DATABASE SUMMARY")
print("="*55)

tables = [
    "League", "League_Tournament_Has", "Club_Teams_Belongs_To",
    "Manager_Manages", "Manager_Years_Started", "Game", "Plays",
    "Player_Plays_For", "Player_Position", "Individual_Award_Wins"
]
for t in tables:
    count = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:<35} {count:>6} rows")

print("="*55)
print(f"\n✓ Database saved as: {DB_NAME}\n")

# ── SAMPLE QUERIES ────────────────────────────────────────────────────────
print("SAMPLE — Top 5 goal scorers:")
for r in cur.execute("""
    SELECT Name, Club_Name, Goals FROM Player_Plays_For
    WHERE Goals IS NOT NULL ORDER BY Goals DESC LIMIT 5
""").fetchall():
    print(f"  {r[0]:<25} {str(r[1]):<35} {r[2]} goals")

print("\nSAMPLE — League champions:")
for r in cur.execute("""
    SELECT League_Name, Year, Winner FROM League_Tournament_Has
    ORDER BY League_Name, Year
""").fetchall():
    print(f"  {r[0]:<20} {r[1]}  →  {r[2]}")

conn.close()
