from time import sleep
from longport.openapi import (
    Config,
    SubType,
    PushQuote,
    QuoteContext,
    Period,
    AdjustType,
    Market,
    SecurityListCategory,
    TradeContext,
    OrderSide,
    OrderType,
    TimeInForceType,
    PushOrderChanged,
    TopicType,
    MarketTemperature,
    WatchlistGroup
)
from typing import List
from datetime import date

from time import sleep
from decimal import Decimal

from pprint import pprint

# Load configuration from environment variables
config = Config.from_env()

# 晒场温度
ctx = QuoteContext(config)
resp:MarketTemperature = ctx.market_temperature(Market.US)
print(resp, type(resp))
# pprint(resp.temperature, resp.sentiment, resp.valuation)

resp: List[WatchlistGroup] = ctx.watchlist()
pprint(resp)

dict_ = {watchgroup.name:[symbol for symbol in watchgroup.securities] for watchgroup in resp}

print(dict_)

print(dict_.keys())
    
exit()


# # A callback to receive quote data
# def on_quote(symbol: str, event: PushQuote):
#     pprint(symbol, event)

# # Create a context for quote APIs
# ctx = QuoteContext(config)
# ctx.set_on_quote(on_quote)

# # Subscribe
# resp = ctx.subscribe(["700.HK"], [SubType.Quote], is_first_push=True)

# # Receive push duration to 30 seconds
# sleep(30)


# 获取标的基础信息
# https://open.longportapp.com/docs/quote/pull/static
# 运行前请访问“开发者中心”确保账户有正确的行情权限。
# 如没有开通行情权限，可以通过“LongPort”手机客户端，并进入“我的 - 我的行情 - 行情商城”购买开通行情权限。


resp = ctx.static_info(["700.HK", "AAPL.US", "TSLA.US", "NFLX.US"])
pprint(resp)

resp = ctx.quote(["700.HK", "AAPL.US", "TSLA.US", "NFLX.US"])
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

exit()

# 获取市场交易日
#
# 运行前请访问“开发者中心”确保账户有正确的行情权限。
# 如没有开通行情权限，可以通过“LongPort”手机客户端，并进入“我的 - 我的行情 - 行情商城”购买开通行情权限。

resp = ctx.trading_days(Market.HK, date(2025, 6, 1), date(2025, 7, 1))
pprint(resp)


ctx = QuoteContext(config)
resp = ctx.market_temperature(Market.US)
pprint(resp)


ctx.subscribe(["700.HK", "AAPL.US"], [SubType.Quote], is_first_push=True)
sleep(30)

ctx.subscribe(["700.HK", "AAPL.US"], [SubType.Quote])
resp = ctx.subscriptions()
pprint(resp)

ctx = QuoteContext(config)
ctx.set_on_quote(on_quote)
ctx.subscribe(["700.HK", "AAPL.US"], [SubType.Quote], is_first_push=True)
sleep(30)


ctx = QuoteContext(config)
resp = ctx.security_list(Market.US, SecurityListCategory.Overnight)
pprint(resp)


config = Config.from_env()
ctx = TradeContext(config)
resp = ctx.account_balance()
pprint(resp)


# 获取股票持仓
# https://open.longportapp.com/docs/trade/asset/stock

config = Config.from_env()
ctx = TradeContext(config)
resp = ctx.stock_positions()
pprint(resp)


def on_order_changed(event: PushOrderChanged):
    pprint(event)


config = Config.from_env()
ctx = TradeContext(config)
ctx.set_on_order_changed(on_order_changed)
ctx.subscribe([TopicType.Private])
resp = ctx.submit_order(
    side=OrderSide.Buy,
    symbol="700.HK",
    order_type=OrderType.LO,
    submitted_price=Decimal(50),
    submitted_quantity=Decimal(200),
    time_in_force=TimeInForceType.Day,
    remark="Hello from Python SDK",
)
pprint(resp)
sleep(5)  # waiting for push event
# Finally, unsubscribe
ctx.unsubscribe([TopicType.Private])


# https://open.longportapp.com/zh-CN/docs/refresh-token-api


# https://open.longportapp.com/zh-CN/docs/llm
