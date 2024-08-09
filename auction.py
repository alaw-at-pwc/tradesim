# This script runs an opening auction, that allows for bots to place, amend and cancel orders, without being executed against, until the end of the auction period, whereby orders are cleared at the clearing price, setting the opening price for the market.
# This is where supporting functions will sit, but for now, everything will be here. Once integration witht the front end is done, then the main function will move into SimulatorCode.ipynb
import pandas as pd
import numpy as np
import participantsetup as ps
import datetime as dt
import time

class auction_state:
    def __init__(self, buy_auction_orderbook, sell_auction_orderbook):
        buy_auction_orderbook.sort_values(by=["Price", "Timestamp"], ascending=[False, True], inplace=True)
        sell_auction_orderbook.sort_values(by=["Price", "Timestamp"], ascending=[True, True], inplace=True)
        if len(buy_auction_orderbook) > 0:
            self.buy_orders_check = True
            self.auction_best_bid = buy_auction_orderbook["Price"].iloc[0]
        else:
            self.buy_orders_check = False
            self.auction_best_bid = None

        if len(sell_auction_orderbook) > 0:
            self.sell_orders_check = True
            self.auction_best_ask = sell_auction_orderbook["Price"].iloc[0]
        else:
            self.sell_orders_check = False
            self.auction_best_ask = None

        if self.buy_orders_check == True and self.sell_orders_check == True:
            self.complete_orders_check = True
            self.priroity_gap = self.auction_best_bid - self.auction_best_ask
            if self.priroity_gap > 0:
                self.provisional_clear_check = "in_excess"
            elif self.priroity_gap == 0:
                self.provisional_clear_check = "equal"
            elif self.priroity_gap < 0:
                self.provisional_clear_check = "no_clear"
        else:
            self.complete_orders_check = False
            self.priroity_gap = None
            self.provisional_clear_check = 'no_clear'

def bot_auction_logic(bot, buy_auction_orderbook, sell_auction_orderbook, open_auction_log):
    timestamp = dt.datetime.now()
    new_order = False
    action = None
    # check if orders already exist 
    open_bot_orders = open_auction_log[open_auction_log["Trader_ID"] == bot["Trader_ID"]]
    open_bot_orders = open_bot_orders[open_bot_orders["Status"] == "Open"]
    if len(open_bot_orders) > 0:
        for index, live_order in open_bot_orders.iterrows():    # if orders exist, look to amend, cancel, maintain, and look to maybe place new order in too
            if live_order["Quantity"] <= 0:
                live_order["Quantity"] = 1
            figures = auction_state(buy_auction_orderbook, sell_auction_orderbook)
            if figures.complete_orders_check == True:                                   
                if figures.provisional_clear_check == "in_excess" and live_order["Side"] == "Buy":      # if on buy side, adjust price, depending on quantity at stake, adjust
                    wealth_ratio = bot["Wealth"] / live_order["Quantity"]
                    target_qty = (bot["Wealth"] / live_order["Price"]) * (bot["Risk"] / 10)
                    # deciding whether to cancel or ammend order. threshold to be calibrated
                    if target_qty - wealth_ratio > 10:
                        action = "Cancel"
                    else:
                        action = "Amend"
                        qty_gap = round((target_qty - wealth_ratio) * np.random.uniform(0.01, 1.0))
                        new_qty = abs(live_order["Quantity"] + qty_gap)

                        if live_order["Price"] == figures.auction_best_bid:
                            # decreases the best_bid price
                            price_diff = round(figures.priroity_gap * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] - price_diff
                        else:
                            # raise price towards best_bid    
                            price_diff = round((figures.auction_best_bid - live_order["Price"]) * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] + price_diff

                elif figures.provisional_clear_check == "in_excess" and live_order["Side"] == "Sell":   # if on sell side, adjust price, depending on quantity at stake, adjust         
                    asset_ratio = bot["Asset"] / live_order["Quantity"]
                    target_qty = (bot["Wealth"] / live_order["Price"]) * (bot["Risk"] / 10)
                    # deciding whether to cancel or ammend order. threshold to be calibrated
                    if target_qty - asset_ratio > 10:
                        action = "Cancel"
                    else:
                        action = "Amend"    
                        qty_gap = round((target_qty - asset_ratio) * np.random.uniform(0.01, 1.0))
                        new_qty = abs(live_order["Quantity"] + qty_gap)

                        if live_order["Price"] == figures.auction_best_ask:
                            # increases the best_ask price
                            price_diff = round(figures.priroity_gap * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] + price_diff
                        else:
                            # lower price towards best_ask  
                            price_diff = round((live_order["Price"] - figures.auction_best_ask) * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] - price_diff

                elif figures.provisional_clear_check == "equal":                                        # depending on quantity at stake, adjust
                    wealth_ratio = bot["Wealth"] / live_order["Quantity"]
                    target_qty = (bot["Wealth"] / live_order["Price"]) * (bot["Risk"] / 10)
                    qty_gap = round((target_qty - wealth_ratio) * np.random.uniform(0.01, 1.0))
                    new_qty = abs(live_order["Quantity"] + qty_gap)
                    new_price = live_order["Price"]
                    action = None

                elif figures.provisional_clear_check == "no_clear" and live_order["Side"] == "Buy":     # if on buy side, adjust price, depending on quantity at stake, adjust
                    wealth_ratio = bot["Wealth"] / live_order["Quantity"]
                    target_qty = (bot["Wealth"] / live_order["Price"]) * (bot["Risk"] / 10)
                    # deciding whether to cancel or ammend order. threshold to be calibrated
                    if target_qty - wealth_ratio > 10:
                        action = "Cancel"
                    else:
                        action = "Amend"
                        qty_gap = round((target_qty - wealth_ratio) * np.random.uniform(0.01, 1.0))
                        new_qty = abs(live_order["Quantity"] + qty_gap)

                        if live_order["Price"] == figures.auction_best_bid:
                            # increases the best_bid price
                            price_diff = round(figures.priroity_gap * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] - price_diff
                        else:
                            # raise price towards best_bid    
                            price_diff = round((figures.auction_best_bid - live_order["Price"]) * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] - price_diff

                elif figures.provisional_clear_check== "no_clear" and live_order["Side"] == "Sell":    # if on sell side, adjust price, depending on quantity at stake, adjust
                    asset_ratio = bot["Asset"] / live_order["Quantity"]
                    target_qty = (bot["Wealth"] / live_order["Price"]) * (bot["Risk"] / 10)
                    # deciding whether to cancel or ammend order. threshold to be calibrated
                    if target_qty - asset_ratio > 10:
                        action = "Cancel"
                    else:
                        action = "Amend"    
                        qty_gap = round((target_qty - asset_ratio) * np.random.uniform(0.01, 1.0))
                        new_qty = abs(live_order["Quantity"] + qty_gap)

                        if live_order["Price"] == figures.auction_best_ask:
                            # decreases the best_ask price
                            price_diff = round(figures.priroity_gap * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] + price_diff
                        else:
                            # lower price towards best_ask  
                            price_diff = round((live_order["Price"] - figures.auction_best_ask) * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] + price_diff

                if action == "Amend":
                    # updating stale order within the orderbook log
                    amend_time = dt.datetime.now()
                    update_cols = ["Status", "Update_Timestamp"]
                    open_auction_log.loc[index, update_cols] = ["Order Amend", amend_time]
                    # writng new price and qty to orderbook log
                    try:
                        version_count = open_auction_log.loc[index, "Version"]
                        version_count = int(version_count + 1)
                    except:
                        version_count = 2
                    to_log = pd.Series({"Order_ID": live_order["Order_ID"], "Trader_ID" : live_order["Trader_ID"], "Timestamp" : amend_time, "Quantity" : new_qty, "Price" : new_price, "Side": "Buy", "Status": "Open", "Update_Timestamp": amend_time, "Version": version_count})
                    open_auction_log = pd.concat([open_auction_log, to_log.to_frame().T], ignore_index=True)
                    new_price = round(new_price, 2)
                    if new_qty <= 0:
                        new_qty = 1
                    new_qty = round(new_qty)
                    
                    # updating the live orderbook
                    if live_order["Side"] == "Buy":
                        buy_auction_orderbook.loc[buy_auction_orderbook["Order_ID"] == live_order["Order_ID"], "Timestamp"] = amend_time
                        buy_auction_orderbook.loc[buy_auction_orderbook["Order_ID"] == live_order["Order_ID"], "Price"] = new_price
                        buy_auction_orderbook.loc[buy_auction_orderbook["Order_ID"] == live_order["Order_ID"], "Quantity"] = new_qty
                    elif live_order["Side"] == "Sell":
                        sell_auction_orderbook.loc[sell_auction_orderbook["Order_ID"] == live_order["Order_ID"], "Timestamp"] = amend_time
                        sell_auction_orderbook.loc[sell_auction_orderbook["Order_ID"] == live_order["Order_ID"], "Price"] = new_price
                        sell_auction_orderbook.loc[sell_auction_orderbook["Order_ID"] == live_order["Order_ID"], "Quantity"] = new_qty         
                    new_order == False
                
                elif action == "Cancel":
                    # updating orderbook log with the cancel
                    cancel_time = dt.datetime.now()
                    update_cols = ["Status", "Update_Timestamp"]
                    open_auction_log.loc[index, update_cols] = ["Cancelled", cancel_time]

                    # removing order from live orderbook
                    if live_order["Side"] == "Buy":
                        buy_auction_orderbook.drop(buy_auction_orderbook[buy_auction_orderbook["Order_ID"] == live_order["Order_ID"]].index, inplace=True)
                    elif live_order["Side"] == "Sell":
                        sell_auction_orderbook.drop(sell_auction_orderbook[sell_auction_orderbook["Order_ID"] == live_order["Order_ID"]].index, inplace=True)
                    new_order == True

        else:                                                                       # if bot has no orders in the market, do basic decision
            # sets the order ID
            if len(open_auction_log) < 1:                                       
                order_id = 1
            else:
                order_id = int(open_auction_log.iloc[-1,0] + 1) 

            # benchmark to decide the side
            wealth_asset_ratio = bot["Wealth"] / bot["Asset"] 
            if wealth_asset_ratio >= 11:
                order_price = round(wealth_asset_ratio, 2)
                order_quantity = round((bot["Wealth"] / order_price) * bot["Risk"]) + 1

                # append order to live log and historic log
                order = pd.Series({"Order_ID": order_id, "Trader_ID" : bot["Trader_ID"], "Timestamp" : timestamp, "Quantity" : order_quantity, "Price" : order_price})
                buy_auction_orderbook = pd.concat([buy_auction_orderbook, order.to_frame().T], ignore_index=True)
                to_log = pd.Series({"Order_ID": order["Order_ID"], "Trader_ID" : order["Trader_ID"], "Timestamp" : order["Timestamp"], "Quantity" : order["Quantity"], "Price" : order["Price"], "Side": "Buy", "Status": "Open", "Update_Timestamp": order["Timestamp"], "Version": 1})
                open_auction_log = pd.concat([open_auction_log, to_log.to_frame().T], ignore_index=True)

            elif wealth_asset_ratio < 11:
                order_quantity = round(bot["Asset"] * bot["Risk"]) + 1
                order_price = round(bot["Asset"] / order_quantity, 2) 

                # append order to live log and historic log
                order = pd.Series({"Order_ID": order_id, "Trader_ID" : bot["Trader_ID"], "Timestamp" : timestamp, "Quantity" : order_quantity, "Price" : order_price})
                sell_auction_orderbook = pd.concat([sell_auction_orderbook, order.to_frame().T], ignore_index=True)
                to_log = pd.Series({"Order_ID": order["Order_ID"], "Trader_ID" : order["Trader_ID"], "Timestamp" : order["Timestamp"], "Quantity" : order["Quantity"], "Price" : order["Price"], "Side": "Sell", "Status": "Open", "Update_Timestamp": order["Timestamp"], "Version": 1})
                open_auction_log = pd.concat([open_auction_log, to_log.to_frame().T], ignore_index=True)
    
    # RP - Bernoulli risk probability test to place another order into the auction:
    # H0: bot will not place a new order 
    # H1: bot will place a new order - high risk option
    test_val = np.random.random()
    if test_val > bot["Risk"]:  
        new_order = True

    # placing a new order if flagged to do so 
    if new_order == True:
        # sets the order ID
        if len(open_auction_log) < 1:                                       
                order_id = 1
        else:
            order_id = int(open_auction_log.iloc[-1,0] + 1)  
        # benchmark to decide the side
        wealth_asset_ratio = bot["Wealth"] / bot["Asset"] 
        if wealth_asset_ratio >= 11:
            order_price = round(wealth_asset_ratio, 2) 
            order_quantity = round((bot["Wealth"] / order_price) * (bot["Risk"]/2)) + 1 # quantity at half

            # append order to live log and historic log
            order = pd.Series({"Order_ID": order_id, "Trader_ID" : bot["Trader_ID"], "Timestamp" : timestamp, "Quantity" : order_quantity, "Price" : order_price})
            buy_auction_orderbook = pd.concat([buy_auction_orderbook, order.to_frame().T], ignore_index=True)
            to_log = pd.Series({"Order_ID": order["Order_ID"], "Trader_ID" : order["Trader_ID"], "Timestamp" : order["Timestamp"], "Quantity" : order["Quantity"], "Price" : order["Price"], "Side": "Buy", "Status": "Open", "Update_Timestamp": order["Timestamp"], "Version": 1})
            open_auction_log = pd.concat([open_auction_log, to_log.to_frame().T], ignore_index=True)

        elif wealth_asset_ratio < 11:
            order_quantity = round(bot["Asset"] * (bot["Risk"]/2)) + 1  # quantity at half
            order_price = round(bot["Asset"] / order_quantity, 2)

            # append order to live log and historic log
            order = pd.Series({"Order_ID": order_id, "Trader_ID" : bot["Trader_ID"], "Timestamp" : timestamp, "Quantity" : order_quantity, "Price" : order_price})
            sell_auction_orderbook = pd.concat([sell_auction_orderbook, order.to_frame().T], ignore_index=True)
            to_log = pd.Series({"Order_ID": order["Order_ID"], "Trader_ID" : order["Trader_ID"], "Timestamp" : order["Timestamp"], "Quantity" : order["Quantity"], "Price" : order["Price"], "Side": "Sell", "Status": "Open", "Update_Timestamp": order["Timestamp"], "Version": 1})
            open_auction_log = pd.concat([open_auction_log, to_log.to_frame().T], ignore_index=True)
            
    # Sorting the orderbooks 
    buy_auction_orderbook.sort_values(by=["Price", "Timestamp"], ascending=[False, True], inplace=True)
    sell_auction_orderbook.sort_values(by=["Price", "Timestamp"], ascending=[True, True], inplace=True)
    open_auction_log.sort_values(by=["Order_ID", "Version"], ascending=[True, True], inplace=True)

    return buy_auction_orderbook, sell_auction_orderbook, open_auction_log

# function that manages the clearing of orders, and credits and debits accordingly
def matching_logic(df_participants, buy_orders, sell_orders, type_clear, open_auction_log):
    timestamp = dt.datetime.now()
    transaction_log = pd.DataFrame(columns=["Timestamp", "Buy_Side_Order_ID", "Buy_Side_Trader_ID", "Sell_Side_Order_ID", "Sell_Side_Trader_ID", "Quantity", "Price"]) 
    def transaction_append (transaction_log, timestamp, buy_order_id, buy_id, sell_order_id, sell_id, quantity, price):
        quantity = int(quantity)
        price = float(price)
        transaction = pd.Series({
            "Timestamp" : timestamp, 
            "Buy_Side_Order_ID" : int(buy_order_id),
            "Buy_Side_Trader_ID" : int(buy_id), 
            "Sell_Side_Order_ID" : int(sell_order_id),
            "Sell_Side_Trader_ID" : int(sell_id), 
            "Quantity" : quantity, 
            "Price" : price})
        transaction_log = pd.concat([transaction_log, transaction.to_frame().T], ignore_index=True)
        transaction_log["Timestamp"] = pd.to_datetime(transaction_log["Timestamp"])
        transaction_log.sort_values(by=["Timestamp"], ascending=[True], inplace=True)
        return transaction_log
    
    def debit_credit (df_participants, buy_id, sell_id, quantity, price):
        transaction_val = round(quantity * price, 2)
        df_participants.loc[df_participants["Trader_ID"] == buy_id, "Wealth"] -= transaction_val
        df_participants.loc[df_participants["Trader_ID"] == buy_id, "Asset"] += quantity
        df_participants.loc[df_participants["Trader_ID"] == sell_id, "Wealth"] += transaction_val
        df_participants.loc[df_participants["Trader_ID"] == sell_id, "Asset"] -= quantity
        return df_participants
    
    if type_clear == "equal" or "buy_excess":
        for index, sell_order in sell_orders.iterrows():
            sell_quantity = sell_order["Quantity"]

            # Pull best bid info
            buy_id = buy_orders['Trader_ID'].iloc[0]
            buy_order_id = buy_orders['Order_ID'].iloc[0]
            buy_qty = buy_orders['Quantity'].iloc[0]
            result = sell_quantity - buy_qty        
            while sell_quantity > 0:
                if result > 0:
                    # writing the transaction, and debiting and crediting accordingly
                    transaction_log = transaction_append(transaction_log, timestamp, buy_order_id, buy_id, sell_order["Order_ID"], sell_order["Trader_ID"], buy_qty, sell_order["Price"])
                    df_participants = debit_credit(df_participants, buy_id, sell_order["Trader_ID"], buy_qty, sell_order["Price"])

                    # updating buy order in the logs
                    cleared_order_index = open_auction_log[(open_auction_log["Order_ID"] == buy_order_id) & (open_auction_log["Quantity"] == buy_qty)].index
                    update_cols = ["Status", "Update_Timestamp"]
                    open_auction_log.loc[cleared_order_index, update_cols] = ["Order Matched", timestamp]
                    # updating sell order in the logs
                    stale_order_index = open_auction_log[(open_auction_log["Order_ID"] == sell_order["Order_ID"]) & (open_auction_log["Quantity"] == sell_order["Quantity"])].index
                    open_auction_log.loc[stale_order_index, update_cols] = ["Order Matched - Partial Fill", timestamp]
                    try:
                        version_count = open_auction_log.loc[stale_order_index, "Version"]
                        version_count = int(version_count + 1)  
                    except:
                        version_count = 2
                    child_order = pd.Series({
                        "Order_ID": sell_order["Order_ID"], 
                        "Trader_ID" : int(sell_order["Trader_ID"]), 
                        "Timestamp" : timestamp, 
                        "Quantity" : result, 
                        "Price" : float(sell_order["Price"]), 
                        "Side": "Sell", 
                        "Status": "Open", 
                        "Update_Timestamp": timestamp, 
                        "Version": version_count
                    })
                    open_auction_log = pd.concat([open_auction_log, child_order.to_frame().T], ignore_index=True)
                    # removing cleared order from buy orderbook
                    buy_orders = buy_orders.iloc[1:]
                    buy_orders.reset_index(drop = True, inplace=True)
                    sell_quantity = result # reset order_quantity to new level
                    result = sell_quantity - buy_qty 

                elif result == 0:
                    transaction_log = transaction_append(transaction_log, timestamp, buy_order_id, buy_id, sell_order["Order_ID"], sell_order["Trader_ID"], buy_qty, sell_order["Price"])
                    df_participants = debit_credit(df_participants, buy_id, sell_order["Trader_ID"], buy_qty, sell_order["Price"])

                    # updating buy order in the logs
                    cleared_order_index = open_auction_log[(open_auction_log["Order_ID"] == buy_order_id) & (open_auction_log["Quantity"] == buy_qty)].index
                    update_cols = ["Status", "Update_Timestamp"]
                    open_auction_log.loc[cleared_order_index, update_cols] = ["Order Matched", timestamp]
                    buy_orders = buy_orders.iloc[1:]
                    buy_orders.reset_index(drop = True, inplace=True)
                    # updating sell order in the logs
                    cleared_order_index = open_auction_log[(open_auction_log["Order_ID"] == sell_order["Order_ID"]) & (open_auction_log["Quantity"] == sell_order["Quantity"])].index
                    open_auction_log.loc[cleared_order_index, update_cols] = ["Order Matched", timestamp]
                    sell_quantity = 0
                    break

                elif result < 0:
                    transaction_log = transaction_append(transaction_log, timestamp, buy_order_id, buy_id, sell_order["Order_ID"], sell_order["Trader_ID"], sell_order["Quantity"], sell_order["Price"])
                    df_participants = debit_credit(df_participants, buy_id, sell_order["Trader_ID"], sell_order["Quantity"], sell_order["Price"])

                    # update sell order in the logs
                    cleared_order_index = open_auction_log[(open_auction_log["Order_ID"] == sell_order["Order_ID"]) & (open_auction_log["Quantity"] == sell_order["Quantity"])].index
                    update_cols = ["Status", "Update_Timestamp"]
                    open_auction_log.loc[cleared_order_index, update_cols] = ["Order Matched", timestamp]

                    # updating partially filled buy order    
                    new_buy_qty = buy_qty - sell_quantity
                    stale_order_index = open_auction_log[(open_auction_log["Order_ID"] == buy_order_id) & (open_auction_log["Quantity"] == buy_qty)].index
                    open_auction_log.loc[stale_order_index, update_cols] = ["Order Matched - Partial Fill", timestamp]
                    try:
                        version_count = open_auction_log.loc[stale_order_index, "Version"]
                        version_count = int(version_count + 1)  
                    except:
                        version_count = 2
                    child_order = pd.Series({
                        "Order_ID": buy_order_id, 
                        "Trader_ID" : int(buy_id), 
                        "Timestamp" : timestamp, 
                        "Quantity" : new_buy_qty, 
                        "Price" : float(sell_order["Price"]), 
                        "Side": "Buy", 
                        "Status": "Open", 
                        "Update_Timestamp": timestamp, 
                        "Version": version_count
                    })
                    open_auction_log = pd.concat([open_auction_log, child_order.to_frame().T], ignore_index=True)
                    # amending quantity within the order book
                    update_buyorder_index = buy_orders[(buy_orders["Order_ID"] == buy_order_id)].index
                    buy_orders.loc[update_buyorder_index,"Quantity"] = new_buy_qty
                    sell_quantity = 0
                    break
                try:
                    buy_id = buy_orders['Trader_ID'].iloc[0]
                    buy_order_id = buy_orders['Order_ID'].iloc[0]
                    buy_qty = buy_orders['Quantity'].iloc[0]
                    result = sell_quantity - buy_qty  
                except:
                    break

    elif type_clear == "sell_excess":
        for index, buy_order in buy_orders.iterrows():
            buy_quantity = buy_order["Quantity"]

            # Pull best bid info
            sell_id = sell_orders['Trader_ID'].iloc[0]
            sell_order_id = sell_orders['Order_ID'].iloc[0]
            sell_qty = sell_orders['Quantity'].iloc[0]
            result = buy_quantity - sell_qty        
            while buy_quantity > 0:
                if result > 0:
                    # writing the transaction, and debiting and crediting accordingly
                    transaction_log = transaction_append(transaction_log, timestamp, buy_order["Order_ID"], buy_order["Trader_ID"], sell_order_id, sell_id, sell_qty, buy_order["Price"])
                    df_participants = debit_credit(df_participants, buy_order["Trader_ID"], sell_id, sell_qty, buy_order["Price"])

                    # updating sell order in the logs
                    cleared_order_index = open_auction_log[(open_auction_log["Order_ID"] == sell_order_id) & (open_auction_log["Quantity"] == sell_qty)].index
                    update_cols = ["Status", "Update_Timestamp"]
                    open_auction_log.loc[cleared_order_index, update_cols] = ["Order Matched", timestamp]
                    # updating buy order in the logs
                    stale_order_index = open_auction_log[(open_auction_log["Order_ID"] == buy_order["Order_ID"]) & (open_auction_log["Quantity"] == buy_order["Quantity"])].index
                    open_auction_log.loc[stale_order_index, update_cols] = ["Order Matched - Partial Fill", timestamp]
                    try:
                        version_count = open_auction_log.loc[stale_order_index, "Version"]
                        version_count = int(version_count + 1)  
                    except:
                        version_count = 2
                    child_order = pd.Series({
                        "Order_ID": buy_order["Order_ID"], 
                        "Trader_ID" : int(buy_order["Trader_ID"]), 
                        "Timestamp" : timestamp, 
                        "Quantity" : result, 
                        "Price" : float(buy_order["Price"]), 
                        "Side": "Buy", 
                        "Status": "Open", 
                        "Update_Timestamp": timestamp, 
                        "Version": version_count
                    })
                    open_auction_log = pd.concat([open_auction_log, child_order.to_frame().T], ignore_index=True)
                    # removing cleared order from sell orderbook
                    sell_orders = sell_orders.iloc[1:]
                    sell_orders.reset_index(drop = True, inplace=True)
                    buy_quantity = result # reset order_quantity to new level
                    result = buy_quantity - sell_qty 

                elif result == 0:
                    transaction_log = transaction_append(transaction_log, timestamp, buy_order["Order_ID"], buy_order["Trader_ID"], sell_order_id, sell_id, sell_qty, buy_order["Price"])
                    df_participants = debit_credit(df_participants, buy_order["Trader_ID"], sell_id, sell_qty, buy_order["Price"])

                    # updating sell order in the logs
                    cleared_order_index = open_auction_log[(open_auction_log["Order_ID"] == sell_order_id) & (open_auction_log["Quantity"] == sell_qty)].index
                    update_cols = ["Status", "Update_Timestamp"]
                    open_auction_log.loc[cleared_order_index, update_cols] = ["Order Matched", timestamp]
                    buy_orders = buy_orders.iloc[1:]
                    buy_orders.reset_index(drop = True, inplace=True)
                    # updating buy order in the logs
                    cleared_order_index = open_auction_log[(open_auction_log["Order_ID"] == buy_order["Order_ID"]) & (open_auction_log["Quantity"] == buy_order["Quantity"])].index
                    open_auction_log.loc[cleared_order_index, update_cols] = ["Order Matched", timestamp]
                    buy_quantity = 0
                    break

                elif result < 0:
                    transaction_log = transaction_append(transaction_log, timestamp, buy_order["Order_ID"], buy_order["Trader_ID"], sell_order_id, sell_id, buy_order["Quantity"], buy_order["Price"])
                    df_participants = debit_credit(df_participants, buy_order["Trader_ID"], sell_id, sell_qty, buy_order["Price"])

                    # update buy order in the logs
                    cleared_order_index = open_auction_log[(open_auction_log["Order_ID"] == buy_order["Order_ID"]) & (open_auction_log["Quantity"] == buy_order["Quantity"])].index
                    update_cols = ["Status", "Update_Timestamp"]
                    open_auction_log.loc[cleared_order_index, update_cols] = ["Order Matched", timestamp]

                    # updating partially filled buy order    
                    new_sell_qty = sell_qty - buy_quantity
                    stale_order_index = open_auction_log[(open_auction_log["Order_ID"] == sell_order_id) & (open_auction_log["Quantity"] == sell_qty)].index
                    open_auction_log.loc[stale_order_index, update_cols] = ["Order Matched - Partial Fill", timestamp]
                    try:
                        version_count = open_auction_log.loc[stale_order_index, "Version"]
                        version_count = int(version_count + 1)  
                    except:
                        version_count = 2
                    child_order = pd.Series({
                        "Order_ID": sell_order_id, 
                        "Trader_ID" : int(sell_id), 
                        "Timestamp" : timestamp, 
                        "Quantity" : new_sell_qty, 
                        "Price" : float(buy_order["Price"]), 
                        "Side": "Sell", 
                        "Status": "Open", 
                        "Update_Timestamp": timestamp, 
                        "Version": version_count
                    })
                    open_auction_log = pd.concat([open_auction_log, child_order.to_frame().T], ignore_index=True)
                    # amending quantity within the order book
                    update_sellorder_index = sell_orders[(sell_orders["Order_ID"] == sell_order_id)].index
                    sell_orders.loc[update_sellorder_index,"Quantity"] = new_sell_qty
                    buy_quantity = 0
                    break
                try:
                    sell_id = sell_orders['Trader_ID'].iloc[0]
                    sell_order_id = sell_orders['Order_ID'].iloc[0]
                    sell_qty = sell_orders['Quantity'].iloc[0]
                    result = buy_quantity - sell_qty  
                except:
                    break
    return df_participants, transaction_log, open_auction_log

def open_auction(df_participants):
    # setup of auction orderbooks and logs 
    buy_auction_orderbook = pd.DataFrame(columns=["Order_ID", "Trader_ID", "Timestamp", "Quantity", "Price"])
    sell_auction_orderbook = pd.DataFrame(columns=["Order_ID", "Trader_ID", "Timestamp", "Quantity", "Price"])
    open_auction_log = pd.DataFrame(columns=["Order_ID", "Trader_ID", "Timestamp", "Quantity", "Price", "Side", "Status", "Update_Timestamp", "Version"])

    # setting the length of the auction call period 
    current_time = time.time()

    auction_end = current_time + 30
    # call period loop, where bots place orders into market
    while current_time < auction_end:
        current_time = time.time()
        df_available = ps.iteration_start(df_participants) 
        for index, bot in df_available.iterrows():
            # run bot logic that decides price level and quantity for the order
            buy_auction_orderbook, sell_auction_orderbook, open_auction_log = bot_auction_logic(bot, buy_auction_orderbook, sell_auction_orderbook, open_auction_log)
            delay = round((1/bot["Activity"]) * abs(np.random.randint(1,20)))
            bot["Delay"] = delay + 1
        if len(df_available) > 0:
            merged_df = df_participants.merge(df_available, on="Trader_ID", how='left', suffixes   =('_old', '_new'))
            merged_df['Delay'] = merged_df['Delay_new'].fillna(merged_df['Delay_old']).infer_objects(copy=False)
            merged_df.drop(['Delay_old','Delay_new'], axis=1, inplace=True)
            merged_df['Trader_ID'] = merged_df['Trader_ID'].astype(int)
            df_participants.update(merged_df)
        # reset time
        df_participants["Delay"] = df_participants["Delay"].apply(lambda x: abs(x - 1))
        df_participants["Wealth"] = df_participants["Wealth"].apply(lambda x: round(x, 2))     
    # once call period has ended, find clearing price, and credit and debit bots accordingly 
    buy_agg_orderbook = pd.DataFrame(columns=["Price", "Quantity"])
    buy_agg_orderbook = buy_auction_orderbook.groupby("Price").agg({"Quantity" : 'sum'}).reset_index()
    buy_agg_orderbook.columns = ['Price', 'Total Quantity']
    buy_auction_orderbook.sort_values(by=["Price"], ascending=False, inplace=True)
    print(buy_agg_orderbook)

    sell_agg_orderbook = pd.DataFrame(columns=["Price", "Quantity"])
    sell_agg_orderbook = sell_auction_orderbook.groupby("Price").agg({"Quantity" : 'sum'}).reset_index()
    sell_agg_orderbook.columns = ['Price', 'Total Quantity']
    sell_auction_orderbook.sort_values(by=["Price"], ascending=True, inplace=True)
    print(sell_agg_orderbook)

    # finds the only price levels that are present in both buy and sell orderbooks
    aggregated_orderbooks = buy_agg_orderbook.merge(sell_agg_orderbook, how='inner', on='Price', suffixes=('_buy', '_sell'))
    aggregated_orderbooks["Delta"] = abs(aggregated_orderbooks["Total Quantity_buy"] - aggregated_orderbooks["Total Quantity_sell"])
    aggregated_orderbooks["Qty_Sum"] = aggregated_orderbooks["Total Quantity_buy"] + aggregated_orderbooks["Total Quantity_sell"]
    aggregated_orderbooks.sort_values(by=["Qty_Sum", "Delta"], ascending=[False, True], inplace=True)
    print(aggregated_orderbooks)
    clearing_price = aggregated_orderbooks["Price"].iloc[0]

    # extract orders to only those that can be cleared
    available_buy_orders = buy_auction_orderbook["Price"] == clearing_price
    available_sell_orders = sell_auction_orderbook["Price"] == clearing_price
    to_clear_buy_orders = buy_auction_orderbook[available_buy_orders].sort_values(by=["Timestamp"], ascending=True)
    to_clear_sell_orders = sell_auction_orderbook[available_sell_orders].sort_values(by=["Timestamp"], ascending=True)

    agg_buy_qty = to_clear_buy_orders["Quantity"].sum()
    agg_sell_qty = to_clear_sell_orders["Quantity"].sum()
    if agg_buy_qty == agg_sell_qty:
        type_clear = "equal"
    elif agg_buy_qty > agg_sell_qty:
        type_clear = "buy_excess"
    elif agg_buy_qty < agg_sell_qty:
        type_clear = "sell_excess"

    # initiate clearing process
    df_participants, transaction_log, open_auction_log = matching_logic(df_participants, to_clear_buy_orders, to_clear_sell_orders, type_clear, open_auction_log)
    # change status of all remaning open orders to be unmatched
    open_auction_log.loc[open_auction_log['Status'] == 'Open', 'Status'] = 'Not Matched'

    return clearing_price, open_auction_log, transaction_log, df_participants