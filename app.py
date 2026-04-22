from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'pitchperfect341'
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
        SELECT League_Name, Winner, Country FROM vw_season_champions
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
    is_saved = False
    if session.get('user_id'):
        is_saved = conn.execute(
            "SELECT 1 FROM Favorite WHERE User_ID=? AND Type='player' AND Reference=?",
            (session['user_id'], str(pid))
        ).fetchone() is not None
    conn.close()
    return render_template('player.html', player=player, positions=positions,
                           awards=awards, is_saved=is_saved)

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
    record = conn.execute(
        "SELECT Games, Wins, Draws, Losses, Goals_For, Goals_Against, Goal_Diff FROM vw_club_record WHERE Name=?",
        (name,)
    ).fetchone()
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
    is_saved = False
    if session.get('user_id'):
        is_saved = conn.execute(
            "SELECT 1 FROM Favorite WHERE User_ID=? AND Type='club' AND Reference=?",
            (session['user_id'], name)
        ).fetchone() is not None
    conn.close()
    return render_template('club.html', club=club, record=record, managers=managers,
                           top_players=top_players, recent_games=recent_games,
                           is_saved=is_saved)

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

    sql    = "SELECT Award_Name, Year, League, Player_Name, Player_ID FROM vw_player_awards WHERE 1=1"
    params = []
    if league:
        sql += " AND League=?"
        params.append(league)
    if year:
        sql += " AND Year=?"
        params.append(year)
    sql += " ORDER BY Year DESC, League, Award_Name"
    rows  = conn.execute(sql, params).fetchall()
    years = [r[0] for r in conn.execute(
        "SELECT DISTINCT Year FROM Individual_Award_Wins ORDER BY Year DESC"
    ).fetchall()]
    conn.close()
    return render_template('awards.html', awards=rows, leagues=LEAGUES,
                           years=years, selected_league=league, selected_year=year)

# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            flash('Username and password required.')
            return render_template('register.html')
        conn = db()
        existing = conn.execute("SELECT 1 FROM User WHERE Username=?", (username,)).fetchone()
        if existing:
            flash('Username already taken.')
            conn.close()
            return render_template('register.html')
        conn.execute("INSERT INTO User (Username, Password_Hash) VALUES (?, ?)",
                     (username, generate_password_hash(password)))
        conn.commit()
        user = conn.execute("SELECT User_ID FROM User WHERE Username=?", (username,)).fetchone()
        conn.close()
        session['user_id'] = user['User_ID']
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = db()
        user = conn.execute("SELECT * FROM User WHERE Username=?", (username,)).fetchone()
        conn.close()
        if not user or not check_password_hash(user['Password_Hash'], password):
            flash('Invalid username or password.')
            return render_template('login.html')
        session['user_id'] = user['User_ID']
        session['username'] = user['Username']
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ── Favorites ─────────────────────────────────────────────────────────────────

@app.route('/favorite/add', methods=['POST'])
def favorite_add():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    ftype = request.form['type']
    ref   = request.form['reference']
    back  = request.form.get('back', '/')
    conn  = db()
    conn.execute("INSERT OR IGNORE INTO Favorite (User_ID, Type, Reference) VALUES (?,?,?)",
                 (session['user_id'], ftype, ref))
    conn.commit()
    conn.close()
    return redirect(back)

@app.route('/favorite/remove', methods=['POST'])
def favorite_remove():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    ftype = request.form['type']
    ref   = request.form['reference']
    back  = request.form.get('back', '/')
    conn  = db()
    conn.execute("DELETE FROM Favorite WHERE User_ID=? AND Type=? AND Reference=?",
                 (session['user_id'], ftype, ref))
    conn.commit()
    conn.close()
    return redirect(back)

@app.route('/favorites')
def favorites():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = db()
    players = conn.execute("""
        SELECT p.Player_ID, p.Name, p.Club_Name, p.Goals
        FROM Favorite f
        JOIN Player_Plays_For p ON f.Reference = CAST(p.Player_ID AS TEXT)
        WHERE f.User_ID=? AND f.Type='player'
        ORDER BY p.Name
    """, (session['user_id'],)).fetchall()
    clubs = conn.execute("""
        SELECT c.Name, c.League_Name, c.Location, c.Number_Of_Wins
        FROM Favorite f
        JOIN Club_Teams_Belongs_To c ON f.Reference = c.Name
        WHERE f.User_ID=? AND f.Type='club'
        ORDER BY c.Name
    """, (session['user_id'],)).fetchall()
    conn.close()
    return render_template('favorites.html', players=players, clubs=clubs)

# ── Quiz ──────────────────────────────────────────────────────────────────────

@app.route('/quiz')
def quiz():
    return render_template('quiz.html', leagues=LEAGUES)

@app.route('/quiz/result', methods=['POST'])
def quiz_result():
    style      = request.form.get('style', 'balanced')
    size       = request.form.get('size', 'giant')
    league     = request.form.get('league', 'any')
    home_pref  = request.form.get('home_pref', 'any')
    efficiency = request.form.get('efficiency', 'any')

    conn = db()
    clubs = conn.execute("""
        WITH home_stats AS (
            SELECT Home_Team AS Club,
                   COUNT(*) AS hg,
                   SUM(Home_Score) AS hgf,
                   SUM(Away_Score) AS hga,
                   SUM(CASE WHEN Winning_team=Home_Team THEN 1 ELSE 0 END) AS hw
            FROM Game GROUP BY Home_Team
        ),
        away_stats AS (
            SELECT Away_Team AS Club,
                   COUNT(*) AS ag,
                   SUM(Away_Score) AS agf,
                   SUM(Home_Score) AS aga,
                   SUM(CASE WHEN Winning_team=Away_Team THEN 1 ELSE 0 END) AS aw
            FROM Game GROUP BY Away_Team
        )
        SELECT c.Name, c.League_Name, c.Location, c.Number_Of_Wins,
               h.hg + a.ag  AS total_games,
               h.hgf + a.agf AS total_gf,
               h.hga + a.aga AS total_ga,
               h.hw + a.aw   AS total_wins,
               h.hw AS home_wins, h.hg AS home_games,
               a.aw AS away_wins, a.ag AS away_games
        FROM Club_Teams_Belongs_To c
        JOIN home_stats h ON c.Name = h.Club
        JOIN away_stats a ON c.Name = a.Club
    """).fetchall()
    conn.close()

    if league != 'any':
        clubs = [c for c in clubs if c['League_Name'] == league]

    # Compute per-club stats
    def stats(c):
        tg = c['total_games'] or 1
        gf = c['total_gf'] or 0
        return {
            'gf_pg':  gf / tg,
            'ga_pg':  c['total_ga'] / tg,
            'wr':     c['total_wins'] / tg,
            'hwr':    c['home_wins'] / (c['home_games'] or 1),
            'awr':    c['away_wins'] / (c['away_games'] or 1),
            'wpg':    c['total_wins'] / (gf + 0.1),  # wins per goal = clinical
        }

    all_stats = [stats(c) for c in clubs]

    def norm(vals):
        lo, hi = min(vals), max(vals)
        return [(v - lo) / (hi - lo + 1e-9) for v in vals]

    gf_n   = norm([s['gf_pg'] for s in all_stats])
    ga_n   = norm([s['ga_pg'] for s in all_stats])
    hwr_n  = norm([s['hwr']   for s in all_stats])
    awr_n  = norm([s['awr']   for s in all_stats])
    wins_n = norm([c['Number_Of_Wins'] or 0 for c in clubs])
    wpg_n  = norm([s['wpg']   for s in all_stats])

    scored = []
    for i, c in enumerate(clubs):
        score = 0
        if style == 'attack':       score += gf_n[i]                           * 25
        elif style == 'defense':    score += (1-ga_n[i])*12 + (1-gf_n[i])*13
        else:                       score += (gf_n[i]+(1-ga_n[i]))            * 12

        if size == 'giant':         score += wins_n[i]                 * 38
        elif size == 'underdog':    score += (1 - wins_n[i])           * 38

        if home_pref == 'home':     score += hwr_n[i]                  * 10
        elif home_pref == 'away':   score += awr_n[i]                  * 10

        if efficiency == 'clinical':score += (1 - gf_n[i])             * 27
        elif efficiency == 'flair': score += gf_n[i]                   * 27

        scored.append((score, dict(c)))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[0][1] if scored else None

    # Build a personalised reason string
    reasons = []
    if style == 'attack':
        reasons.append(f"they score {best['total_gf']//(best['total_games'] or 1)} goals per game on average")
    elif style == 'defense':
        reasons.append(f"they concede only {best['total_ga']//(best['total_games'] or 1)} goals per game")
    else:
        gd = best['total_gf'] - best['total_ga']
        reasons.append(f"they have a goal difference of +{gd}" if gd >= 0 else f"they play a balanced game")

    if size == 'giant':
        reasons.append(f"with {best['Number_Of_Wins']} all-time wins they're a true powerhouse")
    elif size == 'underdog':
        reasons.append("they're a scrappy club that punches above their weight")

    if home_pref == 'home':
        pct = round(best['home_wins'] / (best['home_games'] or 1) * 100)
        reasons.append(f"their home record is fierce — {pct}% win rate at {best['Location'] or 'home'}")
    elif home_pref == 'away':
        pct = round(best['away_wins'] / (best['away_games'] or 1) * 100)
        reasons.append(f"they thrive on the road with a {pct}% away win rate")

    reason = ", and ".join(reasons) + "."
    return render_template('quiz_result.html', club=best, reason=reason,
                           style=style, size=size, league=league, home_pref=home_pref)

if __name__ == '__main__':
    app.run(debug=True)
