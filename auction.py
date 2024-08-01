# This script runs an opening auction, that allows for bots to place, amend and cancel orders, without being executed against, until the end of the auction period, whereby orders are cleared at the clearing price, setting the opening price for the market.
# This is where supporting functions will sit, but for now, everything will be here. Once integration witht the front end is done, then the main function will move into SimulatorCode.ipynb
import pandas as pd
import participantsetup as ps
import time

def bot_auction_logic(bot):
    # check if orders already exist, and if not, do basic decision

    # if orders exist, look to amend, cancel, maintain, and look to maybe place new order in too

    return order

def open_auction(df_participants, transaction_log):
    current_time = time.time()
    auction_end = current_time + 15 
    # call period loop, where bots place orders into market
    while current_time > auction_end:
        df_available = ps.iteration_start(df_participants) 
        for index, bot in df_available.iterrows():
            # run bot logic that decides price level and quantity for the order
            order = bot_auction_logic(bot)
            # append order to live log and historic log


        # reset time
        current_time = time.time()
    
    # once call period has ended, find clearing price 


    return clearing_price, open_auction_log, transction_log
