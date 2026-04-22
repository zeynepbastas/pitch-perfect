-- ============================================================
-- Pitch Perfect — SQL Query Examples
-- CSDS 341 Spring 2026 | Baştaş, Farra, King
-- ============================================================


-- ============================================================
-- EASY QUERIES
-- ============================================================

-- Easy 1: All clubs in a given league (Germany = Bundesliga)
SELECT Club_Teams_Belongs_To.Name, League_Name
FROM Club_Teams_Belongs_To
JOIN League ON League.Name = Club_Teams_Belongs_To.League_Name
WHERE League.Country = 'Germany';

-- Easy 2: Players with significant goals and high market value
SELECT Name, Club_Name, Goals, Market_Value
FROM Player_Plays_For
WHERE Goals > 14 AND Market_Value > 10000000
ORDER BY Goals DESC;


-- ============================================================
-- MEDIUM QUERIES
-- ============================================================

-- Medium 1: Total goals and matches played per league
SELECT League_Name,
       SUM(Home_Score + Away_Score) AS Total_Goals,
       COUNT(*)                     AS Games_Played
FROM Game
GROUP BY League_Name
ORDER BY Total_Goals DESC;

-- Medium 2: Most cost-efficient clubs (market value per goal scored)
SELECT Club_Name,
       SUM(Market_Value)                            AS Total_Market_Value,
       SUM(Goals)                                   AS Total_Goals,
       (SUM(Market_Value) / NULLIF(SUM(Goals), 0)) AS Cost_Per_Goal
FROM Player_Plays_For
GROUP BY Club_Name
HAVING Cost_Per_Goal IS NOT NULL
ORDER BY Cost_Per_Goal ASC
LIMIT 15;

-- Medium 3: Which positions win the most awards?
SELECT Player_Position.position,
       COUNT(*) AS Award_Count
FROM Individual_Award_Wins
JOIN Player_Position ON Individual_Award_Wins.Player_ID = Player_Position.Player_ID
GROUP BY Player_Position.position
ORDER BY Award_Count DESC;

-- Medium 4: Managers ranked by wins per year at their club
SELECT m.Name AS Manager_Name,
       m.Club_Name,
       m.Years_Managed,
       c.Number_Of_Wins,
       (c.Number_Of_Wins / m.Years_Managed) AS Wins_Per_Year
FROM Manager_Manages AS m
JOIN Club_Teams_Belongs_To AS c ON m.Club_Name = c.Name
WHERE m.Years_Managed > 2
ORDER BY Wins_Per_Year DESC;

-- Medium 5: Players who have won at least one individual award
SELECT ppf.Name,
       ppf.Club_Name,
       ppf.Goals,
       COUNT(*) AS Awards_Won
FROM Player_Plays_For ppf
JOIN Individual_Award_Wins iaw ON ppf.Player_ID = iaw.Player_ID
GROUP BY ppf.Player_ID, ppf.Name, ppf.Club_Name, ppf.Goals
ORDER BY Awards_Won DESC, ppf.Goals DESC
LIMIT 10;


-- ============================================================
-- HARD QUERIES
-- ============================================================

-- Hard 1: Top scorer per league (correlated subquery)
SELECT ppf.Name, ppf.Club_Name, ctb.League_Name, ppf.Goals
FROM Player_Plays_For ppf
JOIN Club_Teams_Belongs_To ctb ON ppf.Club_Name = ctb.Name
WHERE ppf.Goals = (
    SELECT MAX(ppf2.Goals)
    FROM Player_Plays_For ppf2
    JOIN Club_Teams_Belongs_To ctb2 ON ppf2.Club_Name = ctb2.Name
    WHERE ctb2.League_Name = ctb.League_Name
)
ORDER BY ppf.Goals DESC;

-- Hard 2: Clubs winning more away than at home (CTE)
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
       h.wins            AS Home_Wins,
       a.wins            AS Away_Wins,
       (a.wins - h.wins) AS Advantage
FROM home_wins h
JOIN away_wins a ON h.Club = a.Club
WHERE a.wins > h.wins
ORDER BY Advantage DESC;

-- Hard 3: Premier League 2024/25 standings (CTE aggregating home + away separately)
WITH sg AS (
    SELECT * FROM Game
    WHERE League_Name = 'Premier League'
      AND CASE WHEN CAST(substr(Start_Time,4,2) AS INT) >= 7
               THEN CAST(substr(Start_Time,7,4) AS INT) + 1
               ELSE CAST(substr(Start_Time,7,4) AS INT) END = 2025
),
home AS (
    SELECT Home_Team AS Club, COUNT(*) AS P,
           SUM(CASE WHEN Winning_team=Home_Team THEN 1 ELSE 0 END) AS W,
           SUM(CASE WHEN Winning_team='Draw'    THEN 1 ELSE 0 END) AS D,
           SUM(CASE WHEN Winning_team=Away_Team THEN 1 ELSE 0 END) AS L,
           SUM(Home_Score) AS GF, SUM(Away_Score) AS GA
    FROM sg GROUP BY Home_Team
),
away AS (
    SELECT Away_Team AS Club, COUNT(*) AS P,
           SUM(CASE WHEN Winning_team=Away_Team THEN 1 ELSE 0 END) AS W,
           SUM(CASE WHEN Winning_team='Draw'    THEN 1 ELSE 0 END) AS D,
           SUM(CASE WHEN Winning_team=Home_Team THEN 1 ELSE 0 END) AS L,
           SUM(Away_Score) AS GF, SUM(Home_Score) AS GA
    FROM sg GROUP BY Away_Team
)
SELECT h.Club,
       h.P+a.P AS P, h.W+a.W AS W, h.D+a.D AS D, h.L+a.L AS L,
       h.GF+a.GF AS GF, h.GA+a.GA AS GA,
       (h.GF+a.GF)-(h.GA+a.GA) AS GD,
       (h.W+a.W)*3 + (h.D+a.D) AS Pts
FROM home h JOIN away a USING(Club)
ORDER BY Pts DESC, GD DESC, GF DESC;
