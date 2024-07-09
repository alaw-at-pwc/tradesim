# This script takes the bot decision, and decides the price level and quantity for the deicion that the bot made
import random
import numpy as np
import pandas as pd
import datetime as dt

# debiting function - takes order info, and debits the money or asset accordinlgy, from the bot
def bot_debiting (bot, price, quantity, result, df_participants):
    if result == "buy_order" or result == "buy_execute":
        order_value = price * quantity
        df_participants.loc[df_participants["Trader_ID"] == bot["Trader_ID"], "Wealth"] -= order_value
        
    elif result == "sell_order" or result == "sell_execute":        
        df_participants.loc[df_participants["Trader_ID"] == bot["Trader_ID"], "Asset"] -= quantity

# deciding order qty levels across multiple price levels
def liquidity_levels_calc(levels, prop_min, prop_max):
    scale = 0.1
    uniform_randoms = np.random.uniform(0, 1, levels) #generates 5 uniform random numbers
    exponential_randoms = -scale * np.log(1 - uniform_randoms) #applies inverse CDF of exponential distribution
    bounded_exponential_randoms = np.clip(exponential_randoms, prop_min, prop_max) #clips values to be bounded between prop_min and prop_max
    order_quantities = -np.sort(-bounded_exponential_randoms) #sorts numbers from highest to lowest
    return order_quantities

def IB_order (result, bot, key_figs, force_priority):
    # D.2, D.3, D.4
    df_input_orders = pd.DataFrame(columns=["Timestamp", "Trader_ID", "Quantity", "Price", "Flag"])
    timestamp = dt.datetime.now()
    trader_id = bot["Trader_ID"]
    max_buy_quantity = bot["Wealth"] / key_figs.market_price
    max_sell_quantity = bot["Asset"]
    bid_ask_spread = key_figs.best_ask - key_figs.best_bid

    if result == 'buy_order' and force_priority == True:
        order_price = round(key_figs.best_bid, 2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
        df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)

    elif result == 'buy_order' and bid_ask_spread > 0.02:
        #D.3.1
        order_price = round(key_figs.best_bid + 0.01,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
        df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)

    elif result == 'buy_order' and bid_ask_spread <= 0.02:
        #D.3.2
        offset = round(abs(np.random.standard_normal()) * 4) * 0.01 
        order_price = round(key_figs.best_bid - offset,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
        df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)

    elif result == 'buy_execute':
        #D.5.1
        order_price = key_figs.best_ask
        order_quantity = round(random.uniform(0.10, 0.20) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
        df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)

        scd_order_price = round(key_figs.best_bid,2)
        scd_order_quantity = round(random.uniform(0.10, 0.25) * max_buy_quantity)
        scd_input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : scd_order_quantity, "Price" : scd_order_price, "Flag" : "bid"})
        df_input_orders = pd.concat([df_input_orders, scd_input_order.to_frame().T], ignore_index=True)

    elif result == 'sell_order' and force_priority == True:
        order_price = round(key_figs.best_ask, 2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
        df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
        
    elif result == 'sell_order' and bid_ask_spread > 0.02:
        #D.4.1
        order_price = round(key_figs.best_ask - 0.01,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
        df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)

    elif result == 'sell_order' and bid_ask_spread <= 0.02:
        #D.4.2
        offset = round(abs(np.random.standard_normal()) * 4) * 0.01 
        order_price = round(key_figs.best_ask + offset,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
        df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)

    elif result == 'sell_execute':
        #D.5.2
        order_price = key_figs.best_bid
        order_quantity = round(random.uniform(0.10, 0.20) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
        df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)

        scd_order_price = round(key_figs.best_ask,2)
        scd_order_quantity = round(random.uniform(0.10, 0.25) * max_buy_quantity)
        scd_input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : scd_order_quantity, "Price" : scd_order_price, "Flag" : "ask"})
        df_input_orders = pd.concat([df_input_orders, scd_input_order.to_frame().T], ignore_index=True)

    elif result == 'multiple_orders':
        num_buy_orders = np.random.randint(0,3)
        if num_buy_orders > 0: 
            order_quantities = liquidity_levels_calc(num_buy_orders, 0.05, 0.15)
            p_level_counter = 0
            for order_qty in order_quantities:
                order_price = round(key_figs.best_bid - p_level_counter,2)
                order_quantity = round(order_qty * max_buy_quantity)
                input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
                df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
                p_level_counter += 0.01
        num_sell_orders = np.random.randint(0,3)
        if num_sell_orders > 0:
            order_quantities = liquidity_levels_calc(num_sell_orders, 0.05, 0.15)
            p_level_counter = 0
            for order_qty in order_quantities:
                order_price = round(key_figs.best_ask + p_level_counter,2)
                order_quantity = round(order_qty * max_sell_quantity)
                input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
                df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
                p_level_counter += 0.01

    return bot, df_input_orders

def WM_order (result, bot, key_figs):
    # D.2, D.3, D.4
    df_input_orders = pd.DataFrame(columns=["Timestamp", "Trader_ID", "Quantity", "Price", "Flag"])
    timestamp = dt.datetime.now()
    trader_id = bot["Trader_ID"]
    max_buy_quantity = bot["Wealth"] / key_figs.market_price
    max_sell_quantity = bot["Asset"]
    bid_ask_spread = key_figs.best_ask - key_figs.best_bid

    if result == 'buy_order' and bid_ask_spread > 0.02:
        #D.3.1
        order_price = round(key_figs.best_bid + 0.01,2)
        order_quantity = round(random.uniform(0.15, 0.30) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

    elif result == 'buy_order' and bid_ask_spread <= 0.02:
        #D.3.2
        offset = round(abs(np.random.standard_normal()) * 4) * 0.01 
        order_price = round(key_figs.best_bid - offset,2)
        order_quantity = round(random.uniform(0.15, 0.30) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

    elif result == 'buy_execute':
        #D.5.1
        order_price = key_figs.best_ask
        order_quantity = round(random.uniform(0.10, 0.20) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

    elif result == 'sell_order' and bid_ask_spread > 0.02:
        #D.4.1
        order_price = round(key_figs.best_ask - 0.01,2)
        order_quantity = round(random.uniform(0.15, 0.30) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})

    elif result == 'sell_order' and bid_ask_spread <= 0.02:
        #D.4.2
        offset = round(abs(np.random.standard_normal()) * 4) * 0.01 
        order_price = round(key_figs.best_ask + offset,2)
        order_quantity = round(random.uniform(0.15, 0.30) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})

    elif result == 'sell_execute':
        #D.5.2
        order_price = key_figs.best_bid
        order_quantity = round(random.uniform(0.10, 0.20) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
    df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
    return bot, df_input_orders

def MM_order (result, bot, key_figs, liquidity_flag):
    # D.2, D.3, D.4
    df_input_orders = pd.DataFrame(columns=["Timestamp", "Trader_ID", "Quantity", "Price", "Flag"])
    timestamp = dt.datetime.now()
    trader_id = bot["Trader_ID"]
    max_buy_quantity = bot["Wealth"] / key_figs.market_price
    max_sell_quantity = bot["Asset"] 
    bid_ask_spread = key_figs.best_ask - key_figs.best_bid
    
    if liquidity_flag == True:
        # deciding order qty levels across multiple price levels
        order_quantities = liquidity_levels_calc(5, 0.01, 0.2)
        p_level_counter = 0
        if result == 'buy_order':
            for order_qty in order_quantities:
                order_price = round(key_figs.best_bid - p_level_counter,2)
                order_quantity = round(order_qty * max_buy_quantity)
                input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
                df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
                p_level_counter += 0.01

        elif result == 'sell_order':
            for order_qty in order_quantities:
                order_price = round(key_figs.best_ask + p_level_counter,2)
                order_quantity = round(order_qty * max_sell_quantity)
                input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
                df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
                p_level_counter += 0.01
            
    elif liquidity_flag == False:
        if result == 'buy_order' and bid_ask_spread >= 0.2:
            order_price = round(key_figs.best_bid + 0.01, 2)
            order_quantity = round(random.uniform(0.20, 0.40) * max_buy_quantity)
            input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
        
        elif result == 'buy_order' and bid_ask_spread < 0.2:
            order_price = round(key_figs.best_bid,2)
            order_quantity = round(random.uniform(0.10, 0.30) * max_buy_quantity)
            input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

        elif result == 'buy_execute':
            order_price = key_figs.best_ask
            order_quantity = round(random.uniform(0.15, 0.35) * max_buy_quantity)
            input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

        elif result == 'sell_order' and bid_ask_spread >= 0.2:
            order_price = round(key_figs.best_ask - 0.01, 2)
            order_quantity = round(random.uniform(0.20, 0.40) * max_sell_quantity)
            input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})

        elif result == 'sell_order' and bid_ask_spread < 0.2:
            order_price = round(key_figs.best_ask, 2)
            order_quantity = round(random.uniform(0.10, 0.30) * max_sell_quantity)
            input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})

        elif result == 'sell_execute':
            order_price = key_figs.best_bid
            order_quantity = round(random.uniform(0.15, 0.35) * max_sell_quantity)
            input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
        df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)

    return bot, df_input_orders

def RI_order (result, bot, key_figs, emotion_bias):
    # D.2, D.3, D.4
    df_input_orders = pd.DataFrame(columns=["Timestamp", "Trader_ID", "Quantity", "Price", "Flag"])
    timestamp = dt.datetime.now()
    trader_id = bot["Trader_ID"]
    max_buy_quantity = (bot["Wealth"] * bot["Risk"]) / key_figs.market_price
    max_sell_quantity = bot["Asset"] * bot["Risk"]
    bid_ask_spread = key_figs.best_ask - key_figs.best_bid

    if result == 'buy_order' and bid_ask_spread > 0.02:
        #D.3.1
        order_price = round(key_figs.best_bid + 0.01,2)
        order_quantity = round(random.uniform(0.15, 0.35) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

    elif result == 'buy_order' and bid_ask_spread <= 0.02:
        #D.3.2
        offset = round(abs(np.random.standard_normal()) * 4) * 0.01 
        order_price = round(key_figs.best_bid - offset,2)
        order_quantity = round(random.uniform(0.15, 0.35) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

    elif result == 'buy_execute' and emotion_bias == "negative":
        #D.5.1
        order_price = key_figs.best_ask
        order_quantity = round(random.uniform(0.15, 0.30) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

    elif result == 'buy_execute' and emotion_bias == "positive":
        #D.5.1
        order_price = key_figs.best_ask
        order_quantity = round(random.uniform(0.25, 0.50) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

    elif result == 'sell_order' and bid_ask_spread > 0.02:
        #D.4.1
        order_price = round(key_figs.best_ask - 0.01,2)
        order_quantity = round(random.uniform(0.15, 0.35) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})

    elif result == 'sell_order' and bid_ask_spread <= 0.02:
        #D.4.2
        offset = round(abs(np.random.standard_normal()) * 4) * 0.01 
        order_price = round(key_figs.best_ask + offset,2)
        order_quantity = round(random.uniform(0.15, 0.35) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})

    elif result == 'sell_execute' and emotion_bias == "negative":
        #D.5.2
        order_price = key_figs.best_bid
        order_quantity = round(random.uniform(0.15, 0.30) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})

    elif result == 'sell_execute' and emotion_bias == "positive":
        #D.5.2
        order_price = key_figs.best_bid
        order_quantity = round(random.uniform(0.25, 0.50) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})

    df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
    return bot, df_input_orders

def PI_order (result, bot, key_figs):
    # D.2, D.3, D.4
    df_input_orders = pd.DataFrame(columns=["Timestamp", "Trader_ID", "Quantity", "Price", "Flag"])
    timestamp = dt.datetime.now()
    trader_id = bot["Trader_ID"]
    max_buy_quantity = (bot["Wealth"] * bot["Risk"]) / key_figs.market_price
    max_sell_quantity = bot["Asset"] * bot["Risk"]
    bid_ask_spread = key_figs.best_ask - key_figs.best_bid

    if result == 'buy_order' and bid_ask_spread > 0.02:
        #D.3.1
        order_price = round(key_figs.best_bid + 0.01,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

    elif result == 'buy_order' and bid_ask_spread <= 0.02:
        #D.3.2
        offset = round(abs(np.random.standard_normal()) * 4) * 0.01 
        order_price = round(key_figs.best_bid - offset,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

    elif result == 'buy_execute':
        #D.5.1
        order_price = key_figs.best_ask
        order_quantity = round(random.uniform(0.10, 0.20) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})

    elif result == 'sell_order' and bid_ask_spread > 0.02:
        #D.4.1
        order_price = round(key_figs.best_ask - 0.01,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})

    elif result == 'sell_order' and bid_ask_spread <= 0.02:
        #D.4.2
        offset = round(abs(np.random.standard_normal()) * 4) * 0.01 
        order_price = round(key_figs.best_ask + offset,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})

    elif result == 'sell_execute':
        #D.5.2
        order_price = key_figs.best_bid
        order_quantity = round(random.uniform(0.10, 0.20) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
    df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
    return bot, df_input_orders

# help create liquidity in orderbooks 
def liquidity_creator (bot, key_figs, buy_orderbook, sell_orderbook):
    def buy_orderbook_append (timestamp, trader_id, quantity, price, buy_orderbook): 
        new_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : quantity, "Price" : price})
        buy_orderbook = pd.concat([buy_orderbook, new_order.to_frame().T], ignore_index=True)
        buy_orderbook.sort_values(by=["Price", "Timestamp"], ascending=[False, True], inplace=True)
        return buy_orderbook

    def sell_orderbook_append (timestamp, trader_id, quantity, price, sell_orderbook):
        new_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : quantity, "Price" : price})
        sell_orderbook = pd.concat([sell_orderbook, new_order.to_frame().T], ignore_index=True)
        sell_orderbook.sort_values(by=["Price", "Timestamp"], ascending=[True, True], inplace=True)
        return sell_orderbook
    
    def bot_debiting(bot, input_orders):
        for index, order in input_orders.iterrows():
            qty = int(order["Quantity"])
            price = round(order["Price"],2)
            if order["Flag"] == "bid":
                order_value = price * qty
                bot[2] -= order_value # wealth
            elif order["Flag"] == "ask":    
                bot[1] -= qty # assets
        return bot

    # D.2, D.3, D.4
    df_input_orders = pd.DataFrame(columns=["Timestamp", "Trader_ID", "Quantity", "Price", "Flag"])
    timestamp = dt.datetime.now()
    trader_id = bot["Trader_ID"]
    max_buy_quantity = bot["Wealth"] / key_figs.market_price
    max_sell_quantity = bot["Asset"]
    p_level_counter = 0

    if key_figs.buy_orderbook_test == "b_fail" and key_figs.sell_orderbook_test == "s_pass":
        order_quantities = liquidity_levels_calc(7, 0.02, 0.3)
        for order_qty in order_quantities:
            order_price = round(key_figs.best_bid - p_level_counter,2)
            order_quantity = round(order_qty * max_buy_quantity)
            buy_orderbook_append(timestamp, trader_id, order_quantity, order_price, buy_orderbook)
            input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
            df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
            p_level_counter += 0.01

    elif key_figs.sell_orderbook_test == "s_fail" and key_figs.buy_orderbook_test == "b_pass":
        order_quantities = liquidity_levels_calc(7, 0.02, 0.3)
        for order_qty in order_quantities:
            order_price = round(key_figs.best_ask + p_level_counter,2)
            order_quantity = round(order_qty * max_sell_quantity)
            sell_orderbook_append(timestamp, trader_id, order_quantity, order_price, sell_orderbook)
            input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
            df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
            p_level_counter += 0.01

    elif key_figs.buy_orderbook_test == "b_fail" and key_figs.sell_orderbook_test == "s_fail":
        buy_order_quantities = liquidity_levels_calc(5, 0.02, 0.2)
        for order_qty in buy_order_quantities:
            order_price = round(key_figs.best_bid - p_level_counter,2)
            order_quantity = round(order_qty * max_buy_quantity)
            buy_orderbook_append(timestamp, trader_id, order_quantity, order_price, buy_orderbook)
            input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
            df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
            p_level_counter += 0.01
        
        sell_order_quantities = liquidity_levels_calc(5, 0.02, 0.2)
        for order_qty in sell_order_quantities:
            order_price = round(key_figs.best_ask + p_level_counter,2)
            order_quantity = round(order_qty * max_sell_quantity)
            sell_orderbook_append(timestamp, trader_id, order_quantity, order_price, sell_orderbook)
            input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
            df_input_orders = pd.concat([df_input_orders, input_order.to_frame().T], ignore_index=True)
            p_level_counter += 0.01
    bot = bot_debiting(bot, df_input_orders)
    return bot, buy_orderbook, sell_orderbook



# This is the legacy function that decides order quantity and price, and is no longer used 
'''def bot_market_interact (result, bot, key_figs):
    # D.2, D.3, D.4
    timestamp = dt.datetime.now()
    trader_id = bot["Trader_ID"]
    max_buy_quantity = bot["Wealth"] / key_figs.market_price
    max_sell_quantity = bot["Asset"]
    best_bid_spread = key_figs.market_price - key_figs.best_bid
    best_ask_spread = key_figs.best_ask - key_figs.market_price

    if result == 'buy_order' and best_bid_spread > 0.02:
        #D.3.1
        order_price = round(key_figs.best_bid + 0.01,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
        bot = bot_debiting(bot, order_price, order_quantity, result)

    elif result == 'buy_order' and best_bid_spread <= 0.02:
        #D.3.2
        offset = round(abs(np.random.standard_normal()) * 4) * 0.01 
        order_price = round(key_figs.best_bid - offset,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
        bot = bot_debiting(bot, order_price, order_quantity, result)

    elif result == 'buy_execute':
        #D.5.1
        order_price = key_figs.best_ask
        order_quantity = round(random.uniform(0.10, 0.20) * max_buy_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "bid"})
        bot = bot_debiting(bot, order_price, order_quantity, result)

    elif result == 'sell_order' and best_ask_spread > 0.02:
        #D.4.1
        order_price = round(key_figs.best_ask - 0.01,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
        bot = bot_debiting(bot, order_price, order_quantity, result)

    elif result == 'sell_order' and best_ask_spread <= 0.02:
        #D.4.2
        offset = round(abs(np.random.standard_normal()) * 4) * 0.01 
        order_price = round(key_figs.best_ask + offset,2)
        order_quantity = round(random.uniform(0.10, 0.25) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
        bot = bot_debiting(bot, order_price, order_quantity, result)

    elif result == 'sell_execute':
        #D.5.2
        order_price = key_figs.best_bid
        order_quantity = round(random.uniform(0.10, 0.20) * max_sell_quantity)
        input_order = pd.Series({"Timestamp" : timestamp, "Trader_ID" : trader_id, "Quantity" : order_quantity, "Price" : order_price, "Flag" : "ask"})
        bot = bot_debiting(bot, order_price, order_quantity, result)
    return bot, input_order'''