# This script sets out the parameters that are used to generate the randomised profiles for all participants. They will be allocated a profile type, and will recive attirbutes based on this allocaiton.
import pandas as pd
import numpy as np

# S.1 & S.2 & S.3
def participant_creation (participant_num):
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

    def generate_ib():
        asset = np.random.randint(500,1000)
        wealth = np.random.randint(5000,10000)
        risk = np.random.uniform(0.01, 0.35)
        activity = np.random.uniform(0.60, 0.90)
        return asset, wealth, risk, activity 
    def generate_wm():
        asset = np.random.randint(400,800)
        wealth = np.random.randint(5000,9000)
        risk = np.random.uniform(0.01, 0.25)
        activity = np.random.uniform(0.01, 0.30)
        return asset, wealth, risk, activity 
    def generate_mm():
        asset = np.random.randint(100,500)
        wealth = np.random.randint(6000,12000)
        risk = np.random.uniform(0.01, 0.10)
        activity = np.random.uniform(0.70, 0.90)
        return asset, wealth, risk, activity 
    def generate_hrri():
        asset = np.random.randint(1,200)
        wealth = np.random.randint(500,4000)
        risk = np.random.uniform(0.70, 1.0)
        activity = np.random.uniform(0.30, 0.80)
        return asset, wealth, risk, activity 
    def generate_lrri():
        asset = np.random.randint(1,200)
        wealth = np.random.randint(500,4000)
        risk = np.random.uniform(0.50, 0.80)
        activity = np.random.uniform(0.30, 0.80)
        return asset, wealth, risk, activity 
    def generate_hrpi():
        asset = np.random.randint(50,400)
        wealth = np.random.randint(1000,5000)
        risk = np.random.uniform(0.40, 0.80)
        activity = np.random.uniform(0.20, 0.50)
        return asset, wealth, risk, activity 
    def generate_lrpi():
        asset = np.random.randint(50,400)
        wealth = np.random.randint(1000,5000)
        risk = np.random.uniform(0.20, 0.50)
        activity = np.random.uniform(0.20, 0.50)
        return asset, wealth, risk, activity 
    
    # Defining the conditions for each profile type
    updates = [
        {'condition': df_participants['Profile'] == "IB Trader", 'generate_values': lambda: generate_ib()},
        {'condition': df_participants['Profile'] == "WM Trader", 'generate_values': lambda: generate_wm()},
        {'condition': df_participants['Profile'] == "Market Maker",'generate_values': lambda: generate_mm()},
        {'condition': df_participants['Profile'] == "HR Retail Investor",'generate_values': lambda: generate_hrri()},
        {'condition': df_participants['Profile'] == "LR Retail Investor",'generate_values': lambda: generate_lrri()},
        {'condition': df_participants['Profile'] == "HR Private Investor",'generate_values': lambda: generate_hrpi()},
        {'condition': df_participants['Profile'] == "LR Private Investor",'generate_values': lambda: generate_lrpi()}
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