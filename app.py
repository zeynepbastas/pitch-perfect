from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)
DB = 'pitch_perfect.db'

LEAGUES       = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
SEASONS       = [2021, 2022, 2023, 2024, 2025]
SEASON_LABELS = {2021:'2020/21', 2022:'2021/22', 2023:'2022/23', 2024:'2023/24', 2025:'2024/25'}

SEASON_SQL = """
    CASE WHEN CAST(substr(Start_Time,4,2) AS INT) >= 7
         THEN CAST(substr(Start_Time,7,4) AS INT) + 1
         ELSE CAST(substr(Start_Time,7,4) AS INT) END = ?
"""

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ── Home ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    conn = db()
    stats = {
        'leagues':  conn.execute("SELECT COUNT(*) FROM League").fetchone()[0],
        'clubs':    conn.execute("SELECT COUNT(*) FROM Club_Teams_Belongs_To").fetchone()[0],
        'players':  conn.execute("SELECT COUNT(*) FROM Player_Plays_For").fetchone()[0],
        'games':    conn.execute("SELECT COUNT(*) FROM Game").fetchone()[0],
    }
    champions = conn.execute("""
        SELECT League_Name, Winner FROM League_Tournament_Has
        WHERE Year = 2025 ORDER BY League_Name
    """).fetchall()
    top_scorers = conn.execute("""
        SELECT Name, Club_Name, Goals, Player_ID FROM Player_Plays_For
        WHERE Goals IS NOT NULL ORDER BY Goals DESC LIMIT 5
    """).fetchall()
    recent_games = conn.execute("""
        SELECT Home_Team, Away_Team, Score, Winning_team, League_Name
        FROM Game ORDER BY Start_Time DESC LIMIT 8
    """).fetchall()
    conn.close()
    return render_template('index.html', stats=stats, champions=champions,
                           top_scorers=top_scorers, recent_games=recent_games)

# ── Leagues ───────────────────────────────────────────────────────────────────

@app.route('/leagues')
def leagues():
    league = request.args.get('league', 'Premier League')
    season = int(request.args.get('season', 2025))

    conn = db()
    standings = conn.execute(f"""
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
    return render_template('leagues.html', standings=standings, leagues=LEAGUES,
                           seasons=SEASONS, season_labels=SEASON_LABELS,
                           selected_league=league, selected_season=season)

# ── Players ───────────────────────────────────────────────────────────────────

@app.route('/players')
def players():
    query   = request.args.get('q', '').strip()
    sort    = request.args.get('sort', 'goals')
    conn    = db()

    if query:
        rows = conn.execute("""
            SELECT p.Player_ID, p.Name, p.DOB, p.Goals, p.Club_Name,
                   p.Market_Value, GROUP_CONCAT(pp.position, ', ') as Positions
            FROM Player_Plays_For p
            LEFT JOIN Player_Position pp ON p.Player_ID = pp.Player_ID
            WHERE p.Name LIKE ?
            GROUP BY p.Player_ID
            LIMIT 50
        """, (f'%{query}%',)).fetchall()
    elif sort == 'market_value':
        rows = conn.execute("""
            SELECT p.Player_ID, p.Name, p.DOB, p.Goals, p.Club_Name,
                   p.Market_Value, GROUP_CONCAT(pp.position, ', ') as Positions
            FROM Player_Plays_For p
            LEFT JOIN Player_Position pp ON p.Player_ID = pp.Player_ID
            WHERE p.Market_Value IS NOT NULL
            GROUP BY p.Player_ID
            ORDER BY p.Market_Value DESC LIMIT 25
        """).fetchall()
    else:
        rows = conn.execute("""
            SELECT p.Player_ID, p.Name, p.DOB, p.Goals, p.Club_Name,
                   p.Market_Value, GROUP_CONCAT(pp.position, ', ') as Positions
            FROM Player_Plays_For p
            LEFT JOIN Player_Position pp ON p.Player_ID = pp.Player_ID
            WHERE p.Goals IS NOT NULL
            GROUP BY p.Player_ID
            ORDER BY p.Goals DESC LIMIT 25
        """).fetchall()
    conn.close()
    return render_template('players.html', players=rows, query=query, sort=sort)

@app.route('/players/<int:pid>')
def player_profile(pid):
    conn = db()
    player = conn.execute(
        "SELECT * FROM Player_Plays_For WHERE Player_ID=?", (pid,)
    ).fetchone()
    if not player:
        conn.close()
        return "Player not found", 404
    positions = conn.execute(
        "SELECT position FROM Player_Position WHERE Player_ID=?", (pid,)
    ).fetchall()
    awards = conn.execute(
        "SELECT Name, Year, League FROM Individual_Award_Wins WHERE Player_ID=? ORDER BY Year",
        (pid,)
    ).fetchall()
    conn.close()
    return render_template('player.html', player=player, positions=positions, awards=awards)

# ── Clubs ─────────────────────────────────────────────────────────────────────

@app.route('/clubs')
def clubs():
    query  = request.args.get('q', '').strip()
    league = request.args.get('league', '')
    conn   = db()

    sql = """
        SELECT Name, Location, League_Name, Number_Of_Wins
        FROM Club_Teams_Belongs_To WHERE 1=1
    """
    params = []
    if query:
        sql += " AND Name LIKE ?"
        params.append(f'%{query}%')
    if league:
        sql += " AND League_Name = ?"
        params.append(league)
    sql += " ORDER BY Number_Of_Wins DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return render_template('clubs.html', clubs=rows, query=query,
                           leagues=LEAGUES, selected_league=league)

@app.route('/clubs/<path:name>')
def club_profile(name):
    conn = db()
    club = conn.execute(
        "SELECT * FROM Club_Teams_Belongs_To WHERE Name=?", (name,)
    ).fetchone()
    if not club:
        conn.close()
        return "Club not found", 404
    managers = conn.execute(
        "SELECT Name, Years_Managed FROM Manager_Manages WHERE Club_Name=? ORDER BY Years_Managed DESC",
        (name,)
    ).fetchall()
    top_players = conn.execute(
        "SELECT Player_ID, Name, Goals, Market_Value FROM Player_Plays_For WHERE Club_Name=? ORDER BY Goals DESC LIMIT 10",
        (name,)
    ).fetchall()
    recent_games = conn.execute("""
        SELECT Home_Team, Away_Team, Score, Winning_team, Start_Time
        FROM Game WHERE Home_Team=? OR Away_Team=?
        ORDER BY Start_Time DESC LIMIT 10
    """, (name, name)).fetchall()
    conn.close()
    return render_template('club.html', club=club, managers=managers,
                           top_players=top_players, recent_games=recent_games)

# ── Managers ──────────────────────────────────────────────────────────────────

@app.route('/managers')
def managers():
    query = request.args.get('q', '').strip()
    conn  = db()
    if query:
        rows = conn.execute("""
            SELECT m.Manager_ID, m.Name, m.Club_Name, m.Years_Managed,
                   COUNT(g.Game_ID) as Wins
            FROM Manager_Manages m
            LEFT JOIN Game g ON m.Club_Name = g.Winning_team
            WHERE m.Name LIKE ?
            GROUP BY m.Manager_ID ORDER BY Wins DESC
        """, (f'%{query}%',)).fetchall()
    else:
        rows = conn.execute("""
            SELECT m.Manager_ID, m.Name, m.Club_Name, m.Years_Managed,
                   COUNT(g.Game_ID) as Wins
            FROM Manager_Manages m
            LEFT JOIN Game g ON m.Club_Name = g.Winning_team
            GROUP BY m.Manager_ID ORDER BY Wins DESC
        """).fetchall()
    conn.close()
    return render_template('managers.html', managers=rows, query=query)

# ── Awards ────────────────────────────────────────────────────────────────────

@app.route('/awards')
def awards():
    league = request.args.get('league', '')
    year   = request.args.get('year', '')
    conn   = db()

    sql    = "SELECT iaw.Name, iaw.Year, iaw.League, p.Name, p.Player_ID FROM Individual_Award_Wins iaw JOIN Player_Plays_For p ON iaw.Player_ID = p.Player_ID WHERE 1=1"
    params = []
    if league:
        sql += " AND iaw.League=?"
        params.append(league)
    if year:
        sql += " AND iaw.Year=?"
        params.append(year)
    sql += " ORDER BY iaw.Year DESC, iaw.League, iaw.Name"
    rows  = conn.execute(sql, params).fetchall()
    years = [r[0] for r in conn.execute(
        "SELECT DISTINCT Year FROM Individual_Award_Wins ORDER BY Year DESC"
    ).fetchall()]
    conn.close()
    return render_template('awards.html', awards=rows, leagues=LEAGUES,
                           years=years, selected_league=league, selected_year=year)

if __name__ == '__main__':
    app.run(debug=True)
