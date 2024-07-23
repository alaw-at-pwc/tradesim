# This script sets out the parameters that are used to generate the randomised profiles for all participants. They will be allocated a profile type, and will recive attirbutes based on this allocaiton.
import pandas as pd
import numpy as np

# S.1 & S.2 & S.3
def participant_creation (participant_num, liquidity):
    participant_num += 1
    i = 1
    profiles = ["IB Trader", "WM Trader", "Market Maker", "HR Retail Investor", "LR Retail Investor", "HR Private Investor", "LR Private Investor"]
    profile_proportions = [0.50, 0.08, 0.02, 0.15, 0.15, 0.05, 0.05]

    # Check to see that the proportions add up to 1
    if not np.isclose(sum(profile_proportions), 1.0):
        raise ValueError("Profile proportions do not sum up to 1.")
    
    # Calculating number of participants for each string, and adjusting to match pariticpant_num
    num_assignments = [int(round(p * participant_num)) for p in profile_proportions]

    total_assigned = sum(num_assignments)
    while total_assigned < participant_num:
        for i in range(len(num_assignments)):
            if total_assigned < participant_num:
                num_assignments [i] += 1
                total_assigned += 1
            else:
                break
    while total_assigned > participant_num:
        for i in range(len(num_assignments)):
            if total_assigned > participant_num and num_assignments[i] > 0:
                num_assignments[i] -= 1
                total_assigned -= 1
            else:
                break
    
    assigned_profiles = []
    for profile, count in zip(profiles, num_assignments):
        assigned_profiles.extend([profile] * count)

    # Validation check against number of participants 
    assigned_profiles = assigned_profiles[:participant_num]
    # Creating unique IDs
    pariticipant_ids = [i for i in range(participant_num)]

    df_participants = pd.DataFrame({
        "Trader_ID" : pariticipant_ids,
        "Asset" : 0,
        "Wealth" : 0,
        "Risk" : 0, 
        "Activity" : 0,
        "Delay" : np.random.poisson(lam=2),
        "Profile" : assigned_profiles,
        "PreAsset" : 0,
        "PreWealth" : 0
    })

    df_participants["Risk"] = df_participants["Risk"].astype(float) 
    df_participants["Activity"] = df_participants["Activity"].astype(float)

    # function to scale the values based on the liquidity setting
    def liquidity_scaler(asset, wealth, activity, liquidity):
        if liquidity == "High":
            asset = 2 * asset
            wealth = 2 * wealth
            activity = activity ** 0.5
        elif liquidity == "Medium":
            asset = asset
            wealth = wealth
            activity = 0.8 * (activity ** 0.5)
        elif liquidity == "Low":
            asset = 0.5 * asset
            wealth = 0.5 * wealth
            activity = 0.5 * (activity ** 0.5)
        return asset, wealth, activity 

    # default generated values and then scaled for the liquidity market
    def generate_ib(liquidity):
        asset = np.random.randint(250,500)
        wealth = np.random.randint(2500,5000)
        risk = np.random.uniform(0.01, 0.35)
        activity = np.random.uniform(0.60, 0.90)
        asset, wealth, activity = liquidity_scaler(asset, wealth, activity, liquidity)
        return asset, wealth, risk, activity 
    def generate_wm(liquidity):
        asset = np.random.randint(200,400)
        wealth = np.random.randint(2500,4500)
        risk = np.random.uniform(0.01, 0.25)
        activity = np.random.uniform(0.01, 0.30)
        asset, wealth, activity = liquidity_scaler(asset, wealth, activity, liquidity)
        return asset, wealth, risk, activity 
    def generate_mm(liquidity):
        asset = np.random.randint(50,250)
        wealth = np.random.randint(3000,6000)
        risk = np.random.uniform(0.01, 0.10)
        activity = np.random.uniform(0.70, 0.90)
        asset, wealth, activity = liquidity_scaler(asset, wealth, activity, liquidity)
        return asset, wealth, risk, activity 
    def generate_hrri(liquidity):
        asset = np.random.randint(1,100)
        wealth = np.random.randint(250,2000)
        risk = np.random.uniform(0.70, 0.90)
        activity = np.random.uniform(0.30, 0.80)
        asset, wealth, activity = liquidity_scaler(asset, wealth, activity, liquidity)
        return asset, wealth, risk, activity 
    def generate_lrri(liquidity):
        asset = np.random.randint(1,100)
        wealth = np.random.randint(250,2000)
        risk = np.random.uniform(0.50, 0.80)
        activity = np.random.uniform(0.30, 0.80)
        asset, wealth, activity = liquidity_scaler(asset, wealth, activity, liquidity)
        return asset, wealth, risk, activity 
    def generate_hrpi(liquidity):
        asset = np.random.randint(25,200)
        wealth = np.random.randint(500,2500)
        risk = np.random.uniform(0.40, 0.80)
        activity = np.random.uniform(0.20, 0.50)
        asset, wealth, activity = liquidity_scaler(asset, wealth, activity, liquidity)
        return asset, wealth, risk, activity 
    def generate_lrpi(liquidity):
        asset = np.random.randint(25,200)
        wealth = np.random.randint(500,2500)
        risk = np.random.uniform(0.20, 0.50)
        activity = np.random.uniform(0.20, 0.50)
        asset, wealth, activity = liquidity_scaler(asset, wealth, activity, liquidity)
        return asset, wealth, risk, activity 
    
    # Defining the conditions for each profile type
    updates = [
        {'condition': df_participants['Profile'] == "IB Trader", 'generate_values': lambda: generate_ib(liquidity)},
        {'condition': df_participants['Profile'] == "WM Trader", 'generate_values': lambda: generate_wm(liquidity)},
        {'condition': df_participants['Profile'] == "Market Maker",'generate_values': lambda: generate_mm(liquidity)},
        {'condition': df_participants['Profile'] == "HR Retail Investor",'generate_values': lambda: generate_hrri(liquidity)},
        {'condition': df_participants['Profile'] == "LR Retail Investor",'generate_values': lambda: generate_lrri(liquidity)},
        {'condition': df_participants['Profile'] == "HR Private Investor",'generate_values': lambda: generate_hrpi(liquidity)},
        {'condition': df_participants['Profile'] == "LR Private Investor",'generate_values': lambda: generate_lrpi(liquidity)}
    ]
    # adding the traits for each profile type
    for update in updates:
        for index, row in df_participants.loc[update['condition']].iterrows():
            asset, wealth, risk, activity = update['generate_values']()
            df_participants.at[index, "Asset"] = int(asset)
            df_participants.at[index, "Wealth"] = int(wealth)
            df_participants.at[index, "Risk"] = float(risk)
            df_participants.at[index, "Activity"] = float(activity)
            df_participants.at[index, "PreAsset"] = int(asset)
            df_participants.at[index, "PreWealth"] = int(wealth)

    return df_participants

def user_creation (df_participants, participant_int):
    user_profile = pd.Series({
        "Trader_ID" : participant_int + 1, 
        "Asset" : 100000, 
        "Wealth" : 100000, 
        "Risk" : 0, 
        "Activity" : 0, 
        "Delay" :0, 
        "Profile" : "User"
        })

    df_participants = pd.concat([df_participants, user_profile.to_frame().T], ignore_index=True)
    return df_participants

# S.4 & B.1
def iteration_start(df_participants):
    df_available = pd.DataFrame()

    bot_profiles = ["IB Trader", "WM Trader", "Market Maker", "HR Retail Investor", "LR Retail Investor", "HR Private Investor", "LR Private Investor"]
    # Could be slow - look to optimise using vectorization/ Numpy function?
    for index, row in df_participants.iterrows():
        if  row["Profile"] in bot_profiles and row["Delay"] == 0:
            df_available = pd.concat([df_available, row.to_frame().T], ignore_index=True)
            # df_available = df_available.astype({"Trader_ID":int, "Asset":float, "Wealth":float, "Risk":float, "Activity":float, "Delay":int})
            df_available = df_available.sample(frac = 1)       
    return df_available

def mm_liquidity_fill(df_participants):
    df_available = pd.DataFrame()
    bot_profile = ["Market Maker"]
    for index, row in df_participants.iterrows():
        if row["Profile"] in bot_profile:
            df_available = pd.concat([df_available, row.to_frame().T], ignore_index=True)
            df_available = df_available.sample(frac = 1)
    return df_available