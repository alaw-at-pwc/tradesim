import pandas as pd
import mplfinance as mpf
import ipywidgets as widgets
from IPython.display import display, clear_output
# Example DataFrame
data = pd.DataFrame({
    'Date': pd.date_range('2024-01-01', periods=100),
    'Open': [100 + i for i in range(100)],
    'High': [110 + i for i in range(100)],
    'Low': [95 + i for i in range(100)],
    'Close': [105 + i for i in range(100)],
    'Volume': [1000 + i * 10 for i in range(100)]
})
data.set_index('Date', inplace=True)
# Create a function to display mplfinance chart
def display_mplfinance_chart(df):
    fig = mpf.plot(df, type='candle', style='charles', volume=True, returnfig=True)
    return fig

# Create an Output widget
output_widget = widgets.Output()

# Define a function to update the output widget with the chart
def update_chart(change):
    with output_widget:
        clear_output(wait=True)
        fig = display_mplfinance_chart(data)
        display(fig)

# Initially display the chart
update_chart(None)

# Display the output widget
display(output_widget)