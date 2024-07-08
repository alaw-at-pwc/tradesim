# This script takes various market info, and runs the bot through its designated decision tree. 
import numpy as np

def random_action_gen ():
        order_val = np.random.random()
        if order_val > 0.5:
            action = 'buy'
        else:
            action = 'sell'
        return action

def setup_bot_decision (bot, IB_market_state):
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
    else:
        result = "no_decision"

    return result, bot, state

def IB_bot_decision (bot, IB_market_state, key_figs, transaction_log, buy_orderbook, sell_orderbook):
    # RP - Bernoulli risk probability test:
        # H0: bot will trade i.e. test fails, they will trade 
        # H1: bot will not trade i.e. test passes, they will be inactive
        # setup to encourage more participation in the market 
    test_val = np.random.random()
    force_flag = "none"
    if test_val < bot["Risk"]:  
        state = "inactive"
    else: 
        state = "active"

    '''if key_figs.key_figs_test == 't_semipass' and state == "inactive":
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
        force_flag = "none"'''
        
    if state == "active":
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
        if key_figs.abs_price_mvmt > 0:
            tree3 = top_price_calc()
        elif key_figs.abs_price_mvmt < 0:
            tree3 = bot_price_calc()    
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
        if key_figs.key_figs_test == 'pass':
            # Calculating orderbook depth
            qty_buy_orderbook = buy_orderbook["Quantity"].sum()
            qty_sell_orderbook = sell_orderbook["Quantity"].sum()
            ordebook_ratio = qty_buy_orderbook / qty_sell_orderbook

            if ordebook_ratio < 0.5:
                tree6 = "buy"
            elif ordebook_ratio > 2:
                tree6 = "sell"
            else: 
                tree6 = "neither"

        # B.3 - vote counting module. If counts are equal, generate random action
        tree_list = [tree1, tree2, tree3, tree5, tree6]
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
            result = 'multiple_orders'
        elif buy_vote > sell_vote:
            bot_action = 'buy'
            order_flag = order_type_calc(buy_vote)
            result = bot_action + "_" + order_flag
        elif sell_vote > buy_vote:
            bot_action = 'sell'
            order_flag = order_type_calc(sell_vote)
            result = bot_action + "_" + order_flag
    else:
        result = "no_decision"

    '''elif state == "inactive" and force_flag == "force":
        if tree6 == "buy":
            result = "buy_order"
        elif tree6 == "sell":
            result = "sell_order"
        elif tree6 == "random_order":
            bot_action = random_action_gen()
            order_flag = 'order'
            result = bot_action + "_" + order_flag'''
    
    return result, bot, state

def WM_bot_decision (bot, IB_market_state, key_figs, transaction_log):
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
        if key_figs.abs_price_mvmt > 0:
            tree3 = top_price_calc()
        elif key_figs.abs_price_mvmt < 0:
            tree3 = bot_price_calc()    
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
        tree_list = [tree2, tree3, tree5]
        buy_vote = 0
        sell_vote = 0
        for choice in tree_list:
            if choice == 'buy':
                buy_vote += 1
            elif choice == 'sell':
                sell_vote += 1

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
    else:
        result = "no_decision"
    return result, bot, state

def MM_bot_decision (bot, key_figs, buy_orderbook, sell_orderbook):
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
        if key_figs.abs_price_mvmt > 0:
            tree3 = top_price_calc()
        elif key_figs.abs_price_mvmt < 0:
            tree3 = bot_price_calc()    
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

    elif key_figs.key_figs_test == 't_semipass':
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
        tree_list = [tree2, tree3, tree6]
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
    return result, bot, state, liquidity_flag

def RI_bot_decision (bot, RI_market_state, key_figs, transaction_log):
    emotion_bias = "none"
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
            #tree2 = 'd_buy'
            tree2 = 'buy'
            emotion_bias = "positive"
        elif current_capital < start_capital and avc_benchmark >= 0.15:
            #tree2 = 'd_sell'
            tree2 = 'sell'
            emotion_bias = "negative"
        elif current_capital < start_capital and avc_benchmark < 0.15:
            tree2 = 'buy'
            emotion_bias = "negative"

        # T.4 - wildcard tree
        if bot["Risk"] >= 0.82: # this restricts this tree to the 10th percentile of risk-takers
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
        
        # B.3 - vote counting module. If counts are equal, generate random action
        tree_list = [tree1, tree2, tree4, tree5]
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
        def order_type_calc(vote_count, emotion_bias):
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
            order_flag = order_type_calc(buy_vote, emotion_bias)
            result = bot_action + "_" + order_flag
        elif sell_vote > buy_vote:
            bot_action = 'sell'
            order_flag = order_type_calc(sell_vote, emotion_bias)
            result = bot_action + "_" + order_flag
    elif state == "inactive":
        result = "no_decision"
        emotion_bias = "none"

    return result, bot, state, emotion_bias

def PI_bot_decision (bot, PI_market_state, key_figs):
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
            #tree2 = 'd_buy'
            tree2 = 'buy'
        elif current_capital < start_capital and avc_benchmark >= 0.15:
            #tree2 = 'd_sell'
            tree2 = 'sell'
        elif current_capital < start_capital and avc_benchmark < 0.15:
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
        if key_figs.abs_price_mvmt > 0:
            tree3 = top_price_calc()
        elif key_figs.abs_price_mvmt < 0:
            tree3 = bot_price_calc()    
        else:
            tree3 = "neither"

        # T.5 - market sentiment
        if PI_market_state == "bull":
            tree5 = "buy"
        elif PI_market_state == "bear":
            tree5 = "sell"
        elif PI_market_state == "neutral" or PI_market_state == None:
            tree5 = "neither" 
        else:
            tree5 = "neither"

        # B.3 - vote counting module. If counts are equal, generate random action
        tree_list = [tree2, tree3, tree5]
        buy_vote = 0
        sell_vote = 0
        
        for choice in tree_list:
            if choice == 'buy':
                buy_vote += 1
            elif choice == 'sell':
                sell_vote += 1

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
    else:
        result = "no_decision"

    return result, bot, state


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