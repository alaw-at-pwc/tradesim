import pandas as pd

df = pd.DataFrame({
    "ID": [1, 2, 3, 4, 5],
    "Profile": ['A','B','B','C', 'A'],
    "Asset": [100, 140, 400, 420, 300]
})

profiles = ['A', 'B']
condition = df["Profile"] != 'C'
condition2 = df["Asset"] < 150
mask = condition & condition2
new_df = df[mask]

print(new_df)