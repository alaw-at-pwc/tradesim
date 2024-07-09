import pandas as pd

data_participants = {
    "Trader_ID": [1, 3, 4, 5],
    "Wealth": [10000, 15000, 20000, 25000],
    "Asset": [100, 150, 200, 250],
    "Profile": ["User", "Admin", "User", "Guest"]
}
df_participants = pd.DataFrame(data_participants)

trader_1 = False
for index, participant in df_participants.iterrows():  
    if participant["Trader_ID"] == 1:
        trader_1 = True

print(trader_1)