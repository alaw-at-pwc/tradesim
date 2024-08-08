# This script runs an opening auction, that allows for bots to place, amend and cancel orders, without being executed against, until the end of the auction period, whereby orders are cleared at the clearing price, setting the opening price for the market.
# This is where supporting functions will sit, but for now, everything will be here. Once integration witht the front end is done, then the main function will move into SimulatorCode.ipynb
import pandas as pd
import numpy as np
import participantsetup as ps
import datetime as dt
import time

class auction_state:
    def __init__(self):
        global buy_auction_orderbook, sell_auction_orderbook, open_auction_log
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

def bot_auction_logic(bot):
    global buy_auction_orderbook, sell_auction_orderbook, open_auction_log
    timestamp = dt.datetime.now()
    # check if orders already exist 
    for index, live_order in open_auction_log.iterrows():
        if live_order["Trader_ID"] == bot["Trader_ID"] and live_order["Status"] == "Open":       # if orders exist, look to amend, cancel, maintain, and look to maybe place new order in too
            figures = auction_state()
            if figures.complete_orders_check == True:                                   
                if figures.complete_orders_check == "in_excess" and live_order["Side"] == "Buy":      # if on buy side, adjust price, depending on quantity at stake, adjust
                    wealth_ratio = bot["Wealth"] / live_order["Quantity"]
                    target_qty = (bot["Wealth"] / live_order["Price"]) * (bot["Risk"] / 10)
                    # deciding whether to cancel or ammend order. threshold to be calibrated
                    if target_qty - wealth_ratio > 10:
                        action = "Cancel"
                    else:
                        action = "Amend"
                        qty_gap = round((target_qty - wealth_ratio) * np.random.uniform(0.01, 1.0))
                        new_qty = live_order["Quantity"] + qty_gap

                        if live_order["Price"] == figures.auction_best_bid:
                            # decreases the best_bid price
                            price_diff = round(figures.priroity_gap * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] - price_diff
                        else:
                            # raise price towards best_bid    
                            price_diff = round((figures.auction_best_bid - live_order["Price"]) * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] + price_diff

                elif figures.complete_orders_check == "in_excess" and live_order["Side"] == "Sell":   # if on sell side, adjust price, depending on quantity at stake, adjust         
                    asset_ratio = bot["Asset"] / live_order["Quantity"]
                    target_qty = (bot["Wealth"] / live_order["Price"]) * (bot["Risk"] / 10)
                    # deciding whether to cancel or ammend order. threshold to be calibrated
                    if target_qty - asset_ratio > 10:
                        action = "Cancel"
                    else:
                        action = "Amend"    
                        qty_gap = round((target_qty - wealth_ratio) * np.random.uniform(0.01, 1.0))
                        new_qty = live_order["Quantity"] + qty_gap

                        if live_order["Price"] == figures.auction_best_ask:
                            # increases the best_ask price
                            price_diff = round(figures.priroity_gap * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] + price_diff
                        else:
                            # lower price towards best_ask  
                            price_diff = round((live_order["Price"] - figures.auction_best_ask) * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] - price_diff

                elif figures.complete_orders_check == "equal":                                        # depending on quantity at stake, adjust
                    wealth_ratio = bot["Wealth"] / live_order["Quantity"]
                    target_qty = (bot["Wealth"] / live_order["Price"]) * (bot["Risk"] / 10)
                    qty_gap = round((target_qty - wealth_ratio) * np.random.uniform(0.01, 1.0))
                    new_qty = live_order["Quantity"] + qty_gap
                    new_price = live_order["Price"]

                elif figures.complete_orders_check == "no_clear" and live_order["Side"] == "Buy":     # if on buy side, adjust price, depending on quantity at stake, adjust
                    wealth_ratio = bot["Wealth"] / live_order["Quantity"]
                    target_qty = (bot["Wealth"] / live_order["Price"]) * (bot["Risk"] / 10)
                    # deciding whether to cancel or ammend order. threshold to be calibrated
                    if target_qty - wealth_ratio > 10:
                        action = "Cancel"
                    else:
                        action = "Amend"
                        qty_gap = round((target_qty - wealth_ratio) * np.random.uniform(0.01, 1.0))
                        new_qty = live_order["Quantity"] + qty_gap

                        if live_order["Price"] == figures.auction_best_bid:
                            # increases the best_bid price
                            price_diff = round(figures.priroity_gap * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] - price_diff
                        else:
                            # raise price towards best_bid    
                            price_diff = round((figures.auction_best_bid - live_order["Price"]) * np.random.uniform(0.1, 1.0), 2)
                            new_price = live_order["Price"] - price_diff
                elif figures.complete_orders_check == "no_clear" and live_order["Side"] == "Sell":    # if on sell side, adjust price, depending on quantity at stake, adjust
                    asset_ratio = bot["Asset"] / live_order["Quantity"]
                    target_qty = (bot["Wealth"] / live_order["Price"]) * (bot["Risk"] / 10)
                    # deciding whether to cancel or ammend order. threshold to be calibrated
                    if target_qty - asset_ratio > 10:
                        action = "Cancel"
                    else:
                        action = "Amend"    
                        qty_gap = round((target_qty - wealth_ratio) * np.random.uniform(0.01, 1.0))
                        new_qty = live_order["Quantity"] + qty_gap

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
                    version_count = open_auction_log.loc[index, "Version"].values[0]
                    version_count = int(version_count + 1)
                    to_log = pd.Series({"Order_ID": live_order["Order_ID"], "Trader_ID" : live_order["Trader_ID"], "Timestamp" : amend_time, "Quantity" : new_qty, "Price" : new_price, "Side": "Buy", "Status": "Open", "Update_Timestamp": amend_time, "Version": version_count})
                    open_auction_log = pd.concat([open_auction_log, to_log.to_frame().T], ignore_index=True)

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
                    continue
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
                    continue

        else:                                                                       # if bot has no orders in the market, do basic decision
            # sets the order ID
            if len(open_auction_log) < 1:                                       
                order_id = 1
            else:
                order_id = int(open_auction_log.iloc[-1,0] + 1) 

            # benchmark to decide the side
            wealth_asset_ratio = bot["Wealth"] / bot["Asset"] 
            if wealth_asset_ratio >= 11:
                side = "buy"
                order_price = round(wealth_asset_ratio, 2)
                order_quantity = round((bot["Wealth"] / order_price) * bot["Risk"])

                # append order to live log and historic log
                order = pd.Series({"Order_ID": order_id, "Trader_ID" : bot["Trader_ID"], "Timestamp" : timestamp, "Quantity" : order_quantity, "Price" : order_price})
                buy_auction_orderbook = pd.concat([buy_auction_orderbook, order.to_frame().T], ignore_index=True)
                to_log = pd.Series({"Order_ID": order["Order_ID"], "Trader_ID" : order["Trader_ID"], "Timestamp" : order["Timestamp"], "Quantity" : order["Quantity"], "Price" : order["Price"], "Side": "Buy", "Status": "Open", "Update_Timestamp": order["Timestamp"], "Version": 1})
                open_auction_log = pd.concat([open_auction_log, to_log.to_frame().T], ignore_index=True)

            elif wealth_asset_ratio < 11:
                side = "sell"
                order_quantity = round(bot["Asset"] * bot["Risk"])  
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
        order_id = int(open_auction_log.iloc[-1,0] + 1)      
        # benchmark to decide the side
        wealth_asset_ratio = bot["Wealth"] / bot["Asset"] 
        if wealth_asset_ratio >= 11:
            side = "buy"
            order_price = round(wealth_asset_ratio, 2) 
            order_quantity = round((bot["Wealth"] / order_price) * (bot["Risk"]/2)) # quantity at half

            # append order to live log and historic log
            order = pd.Series({"Order_ID": order_id, "Trader_ID" : bot["Trader_ID"], "Timestamp" : timestamp, "Quantity" : order_quantity, "Price" : order_price})
            buy_auction_orderbook = pd.concat([buy_auction_orderbook, order.to_frame().T], ignore_index=True)
            to_log = pd.Series({"Order_ID": order["Order_ID"], "Trader_ID" : order["Trader_ID"], "Timestamp" : order["Timestamp"], "Quantity" : order["Quantity"], "Price" : order["Price"], "Side": "Buy", "Status": "Open", "Update_Timestamp": order["Timestamp"], "Version": 1})
            open_auction_log = pd.concat([open_auction_log, to_log.to_frame().T], ignore_index=True)

        elif wealth_asset_ratio < 11:
            side = "sell"
            order_quantity = round(bot["Asset"] * (bot["Risk"]/2))  # quantity at half
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

def open_auction(df_participants, transaction_log):
    global buy_auction_orderbook, sell_auction_orderbook, open_auction_log

    # setup of auction orderbooks and logs 
    buy_auction_orderbook = pd.DataFrame(columns=["Order_ID", "Trader_ID", "Timestamp", "Quantity", "Price"])
    sell_auction_orderbook = pd.DataFrame(columns=["Order_ID", "Trader_ID", "Timestamp", "Quantity", "Price"])
    open_auction_log = pd.DataFrame(columns=["Order_ID", "Trader_ID", "Timestamp", "Quantity", "Price", "Side", "Status", "Update_Timestamp", "Version"])

    # setting the length of the auction call period 
    current_time = time.time()

    auction_end = current_time + 15 
    # call period loop, where bots place orders into market
    while current_time > auction_end:
        df_available = ps.iteration_start(df_participants) 
        for index, bot in df_available.iterrows():
            # run bot logic that decides price level and quantity for the order
            bot_auction_logic(bot)
        # reset time
        current_time = time.time()
    
    # once call period has ended, find clearing price, and credit and debit bots accordingly 
    

    return clearing_price, open_auction_log, transaction_log
