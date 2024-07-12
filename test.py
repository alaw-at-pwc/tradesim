import pandas as pd
orderbook = pd.DataFrame()
new_order = {
    "Order_ID": 3, 
    "Trader_ID" : 4, 
    "Timestamp" : 5, 
    "Quantity" : 6, 
    "Price" : 7, 
    "Side": "Sell", 
    "Status": "Open", 
    "Update_Timestamp": 5, 
    "Version": 1}
order = pd.Series(new_order)
orderbook = pd.concat([orderbook, order.to_frame().T], ignore_index=True)
print(orderbook)
inp = {
    "Order_ID": 3, 
    "Trader_ID" : 4, 
    "Timestamp" : 5, 
    "Quantity" : 6, 
    "Price" : 7, 
    "Side": "Sell", 
    "Status": "Open", 
    "Update_Timestamp": 5, 
    "Version": 1}
stale_order = orderbook[(orderbook["Order_ID"] == inp["Order_ID"]) & (orderbook["Quantity"] == inp["Quantity"])].index
update_cols = ["Status", "Update_Timestamp"]
orderbook.loc[stale_order, update_cols] = ["Partial Fill", 6]
ver_count = int(orderbook.loc[stale_order, "Version"]) + 1
amend = {
    "Order_ID": 3, 
    "Trader_ID" : 4, 
    "Timestamp" : 5, 
    "Quantity" : 6, 
    "Price" : 7, 
    "Side": "Sell", 
    "Status": "Open", 
    "Update_Timestamp": 6, 
    "Version": ver_count}
amend_order = pd.Series(amend)
orderbook = pd.concat([orderbook, amend_order.to_frame().T], ignore_index=True)
print (ver_count)
print(orderbook)
