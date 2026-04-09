import sqlite3

DB = 'pitch_perfect.db'

LEAGUES  = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
SEASONS  = [2021, 2022, 2023, 2024, 2025]
SEASON_LABELS = ['2020/21', '2021/22', '2022/23', '2023/24', '2024/25']

def conn():
    return sqlite3.connect(DB)

# ── helpers ──────────────────────────────────────────────────────────────────

def pick(options, labels=None, prompt="Select: "):
    labels = labels or [str(o) for o in options]
    for i, label in enumerate(labels, 1):
        print(f"  {i}. {label}")
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("  Invalid choice, try again.")

SEASON_SQL = """
    CASE WHEN CAST(substr(Start_Time,4,2) AS INT) >= 7
         THEN CAST(substr(Start_Time,7,4) AS INT) + 1
         ELSE CAST(substr(Start_Time,7,4) AS INT) END = ?
"""

# ── 1. Top scorers ───────────────────────────────────────────────────────────

def top_scorers():
    c = conn()
    rows = c.execute("""
        SELECT Name, Club_Name, Goals
        FROM Player_Plays_For
        WHERE Goals IS NOT NULL
        ORDER BY Goals DESC LIMIT 10
    """).fetchall()
    c.close()
    print("\n" + "="*52)
    print("   TOP 10 ALL-TIME SCORERS")
    print("="*52)
    print(f"  {'#':<3} {'NAME':<22} {'CLUB':<20} GOALS")
    print("-"*52)
    for i, (name, club, goals) in enumerate(rows, 1):
        print(f"  {i:<3} {name:<22} {str(club):<20} {goals}")

# ── 2. Manager performance ───────────────────────────────────────────────────

def manager_performance():
    c = conn()
    rows = c.execute("""
        SELECT m.Name, m.Club_Name,
               COUNT(g.Game_ID) as Wins,
               m.Years_Managed
        FROM Manager_Manages m
        JOIN Game g ON m.Club_Name = g.Winning_team
        GROUP BY m.Manager_ID, m.Name, m.Club_Name
        ORDER BY Wins DESC LIMIT 10
    """).fetchall()
    c.close()
    print("\n" + "="*60)
    print("   TOP 10 WINNINGEST MANAGERS")
    print("="*60)
    print(f"  {'#':<3} {'MANAGER':<22} {'CLUB':<22} {'WINS':<6} YRS")
    print("-"*60)
    for i, (name, club, wins, yrs) in enumerate(rows, 1):
        print(f"  {i:<3} {name:<22} {club:<22} {wins:<6} {yrs}")

# ── 3. Player search ─────────────────────────────────────────────────────────

def search_player():
    query = input("\n  Enter player name: ").strip()
    c = conn()
    player = c.execute("""
        SELECT Player_ID, Name, DOB, Club_Name, Goals
        FROM Player_Plays_For WHERE Name LIKE ?
    """, (f'%{query}%',)).fetchone()

    if not player:
        print("  No player found.")
        c.close()
        return

    pid, name, dob, club, goals = player
    print(f"\n  {'─'*40}")
    print(f"  {name}")
    print(f"  {'─'*40}")
    print(f"  Club:   {club or 'N/A'}")
    print(f"  DOB:    {dob or 'N/A'}")
    print(f"  Goals:  {goals}")

    positions = c.execute(
        "SELECT position FROM Player_Position WHERE Player_ID=?", (pid,)
    ).fetchall()
    if positions:
        print(f"  Pos:    {', '.join(p[0] for p in positions)}")

    awards = c.execute(
        "SELECT Name, Year, League FROM Individual_Award_Wins WHERE Player_ID=? ORDER BY Year",
        (pid,)
    ).fetchall()
    if awards:
        print("  Awards:")
        for aname, yr, league in awards:
            print(f"    {yr}  {aname}  ({league})")
    else:
        print("  Awards: none")
    c.close()

# ── 4. League standings ──────────────────────────────────────────────────────

def league_standings():
    print("\n  Select league:")
    league = pick(LEAGUES)
    print("\n  Select season:")
    season = pick(SEASONS, SEASON_LABELS)

    c = conn()
    rows = c.execute(f"""
        WITH sg AS (
            SELECT * FROM Game
            WHERE League_Name = ? AND {SEASON_SQL}
        ),
        home AS (
            SELECT Home_Team as Club, COUNT(*) as P,
                   SUM(CASE WHEN Winning_team=Home_Team THEN 1 ELSE 0 END) as W,
                   SUM(CASE WHEN Winning_team='Draw'    THEN 1 ELSE 0 END) as D,
                   SUM(CASE WHEN Winning_team=Away_Team THEN 1 ELSE 0 END) as L,
                   SUM(Home_Score) as GF, SUM(Away_Score) as GA
            FROM sg GROUP BY Home_Team
        ),
        away AS (
            SELECT Away_Team as Club, COUNT(*) as P,
                   SUM(CASE WHEN Winning_team=Away_Team THEN 1 ELSE 0 END) as W,
                   SUM(CASE WHEN Winning_team='Draw'    THEN 1 ELSE 0 END) as D,
                   SUM(CASE WHEN Winning_team=Home_Team THEN 1 ELSE 0 END) as L,
                   SUM(Away_Score) as GF, SUM(Home_Score) as GA
            FROM sg GROUP BY Away_Team
        )
        SELECT h.Club,
               h.P+a.P as P, h.W+a.W as W, h.D+a.D as D, h.L+a.L as L,
               h.GF+a.GF as GF, h.GA+a.GA as GA,
               (h.GF+a.GF)-(h.GA+a.GA) as GD,
               (h.W+a.W)*3 + (h.D+a.D) as Pts
        FROM home h JOIN away a USING(Club)
        ORDER BY Pts DESC, GD DESC, GF DESC
    """, (league, season)).fetchall()
    c.close()

    season_label = SEASON_LABELS[SEASONS.index(season)]
    print(f"\n  {'─'*70}")
    print(f"  {league}  —  {season_label} Standings")
    print(f"  {'─'*70}")
    print(f"  {'#':<3} {'CLUB':<25} {'P':>3} {'W':>3} {'D':>3} {'L':>3} {'GF':>4} {'GA':>4} {'GD':>5} {'PTS':>4}")
    print(f"  {'─'*70}")
    for i, (club, p, w, d, l, gf, ga, gd, pts) in enumerate(rows, 1):
        gd_str = f"+{gd}" if gd > 0 else str(gd)
        print(f"  {i:<3} {club:<25} {p:>3} {w:>3} {d:>3} {l:>3} {gf:>4} {ga:>4} {gd_str:>5} {pts:>4}")

# ── 5. Club profile ──────────────────────────────────────────────────────────

def club_profile():
    query = input("\n  Enter club name: ").strip()
    c = conn()
    club = c.execute("""
        SELECT Name, Location, League_Name, Number_Of_Wins
        FROM Club_Teams_Belongs_To WHERE Name LIKE ?
    """, (f'%{query}%',)).fetchone()

    if not club:
        print("  Club not found.")
        c.close()
        return

    name, location, league, wins = club
    managers = c.execute("""
        SELECT Name, Years_Managed FROM Manager_Manages WHERE Club_Name=? ORDER BY Years_Managed DESC
    """, (name,)).fetchall()
    top_players = c.execute("""
        SELECT Name, Goals FROM Player_Plays_For WHERE Club_Name=? ORDER BY Goals DESC LIMIT 5
    """, (name,)).fetchall()
    awards = c.execute("""
        SELECT COUNT(*) FROM Individual_Award_Wins iaw
        JOIN Player_Plays_For p ON iaw.Player_ID = p.Player_ID
        WHERE p.Club_Name=?
    """, (name,)).fetchone()[0]

    print(f"\n  {'─'*45}")
    print(f"  {name}")
    print(f"  {'─'*45}")
    print(f"  League:   {league}")
    print(f"  Stadium:  {location or 'N/A'}")
    print(f"  Wins:     {wins}")
    print(f"  Awards:   {awards} (current squad)")

    if managers:
        print("  Managers:")
        for mname, yrs in managers:
            print(f"    {mname} ({yrs} yrs)")

    if top_players:
        print("  Top Scorers:")
        for pname, goals in top_players:
            print(f"    {pname:<22}  {goals} goals")
    c.close()

# ── 6. Awards by league ──────────────────────────────────────────────────────

def awards_by_league():
    print("\n  Select league:")
    league = pick(LEAGUES)
    c = conn()
    rows = c.execute("""
        SELECT Name, Year, Player
        FROM Individual_Award_Wins
        WHERE League = ?
        ORDER BY Name, Year
    """, (league,)).fetchall()
    c.close()

    print(f"\n  {'─'*55}")
    print(f"  Awards — {league}")
    print(f"  {'─'*55}")
    print(f"  {'AWARD':<28} {'YEAR':<6} WINNER")
    print(f"  {'─'*55}")
    for award, year, player in rows:
        print(f"  {award:<28} {year:<6} {player}")

# ── 7. Season summary ────────────────────────────────────────────────────────

def season_summary():
    print("\n  Select season:")
    season = pick(SEASONS, SEASON_LABELS)
    season_label = SEASON_LABELS[SEASONS.index(season)]
    c = conn()

    champions = c.execute("""
        SELECT League_Name, Winner FROM League_Tournament_Has WHERE Year=? ORDER BY League_Name
    """, (season,)).fetchall()

    awards = c.execute("""
        SELECT League, Name, Player FROM Individual_Award_Wins WHERE Year=? ORDER BY League, Name
    """, (season,)).fetchall()
    c.close()

    print(f"\n  {'─'*55}")
    print(f"  Season Summary — {season_label}")
    print(f"  {'─'*55}")
    print(f"\n  CHAMPIONS")
    for league, winner in champions:
        print(f"    {league:<22}  {winner}")

    print(f"\n  INDIVIDUAL AWARDS")
    for league, award, player in awards:
        print(f"    {league:<22}  {award:<28}  {player}")

# ── 8. Head-to-head ──────────────────────────────────────────────────────────

def head_to_head():
    club1 = input("\n  Enter first club:  ").strip()
    club2 = input("  Enter second club: ").strip()

    c = conn()
    # Resolve partial names
    r1 = c.execute("SELECT Name FROM Club_Teams_Belongs_To WHERE Name LIKE ? LIMIT 1", (f'%{club1}%',)).fetchone()
    r2 = c.execute("SELECT Name FROM Club_Teams_Belongs_To WHERE Name LIKE ? LIMIT 1", (f'%{club2}%',)).fetchone()

    if not r1 or not r2:
        print("  One or both clubs not found.")
        c.close()
        return

    name1, name2 = r1[0], r2[0]
    rows = c.execute("""
        SELECT Home_Team, Away_Team, Home_Score, Away_Score, Winning_team,
               substr(Start_Time,7,4) as Year
        FROM Game
        WHERE (Home_Team=? AND Away_Team=?) OR (Home_Team=? AND Away_Team=?)
        ORDER BY Start_Time
    """, (name1, name2, name2, name1)).fetchall()

    if not rows:
        print(f"  No matches found between {name1} and {name2}.")
        c.close()
        return

    w1 = sum(1 for r in rows if r[4]==name1)
    w2 = sum(1 for r in rows if r[4]==name2)
    draws = sum(1 for r in rows if r[4]=='Draw')

    print(f"\n  {'─'*55}")
    print(f"  {name1}  vs  {name2}")
    print(f"  {'─'*55}")
    print(f"  All-time: {name1} {w1} — {draws} — {w2} {name2}  ({len(rows)} matches)\n")
    print(f"  {'HOME':<25} {'SCORE':^7} {'AWAY':<25} {'YEAR'}")
    print(f"  {'─'*60}")
    for home, away, hs, as_, winner, yr in rows[-10:]:  # last 10
        score = f"{hs}-{as_}"
        result = "<" if winner == home else (">" if winner == away else "=")
        print(f"  {home:<25} {score:^7} {away:<25} {yr}  {result}")
    if len(rows) > 10:
        print(f"  (showing last 10 of {len(rows)} matches)")
    c.close()

# ── main menu ────────────────────────────────────────────────────────────────

MENU = [
    ("Top 10 All-Time Scorers",        top_scorers),
    ("Top 10 Winningest Managers",      manager_performance),
    ("Search Player Stats & Awards",   search_player),
    ("League Standings",               league_standings),
    ("Club Profile",                   club_profile),
    ("Award Winners by League",        awards_by_league),
    ("Season Summary",                 season_summary),
    ("Head-to-Head Record",            head_to_head),
    ("Exit",                           None),
]

def main():
    while True:
        print("\n" + "█"*50)
        print("      PITCH PERFECT  —  SOCCER ANALYTICS")
        print("█"*50)
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  {i}. {label}")
        choice = input("\n  Select an option: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(MENU):
                label, fn = MENU[idx]
                if fn is None:
                    print("  Goodbye!")
                    break
                fn()
                continue
        print("  Invalid choice.")

if __name__ == "__main__":
    main()
