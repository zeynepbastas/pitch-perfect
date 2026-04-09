import sqlite3

DB = 'pitch_perfect.db'

LEAGUES       = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
SEASONS       = [2021, 2022, 2023, 2024, 2025]
SEASON_LABELS = ['2020/21', '2021/22', '2022/23', '2023/24', '2024/25']

def connect():
    return sqlite3.connect(DB)

# ── shared helpers ────────────────────────────────────────────────────────────

def pick(options, labels=None, prompt="  Select: "):
    labels = labels or [str(o) for o in options]
    for i, label in enumerate(labels, 1):
        print(f"    {i}. {label}")
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("  Invalid choice, try again.")

# Season end-year → calendar year SQL filter (DD/MM/YYYY format)
SEASON_SQL = """
    CASE WHEN CAST(substr(Start_Time,4,2) AS INT) >= 7
         THEN CAST(substr(Start_Time,7,4) AS INT) + 1
         ELSE CAST(substr(Start_Time,7,4) AS INT) END = ?
"""

# ═══════════════════════════════════════════════════════════════════
#  LEAGUE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def view_all_leagues():
    conn = connect()
    rows = conn.execute("SELECT * FROM League").fetchall()
    conn.close()
    print(f"\n  {'LEAGUE':<30} {'COUNTRY':<20} TEAMS")
    print("  " + "-"*55)
    for row in rows:
        print(f"  {row[0]:<30} {row[1]:<20} {row[2]}")

def view_leagues_by_country():
    country = input("\n  Enter country: ").strip()
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM League WHERE Country LIKE ?", (f'%{country}%',)
    ).fetchall()
    conn.close()
    if not rows:
        print("  No leagues found.")
        return
    print(f"\n  {'LEAGUE':<30} {'COUNTRY':<20} TEAMS")
    print("  " + "-"*55)
    for row in rows:
        print(f"  {row[0]:<30} {row[1]:<20} {row[2]}")

def view_tournament_winners():
    year = input("\n  Enter year (or Enter for all): ").strip()
    conn = connect()
    if year == "":
        rows = conn.execute(
            "SELECT Name, Year, League_Name, Winner FROM League_Tournament_Has ORDER BY Year DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT Name, Year, League_Name, Winner FROM League_Tournament_Has WHERE Year=? ORDER BY League_Name",
            (year,)
        ).fetchall()
    conn.close()
    if not rows:
        print("  No results found.")
        return
    print(f"\n  {'TOURNAMENT':<25} {'YEAR':<6} {'LEAGUE':<25} WINNER")
    print("  " + "-"*75)
    for row in rows:
        print(f"  {row[0]:<25} {row[1]:<6} {row[2]:<25} {row[3]}")

def season_summary():
    print("\n  Select season:")
    season = pick(SEASONS, SEASON_LABELS)
    season_label = SEASON_LABELS[SEASONS.index(season)]
    conn = connect()
    champions = conn.execute(
        "SELECT League_Name, Winner FROM League_Tournament_Has WHERE Year=? ORDER BY League_Name",
        (season,)
    ).fetchall()
    awards = conn.execute(
        "SELECT League, Name, Player FROM Individual_Award_Wins WHERE Year=? ORDER BY League, Name",
        (season,)
    ).fetchall()
    conn.close()
    print(f"\n  {'─'*58}")
    print(f"  Season Summary — {season_label}")
    print(f"  {'─'*58}")
    print(f"\n  CHAMPIONS")
    for league, winner in champions:
        print(f"    {league:<25} {winner}")
    print(f"\n  INDIVIDUAL AWARDS")
    for league, award, player in awards:
        print(f"    {league:<25} {award:<30} {player}")

def league_standings():
    print("\n  Select league:")
    league = pick(LEAGUES)
    print("\n  Select season:")
    season = pick(SEASONS, SEASON_LABELS)
    season_label = SEASON_LABELS[SEASONS.index(season)]
    conn = connect()
    rows = conn.execute(f"""
        WITH sg AS (
            SELECT * FROM Game WHERE League_Name = ? AND {SEASON_SQL}
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
    conn.close()
    print(f"\n  {'─'*72}")
    print(f"  {league}  —  {season_label}")
    print(f"  {'─'*72}")
    print(f"  {'#':<3} {'CLUB':<25} {'P':>3} {'W':>3} {'D':>3} {'L':>3} {'GF':>4} {'GA':>4} {'GD':>5} {'PTS':>4}")
    print(f"  {'─'*72}")
    for i, (club, p, w, d, l, gf, ga, gd, pts) in enumerate(rows, 1):
        gd_str = f"+{gd}" if gd > 0 else str(gd)
        print(f"  {i:<3} {club:<25} {p:>3} {w:>3} {d:>3} {l:>3} {gf:>4} {ga:>4} {gd_str:>5} {pts:>4}")

# ═══════════════════════════════════════════════════════════════════
#  CLUB FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def view_all_clubs():
    conn = connect()
    rows = conn.execute(
        "SELECT Name, Location, Number_Of_Wins, League_Name FROM Club_Teams_Belongs_To ORDER BY League_Name, Name"
    ).fetchall()
    conn.close()
    print(f"\n  {'CLUB':<28} {'STADIUM':<28} {'WINS':>5}  LEAGUE")
    print("  " + "-"*80)
    for row in rows:
        print(f"  {row[0]:<28} {str(row[1]):<28} {str(row[2]):>5}  {row[3]}")

def search_club_by_name():
    name = input("\n  Enter club name: ").strip()
    conn = connect()
    rows = conn.execute(
        "SELECT Name, Location, Number_Of_Wins, League_Name FROM Club_Teams_Belongs_To WHERE Name LIKE ?",
        (f'%{name}%',)
    ).fetchall()
    conn.close()
    if not rows:
        print("  No clubs found.")
        return
    print(f"\n  {'CLUB':<28} {'STADIUM':<28} {'WINS':>5}  LEAGUE")
    print("  " + "-"*80)
    for row in rows:
        print(f"  {row[0]:<28} {str(row[1]):<28} {str(row[2]):>5}  {row[3]}")

def view_clubs_by_league():
    print("\n  Select league:")
    league = pick(LEAGUES)
    conn = connect()
    rows = conn.execute(
        "SELECT Name, Location, Number_Of_Wins FROM Club_Teams_Belongs_To WHERE League_Name=? ORDER BY Number_Of_Wins DESC",
        (league,)
    ).fetchall()
    conn.close()
    print(f"\n  {'CLUB':<28} {'STADIUM':<30} WINS")
    print("  " + "-"*65)
    for row in rows:
        print(f"  {row[0]:<28} {str(row[1]):<30} {row[2]}")

def view_clubs_by_location():
    location = input("\n  Enter stadium/city: ").strip()
    conn = connect()
    rows = conn.execute(
        "SELECT Name, Location, League_Name FROM Club_Teams_Belongs_To WHERE Location LIKE ?",
        (f'%{location}%',)
    ).fetchall()
    conn.close()
    if not rows:
        print("  No clubs found.")
        return
    for row in rows:
        print(f"  {row[0]:<28} {str(row[1]):<30} {row[2]}")

def view_top_clubs_by_wins():
    conn = connect()
    rows = conn.execute(
        "SELECT Name, Number_Of_Wins, League_Name FROM Club_Teams_Belongs_To ORDER BY Number_Of_Wins DESC LIMIT 20"
    ).fetchall()
    conn.close()
    print(f"\n  {'#':<3} {'CLUB':<28} {'WINS':>5}  LEAGUE")
    print("  " + "-"*60)
    for i, row in enumerate(rows, 1):
        print(f"  {i:<3} {row[0]:<28} {row[1]:>5}  {row[2]}")

def club_profile():
    query = input("\n  Enter club name: ").strip()
    conn = connect()
    club = conn.execute(
        "SELECT Name, Location, League_Name, Number_Of_Wins FROM Club_Teams_Belongs_To WHERE Name LIKE ?",
        (f'%{query}%',)
    ).fetchone()
    if not club:
        print("  Club not found.")
        conn.close()
        return
    name, location, league, wins = club
    managers = conn.execute(
        "SELECT Name, Years_Managed FROM Manager_Manages WHERE Club_Name=? ORDER BY Years_Managed DESC",
        (name,)
    ).fetchall()
    top_players = conn.execute(
        "SELECT Name, Goals FROM Player_Plays_For WHERE Club_Name=? ORDER BY Goals DESC LIMIT 5",
        (name,)
    ).fetchall()
    award_count = conn.execute("""
        SELECT COUNT(*) FROM Individual_Award_Wins iaw
        JOIN Player_Plays_For p ON iaw.Player_ID = p.Player_ID
        WHERE p.Club_Name=?
    """, (name,)).fetchone()[0]
    conn.close()
    print(f"\n  {'─'*48}")
    print(f"  {name}")
    print(f"  {'─'*48}")
    print(f"  League:   {league}")
    print(f"  Stadium:  {location or 'N/A'}")
    print(f"  Wins:     {wins}")
    print(f"  Awards:   {award_count} (current squad)")
    if managers:
        print("  Managers:")
        for mname, yrs in managers:
            print(f"    {mname} ({yrs} yrs)")
    if top_players:
        print("  Top Scorers:")
        for pname, goals in top_players:
            print(f"    {pname:<25} {goals} goals")

def head_to_head():
    club1 = input("\n  Enter first club:  ").strip()
    club2 = input("  Enter second club: ").strip()
    conn = connect()
    r1 = conn.execute(
        "SELECT Name FROM Club_Teams_Belongs_To WHERE Name LIKE ? LIMIT 1", (f'%{club1}%',)
    ).fetchone()
    r2 = conn.execute(
        "SELECT Name FROM Club_Teams_Belongs_To WHERE Name LIKE ? LIMIT 1", (f'%{club2}%',)
    ).fetchone()
    if not r1 or not r2:
        print("  One or both clubs not found.")
        conn.close()
        return
    name1, name2 = r1[0], r2[0]
    rows = conn.execute("""
        SELECT Home_Team, Away_Team, Home_Score, Away_Score, Winning_team,
               substr(Start_Time,7,4) as Year
        FROM Game
        WHERE (Home_Team=? AND Away_Team=?) OR (Home_Team=? AND Away_Team=?)
        ORDER BY Start_Time
    """, (name1, name2, name2, name1)).fetchall()
    conn.close()
    if not rows:
        print(f"  No matches found between {name1} and {name2}.")
        return
    w1    = sum(1 for r in rows if r[4] == name1)
    w2    = sum(1 for r in rows if r[4] == name2)
    draws = sum(1 for r in rows if r[4] == 'Draw')
    print(f"\n  {'─'*62}")
    print(f"  {name1}  vs  {name2}")
    print(f"  {'─'*62}")
    print(f"  All-time: {name1} {w1} — {draws} — {w2} {name2}  ({len(rows)} matches)\n")
    print(f"  {'HOME':<25} {'SCORE':^7} {'AWAY':<25} YEAR  W")
    print(f"  {'─'*62}")
    for home, away, hs, as_, winner, yr in rows[-10:]:
        result = "<" if winner == home else (">" if winner == away else "=")
        print(f"  {home:<25} {hs}-{as_:^5} {away:<25} {yr}  {result}")
    if len(rows) > 10:
        print(f"  (showing last 10 of {len(rows)} matches)")

# ═══════════════════════════════════════════════════════════════════
#  PLAYER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def view_all_players():
    limit = input("\n  How many players to show? ").strip()
    conn = connect()
    rows = conn.execute(
        "SELECT Player_ID, Name, DOB, Goals, Club_Name FROM Player_Plays_For ORDER BY Name LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    print(f"\n  {'ID':<8} {'NAME':<25} {'DOB':<12} {'GOALS':>6}  CLUB")
    print("  " + "-"*80)
    for row in rows:
        print(f"  {row[0]:<8} {row[1]:<25} {str(row[2]):<12} {str(row[3]):>6}  {str(row[4])}")

def view_top_market_values():
    limit = input("\n  How many players to show? ").strip()
    conn  = connect()
    rows  = conn.execute("""
        SELECT Name, Club_Name, Goals, Market_Value
        FROM Player_Plays_For
        WHERE Market_Value IS NOT NULL
        ORDER BY Market_Value DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    print(f"\n  {'#':<3} {'NAME':<25} {'CLUB':<25} {'GOALS':>6}  MARKET VALUE (€)")
    print("  " + "-"*80)
    for i, (name, club, goals, mv) in enumerate(rows, 1):
        print(f"  {i:<3} {name:<25} {str(club):<25} {goals:>6}  €{int(mv):,}")

def search_player_by_name():
    query = input("\n  Enter player name: ").strip()
    conn = connect()
    player = conn.execute(
        "SELECT Player_ID, Name, DOB, Goals, Club_Name, Market_Value FROM Player_Plays_For WHERE Name LIKE ?",
        (f'%{query}%',)
    ).fetchone()
    if not player:
        print("  No player found.")
        conn.close()
        return
    pid, name, dob, goals, club, mv = player
    positions = conn.execute(
        "SELECT position FROM Player_Position WHERE Player_ID=?", (pid,)
    ).fetchall()
    awards = conn.execute(
        "SELECT Name, Year, League FROM Individual_Award_Wins WHERE Player_ID=? ORDER BY Year",
        (pid,)
    ).fetchall()
    conn.close()
    print(f"\n  {'─'*45}")
    print(f"  {name}")
    print(f"  {'─'*45}")
    print(f"  Club:     {club or 'N/A'}")
    print(f"  DOB:      {dob or 'N/A'}")
    print(f"  Goals:    {goals}")
    print(f"  Mkt Val:  €{int(mv):,}" if mv else "  Mkt Val:  N/A")
    if positions:
        print(f"  Position: {', '.join(p[0] for p in positions)}")
    if awards:
        print("  Awards:")
        for aname, yr, league in awards:
            print(f"    {yr}  {aname:<30} ({league})")
    else:
        print("  Awards:   none")

def view_players_by_club():
    club  = input("\n  Enter club name: ").strip()
    limit = input("  How many players to show? ").strip()
    conn  = connect()
    rows  = conn.execute("""
        SELECT p.Player_ID, p.Name, p.DOB, p.Goals, pp.position
        FROM Player_Plays_For p
        LEFT JOIN Player_Position pp ON p.Player_ID = pp.Player_ID
        WHERE p.Club_Name LIKE ?
        ORDER BY p.Goals DESC LIMIT ?
    """, (f'%{club}%', limit)).fetchall()
    conn.close()
    if not rows:
        print("  No players found.")
        return
    print(f"\n  {'ID':<8} {'NAME':<25} {'DOB':<12} {'GOALS':>6}  POSITION")
    print("  " + "-"*70)
    for row in rows:
        print(f"  {row[0]:<8} {row[1]:<25} {str(row[2]):<12} {str(row[3]):>6}  {str(row[4])}")

def view_players_by_position():
    position = input("\n  Enter position (e.g. Forward, Midfielder, Defender, Goalkeeper): ").strip()
    limit    = input("  How many players to show? ").strip()
    conn     = connect()
    rows     = conn.execute("""
        SELECT p.Player_ID, p.Name, p.Goals, p.Club_Name, pp.position
        FROM Player_Plays_For p
        JOIN Player_Position pp ON p.Player_ID = pp.Player_ID
        WHERE pp.position LIKE ?
        ORDER BY p.Goals DESC LIMIT ?
    """, (f'%{position}%', limit)).fetchall()
    conn.close()
    if not rows:
        print("  No players found.")
        return
    print(f"\n  {'ID':<8} {'NAME':<25} {'GOALS':>6}  {'CLUB':<25} POSITION")
    print("  " + "-"*80)
    for row in rows:
        print(f"  {row[0]:<8} {row[1]:<25} {str(row[2]):>6}  {str(row[3]):<25} {row[4]}")

def view_top_scorers():
    conn = connect()
    rows = conn.execute("""
        SELECT Name, Club_Name, Goals
        FROM Player_Plays_For
        WHERE Goals IS NOT NULL
        ORDER BY Goals DESC LIMIT 15
    """).fetchall()
    conn.close()
    print(f"\n  {'#':<3} {'NAME':<25} {'CLUB':<25} GOALS")
    print("  " + "-"*65)
    for i, (name, club, goals) in enumerate(rows, 1):
        print(f"  {i:<3} {name:<25} {str(club):<25} {goals}")

def view_players_by_age():
    limit = input("\n  How many players to show? ").strip()
    conn  = connect()
    rows  = conn.execute("""
        SELECT Player_ID, Name, DOB, Goals, Club_Name
        FROM Player_Plays_For
        WHERE DOB IS NOT NULL
        ORDER BY DOB ASC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    print(f"\n  {'ID':<8} {'NAME':<25} {'DOB':<12} {'GOALS':>6}  CLUB")
    print("  " + "-"*75)
    for row in rows:
        print(f"  {row[0]:<8} {row[1]:<25} {str(row[2]):<12} {str(row[3]):>6}  {str(row[4])}")

def view_player_awards():
    conn = connect()
    rows = conn.execute("""
        SELECT iaw.Name, iaw.Year, iaw.League, p.Name
        FROM Individual_Award_Wins iaw
        JOIN Player_Plays_For p ON iaw.Player_ID = p.Player_ID
        ORDER BY iaw.Year DESC, iaw.League
    """).fetchall()
    conn.close()
    print(f"\n  {'AWARD':<30} {'YEAR':<6} {'LEAGUE':<25} PLAYER")
    print("  " + "-"*85)
    for row in rows:
        print(f"  {row[0]:<30} {row[1]:<6} {row[2]:<25} {row[3]}")

def awards_by_league():
    print("\n  Select league:")
    league = pick(LEAGUES)
    conn   = connect()
    rows   = conn.execute("""
        SELECT Name, Year, Player
        FROM Individual_Award_Wins
        WHERE League = ?
        ORDER BY Name, Year
    """, (league,)).fetchall()
    conn.close()
    print(f"\n  {'─'*58}")
    print(f"  Awards — {league}")
    print(f"  {'─'*58}")
    print(f"  {'AWARD':<30} {'YEAR':<6} WINNER")
    print("  " + "-"*58)
    for award, year, player in rows:
        print(f"  {award:<30} {year:<6} {player}")

# ═══════════════════════════════════════════════════════════════════
#  MANAGER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def view_all_managers():
    conn = connect()
    rows = conn.execute(
        "SELECT Manager_ID, Name, Club_Name, Years_Managed FROM Manager_Manages ORDER BY Club_Name"
    ).fetchall()
    conn.close()
    print(f"\n  {'ID':<6} {'NAME':<25} {'CLUB':<25} YRS")
    print("  " + "-"*65)
    for row in rows:
        print(f"  {row[0]:<6} {row[1]:<25} {row[2]:<25} {row[3]}")

def search_manager_by_name():
    name = input("\n  Enter manager name: ").strip()
    conn = connect()
    rows = conn.execute(
        "SELECT Manager_ID, Name, Club_Name, Years_Managed FROM Manager_Manages WHERE Name LIKE ?",
        (f'%{name}%',)
    ).fetchall()
    conn.close()
    if not rows:
        print("  No managers found.")
        return
    for row in rows:
        print(f"  {row[0]:<6} {row[1]:<25} {row[2]:<25} {row[3]} yrs")

def view_manager_history():
    mid = input("\n  Enter Manager ID: ").strip()
    conn = connect()
    rows = conn.execute("""
        SELECT m.Name, m.Club_Name, y.Years
        FROM Manager_Manages m
        JOIN Manager_Years_Started y ON m.Manager_ID=y.Manager_ID AND m.Club_Name=y.Club_Name
        WHERE m.Manager_ID=? ORDER BY y.Years
    """, (mid,)).fetchall()
    conn.close()
    if not rows:
        print("  No manager found.")
        return
    print(f"\n  {'NAME':<25} {'CLUB':<25} YEAR STARTED")
    print("  " + "-"*60)
    for row in rows:
        print(f"  {row[0]:<25} {row[1]:<25} {row[2]}")

def view_managers_by_club():
    club = input("\n  Enter club name: ").strip()
    conn = connect()
    rows = conn.execute("""
        SELECT Manager_ID, Name, Club_Name, Years_Managed
        FROM Manager_Manages WHERE Club_Name LIKE ? ORDER BY Years_Managed DESC
    """, (f'%{club}%',)).fetchall()
    conn.close()
    if not rows:
        print("  No managers found.")
        return
    for row in rows:
        print(f"  {row[0]:<6} {row[1]:<25} {row[2]:<25} {row[3]} yrs")

def view_top_managers():
    conn = connect()
    rows = conn.execute("""
        SELECT m.Name, m.Club_Name, COUNT(g.Game_ID) as Wins, m.Years_Managed
        FROM Manager_Manages m
        JOIN Game g ON m.Club_Name = g.Winning_team
        GROUP BY m.Manager_ID, m.Name, m.Club_Name
        ORDER BY Wins DESC LIMIT 10
    """).fetchall()
    conn.close()
    print(f"\n  {'#':<3} {'MANAGER':<25} {'CLUB':<25} {'WINS':<6} YRS")
    print("  " + "-"*65)
    for i, (name, club, wins, yrs) in enumerate(rows, 1):
        print(f"  {i:<3} {name:<25} {club:<25} {wins:<6} {yrs}")

# ═══════════════════════════════════════════════════════════════════
#  GAME FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def view_recent_games():
    conn = connect()
    rows = conn.execute("""
        SELECT Game_ID, Home_Team, Away_Team, Start_Time, Score, Winning_team
        FROM Game ORDER BY Start_Time DESC LIMIT 15
    """).fetchall()
    conn.close()
    print(f"\n  {'ID':<8} {'HOME':<22} {'AWAY':<22} {'DATE':<12} {'SCORE':<8} WINNER")
    print("  " + "-"*90)
    for row in rows:
        date = str(row[3])[:10] if row[3] else ''
        print(f"  {row[0]:<8} {row[1]:<22} {row[2]:<22} {date:<12} {str(row[4]):<8} {str(row[5])}")

def search_games_by_club():
    club = input("\n  Enter club name: ").strip()
    conn = connect()
    rows = conn.execute("""
        SELECT g.Game_ID, g.Home_Team, g.Away_Team, g.Start_Time, g.Score, g.Winning_team
        FROM Game g JOIN Plays p ON g.Game_ID = p.Game_ID
        WHERE p.Club_Name LIKE ?
        ORDER BY g.Start_Time DESC LIMIT 20
    """, (f'%{club}%',)).fetchall()
    conn.close()
    if not rows:
        print("  No games found.")
        return
    print(f"\n  {'ID':<8} {'HOME':<22} {'AWAY':<22} {'DATE':<12} {'SCORE':<8} WINNER")
    print("  " + "-"*90)
    for row in rows:
        date = str(row[3])[:10] if row[3] else ''
        print(f"  {row[0]:<8} {row[1]:<22} {row[2]:<22} {date:<12} {str(row[4]):<8} {str(row[5])}")

def view_games_by_winning_team():
    team = input("\n  Enter winning team: ").strip()
    conn = connect()
    rows = conn.execute("""
        SELECT Game_ID, Home_Team, Away_Team, Start_Time, Score, Winning_team
        FROM Game WHERE Winning_team LIKE ?
        ORDER BY Start_Time DESC LIMIT 20
    """, (f'%{team}%',)).fetchall()
    conn.close()
    if not rows:
        print("  No games found.")
        return
    print(f"\n  {'ID':<8} {'HOME':<22} {'AWAY':<22} {'DATE':<12} {'SCORE':<8} WINNER")
    print("  " + "-"*90)
    for row in rows:
        date = str(row[3])[:10] if row[3] else ''
        print(f"  {row[0]:<8} {row[1]:<22} {row[2]:<22} {date:<12} {str(row[4]):<8} {str(row[5])}")

def view_games_by_location():
    location = input("\n  Enter stadium: ").strip()
    conn = connect()
    rows = conn.execute("""
        SELECT Game_ID, Home_Team, Away_Team, Start_Time, Location, Score, Winning_team
        FROM Game WHERE Location LIKE ?
        ORDER BY Start_Time DESC LIMIT 20
    """, (f'%{location}%',)).fetchall()
    conn.close()
    if not rows:
        print("  No games found.")
        return
    print(f"\n  {'ID':<8} {'HOME':<20} {'AWAY':<20} {'DATE':<12} {'STADIUM':<25} SCORE")
    print("  " + "-"*95)
    for row in rows:
        date = str(row[3])[:10] if row[3] else ''
        print(f"  {row[0]:<8} {row[1]:<20} {row[2]:<20} {date:<12} {str(row[4]):<25} {str(row[5])}")

# ═══════════════════════════════════════════════════════════════════
#  SUB-MENUS
# ═══════════════════════════════════════════════════════════════════

def league_menu():
    while True:
        print("\n  ── League Menu ──────────────────")
        print("  1. View all leagues")
        print("  2. View leagues by country")
        print("  3. Tournament winners by year")
        print("  4. Season summary")
        print("  5. League standings")
        print("  0. Back")
        choice = input("\n  Select: ").strip()
        if   choice == "1": view_all_leagues()
        elif choice == "2": view_leagues_by_country()
        elif choice == "3": view_tournament_winners()
        elif choice == "4": season_summary()
        elif choice == "5": league_standings()
        elif choice == "0": break
        else: print("  Invalid choice.")

def club_menu():
    while True:
        print("\n  ── Club Menu ────────────────────")
        print("  1. View all clubs")
        print("  2. Search club by name")
        print("  3. View clubs by league")
        print("  4. View clubs by stadium/city")
        print("  5. Top clubs by wins")
        print("  6. Club profile (detailed)")
        print("  7. Head-to-head record")
        print("  0. Back")
        choice = input("\n  Select: ").strip()
        if   choice == "1": view_all_clubs()
        elif choice == "2": search_club_by_name()
        elif choice == "3": view_clubs_by_league()
        elif choice == "4": view_clubs_by_location()
        elif choice == "5": view_top_clubs_by_wins()
        elif choice == "6": club_profile()
        elif choice == "7": head_to_head()
        elif choice == "0": break
        else: print("  Invalid choice.")

def player_menu():
    while True:
        print("\n  ── Player Menu ──────────────────")
        print("  1. View all players")
        print("  2. Search player by name")
        print("  3. View players by club")
        print("  4. View players by position")
        print("  5. Top scorers")
        print("  6. Top market values")
        print("  7. View players by age")
        print("  8. All award winners")
        print("  9. Awards by league")
        print("  0. Back")
        choice = input("\n  Select: ").strip()
        if   choice == "1": view_all_players()
        elif choice == "2": search_player_by_name()
        elif choice == "3": view_players_by_club()
        elif choice == "4": view_players_by_position()
        elif choice == "5": view_top_scorers()
        elif choice == "6": view_top_market_values()
        elif choice == "7": view_players_by_age()
        elif choice == "8": view_player_awards()
        elif choice == "9": awards_by_league()
        elif choice == "0": break
        else: print("  Invalid choice.")

def manager_menu():
    while True:
        print("\n  ── Manager Menu ─────────────────")
        print("  1. View all managers")
        print("  2. Search manager by name")
        print("  3. Manager history by ID")
        print("  4. Managers by club")
        print("  5. Top 10 winningest managers")
        print("  0. Back")
        choice = input("\n  Select: ").strip()
        if   choice == "1": view_all_managers()
        elif choice == "2": search_manager_by_name()
        elif choice == "3": view_manager_history()
        elif choice == "4": view_managers_by_club()
        elif choice == "5": view_top_managers()
        elif choice == "0": break
        else: print("  Invalid choice.")

def game_menu():
    while True:
        print("\n  ── Game Menu ────────────────────")
        print("  1. Most recent games")
        print("  2. Search games by club")
        print("  3. Games by winning team")
        print("  4. Games by stadium")
        print("  5. Head-to-head record")
        print("  0. Back")
        choice = input("\n  Select: ").strip()
        if   choice == "1": view_recent_games()
        elif choice == "2": search_games_by_club()
        elif choice == "3": view_games_by_winning_team()
        elif choice == "4": view_games_by_location()
        elif choice == "5": head_to_head()
        elif choice == "0": break
        else: print("  Invalid choice.")

# ═══════════════════════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════════════════════

def main():
    while True:
        print("\n" + "█"*42)
        print("   PITCH PERFECT — SOCCER ANALYTICS")
        print("█"*42)
        print("  1. Leagues")
        print("  2. Clubs")
        print("  3. Players")
        print("  4. Managers")
        print("  5. Games")
        print("  0. Exit")
        choice = input("\n  Select: ").strip()
        if   choice == "1": league_menu()
        elif choice == "2": club_menu()
        elif choice == "3": player_menu()
        elif choice == "4": manager_menu()
        elif choice == "5": game_menu()
        elif choice == "0":
            print("  Goodbye!")
            break
        else:
            print("  Invalid choice.")

if __name__ == "__main__":
    main()
