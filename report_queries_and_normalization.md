# Pitch Perfect — SQL Queries, RA, TRC, and Normalization Analysis
## CSDS 341 Spring 2026 | Zeynep Baştaş, Maggie Farra, Baxter King

---

## Part 1: SQL Query Examples

### Easy Queries

**Easy 1 — Prolific Scorers**
*List all players who have scored more than 100 goals, sorted by goals descending.*

```sql
SELECT Name, Club_Name, Goals
FROM Player_Plays_For
WHERE Goals > 100
ORDER BY Goals DESC;
```

Sample output:
| Name | Club_Name | Goals |
|---|---|---|
| Robert Lewandowski | Barcelona | 362 |
| Harry Kane | Bayern München | 305 |
| Mohamed Salah | Liverpool | 226 |
| … | … | … |

---

**Easy 2 — Premier League Clubs and Their Stadiums**
*List all club names and their stadium locations in the Premier League.*

```sql
SELECT Name, Location
FROM Club_Teams_Belongs_To
WHERE League_Name = 'Premier League';
```

---

### Medium Queries

**Medium 1 — Goals Scored Per League**
*Total goals and number of matches played per league, most prolific first.*

```sql
SELECT League_Name,
       SUM(Home_Score + Away_Score) AS Total_Goals,
       COUNT(*)                     AS Games_Played
FROM Game
GROUP BY League_Name
ORDER BY Total_Goals DESC;
```

Sample output:
| League_Name | Total_Goals | Games_Played |
|---|---|---|
| Premier League | 10438 | 3040 |
| La Liga | 10011 | 2756 |
| Bundesliga | 9167 | 2652 |
| Serie A | 9024 | 3044 |
| Ligue 1 | 8363 | 3034 |

---

**Medium 2 — Award-Winning Players**
*Players who have won at least one individual award, ranked by awards won.*

```sql
SELECT ppf.Name,
       ppf.Club_Name,
       ppf.Goals,
       COUNT(*) AS Awards_Won
FROM Player_Plays_For ppf
JOIN Individual_Award_Wins iaw ON ppf.Player_ID = iaw.Player_ID
GROUP BY ppf.Player_ID, ppf.Name, ppf.Club_Name, ppf.Goals
ORDER BY Awards_Won DESC, ppf.Goals DESC
LIMIT 10;
```

Sample output:
| Name | Club_Name | Goals | Awards_Won |
|---|---|---|---|
| Kylian Mbappé | Real Madrid | 245 | 8 |
| Robert Lewandowski | Barcelona | 362 | 6 |
| Harry Kane | Bayern München | 305 | 5 |
| Erling Haaland | Manchester City | 169 | 3 |

---

### Hard Queries

**Hard 1 — Clubs That Win More Away Than at Home (CTE)**
*Using Common Table Expressions, find clubs whose away-win count exceeds their home-win count.*

```sql
WITH home_wins AS (
    SELECT Home_Team AS Club, COUNT(*) AS wins
    FROM Game
    WHERE Winning_Team = Home_Team
    GROUP BY Home_Team
),
away_wins AS (
    SELECT Away_Team AS Club, COUNT(*) AS wins
    FROM Game
    WHERE Winning_Team = Away_Team
    GROUP BY Away_Team
)
SELECT h.Club,
       h.wins AS Home_Wins,
       a.wins AS Away_Wins,
       (a.wins - h.wins) AS Advantage
FROM home_wins h
JOIN away_wins a ON h.Club = a.Club
WHERE a.wins > h.wins
ORDER BY Advantage DESC;
```

Sample output:
| Club | Home_Wins | Away_Wins | Advantage |
|---|---|---|---|
| Toulouse | 14 | 21 | 7 |
| Atalanta | 48 | 53 | 5 |
| Milan | 54 | 56 | 2 |

---

**Hard 2 — Top Scorer Per League (Correlated Subquery)**
*For each of the five leagues, find the player with the highest career goal tally.*

```sql
SELECT ppf.Name,
       ppf.Club_Name,
       ctb.League_Name,
       ppf.Goals
FROM Player_Plays_For ppf
JOIN Club_Teams_Belongs_To ctb ON ppf.Club_Name = ctb.Name
WHERE ppf.Goals = (
    SELECT MAX(ppf2.Goals)
    FROM Player_Plays_For ppf2
    JOIN Club_Teams_Belongs_To ctb2 ON ppf2.Club_Name = ctb2.Name
    WHERE ctb2.League_Name = ctb.League_Name
)
ORDER BY ppf.Goals DESC;
```

Sample output:
| Name | Club_Name | League_Name | Goals |
|---|---|---|---|
| Robert Lewandowski | Barcelona | La Liga | 362 |
| Harry Kane | Bayern München | Bundesliga | 305 |
| Mohamed Salah | Liverpool | Premier League | 226 |
| Pierre-Emerick Aubameyang | Marseille | Ligue 1 | 222 |
| Romelu Lukaku | Napoli | Serie A | 206 |

---

## Part 2: Relational Algebra (RA)

**RA 1 (Easy) — Premier League Clubs**

π_{Name, Location}(σ_{League_Name = 'Premier League'}(Club_Teams_Belongs_To))

---

**RA 2 (Medium) — Award-Winning Players**

*Find names and club affiliations of players who have won at least one award.*

π_{Name, Club_Name}(Player_Plays_For ⋈_{Player_Plays_For.Player_ID = Individual_Award_Wins.Player_ID} Individual_Award_Wins)

---

**RA 3 (Hard) — Players with Goals Above League Average**

Let Avg_Goals be the average goals per league (computed via grouping):

```
LeagueAvg ← _{League_Name} G_{AVG(Goals) → Avg_Goals}(
    Player_Plays_For ⋈_{Club_Name = Name} Club_Teams_Belongs_To
)

PlayerLeague ← Player_Plays_For ⋈_{Club_Name = Name} Club_Teams_Belongs_To

Result ← π_{Name, Goals, League_Name}(
    σ_{Goals > Avg_Goals}(PlayerLeague ⋈_{League_Name = League_Name} LeagueAvg)
)
```

---

## Part 3: Tuple Relational Calculus (TRC)

**TRC 1 (Easy) — Premier League Clubs**

{ t | ∃c ∈ Club_Teams_Belongs_To (
    c.League_Name = 'Premier League' ∧
    t.Name = c.Name ∧
    t.Location = c.Location
)}

---

**TRC 2 (Medium) — Award-Winning Players**

{ t | ∃p ∈ Player_Plays_For ∃a ∈ Individual_Award_Wins (
    p.Player_ID = a.Player_ID ∧
    t.Name = p.Name ∧
    t.Club_Name = p.Club_Name
)}

---

**TRC 3 (Hard) — Players Scoring More Than 200 Goals in Their League**

{ t | ∃p ∈ Player_Plays_For ∃c ∈ Club_Teams_Belongs_To (
    p.Club_Name = c.Name ∧
    p.Goals > 200 ∧
    t.Name = p.Name ∧
    t.Goals = p.Goals ∧
    t.League_Name = c.League_Name
)}

---

## Part 4: Functional Dependency (FD) Analysis

### League
**Attributes:** Name, Country, Number_Of_Teams  
**FDs:**
- Name → Country, Number_Of_Teams

**Candidate Keys:** {Name}  
**BCNF:** ✅ Yes — every FD's LHS is a superkey.

---

### League_Tournament_Has
**Attributes:** Name, Year, League_Name, Winner  
**Declared PK:** (Name, Year)  
**FDs:**
- (Name, Year) → League_Name, Winner
- Name → Year *(the Year is encoded in Name, e.g., "Bundesliga 2021" → 2021)*
- Name → League_Name, Winner *(by transitivity)*

**Candidate Keys:** {Name} *(Name alone determines all attributes)*  
**BCNF:** ✅ Technically satisfied — all determinants are superkeys.  
**Design note:** Year is redundant (embedded in Name), which is a denormalization smell. In a stricter design the Name would be just the league name and (Name, Year) would be a natural composite key with no embedded data.

---

### Club_Teams_Belongs_To
**Attributes:** Name, Location, Number_Players, Number_Of_Wins, League_Name  
**FDs:**
- Name → Location, Number_Players, Number_Of_Wins, League_Name

**Candidate Keys:** {Name}  
**BCNF:** ✅ Yes.

---

### Manager_Manages
**Attributes:** Manager_ID, Club_Name, Name, Years_Managed  
**Declared PK:** (Manager_ID, Club_Name)  
**FDs:**
- (Manager_ID, Club_Name) → Name, Years_Managed
- **Manager_ID → Name** *(a manager's personal name is determined by their ID alone, independent of which club they managed)*

**Candidate Keys:** {(Manager_ID, Club_Name)}  
**BCNF:** ❌ **Violation** — Manager_ID → Name, but Manager_ID is not a superkey.  
**2NF:** ❌ Also a 2NF violation — Name is partially dependent on the composite PK.

**BCNF Decomposition:**
```
Manager(Manager_ID PK, Name)
Manager_Manages(Manager_ID FK, Club_Name FK, Years_Managed)  PK: (Manager_ID, Club_Name)
```

---

### Manager_Years_Started
**Attributes:** Manager_ID, Club_Name, Years  
**PK:** (Manager_ID, Club_Name, Years)  
**FDs:** None beyond the trivial (all attributes are part of the key).  
**BCNF:** ✅ Yes — no non-key attributes.

---

### Game
**Attributes:** Game_ID, Home_Team, Away_Team, Start_Time, Location, Score, Winning_team, Home_Score, Away_Score, League_Name  
**PK:** Game_ID  
**FDs:**
- Game_ID → all other attributes *(from PK)*
- **Home_Team → League_Name** *(each club belongs to exactly one league — transitive via Club_Teams_Belongs_To)*
- **Away_Team → League_Name** *(same reasoning)*

**Candidate Keys:** {Game_ID}  
**BCNF:** ❌ **Violation** — Home_Team → League_Name (and Away_Team → League_Name), but neither is a superkey of Game.

**Explanation:** League_Name was added to Game as a denormalization to speed up queries (avoiding a JOIN to Club_Teams_Belongs_To). In a fully normalized schema, League_Name would be omitted from Game and derived via join. This is an intentional trade-off between normalization and query performance.

**BCNF Decomposition (if strictly applied):**
```
Game(Game_ID, Home_Team, Away_Team, Start_Time, Location, Score, Winning_team, Home_Score, Away_Score)
-- League_Name retrieved by: Game JOIN Club_Teams_Belongs_To ON Home_Team = Name
```

---

### Plays
**Attributes:** Game_ID, Club_Name  
**PK:** (Game_ID, Club_Name)  
**FDs:** None — all attributes are part of the key.  
**BCNF:** ✅ Yes.

---

### Player_Plays_For
**Attributes:** Player_ID, Name, DOB, Market_Value, Goals, Club_Name  
**FDs:**
- Player_ID → Name, DOB, Market_Value, Goals, Club_Name

**Candidate Keys:** {Player_ID}  
**BCNF:** ✅ Yes.

---

### Player_Position
**Attributes:** Player_ID, position  
**PK:** (Player_ID, position)  
**FDs:** None — all attributes are part of the key.  
**BCNF:** ✅ Yes.

---

### Individual_Award_Wins
**Original Attributes:** Name, Year, League, Player, Player_ID  
**PK:** (Name, Year, League)  
**FDs (original schema):**
- (Name, Year, League) → Player, Player_ID
- **Player_ID → Player** *(a player's name is determined by their ID — stored redundantly here and in Player_Plays_For)*

**Candidate Keys:** {(Name, Year, League)}  
**BCNF:** ❌ **Violation detected** — Player_ID → Player, but Player_ID is not a superkey.

**Explanation:** The `Player` (name text) column was redundant — it can always be retrieved by joining on `Player_ID` to `Player_Plays_For`. Storing it here duplicated data and risked inconsistency (if a player's name was corrected in one table but not the other).

**BCNF Decomposition (implemented):**
```sql
-- Applied via: ALTER TABLE Individual_Award_Wins DROP COLUMN Player;
Individual_Award_Wins(Name, Year, League, Player_ID)  PK: (Name, Year, League)
```

All queries that previously read `Player` from `Individual_Award_Wins` were updated to JOIN `Player_Plays_For`:

```sql
-- Before (violates BCNF — Player stored redundantly):
SELECT Name, Year, League, Player FROM Individual_Award_Wins;

-- After (BCNF-compliant — name derived via join):
SELECT iaw.Name, iaw.Year, iaw.League, p.Name
FROM Individual_Award_Wins iaw
JOIN Player_Plays_For p ON iaw.Player_ID = p.Player_ID;
```

**Result:** `Individual_Award_Wins` is now in BCNF. ✅

---

## Part 5: Normalization Summary

| Table | 1NF | 2NF | 3NF | BCNF | Violation |
|---|---|---|---|---|---|
| League | ✅ | ✅ | ✅ | ✅ | — |
| League_Tournament_Has | ✅ | ✅ | ✅ | ✅ | Year embedded in Name (design smell) |
| Club_Teams_Belongs_To | ✅ | ✅ | ✅ | ✅ | — |
| **Manager_Manages** | ✅ | ❌ | ❌ | ❌ | Manager_ID → Name (partial dep on composite PK) |
| Manager_Years_Started | ✅ | ✅ | ✅ | ✅ | — |
| **Game** | ✅ | ✅ | ❌ | ❌ | Home_Team → League_Name (transitive, intentional) |
| Plays | ✅ | ✅ | ✅ | ✅ | — |
| Player_Plays_For | ✅ | ✅ | ✅ | ✅ | — |
| Player_Position | ✅ | ✅ | ✅ | ✅ | — |
| Individual_Award_Wins | ✅ | ✅ | ✅ | ✅ | **Fixed** — dropped `Player` column, now joins `Player_Plays_For` |

### BCNF Violations — Status

| # | Table | Violation | Status |
|---|---|---|---|
| 1 | Manager_Manages | Manager_ID → Name (partial dep on composite PK) | Documented; decomposition shown above |
| 2 | Game | Home_Team → League_Name (transitive) | Intentional denormalization — retained for performance |
| 3 | Individual_Award_Wins | Player_ID → Player (redundant name storage) | **Fixed** — `Player` column dropped, all queries updated to JOIN |
