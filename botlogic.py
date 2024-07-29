# This script takes various market info, and runs the bot through its designated decision tree. 
import numpy as np
import pandas as pd
import datetime as dt

def random_action_gen ():
        order_val = np.random.random()
        if order_val > 0.5:
            action = 'buy'
        else:
            action = 'sell'
        return action

def top_price_calc (key_figs):
    top_price_dist = key_figs.price_max - key_figs.market_price
    if top_price_dist <= 0.02:
        tree3 = 'sell'
    else:
        tree3 = 'buy'
    return tree3
        
def bot_price_calc (key_figs):
    bot_price_dist = key_figs.market_price - key_figs.price_min    
    if bot_price_dist <= 0.02:
        tree3 = 'buy'
    else:
        tree3 = 'sell'
    return tree3

def order_type_calc(vote_count):
    if vote_count > 2:
        order_flag = 'execute'
    else:
        order_flag = 'order'
    return order_flag

# Function that considers what current orders the bot has in the market
def open_orders(id, orderbook, prio_price):
    open_prio_orders = False # flags true if there are orders at priority
    open_np_orders = False # flags true if there are orders away from priority 
    open_prio_qty = 0
    open_np_qty = 0
    for index, order in orderbook.iterrows():
        if id == order["Trader_ID"] and order["Price"] == prio_price:
            open_prio_orders = True
            open_np_qty += order["Quantity"]
        elif id == order["Trader_ID"] and order["Price"] < prio_price:
            open_np_orders = True
            open_np_qty += order["Quantity"]
    return open_prio_orders, open_prio_qty, open_np_orders, open_np_qty

def setup_bot_decision (bot, IB_market_state, df_decisions):
    # RP - Bernoulli risk probability test:
        # H0: bot will trade i.e. test fails, they will trade 
        # H1: bot will not trade i.e. test passes, they will be inactive
        # setup to encourage more participation in the market 
    test_val = np.random.random()
    if test_val < bot["Risk"]:  
        state = "inactive"
    else: 
        state = "active"
    
    if state == "active":
        #T.2 - asset-capital ratio tree - for when market key figs are not available
        wealth_asset_ratio = bot["Wealth"] / bot["Asset"] 
        if wealth_asset_ratio >= 11:
            tree2 = "buy"
        elif wealth_asset_ratio < 11:
            tree2 = "sell"

        #T.4 - random risk tree
        if bot["Risk"] >= 0.82: # this restricts this tree to the 10th percentile of risk-takers
            tree4 = random_action_gen()
        else:
            tree4 = 'neither'

        #T.5 - market sentiment tree
        if IB_market_state == "bull":
            tree5 = "buy"
        elif IB_market_state == "bear":
            tree5 = "sell"
        elif  IB_market_state == "neutral":
            tree5 = "neither" 
        else:
            tree5 = "neither"
        
        # B.3 - vote counting module. If counts are equal, generate random action 
        tree_list = [tree2, tree4, tree5]
        buy_vote = 0
        sell_vote = 0
        for choice in tree_list:
            if choice == 'buy':
                buy_vote += 1
            elif choice == 'sell':
                sell_vote += 1

        # D.1 deciding on type of order, based on number of vote counts
        if buy_vote == sell_vote:
            bot_action = random_action_gen()
            order_flag = 'execute'
            result = bot_action + "_" + order_flag
        elif buy_vote > sell_vote:
            bot_action = 'buy'
            order_flag = order_type_calc(buy_vote)
            result = bot_action + "_" + order_flag
        elif sell_vote > buy_vote:
            bot_action = 'sell'
            order_flag = order_type_calc(sell_vote)
            result = bot_action + "_" + order_flag
        decision = pd.Series({
            "Trader_ID": bot["Trader_ID"],
            "Profile" : bot["Profile"],
            "Risk" : bot["Risk"],
            "Result" : result,
            "Tree2" : tree2,
            "Tree4" : tree4,
            "Tree5" : tree5
        })
        df_decisions = pd.concat([df_decisions, decision.to_frame().T], ignore_index=True)
    else:
        result = "no_decision"

    return result, state, df_decisions

def IB_bot_decision (bot, IB_market_state, key_figs, transaction_log, buy_orderbook, sell_orderbook, df_decisions):
    # RP - Bernoulli risk probability test:
        # H0: bot will trade i.e. test fails, they will trade 
        # H1: bot will not trade i.e. test passes, they will be inactive
        # setup to encourage more participation in the market 
    test_val = np.random.random()
    if test_val < bot["Risk"]:  
        state = "inactive"
    else: 
        state = "active"
        
    if state == "active":
        # T.1 - market movement tree
        # T.1.2: function to calculate the price movement in the last 25 transactions
        if len(transaction_log) > 24:
            prev_price = transaction_log.iat[-25,-3]
        else:
            prev_price = transaction_log.iat[-1,-3]
        market_delta = prev_price - key_figs.market_price
        if market_delta > 0.02:
            tree1 = 'buy'
        elif market_delta < -0.02:
            tree1 = 'sell'
        else:
            tree1 = 'neither'

        # T.2 - Calculating the asset value/ capital ratio
        asset_value = key_figs.market_price * bot["Asset"]
        avc_ratio = asset_value / bot["Wealth"]
        avc_benchmark = avc_ratio * bot["Risk"]

        # Calculating if the bot has made a profit or loss 
        start_capital = (key_figs.open_price * bot["PreAsset"]) + bot["PreWealth"]
        current_capital = (key_figs.market_price * bot["Asset"]) + bot["Wealth"]

        # Asset-capital ratio tree and PnL - for when it is possible to call from market    
        if current_capital >= start_capital and avc_benchmark >= 0.09:
            tree2 = 'sell'
        elif current_capital >= start_capital and avc_benchmark < 0.09:
            #tree2 = 'd_buy'
            tree2 = 'buy'
        elif current_capital < start_capital and avc_benchmark >= 0.09:
            #tree2 = 'd_sell'
            tree2 = 'sell'
        elif current_capital < start_capital and avc_benchmark < 0.09:
            tree2 = 'buy'

        # T.3
        if key_figs.abs_price_mvmt > 0:
            tree3 = top_price_calc(key_figs)
        elif key_figs.abs_price_mvmt < 0:
            tree3 = bot_price_calc(key_figs)    
        else:
            tree3 = "neither"

        # T.5 - market sentiment
        if IB_market_state == "bull":
            tree5 = "buy"
        elif IB_market_state == "bear":
            tree5 = "sell"
        elif IB_market_state == "neutral":
            tree5 = "neither" 
        else:
            tree5 = "neither"

        # T.6 - orderbook consideration tree 
        # Calculating orderbook depth
        qty_buy_orderbook = buy_orderbook["Quantity"].sum()
        qty_sell_orderbook = sell_orderbook["Quantity"].sum()
        ordebook_ratio = qty_buy_orderbook / qty_sell_orderbook

        if ordebook_ratio <= 0.25:
            tree6 = "buy"
        elif ordebook_ratio < 0.5 and ordebook_ratio > 0.25:
            tree6 = "buy"
        elif ordebook_ratio > 2 and ordebook_ratio < 4:
            tree6 = "sell"
        elif ordebook_ratio >= 4:
            tree6 = "sell"
        else: 
            tree6 = "neither"

        # T.TransactionQty - Evaluate the number of transactions on each side of the orderbook in the last 30 seconds
        transaction_buy_qty = 0
        transaction_sell_qty = 0
        for index, order in transaction_log.iterrows():
            transaction_time_check = dt.datetime.now() - order["Timestamp"]
            if transaction_time_check.seconds <= 30 and order["Aggressor"] == "Buy":
                transaction_buy_qty += order["Quantity"]
            elif transaction_time_check.seconds <= 30 and order["Aggressor"] == "Sell":
                transaction_sell_qty += order["Quantity"]
        try:
            buy_to_sell_ratio = transaction_buy_qty / transaction_sell_qty

            if buy_to_sell_ratio >= 4:
                tree_transaction = "buy"
            elif buy_to_sell_ratio < 4 and buy_to_sell_ratio >= 2:
                tree_transaction = "sell"
            elif buy_to_sell_ratio > 0.25 and buy_to_sell_ratio <= 0.5:
                tree_transaction = "buy"
            elif buy_to_sell_ratio <= 0.25:
                tree_transaction = "sell"
            else:
                tree_transaction = "neither"
        except: # for when transacted sells = 0
            tree_transaction = "buy"
         
        # T.IB - Looking at what current orders the trader has in the market
        open_bb_orders, open_bb_qty, open_bnp_orders, open_bnp_qty = open_orders(bot.iloc[0], buy_orderbook, key_figs.best_bid)   
        open_ba_orders, open_ba_qty, open_snp_orders, open_snp_qty = open_orders(bot.iloc[0], sell_orderbook, key_figs.best_ask)
        buy_side_risk_exposure = open_bnp_qty/bot["Asset"] 
        sell_side_risk_exposure = open_snp_qty/bot["Asset"]

        exec_buy_order = 0
        exec_sell_order = 0
        prio_buy_order = 0
        prio_sell_order = 0

        if open_bb_orders == True and open_bb_qty > 100:                    # substantial order sitting at priority
            exec_buy_order += 1                                             # vote for an execute in the market if buy, away from priotiy if sell
            prio_sell_order += 1
        elif open_bb_orders == False and open_bnp_orders == True:
            if buy_side_risk_exposure > 0.25 and open_bnp_qty > 100:        # more than a fifth in the market 
                prio_buy_order -= 1                                         # vote for an order away from priority, and an execution on sell
                exec_sell_order += 1
            elif buy_side_risk_exposure <= 0.25 and open_bnp_qty > 100:     # less than a fifth in the market 
                prio_buy_order += 1                                         # vote for an order at priority, and an order at priotiy on sell
                prio_sell_order += 1
        
        if open_ba_orders == True and open_ba_qty > 100:                    # same logic as above, but considering any open sell side orders 
            exec_sell_order += 1
            prio_buy_order += 1
        elif open_ba_orders == False and open_snp_orders == True:
            if sell_side_risk_exposure > 0.25 and open_snp_qty > 100:
                prio_sell_order -= 1
                exec_buy_order += 1
            elif sell_side_risk_exposure <= 0.25 and open_snp_qty > 100:
                prio_sell_order += 1
                prio_buy_order += 1

        if exec_buy_order == 2:
            t_open_order = "buy_execute"
            force_priortiy = False
        elif exec_sell_order == 2:
            t_open_order = "sell_execute"
            force_priortiy = False
        elif prio_buy_order == 2:
            t_open_order = "buy_priority"
            force_priortiy = True
        elif prio_sell_order == 2:
            t_open_order = "sell_priority"
            force_priortiy = True
        else:
            t_open_order = "order"
            force_priortiy = False

        # B.3 - vote counting module. If counts are equal, generate random action
        tree_list = [tree1, tree2, tree3, tree5, tree6, tree_transaction]
        buy_vote = 0
        sell_vote = 0
        
        for choice in tree_list:
            if choice == 'buy':
                buy_vote += 1
            elif choice == "d_buy":
                buy_vote += 2
            elif choice == 'sell':
                sell_vote += 1
            elif choice == "d_sell":
                sell_vote += 2

        # D.1 deciding on type of order, based on number of vote counts   
        if buy_vote == sell_vote:
            result = 'multiple_orders'
        elif (buy_vote > sell_vote and t_open_order == "buy_execute") or (sell_vote > buy_vote and t_open_order == "sell_execute"):
            result = t_open_order
        elif buy_vote > sell_vote and (t_open_order == "buy_priority" or t_open_order == "order"):
            bot_action = 'buy'
            order_flag = order_type_calc(buy_vote)
            result = bot_action + "_" + order_flag
        elif sell_vote > buy_vote and (t_open_order == "buy_priority" or t_open_order == "order"):
            bot_action = 'sell'
            order_flag = order_type_calc(sell_vote)
            result = bot_action + "_" + order_flag

        decision = pd.Series({
            "Trader_ID": bot["Trader_ID"],
            "Profile" : bot["Profile"],
            "Risk" : bot["Risk"],
            "Result" : result,
            "T_Open" : t_open_order,
            "Tree1" : tree1,
            "Tree2" : tree2,
            "Tree3" : tree3,
            "Tree5" : tree5,
            "Tree6" : tree6,
            "Transactions" : tree_transaction,
            "Prio" : force_priortiy
        })
        df_decisions = pd.concat([df_decisions, decision.to_frame().T], ignore_index=True)
    else:
        result = "no_decision"
        force_priortiy = False
    
    return result, state, force_priortiy, df_decisions

def WM_bot_decision (bot, IB_market_state, key_figs, transaction_log, df_decisions):
     # RP - Bernoulli risk probability test:
        # H0: bot will trade i.e. test fails, they will trade 
        # H1: bot will not trade i.e. test passes, they will be inactive
        # setup to encourage more participation in the market 
    test_val = np.random.random()
    if test_val < bot["Risk"]:  
        state = "inactive"
    else: 
        state = "active"
        
    if state == "active":
        # T.1 - market movement tree
        # T.1.2: function to calculate the price movement in the last 25 transactions
        if len(transaction_log) > 24:
            prev_price = transaction_log.iat[-25,-3]
        else:
            prev_price = transaction_log.iat[-1,-3]
        market_delta = prev_price - key_figs.market_price
        if market_delta > 0.02:
            tree1 = 'buy'
        elif market_delta < -0.02:
            tree1 = 'sell'
        else:
            tree1 = 'neither'

        # T.2 - Calculating the asset value/ capital ratio
        asset_value = key_figs.market_price * bot["Asset"]
        avc_ratio = asset_value / bot["Wealth"]
        avc_benchmark = avc_ratio * bot["Risk"]

        # Calculating if the bot has made a profit or loss 
        start_capital = (key_figs.open_price * bot["PreAsset"]) + bot["PreWealth"]
        current_capital = (key_figs.market_price * bot["Asset"]) + bot["Wealth"]

        # Asset-capital ratio tree and PnL - for when it is possible to call from market    
        if current_capital >= start_capital and avc_benchmark >= 0.09:
            tree2 = 'sell'
        elif current_capital >= start_capital and avc_benchmark < 0.09:
            #tree2 = 'd_buy'
            tree2 = 'buy'
        elif current_capital < start_capital and avc_benchmark >= 0.09:
            #tree2 = 'd_sell'
            tree2 = 'sell'
        elif current_capital < start_capital and avc_benchmark < 0.09:
            tree2 = 'buy'

        # T.3
        if key_figs.abs_price_mvmt > 0:
            tree3 = top_price_calc(key_figs)
        elif key_figs.abs_price_mvmt < 0:
            tree3 = bot_price_calc(key_figs)    
        else:
            tree3 = "neither"

        # T.5 - market sentiment
        if IB_market_state == "bull":
            tree5 = "buy"
        elif IB_market_state == "bear":
            tree5 = "sell"
        elif IB_market_state == "neutral":
            tree5 = "neither" 
        else:
            tree5 = "neither"

        # B.3 - vote counting module. If counts are equal, generate random action 
        tree_list = [tree1, tree2, tree3, tree5]
        buy_vote = 0
        sell_vote = 0
        for choice in tree_list:
            if choice == 'buy':
                buy_vote += 1
            elif choice == 'sell':
                sell_vote += 1

        # D.1 deciding on type of order, based on number of vote counts
        if buy_vote == sell_vote:
            bot_action = random_action_gen()
            order_flag = 'execute'
            result = bot_action + "_" + order_flag
        elif buy_vote > sell_vote:
            bot_action = 'buy'
            order_flag = order_type_calc(buy_vote)
            result = bot_action + "_" + order_flag
        elif sell_vote > buy_vote:
            bot_action = 'sell'
            order_flag = order_type_calc(sell_vote)
            result = bot_action + "_" + order_flag
        decision = pd.Series({
            "Trader_ID": bot["Trader_ID"],
            "Profile" : bot["Profile"],
            "Risk" : bot["Risk"],
            "Result" : result,
            "Tree1" : tree1,
            "Tree2" : tree2,
            "Tree3" : tree3,
            "Tree5" : tree5
        })
        df_decisions = pd.concat([df_decisions, decision.to_frame().T], ignore_index=True)
    else:
        result = "no_decision"
    return result, state, df_decisions

def MM_bot_decision (bot, key_figs, buy_orderbook, sell_orderbook, transaction_log, df_decisions):
    # RP - Bernoulli risk probability test:
        # H0: bot will trade i.e. test fails, they will trade 
        # H1: bot will not trade i.e. test passes, they will be inactive
        # setup to encourage more participation in the market 
    test_val = np.random.random()
    if test_val < bot["Risk"]:  
        state = "inactive"
    else: 
        state = "active"

    '''if key_figs.key_figs_test == 't_semipass':
        # This forces the bot to make an order in the market if an orderbook is empty, even if inactive
        if key_figs.buy_orderbook_test == "b_fail" and key_figs.sell_orderbook_test == "s_pass":
            tree6 = "buy"
            force_flag = "force"
        elif key_figs.sell_orderbook_test == "s_fail" and key_figs.buy_orderbook_test == "b_pass":
            tree6 = "sell"
            force_flag = "force"
        elif key_figs.buy_orderbook_test == "b_fail" and key_figs.sell_orderbook_test == "s_fail":
            tree6 = "random_order"
            force_flag = "force"'''

    if state == "active":
        # T.2 - Calculating the asset value/ capital ratio
        asset_value = key_figs.market_price * bot["Asset"]
        avc_ratio = asset_value / bot["Wealth"]
        avc_benchmark = avc_ratio * bot["Risk"]

        # Calculating if the bot has made a profit or loss 
        start_capital = (key_figs.open_price * bot["PreAsset"]) + bot["PreWealth"]
        current_capital = (key_figs.market_price * bot["Asset"]) + bot["Wealth"]

        # Asset-capital ratio tree and PnL - for when it is possible to call from market    
        if current_capital >= start_capital and avc_benchmark >= 0.02:
            tree2 = 'sell'
        elif current_capital >= start_capital and avc_benchmark < 0.02:
            #tree2 = 'd_buy'
            tree2 = 'buy'
        elif current_capital < start_capital and avc_benchmark >= 0.02:
            #tree2 = 'd_sell'
            tree2 = 'sell'
        elif current_capital < start_capital and avc_benchmark < 0.02:
            tree2 = 'buy'

        # T.3
        if key_figs.abs_price_mvmt > 0:
            tree3 = top_price_calc(key_figs)
        elif key_figs.abs_price_mvmt < 0:
            tree3 = bot_price_calc(key_figs)    
        else:
            tree3 = "neither"

        # T.6
        if key_figs.key_figs_test == 'pass':
            # Calculating orderbook depth
            qty_buy_orderbook = buy_orderbook["Quantity"].sum()
            qty_sell_orderbook = sell_orderbook["Quantity"].sum()
            orderbook_ratio = qty_buy_orderbook / qty_sell_orderbook
            if orderbook_ratio < 0.5:
                tree6 = "d_buy"
                force_flag = "none"
            elif orderbook_ratio < 0.2:
                tree6 = "buy"
                force_flag = "force"
            elif orderbook_ratio > 2:
                tree6 = "d_sell"
                force_flag = "none"
            elif orderbook_ratio > 5:
                tree6 = "sell"
                force_flag = "force"
            else: 
                tree6 = "neither"
                force_flag = "none"
        # T.TransactionQty - Evaluate the number of transactions on each side of the orderbook in the last 30 seconds
        transaction_buy_qty = 0
        transaction_sell_qty = 0
        for index, order in transaction_log.iterrows():
            transaction_time_check = dt.datetime.now() - order["Timestamp"]
            if transaction_time_check.seconds <= 30 and order["Aggressor"] == "Buy":
                transaction_buy_qty += order["Quantity"]
            elif transaction_time_check.seconds <= 30 and order["Aggressor"] == "Sell":
                transaction_sell_qty += order["Quantity"]
        try:       
            buy_to_sell_ratio = transaction_buy_qty / transaction_sell_qty
            if buy_to_sell_ratio >= 3:
                tree_transaction = "sell"
            elif buy_to_sell_ratio <= 0.33:
                tree_transaction = "buy"
            else:
                tree_transaction = "neither"
        except: # for when the transacted sell quantity is 0
            tree_transaction = "sell"
    else:    
        result = "no_decision"
        force_flag = "na"
        tree6 = "none"
        liquidity_flag = False

    # B.3 - vote counting module. If counts are equal, generate random action
    if force_flag == "force" and tree6 == "buy":
        result = "buy_order"
        liquidity_flag = True
    elif force_flag == "force" and tree6 == "sell":
        result = "sell_order"
        liquidity_flag = True
    elif force_flag == "force" and tree6 == "random_order":
        bot_action = random_action_gen()
        order_flag = 'order'
        result = bot_action + "_" + order_flag
        liquidity_flag = True
    elif force_flag == "none":
        tree_list = [tree2, tree3, tree6, tree_transaction]
        buy_vote = 0
        sell_vote = 0
        liquidity_flag = False
        
        for choice in tree_list:
            if choice == 'buy':
                buy_vote += 1
            elif choice == "d_buy":
                buy_vote += 2
            elif choice == 'sell':
                sell_vote += 1
            elif choice == "d_sell":
                sell_vote += 2

        # D.1 deciding on type of order, based on number of vote counts
        if buy_vote == sell_vote:
            bot_action = random_action_gen()
            order_flag = 'execute'
            result = bot_action + "_" + order_flag
        elif buy_vote > sell_vote:
            bot_action = 'buy'
            order_flag = order_type_calc(buy_vote)
            result = bot_action + "_" + order_flag
        elif sell_vote > buy_vote:
            bot_action = 'sell'
            order_flag = order_type_calc(sell_vote)
            result = bot_action + "_" + order_flag
        decision = pd.Series({
            "Trader_ID": bot["Trader_ID"],
            "Profile" : bot["Profile"],
            "Risk" : bot["Risk"],
            "Result" : result,
            "Tree2" : tree2,
            "Tree3" : tree3,
            "Tree6" : tree6,
            "Transactions" : tree_transaction,
            "Liquidity" : liquidity_flag
        })
        df_decisions = pd.concat([df_decisions, decision.to_frame().T], ignore_index=True)
    return result, state, liquidity_flag, df_decisions

def RI_bot_decision (bot, RI_market_state, key_figs, transaction_log, df_decisions):
    emotion_bias = "none"
    # B.3 - vote counting module. If counts are equal, generate random action
    def vote_counter(tree_list):
        buy_vote = 0
        sell_vote = 0
            
        for choice in tree_list:
            if choice == 'buy':
                buy_vote += 1
            elif choice == "d_buy":
                buy_vote += 2
            elif choice == 'sell':
                sell_vote += 1
            elif choice == "d_sell":
                sell_vote += 2

        # D.1 deciding on type of order, based on number of vote counts and emotional bias
        def RI_order_type_calc(vote_count, emotion_bias):
            if vote_count > 2:
                order_flag = 'execute'
            elif vote_count == 2 and emotion_bias == "negative": # simulating a form of desperation
                order_flag = 'execute'
            else:
                order_flag = 'order'
            return order_flag
        
        if buy_vote == sell_vote:
            bot_action = random_action_gen()
            order_flag = 'execute'
            result = bot_action + "_" + order_flag
        elif buy_vote > sell_vote:
            bot_action = 'buy'
            order_flag = RI_order_type_calc(buy_vote, emotion_bias)
            result = bot_action + "_" + order_flag
        elif sell_vote > buy_vote:
            bot_action = 'sell'
            order_flag = RI_order_type_calc(sell_vote, emotion_bias)
            result = bot_action + "_" + order_flag
        return result

    # RP - Bernoulli risk probability test:
        # H0: bot will trade i.e. test fails, they will trade 
        # H1: bot will not trade i.e. test passes, they will be inactive
        # setup to encourage more participation in the market 
    test_val = np.random.random()
    if test_val < bot["Risk"]:  
        state = "inactive"
    else: 
        state = "active"
    
    # determine if the bot is a high risk or low risk participant
    if bot["Profile"] == "HR Retail Investor":
        high_risk = True 
    elif bot["Profile"] == "LR Retail Investor":
        high_risk = False

    if state == "active" and high_risk == False: # regular RI tree
        # T.1 - market movement tree
        # T.1.2: function to calculate the price movement in the last 25 transactions
        if len(transaction_log) > 24:
            prev_price = transaction_log.iat[-25,-3]
        else:
            prev_price = transaction_log.iat[-1,-3]
        market_delta = prev_price - key_figs.market_price
        if market_delta > 0.02:
            tree1 = 'buy'
        elif market_delta < -0.02:
            tree1 = 'sell'
        else:
            tree1 = 'neither'

        # T.2 - Calculating the asset value/ capital ratio
        asset_value = key_figs.market_price * bot["Asset"]
        avc_ratio = asset_value / bot["Wealth"]
        avc_benchmark = avc_ratio * bot["Risk"]

        # Calculating if the bot has made a profit or loss 
        start_capital = (key_figs.open_price * bot["PreAsset"]) + bot["PreWealth"]
        current_capital = (key_figs.market_price * bot["Asset"]) + bot["Wealth"]

        # Asset-capital ratio tree and PnL - for when it is possible to call from market    
        if current_capital >= start_capital and avc_benchmark >= 0.15:
            tree2 = 'sell'
            emotion_bias = "positive"
        elif current_capital >= start_capital and avc_benchmark < 0.15:
            tree2 = 'buy'
            emotion_bias = "positive"
        elif current_capital < start_capital and avc_benchmark >= 0.15:
            tree2 = 'sell'
            emotion_bias = "negative"
        elif current_capital < start_capital and avc_benchmark < 0.15:
            tree2 = 'buy'
            emotion_bias = "negative"

        # T.4 - wildcard tree
        if bot["Risk"] >= 0.76: # this restricts this tree to the tail-end of low-risk retail investors
            tree4 = random_action_gen()
        else:
            tree4 = 'neither'

        # T.5 - market sentiment tree
        if RI_market_state == "h_bull":
            tree5 = "d_buy"
        elif RI_market_state == "bull":
            tree5 = "buy"
        elif RI_market_state == "bear":
            tree5 = "sell"
        elif RI_market_state == "h_bear":
            tree5 = "d_sell"
        elif RI_market_state == "neutral" or RI_market_state == None:
            tree5 = "neither" 
        tree_list = [tree1, tree2, tree4, tree5]
        result = vote_counter(tree_list)
        decision = pd.Series({
            "Trader_ID": bot["Trader_ID"],
            "Profile" : bot["Profile"],
            "Risk" : bot["Risk"],
            "Result" : result,
            "Tree1" : tree1,
            "Tree2" : tree2,
            "Tree4" : tree4,
            "Tree5" : tree5,
            "Emotion" : emotion_bias
        })
        df_decisions = pd.concat([df_decisions, decision.to_frame().T], ignore_index=True)

    elif state == "active" and high_risk == True: # Same decision tree, but with increased risk
        # T.1 - market movement tree
        # T.1.2: function to calculate the price movement in the last 25 transactions
        if len(transaction_log) > 24:
            prev_price = transaction_log.iat[-25,-3]
        else:
            prev_price = transaction_log.iat[-1,-3]
        market_delta = prev_price - key_figs.market_price
        if market_delta > 0.02:
            tree1 = 'buy'
        elif market_delta < -0.02:
            tree1 = 'sell'
        else:
            tree1 = 'neither'

        # T.2 - Calculating the asset value/ capital ratio
        asset_value = key_figs.market_price * bot["Asset"]
        avc_ratio = asset_value / bot["Wealth"]
        avc_benchmark = avc_ratio * bot["Risk"]

        # Calculating if the bot has made a profit or loss 
        start_capital = (key_figs.open_price * bot["PreAsset"]) + bot["PreWealth"]
        current_capital = (key_figs.market_price * bot["Asset"]) + bot["Wealth"]

        # Asset-capital ratio tree and PnL - for when it is possible to call from market    
        if current_capital >= start_capital and avc_benchmark >= 0.15:
            tree2 = 'sell'
            emotion_bias = "positive"
        elif current_capital >= start_capital and avc_benchmark < 0.15:
            tree2 = 'd_buy'
            emotion_bias = "positive"
        elif current_capital < start_capital and avc_benchmark >= 0.15:
            tree2 = 'd_sell'
            emotion_bias = "negative"
        elif current_capital < start_capital and avc_benchmark < 0.15:
            tree2 = 'buy'
            emotion_bias = "negative"

        # T.4 - wildcard tree
        if bot["Risk"] >= 0.85: # this restricts this tree to the 50th percentile of high-risk retail investors 
            tree4 = random_action_gen()
        else:
            tree4 = 'neither'

        # T.5 - market sentiment tree
        if RI_market_state == "h_bull":
            tree5 = "d_buy"
        elif RI_market_state == "bull":
            tree5 = "buy"
        elif RI_market_state == "bear":
            tree5 = "sell"
        elif RI_market_state == "h_bear":
            tree5 = "d_sell"
        elif RI_market_state == "neutral" or RI_market_state == None:
            tree5 = "neither" 
        tree_list = [tree1, tree2, tree4, tree5]
        result = vote_counter(tree_list)
        decision = pd.Series({
            "Trader_ID": bot["Trader_ID"],
            "Profile" : bot["Profile"],
            "Risk" : bot["Risk"],
            "Result" : result,
            "Tree1" : tree1,
            "Tree2" : tree2,
            "Tree4" : tree4,
            "Tree5" : tree5,
            "Emotion" : emotion_bias
        })
        df_decisions = pd.concat([df_decisions, decision.to_frame().T], ignore_index=True)

    elif state == "inactive":
        result = "no_decision"
        emotion_bias = "none"

    return result, state, emotion_bias, df_decisions

def PI_bot_decision (bot, PI_market_state, key_figs, df_decisions):
    def vote_counter(tree_list):
        # B.3 - vote counting module. If counts are equal, generate random action
        buy_vote = 0
        sell_vote = 0
        
        for choice in tree_list:
            if choice == 'buy':
                buy_vote += 1
            elif choice == "d_buy":
                buy_vote += 2
            elif choice == 'sell':
                sell_vote += 1
            elif choice == "d_sell":
                sell_vote += 2

        # D.1 deciding on type of order, based on number of vote counts
        if buy_vote == sell_vote:
            bot_action = random_action_gen()
            order_flag = 'execute'
            result = bot_action + "_" + order_flag
        elif buy_vote > sell_vote:
            bot_action = 'buy'
            order_flag = order_type_calc(buy_vote)
            result = bot_action + "_" + order_flag
        elif sell_vote > buy_vote:
            bot_action = 'sell'
            order_flag = order_type_calc(sell_vote)
            result = bot_action + "_" + order_flag
        return result

    # determine if the bot is a high risk or low risk participant
    if bot["Profile"] == "HR Private Investor":
        high_risk = True 
    elif bot["Profile"] == "LR Private Investor":
        high_risk = False

    # RP - Bernoulli risk probability test:
        # H0: bot will trade i.e. test fails, they will trade 
        # H1: bot will not trade i.e. test passes, they will be inactive
        # setup to encourage more participation in the market 
    test_val = np.random.random()
    if test_val < bot["Risk"]:  
        state = "inactive"
    else: 
        state = "active"
        
    if state == "active" and high_risk == False: # regular tree for low risk private investors 
        # T.2 - Calculating the asset value/ capital ratio
        asset_value = key_figs.market_price * bot["Asset"]
        avc_ratio = asset_value / bot["Wealth"]
        avc_benchmark = avc_ratio * bot["Risk"]

        # Calculating if the bot has made a profit or loss 
        start_capital = (key_figs.open_price * bot["PreAsset"]) + bot["PreWealth"]
        current_capital = (key_figs.market_price * bot["Asset"]) + bot["Wealth"]

        # Asset-capital ratio tree and PnL - for when it is possible to call from market    
        if current_capital >= start_capital and avc_benchmark >= 0.15:
            tree2 = 'sell'
        elif current_capital >= start_capital and avc_benchmark < 0.15:
            tree2 = 'buy'
        elif current_capital < start_capital and avc_benchmark >= 0.15:
            tree2 = 'sell'
        elif current_capital < start_capital and avc_benchmark < 0.15:
            tree2 = 'buy'

        # T.3
        if key_figs.abs_price_mvmt > 0:
            tree3 = top_price_calc(key_figs)
        elif key_figs.abs_price_mvmt < 0:
            tree3 = bot_price_calc(key_figs)    
        else:
            tree3 = "neither"

        # T.5 - market sentiment
        if PI_market_state == "bull" or PI_market_state == "h_bull":
            tree5 = "buy"
        elif PI_market_state == "bear" or PI_market_state == "h_bear":
            tree5 = "sell"
        elif PI_market_state == "neutral" or PI_market_state == None:
            tree5 = "neither" 
        else:
            tree5 = "neither"
        tree_list = [tree2, tree3, tree5]
        result = vote_counter(tree_list)
        decision = pd.Series({
            "Trader_ID": bot["Trader_ID"],
            "Profile" : bot["Profile"],
            "Risk" : bot["Risk"],
            "Result" : result,
            "Tree2" : tree2,
            "Tree3" : tree3,
            "Tree5" : tree5,
        })
        df_decisions = pd.concat([df_decisions, decision.to_frame().T], ignore_index=True)
    elif state == "active" and high_risk == True: # regular tree for low risk private investors 
        # T.2 - Calculating the asset value/ capital ratio
        asset_value = key_figs.market_price * bot["Asset"]
        avc_ratio = asset_value / bot["Wealth"]
        avc_benchmark = avc_ratio * bot["Risk"]

        # Calculating if the bot has made a profit or loss 
        start_capital = (key_figs.open_price * bot["PreAsset"]) + bot["PreWealth"]
        current_capital = (key_figs.market_price * bot["Asset"]) + bot["Wealth"]

        # Asset-capital ratio tree and PnL - for when it is possible to call from market    
        if current_capital >= start_capital and avc_benchmark >= 0.15:
            tree2 = 'sell'
        elif current_capital >= start_capital and avc_benchmark < 0.15:
            tree2 = 'd_buy'
        elif current_capital < start_capital and avc_benchmark >= 0.15:
            tree2 = 'd_sell'
        elif current_capital < start_capital and avc_benchmark < 0.15:
            tree2 = 'buy'

        # T.3
        if key_figs.abs_price_mvmt > 0:
            tree3 = top_price_calc(key_figs)
        elif key_figs.abs_price_mvmt < 0:
            tree3 = bot_price_calc(key_figs)    
        else:
            tree3 = "neither"

        # T.5 - market sentiment
        if PI_market_state == "bull":
            tree5 = "buy"
        elif PI_market_state == "h_bull":
            tree5 = "d_buy"
        elif PI_market_state == "bear":
            tree5 = "sell"
        elif PI_market_state == "h_bear":
            tree5 = "d_sell"
        elif PI_market_state == "neutral" or PI_market_state == None:
            tree5 = "neither" 
        else:
            tree5 = "neither"
        tree_list = [tree2, tree3, tree5]
        result = vote_counter(tree_list)
        decision = pd.Series({
            "Trader_ID": bot["Trader_ID"],
            "Profile" : bot["Profile"],
            "Risk" : bot["Risk"],
            "Result" : result,
            "Tree2" : tree2,
            "Tree3" : tree3,
            "Tree5" : tree5,
        })
        df_decisions = pd.concat([df_decisions, decision.to_frame().T], ignore_index=True)
    else:
        result = "no_decision"

    return result, state, df_decisions


# Below is the legacy blanket function - this is kept as a reference baseline for the original version of each decision tree
'''def bot_decision (bot,market_state, key_figs, transaction_log, buy_orderbook, sell_orderbook):
    # RP - Bernoulli risk probability test:
        # H0: bot will trade i.e. test fails, they will trade 
        # H1: bot will not trade i.e. test passes, they will be inactive
        # setup to encourage more participation in the market 
    test_val = np.random.random()
    if test_val < bot["Risk"]:  
        state = "inactive"
    else: 
        state = "active"
    
    # T.1 - market movement tree
    # T.1.2: function to calculate the price movement in the last 25 transactions
    if len(transaction_log) > 24:
        prev_price = transaction_log.iat[-25,4]
    else:
        prev_price = transaction_log.iat[-1,4]
    market_delta = prev_price - key_figs.market_price
    if market_delta > 0.02:
        tree1 = 'sell'
    elif market_delta < -0.02:
        tree1 = 'buy'
    else:
        tree1 = 'neither'
  
    if (key_figs.key_figs_test == 'pass' or key_figs.key_figs_test == 't_semipass') and state == "active":   
        # Calculating the asset value/ capital ratio
        asset_value = key_figs.market_price * bot["Asset"]
        avc_ratio = asset_value / bot["Wealth"]
        avc_benchmark = avc_ratio * bot["Risk"]

        # Calculating if the bot has made a profit or loss 
        start_capital = (key_figs.open_price * bot["PreAsset"]) + bot["PreWealth"]
        current_capital = (key_figs.market_price * bot["Asset"]) + bot["Wealth"]

        # T.2 - asset-capital ratio tree and PnL - for when it is possible to call from market    
        if current_capital >= start_capital and avc_benchmark >= 0.07:
            tree2 = 'sell'
        elif current_capital >= start_capital and avc_benchmark < 0.07:
            #tree2 = 'd_buy'
            tree2 = 'buy'
        elif current_capital < start_capital and avc_benchmark >= 0.07:
            #tree2 = 'd_sell'
            tree2 = 'sell'
        elif current_capital < start_capital and avc_benchmark < 0.07:
            tree2 = 'buy'

        # T.3
        def top_price_calc ():
            top_price_dist = key_figs.price_max - key_figs.market_price
            if top_price_dist <= 0.02:
                tree3 = 'sell'
            else:
                tree3 = 'buy'
            return tree3
        
        def bot_price_calc ():
            bot_price_dist = key_figs.market_price - key_figs.price_min    
            if bot_price_dist <= 0.02:
                tree3 = 'buy'
            else:
                tree3 = 'sell'
            return tree3

        if state == "active" and key_figs.abs_price_mvmt > 0:
            tree3 = top_price_calc()
        elif state == "active" and key_figs.abs_price_mvmt < 0:
            tree3 = bot_price_calc()    
        else:
            tree3 = "neither"

    elif (key_figs.key_figs_test == 'fail' or key_figs.key_figs_test == 'o_semipass') and state == "active":
        #T.2 - asset-capital ratio tree - for when market key figs are not available
        wealth_asset_ratio = bot["Wealth"] / bot["Asset"] 
        if wealth_asset_ratio >= 4:
            tree2 = "buy"
        elif wealth_asset_ratio < 4:
            tree2 = "sell"

        tree3 = 'neither'

    # T.4 - wildcard tree
    # function for random action choice
    def random_action_gen ():
        order_val = np.random.random()
        if order_val > 0.5:
            action = 'buy'
        else:
            action = 'sell'
        return action

    if state == "active" and bot["Risk"] >= 0.82: # this restricts this tree to the 10th percentile of risk-takers
        tree4 = random_action_gen()
    else:
        tree4 = 'neither'
    
   
    # alternative tree - introduce more variation? 

    #t4_risk = abs(np.random.standard_normal())
    #if state == "active" and t4_risk > 2: # this restricts this tree to the risk takers 2 std above the mean
    #    tree4 = 'buy'
    #else:
    #    tree4 = 'sell'
    
    # T.5 - market sentiment tree
    if state == "active" and market_state == "h_bull":
        tree5 = "d_buy"
    elif state == "active" and market_state == "bull":
        tree5 = "buy"
    elif state == "active" and market_state == "bear":
        tree5 = "sell"
    elif state == "active" and market_state == "h_bear":
        tree5 = "d_sell"
    elif state == "active" and market_state == "neutral":
        tree5 = "neither" 
    else:
        tree5 = "neither"

    # T.6 - orderbook consideration tree 
    if key_figs.key_figs_test == 'pass' and state == "active":
        # Calculating orderbook depth
        qty_buy_orderbook = buy_orderbook["Quantity"].sum()
        qty_sell_orderbook = sell_orderbook["Quantity"].sum()
        ordebook_ratio = qty_buy_orderbook / qty_sell_orderbook
        potential_qty = bot["Wealth"] / key_figs.market_price

        if ordebook_ratio < 0.5 and potential_qty >= 100:
            tree6 = "buy"
            force_flag = "none"
        elif ordebook_ratio < 0.2:
            tree6 = "buy"
            force_flag = "force"
        elif ordebook_ratio > 2 and bot["Asset"] >= 25:
            tree6 = "sell"
            force_flag = "none"
        elif ordebook_ratio > 5:
            tree6 = "sell"
            force_flag = "force"
        else: 
            tree6 = "neither"
            force_flag = "none"

    elif key_figs.key_figs_test == 't_semipass' and (state == "active" or state == "inactive"):
        # This forces the bot to make an order in the market if an orderbook is empty, even if inactive
        if key_figs.buy_orderbook_test == "b_fail" and key_figs.sell_orderbook_test == "s_pass":
            tree6 = "buy"
            force_flag = "force"
        elif key_figs.sell_orderbook_test == "s_fail" and key_figs.buy_orderbook_test == "b_pass":
            tree6 = "sell"
            force_flag = "force"
        elif key_figs.buy_orderbook_test == "b_fail" and key_figs.sell_orderbook_test == "s_fail":
            tree6 = "random_order"
            force_flag = "force"
    else:
        tree6 = "neither"
        force_flag = "none"
    
    # B.3 - vote counting module. If counts are equal, generate random action
    if state == "active":
        if force_flag == "force" and tree6 == "buy":
            result = "buy_order"
        elif force_flag == "force" and tree6 == "sell":
            result = "sell_order"
        elif force_flag == "force" and tree6 == "random_order":
            bot_action = random_action_gen()
            order_flag = 'order'
            result = bot_action + "_" + order_flag
        elif force_flag == "none":
            tree_list = [tree1, tree2, tree3, tree4, tree5, tree6]
            buy_vote = 0
            sell_vote = 0
            
            for choice in tree_list:
                if choice == 'buy':
                    buy_vote += 1
                elif choice == "d_buy":
                    buy_vote += 2
                elif choice == 'sell':
                    sell_vote += 1
                elif choice == "d_sell":
                    sell_vote += 2

            # D.1 deciding on type of order, based on number of vote counts
            def order_type_calc(vote_count):
                if vote_count > 2:
                    order_flag = 'execute'
                else:
                    order_flag = 'order'
                return order_flag
            
            if buy_vote == sell_vote:
                bot_action = random_action_gen()
                order_flag = 'execute'
                result = bot_action + "_" + order_flag
            elif buy_vote > sell_vote:
                bot_action = 'buy'
                order_flag = order_type_calc(buy_vote)
                result = bot_action + "_" + order_flag
            elif sell_vote > buy_vote:
                bot_action = 'sell'
                order_flag = order_type_calc(sell_vote)
                result = bot_action + "_" + order_flag

    elif state == "inactive" and force_flag == "force":
        if tree6 == "buy":
            result = "buy_order"
        elif tree6 == "sell":
            result = "sell_order"
        elif tree6 == "random_order":
            bot_action = random_action_gen()
            order_flag = 'order'
            result = bot_action + "_" + order_flag
    else:
        result = "no_decision"
    
    return result, bot, state'''