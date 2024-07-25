import pandas as pd

df = pd.DataFrame({
    "ID": [1, 2, 3, 4, 5],
    "Profile": ['A','B','B','C', 'A'],
    "Asset": [100, 140, 400, 420, 300]
})

new_profile = pd.Series({
    "ID" : 6,
    "Asset" : 200
})
df = pd.concat([df, new_profile.to_frame().T], ignore_index=True)
print(df)