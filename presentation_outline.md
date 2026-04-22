# Pitch Perfect — Presentation Outline
## CSDS 341 Spring 2026 | Zeynep Baştaş, Maggie Farra, Baxter King
## 5 minutes total — ~1 min per slide

---

## SLIDE 1 — Title (~15 sec)

**Pitch Perfect**
A European Football Database

CSDS 341 Database Systems — Spring 2026
Zeynep Baştaş · Maggie Farra · Baxter King

---

## SLIDE 2 — Background (~1 min)

**What is Pitch Perfect?**
A relational database for European football — built to answer real questions
about players, clubs, leagues, and season performance.

**Data scope:**
- 5 leagues: Premier League, La Liga, Serie A, Bundesliga, Ligue 1
- 5 seasons: 2020/21 through 2024/25

| 132 | Clubs | 7,125 | Players |
|---|---|---|---|
| 8,982 | Matches | 48 | Managers |

**Why football?**
Rich, relational data — players belong to clubs, clubs belong to leagues,
games have two clubs, players win awards. Perfect for a relational schema.

**Tech stack:**
- SQLite (database)
- Python (data loading, cleaning, CLI)
- Flask + Bootstrap 5 (web UI)

---

## SLIDE 3 — Technologies Used (~45 sec)

| Layer | Technology |
|---|---|
| Database | SQLite 3.43 |
| Schema & loading | Python, pandas, sqlite3 |
| Data sources | football-data.co.uk (matches), transfermarkt-datasets (players), manual research (managers, awards) |
| Data cleaning | Manual mapping dict (club name standardization), rapidfuzz (stadium + award name fuzzy matching) |
| CLI | Python (argparse-style menus, 25+ queries) |
| Web UI | Flask 3.1, Jinja2, Bootstrap 5 (dark theme) |
| Version control | Git / GitHub |

**Schema:** 10 tables + 3 SQL views, foreign key constraints enforced, BCNF analysis performed

---

## SLIDE 4 — Project Functionalities (~1.5 min)

**Command-Line Interface**
- Hierarchical menu with 5 categories
- League standings by season, season summary, head-to-head records
- Player search, top scorers, market values
- Awards by league, manager stats

**Web Application (8 pages)**
- Home dashboard — stats, 2024/25 champions, top scorers, recent results
- League standings — with Champions League / Europa / Relegation zone coloring
- Player profiles — goals, market value, positions, awards
- Club profiles — all-time record (W/D/L), managers, top scorers, recent results
- Awards — filterable by league and year, links to player profiles

**Database features**
- CTEs, correlated subqueries, aggregations across 5 leagues
- 3 SQL views: `vw_player_awards`, `vw_club_record`, `vw_season_champions`
- BCNF violation in `Individual_Award_Wins` identified and fixed
  (dropped redundant `Player` name column — now derived via JOIN)

---

## SLIDE 5 — Team Roles & Contributions (~1 min)

| Team Member | Contributions |
|---|---|
| **Zeynep Baştaş** | Database schema design, data loading scripts, league standings CTE query, season summary, head-to-head, BCNF analysis, SQL views, web UI (Flask/Jinja2) |
| **Maggie Farra** | CLI architecture, player/club/manager query functions, data cleaning (club name standardization, rapidfuzz matching) |
| **Baxter King** | [fill in Baxter's contributions] |

**Shared:**
- Database quality fixes (FK violations, club name standardization, market values)
- CLI merge and integration
- Testing and demo preparation

---

## DEMO FLOW for TA Session
*(separate from the 5-min presentation — TA will test functionality)*

1. Home page → stats dashboard
2. Leagues → Premier League 2024/25 standings (zone colors)
3. Click a club → club profile (all-time record, managers, top scorers, W/D/L results)
4. Click a player → player profile (awards)
5. Awards page → filter by league/year → click player link
6. Players → search a name
7. CLI → season summary or head-to-head demo

**Likely TA questions:**
- How does the standings query work? *(CTE aggregating home + away separately, then JOINed)*
- Why use SQL views? *(Encapsulate complex aggregations — vw_club_record, vw_season_champions, vw_player_awards)*
- What BCNF violations did you find? *(3 found, 1 fixed — Individual_Award_Wins dropped redundant Player column)*
- How did you handle club name inconsistencies? *(Manual mapping dict in standardize_clubs.py; rapidfuzz for stadium/award fuzzy matching)*
- Where does your data come from? *(football-data.co.uk for matches, transfermarkt-datasets for player market values, manual research for managers and awards)*
