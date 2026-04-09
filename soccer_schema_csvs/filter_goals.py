import pandas as pd
print("Reading appearances.csv...")
df = pd.read_csv("appearances.csv")
big5 = ["GB1", "ES1", "IT1", "L1", "FR1"]
df_filtered = df[df["competition_id"].isin(big5)].copy()
goals_by_player = df_filtered.groupby("player_id")["goals"].sum().reset_index()
goals_by_player.columns = ["player_id", "goals"]
goals_by_player.to_csv("player_goals_summary.csv", index=False)
print(f"Done! {len(goals_by_player)} players saved to player_goals_summary.csv")
