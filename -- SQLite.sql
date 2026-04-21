-- SQLite
SELECT Club_Teams_Belongs_To.Name, League_Name 
FROM 'Club_Teams_Belongs_To' 
JOIN League ON League.Name = Club_Teams_Belongs_To.League_Name 
WHERE League.Country = 'Germany';

SELECT Name, Club_Name, Goals, Market_Value 
FROM Player_Plays_For 
WHERE Goals > 14 AND Market_Value > 10000000 
ORDER BY Goals DESC;


SELECT Club_Name, 
SUM(Market_Value) AS Total_Wages, 
SUM(Goals) AS Total_Goals,
 (SUM(Market_Value) / NULLIF(SUM(Goals), 0)) AS Cost_Per_Goal 
FROM Player_Plays_For 
GROUP BY Club_Name 
HAVING Cost_Per_Goal IS NOT NULL 
ORDER BY Cost_Per_Goal ASC;

SELECT Player_Position.position, 
COUNT(Individual_Award_Wins.Name) AS Award_Count 
FROM Individual_Award_Wins 
JOIN Player_Position ON Individual_Award_Wins.Player_ID = Player_Position.Player_ID WHERE Individual_Award_Wins.Year < 2024 AND Individual_Award_Wins.Year > 2018 
GROUP BY Player_Position.position 
ORDER BY Award_Count DESC;

SELECT m.Name AS Manager_Name, m.Club_Name, m.Years_Managed, 
c.Number_Of_Wins, (c.Number_Of_Wins / m.Years_Managed) AS Wins_Per_Year 
FROM Manager_Manages as m 
JOIN Club_Teams_Belongs_To AS c ON m.Club_Name = c.Name 
WHERE m.Years_Managed > 2 
ORDER BY Wins_Per_Year DESC;

SELECT m.Name AS Manager_Name, m.Club_Name, m.Years_Managed, 
c.Number_Of_Wins, (c.Number_Of_Wins / m.Years_Managed) AS Wins_Per_Year 
FROM Manager_Manages as m 
JOIN Club_Teams_Belongs_To AS c ON m.Club_Name = c.Name 
WHERE m.Years_Managed > 2 
ORDER BY Wins_Per_Year DESC;


