import pandas as pd
#################################################################################################################
########################################### BEGINING OF RISK TESTS ##############################################
#################################################################################################################
# Calculates profit and loss, and returns the result to change the risk value
def pnl_calculation (bot, key_figs, type):
    start_capital = (key_figs.open_price * bot["PreAsset"]) + bot["PreWealth"]
    current_capital = (key_figs.market_price * bot["Asset"]) + bot["Wealth"]
    net_capital = current_capital - start_capital
    percentage_change = abs(net_capital/start_capital)

    # Tailoring benchmark to different trader categories. retail investors aim for 5%, private investors aim for 7%
    if type == 'RI':
        benchmark = 0.05
    elif type == 'PI':
        benchmark = 0.07
    else:
        benchmark = None
    
    # basic type purely looks and profit and loss
    # RI and PI types look at percentage gain to influence level of change to risk value
    if type == 'basic':
        if net_capital >= 0:
            profit_result = True
        elif net_capital < 0:
            profit_result = False
    elif type == 'RI' or type == 'PI':
        if percentage_change >= benchmark:
            profit_result = True
        elif percentage_change < benchmark:
            profit_result = False
    return profit_result

# Calculate how much exposure the bot has currently in the market 
def exposure_calculation(bot, buy_orderbook, sell_orderbook, key_figs):
    buy_exposure_score = 0
    sell_exposure_score = 0

    # for each orderbook, given it has orders, find any orders from the bot, calculate the fraction of the bots capital/asset
    # then calulate proximity to priority, and generate a score
    if not buy_orderbook.empty:
        for index, order in buy_orderbook.iterrows():
            if bot["Trader_ID"] == order["Trader_ID"]:
                order_val = order["Quantity"] * order["Price"]
                order_fraction = order_val / bot["Wealth"]
                price_diff = ((key_figs.best_bid - order["Price"]) * 100) + 1
                order_exposure = order_fraction / price_diff
                buy_exposure_score += order_exposure
    if not sell_orderbook.empty:
        for index, order in sell_orderbook.iterrows():
            if bot["Trader_ID"] == order["Trader_ID"]:
                order_fraction = order["Quantity"] / bot["Asset"]
                price_diff = ((order["Price"] - key_figs.best_ask) * 100) + 1
                order_exposure = order_fraction / price_diff
                sell_exposure_score += order_exposure
    exposure_score = (buy_exposure_score + sell_exposure_score) / 2     # aggregate both exposure scores, and divide by two to find average

    # generate the result band based on the exposure score
    if exposure_score == 0:
        result = 0                  # no exposure
    elif exposure_score <= 0.2 and exposure_score > 0:
        result = 1                  # low exposure
    elif exposure_score <= 0.5 and exposure_score > 0.2:
        result = 2                  # medium exposure
    elif exposure_score > 0.5:
        result = 3                  # high exposure
    return result

# Calculating various metrics to measure how volatile the market is 
def market_volatility(key_figs, transaction_log):
    volatility_score = 0
    # Calculating result for absolute price movement
    abs_price_mvmt = abs(key_figs.abs_price_mvmt)
    if abs_price_mvmt < 0.02:
        volatility_score += 1        # low movement
    elif abs_price_mvmt >= 0.02 and abs_price_mvmt < 0.05:
        volatility_score += 2        # medium movement
    elif abs_price_mvmt >= 0.05:    
        volatility_score += 3        # high movement
    
    # Calculating result for price range
    if key_figs.price_range < 0.02:
        volatility_score += 1      #low movement
    elif key_figs.price_range >= 0.02 and key_figs.price_range < 0.10:
        volatility_score += 2      # medium movement
    elif key_figs.price_range >= 0.10:
        volatility_score += 3      # high movement

    # Calculating result for recent price movement
    if len(transaction_log) > 49:
            prev_price = transaction_log.iat[-50,4]
    else:
        prev_price = transaction_log.iat[-1,4]
    market_delta = abs(prev_price - key_figs.market_price)
    if market_delta < 0.02:    
        volatility_score += 1      # low movement
    elif market_delta >= 0.02:     
        volatility_score += 2      # high movement

    if volatility_score <= 4:
        volatility_result = 1
    elif volatility_score > 4 and volatility_score < 7:
        volatility_result = 2
    elif volatility_score >= 7:
        volatility_result = 3

    return volatility_result
#################################################################################################################
########################################### BEGINING OF RISK TREES ##############################################
#################################################################################################################
# Aggregating risk results for Investment Bankers
def IB_risk(pnl_result, exposure_result, volatility_result):
    aggregate_change = 0
    # Aggregating PnL test result
    pnl_tests = {
        True: -0.001,
        False: 0.001
    }
    pnl = pnl_tests.get(pnl_result)
    aggregate_change += pnl
    # Aggregating exposure test result
    exposures = {
        0 : 0.010,
        1 : 0.005,
        2 : -0.005,
        3 : -0.010
    }
    exposure = exposures.get(exposure_result)
    aggregate_change += exposure
    # Aggregating vaoltaility test results 
    volatilities = {
        1 : 0.005,
        2 : 0,
        3 : -0.005
    }
    volatility = volatilities.get(volatility_result)
    aggregate_change += volatility
    return aggregate_change

# Aggregating risk results for Wealth Managers
def WM_risk(pnl_result, exposure_result, volatility_result):
    aggregate_change = 0
    # Aggregating PnL test result
    pnl_tests = {
        True: 0.010,
        False: -0.010
    }
    pnl = pnl_tests.get(pnl_result)
    aggregate_change += pnl
    # Aggregating exposure test result
    exposures = {
        0 : 0.005,
        1 : 0.0025,
        2 : -0.0025,
        3 : -0.005
    }
    exposure = exposures.get(exposure_result)
    aggregate_change += exposure
    # Aggregating vaoltaility test results 
    volatilities = {
        1 : 0.001,
        2 : 0,
        3 : -0.001
    }
    volatility = volatilities.get(volatility_result)
    aggregate_change += volatility
    return aggregate_change

# Aggregating risk results for Market Makers
def MM_risk(pnl_result, exposure_result, volatility_result):
    aggregate_change = 0
    # Aggregating PnL test result
    pnl_tests = {
        True: -0.001,
        False: 0.001
    }
    pnl = pnl_tests.get(pnl_result)
    aggregate_change += pnl
    # Aggregating exposure test result
    exposures = {
        0 : 0.001,
        1 : 0.001,
        2 : -0.001,
        3 : -0.001
    }
    exposure = exposures.get(exposure_result)
    aggregate_change += exposure
    # Aggregating vaoltaility test results 
    volatilities = {
        1 : -0.005,
        2 : 0,
        3 : 0.005
    }
    volatility = volatilities.get(volatility_result)
    aggregate_change += volatility
    return aggregate_change

# Aggregating risk results for High Risk Retail Investors
def HRRI_risk(pnl_sub_result, exposure_result, volatility_result):
    aggregate_change = 0
    # Aggregating PnL test result
    pnl_tests = {
        True: -0.005,
        False: 0.005
    }
    pnl = pnl_tests.get(pnl_sub_result)
    aggregate_change += pnl
    # Aggregating exposure test result
    exposures = {
        0 : 0.001,
        1 : 0.001,
        2 : -0.001,
        3 : -0.001
    }
    exposure = exposures.get(exposure_result)
    aggregate_change += exposure
    # Aggregating vaoltaility test results 
    volatilities = {
        1 : -0.001,
        2 : 0,
        3 : 0.002
    }
    volatility = volatilities.get(volatility_result)
    aggregate_change += volatility
    return aggregate_change

# Aggregating risk results for Low Risk Retail Investors
def LRRI_risk(pnl_sub_result, exposure_result, volatility_result):
    aggregate_change = 0
    # Aggregating PnL test result
    pnl_tests = {
        True: -0.005,
        False: 0.0025
    }
    pnl = pnl_tests.get(pnl_sub_result)
    aggregate_change += pnl
    # Aggregating exposure test result
    exposures = {
        0 : 0.005,
        1 : 0.0025,
        2 : -0.0025,
        3 : -0.005
    }
    exposure = exposures.get(exposure_result)
    aggregate_change += exposure
    # Aggregating vaoltaility test results 
    volatilities = {
        1 : -0.001,
        2 : 0,
        3 : 0.001
    }
    volatility = volatilities.get(volatility_result)
    aggregate_change += volatility
    return aggregate_change

# Aggregating risk results for High Risk Private Investors
def HRPI_risk(pnl_sub_result, exposure_result, volatility_result):
    aggregate_change = 0
    # Aggregating PnL test result
    pnl_tests = {
        True: -0.005,
        False: 0.005
    }
    pnl = pnl_tests.get(pnl_sub_result)
    aggregate_change += pnl
    # Aggregating exposure test result
    exposures = {
        0 : 0.010,
        1 : 0.005,
        2 : -0.005,
        3 : -0.010
    }
    exposure = exposures.get(exposure_result)
    aggregate_change += exposure
    # Aggregating vaoltaility test results 
    volatilities = {
        1 : 0.001,
        2 : 0,
        3 : -0.001
    }
    volatility = volatilities.get(volatility_result)
    aggregate_change += volatility
    return aggregate_change

# Aggregating risk results for Low Risk Private Investors
def LRPI_risk(pnl_sub_result, exposure_result, volatility_result):
    aggregate_change = 0
    # Aggregating PnL test result
    pnl_tests = {
        True: -0.005,
        False: 0.005
    }
    pnl = pnl_tests.get(pnl_sub_result)
    aggregate_change += pnl
    # Aggregating exposure test result
    exposures = {
        0 : 0.005,
        1 : 0.0025,
        2 : -0.0025,
        3 : -0.005
    }
    exposure = exposures.get(exposure_result)
    aggregate_change += exposure
    # Aggregating vaoltaility test results 
    volatilities = {
        1 : 0.010,
        2 : 0,
        3 : -0.010
    }
    volatility = volatilities.get(volatility_result)
    aggregate_change += volatility
    return aggregate_change

# Conducting all tests
def risk_calculation(bot, buy_orderbook, sell_orderbook, key_figs, transaction_log, risk_df):
    if bot["Profile"] == "HR Retail Investor" or bot["Profile"] == "LR Retail Investor":
        profile = "RI"
    elif bot["Profile"] == "HR Private Investor" or bot["Profile"] == "LR Private Investor":
        profile = "PI"
    else:
        profile = "basic"
    pnl_result = pnl_calculation(bot, key_figs, profile)
    exposure_result = exposure_calculation(bot, buy_orderbook, sell_orderbook, key_figs)
    volatility_result = market_volatility(key_figs, transaction_log)

    conditions = {
        "IB Trader" : IB_risk(pnl_result, exposure_result, volatility_result),
        "WM Trader" : WM_risk(pnl_result, exposure_result, volatility_result),
        "Market Maker" : MM_risk(pnl_result, exposure_result, volatility_result),
        "HR Retail Investor" : HRRI_risk(pnl_result, exposure_result, volatility_result),
        "LR Retail Investor" : LRRI_risk(pnl_result, exposure_result, volatility_result),
        "HR Private Investor" : HRPI_risk(pnl_result, exposure_result, volatility_result),
        "LR Private Investor" : LRPI_risk(pnl_result, exposure_result, volatility_result)
    }
    risk_change = conditions.get(bot["Profile"])

    # maintain a history of risk changes for testing
    new_risk = bot["Risk"] + risk_change
    risk_log = pd.Series({"Trader_ID" : bot["Trader_ID"], "Old Risk" : bot["Risk"], "New Risk" : new_risk, "PnL": pnl_result, "Exposure" : exposure_result, "Volatility" : volatility_result})
    risk_df = pd.concat([risk_df, risk_log.to_frame().T], ignore_index=True)

    # update bot's risk level. If breaching the limit, it will hard-cap the risk to be bounded between 0.01 and 0.99
    bot["Risk"] += risk_change
    if bot["Risk"] <= 0:
        bot["Risk"] = 0.01
    elif bot["Risk"] >= 1:
        bot["Risk"] = 0.99

    return bot, risk_df

    