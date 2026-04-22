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

| 132 | Clubs | 7,130 | Players |
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
| Data cleaning | rapidfuzz (fuzzy club name matching) |
| CLI | Python (argparse-style menus, 25+ queries) |
| Web UI | Flask 3.1, Jinja2, Bootstrap 5 (dark theme) |
| Version control | Git / GitHub |

**Schema:** 10 tables, foreign key constraints enforced, BCNF analysis performed

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
- Club profiles — managers, top scorers, W/D/L recent results
- Awards — filterable by league and year, links to player profiles

**Database features**
- Correlated subqueries, CTEs, aggregations across 5 leagues
- BCNF violation in `Individual_Award_Wins` identified and fixed
  (dropped redundant `Player` name column — now derived via JOIN)

---

## SLIDE 5 — Team Roles & Contributions (~1 min)

| Team Member | Contributions |
|---|---|
| **Zeynep Baştaş** | Database schema design, data loading scripts, league standings query, season summary, head-to-head, BCNF analysis, web UI |
| **Maggie Farra** | CLI architecture, player/club/manager query functions, data cleaning |
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
3. Click a club → club profile (managers, top scorers, W/D/L results)
4. Click a player → player profile (awards)
5. Awards page → filter by league/year → click player link
6. Players → search a name
7. CLI → season summary or head-to-head demo

**Likely TA questions:**
- How does the standings query work? *(CTE aggregating home + away separately)*
- Why does Game have League_Name if clubs already know their league? *(intentional denormalization for query performance — BCNF violation, documented)*
- What BCNF violations did you find? *(3 found, 1 fixed — Individual_Award_Wins)*
- How did you handle club name inconsistencies? *(standardize_clubs.py with fuzzy matching)*
