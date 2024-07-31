This is a trade simulator, that takes bots trading in a virtual CLOB, and provides the ability for a user to place their own orders into that environment. 

**Note**: it is recommended to run this code in Visual Studio Code (VS Code), since it leverages Jupyter Notebooks and Ipywidgets, which are well integrated in VS Code, although other editors may work.

Supporting docs to explain bot logic, assumptions and such will be added in the future as this project progresses.

## User Guide
- After downloading the repository, ensure to create a Python local Virtual Environment, with the packages outlined in [*requirements.txt*](https://github.com/alaw-at-pwc/tradesim/blob/main/requirements.txt).
- Navigate to [*SimulatorCode.ipynb*](https://github.com/alaw-at-pwc/tradesim/blob/main/SimulatorCode.ipynb), as this is where the the simulation loop runs.
- Run the first cell block, which should then generate the front-end simulation setup box.
- In here, you can specify:
    1. the number of participants;
    2. the level of liquidity to model in the market;
    3. the runtime of the simulation in seconds (or untick the checkbox for an endless simulation);
    4. to fabricate market data for a specified period of time;
    5. and, the name of the output file, which will be generated into the *output* folder once the simulation has ended.
- Once configured, click the *Start* button below. Shortly, the front-end graphics will generate, displaying market figures, orderbooks, recent transactions, a candlestick chart and market sentiments.
- If you wish to terminate the simulation, click the *End* button.

### User Interaction
Before any user interaction, you must **click the *Pause* button.** This is required in order for this feature to work.

Should you wish to **place** your own orders, please do the following:
- Under the User Profile section, the total available assets and wealth are displayed.
- In the middle console, select the side for which you would like to place the order *(Buy or Sell side)*, and the type of order *(Order (meaning a limit order), or Execute (meaning a market order))*.
- If a Limit Order is selected, enter the Price for the order.
- Choose the quantity you wish to order.
- CLick the *Place Order* button.
- Relevant front-end elements should shortly update in accordance with your order.
- Once you have placed all the orders you wish, then click the *Resume* button to continue the simulation.

Should you wish to **cancel** your order, please do the following:
- Select for which side you wish to cancel.
- Enter the *OrderID*, which is displayed in the Open User Position tables.
- Relevant front-end elements should shortly update in accordance with your order.
- Once you have cancelled all the orders you wish, then click the *Resume* button to continue the simulation.

### Results Analysis
Once you have ended the simulation, the below cells provide functions to perform analysis over the simulation, reviewing the profitability of the bots. So far, the following has been implemented:
1. Calculates the individual performance of each bot from the start, and the end of the simulation;
2. The performance of the market overall throughout the simulation;
3. The highest and lowest performing bots:
4. The aggregated performance for each market participant type.

Should you wish to view these, run each of the corresponding cells, which will display the reuslts below the cell. 

### Orderbook Replay 
The [*replay.ipynb*](https://github.com/alaw-at-pwc/tradesim/blob/replay/replay.ipynb) script allows for the user to replay what happened during the simulation, based on the output file.
- Run the first cell block, which should then generate the front-end replay UI.
- Enter the **full file name** e.g. output.xlsx, and click the submit button.
- If successful, you will then be able to specify a time (in seconds) or use the play button to view the market.
- The '<<<' allows for the user to rewind if desired, whilst '>>>' forward replay is selected by default, with the speed of the replay being able to be selected by the buttons to the right.  