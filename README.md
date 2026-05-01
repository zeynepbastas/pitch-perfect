# Pitch Perfect: A Soccer Database For The Big 5 European Football Leagues
CSDS 341 Introduction to Database Systems — Spring 2026
Maggie Farra, Zeynep Baştaş, Baxter King

---

## Requirements

Python 3.11 or later is required. Install dependencies with:

```
pip install flask pandas rapidfuzz bcrypt
```

---

## Database

The database file `pitch_perfect.db` is included in the project directory. No additional setup or data loading is needed.

---

## Running the Web Application

```
python3 app.py
```

Then open your browser and go to:

```
http://127.0.0.1:5000
```

### Pages available:
| Page | URL |
|---|---|
| Home dashboard | / |
| League standings | /leagues |
| Players | /players |
| Player profile | /players/<id> |
| Clubs | /clubs |
| Club profile | /clubs/<name> |
| Awards | /awards |
| Club matching quiz | /quiz |

To use the favorites system, register an account via the Register link in the navigation bar.

---

## Running the Command-Line Interface

```
python3 main.py
```

Use the numbered menus to navigate. Options include:

1. **Leagues** — view all leagues, standings by season, season summary, tournament winners
2. **Clubs** — search clubs, view by league, head-to-head records, top clubs by wins
3. **Players** — search players, top scorers, top market values, awards
4. **Managers** — view all managers, search by name or club
5. **Games** — recent games, search by club or stadium, head-to-head records

Enter `0` at any menu to go back.

---

## Project Structure

```
pitch_perfect.db       — SQLite database
app.py                 — Flask web application
main.py                — Command-line interface
templates/             — HTML templates (Jinja2)
static/                — CSS and static assets
```
