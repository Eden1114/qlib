from longport.openapi import (
    TradeContext,
    QuoteContext,
    Config,
    Market,
    AdjustType,
    SecurityListCategory,
    Period,
)
from pprint import pprint
from time import sleep
from longport.openapi import QuoteContext, Config, SubType, PushQuote
from dotenv import load_dotenv
from datetime import date
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from matplotlib.ticker import FuncFormatter
import numpy as np
from datetime import datetime

debug = True

load_dotenv(override=True)

config = Config(
    app_key=os.getenv("LONGPORT_APP_KEY"),
    app_secret=os.getenv("LONGPORT_APP_SECRET"),
    access_token=os.getenv("LONGPORT_DEBUG_ACCESS_TOKEN")
    if debug
    else os.getenv("LONGPORT_ACCESS_TOKEN"),
)

# config: Config = Config.from_env()
# ctx = QuoteContext(config)

# 当前仅支持US
# resp = ctx.security_list(Market.US, SecurityListCategory.Overnight)
# pprint(resp)
# print(len(resp))


# resp = ctx.watchlist()
# pprint(resp)


def my_account_info():
    resp = TradeContext(Config.from_env()).account_balance()
    print(f"Net assets {resp[0].net_assets} HKD, {float(resp[0].net_assets )/ 7.8} USD")

    resp = TradeContext(Config.from_env()).stock_positions()
    pprint(resp.channels[0].account_channel)
    pprint(len(resp.channels[0].positions))

    for position in resp.channels[0].positions:
        print(position)
        
        fstring = f"{position.symbol}/{position.symbol_name} \t "
        fstring = f"Current position: {position.available_quantity} shares \t"
        fstring += f"Cost price {position.cost_price} {position.currency}\t"
        print(fstring)


def subscribe_quote():
    def on_quote(symbol: str, quote: PushQuote):
        print(symbol, quote)

    config = Config.from_env()
    ctx = QuoteContext(config)

    ctx.set_on_quote(on_quote)
    

    symbols = [
        position.symbol
        for position in TradeContext(Config.from_env())
        .stock_positions()
        .channels[0]
        .positions
    ]
    symbols = ["SOXL.US"]

    ctx.subscribe(symbols, [SubType.Quote], True)
    sleep(30)


def submit_order():
    from decimal import Decimal
    from longport.openapi import (
        TradeContext,
        Config,
        OrderSide,
        OrderType,
        TimeInForceType,
    )

    config = Config.from_env()
    ctx = TradeContext(config)

    #
    # resp = ctx.submit_order(
    #     side=OrderSide.Buy,
    #     symbol="700.HK",
    #     order_type=OrderType.LO,
    #     submitted_price=Decimal(50),
    #     submitted_quantity=Decimal(200),
    #     time_in_force=TimeInForceType.Day,
    #     remark="Hello from Python SDK",
    # )
    # print(resp)


def get_ticker():
    ctx = QuoteContext(config)
    symbols = ["SOXL.US"]
    resp = ctx.static_info(symbols)
    pprint(resp)

    resp = ctx.quote(symbols)
    pprint(resp)

    # resp = ctx.option_quote(["AAPL230317P160000.US"])
    # pprint(resp)

    resp = ctx.depth("AAPL.US")
    pprint(resp)

    resp = ctx.intraday("700.HK")
    pprint(resp)


    resp = ctx.history_candlesticks_by_date(
        "SOXL.US", Period.Day, AdjustType.NoAdjust, date(2025, 1, 1), date(2025, 6, 28)
    )
    pprint(resp)


def plot_candlestick(symbol, candlesticks):
    """
    Draw candlestick chart
    
    Parameters:
    - symbol: Stock symbol
    - candlesticks: Candlestick data list from API
    """
    # Convert data to pandas DataFrame
    data = []
    for candle in candlesticks:
        # Print first candle object for debugging
        if len(data) == 0:
            print("Candle object example:")
            print(f"Type: {type(candle)}")
            print(f"Attributes: {dir(candle)}")
            print(f"Timestamp: {candle.timestamp} Type: {type(candle.timestamp)}")
        
        # If timestamp is already a datetime object, use it directly
        if isinstance(candle.timestamp, datetime):
            timestamp = candle.timestamp
        else:
            # Try different time formats
            try:
                timestamp = datetime.strptime(candle.timestamp, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                try:
                    timestamp = datetime.strptime(candle.timestamp, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # If above formats don't match, try ISO format
                    timestamp = pd.to_datetime(candle.timestamp)
        
        data.append({
            'Date': timestamp,
            'Open': candle.open,
            'High': candle.high,
            'Low': candle.low,
            'Close': candle.close,
            'Volume': candle.volume
        })
    
    # Return if no data
    if not data:
        print("No candlestick data available")
        return
        
    df = pd.DataFrame(data)
    df.set_index('Date', inplace=True)
    
    # Create chart
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    
    # Draw candlestick chart
    up_color = 'red'
    down_color = 'green'
    
    for i, (idx, row) in enumerate(df.iterrows()):
        # Calculate candle position and size
        date_num = mdates.date2num(idx)
        
        # Determine color (up or down)
        color = up_color if row['Close'] >= row['Open'] else down_color
        
        # Draw body
        rect_height = abs(row['Close'] - row['Open'])
        rect_bottom = min(row['Close'], row['Open'])
        rect = plt.Rectangle((date_num-0.4, rect_bottom), 0.8, rect_height, 
                            fill=True, color=color, alpha=0.6)
        ax1.add_patch(rect)
        
        # Draw wicks
        ax1.plot([date_num, date_num], [row['Low'], rect_bottom], color='black', linewidth=1)
        ax1.plot([date_num, date_num], [row['High'], rect_bottom + rect_height], color='black', linewidth=1)
    
    # Draw volume
    ax2.bar(df.index, df['Volume'], color=[up_color if df['Close'][i] >= df['Open'][i] else down_color for i in range(len(df))], alpha=0.6)
    
    # Set x-axis format
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.xticks(rotation=45)
    
    # Set volume y-axis format (in millions)
    def millions(x, pos):
        return f'{x/1000000:.1f}M'
    
    ax2.yaxis.set_major_formatter(FuncFormatter(millions))
    
    # Set title and labels
    ax1.set_title(f'{symbol} Candlestick Chart')
    ax1.set_ylabel('Price')
    ax2.set_ylabel('Volume')
    ax2.set_xlabel('Date')
    
    # Auto adjust date labels
    fig.autofmt_xdate()
    
    # Add grid
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    # Adjust layout
    plt.tight_layout()
    
    # Show chart
    plt.show()


if __name__ == "__main__":
    
    # my_account_info()
    # subscribe_quote()
    
    # Get historical candlestick data
    ctx = QuoteContext(config)
    symbol = "SOXL.US"
    resp = ctx.history_candlesticks_by_date(
        symbol, Period.Day, AdjustType.NoAdjust, date(2025, 1, 1), date(2025, 6, 28)
    )
    
    # Print return data type and length
    print(f"Return data type: {type(resp)}")
    print(f"Data length: {len(resp)}")
    
    # Print first data details
    if resp and len(resp) > 0:
        print("\nFirst candlestick data:")
        print(resp[0])
    
    # Draw candlestick chart
    plot_candlestick(symbol, resp)
    
    # get_ticker()


# for watchlistgroup in resp:
#     print(watchlistgroup.name)
#     if watchlistgroup.name == 'holdings':
#         print(watchlistgroup.securities)

#         for security in watchlistgroup.securities:
#             print(security.symbol)
#             print(security.market)
#             print(security.watched_at)
#             print(security.watched_price)
#             print(security.name)

# for watchlist in watchlistgroup.watchlist:
#     print(watchlist.name)
# print(watchlist.security_list)
# print(watchlist.security_list_id)
# print(watchlist.security_list_name)
# print(watchlist.security_list_type)
# print(watchlist.security_list_type_name)
