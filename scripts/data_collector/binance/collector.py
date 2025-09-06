# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import abc
import sys
import time
import datetime
from pathlib import Path
from typing import Iterable, Union, List

import fire
import numpy as np
import pandas as pd
from loguru import logger
from pbinance import Binance
from dotenv import load_dotenv
import os

CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent))

from data_collector.base import BaseCollector, BaseNormalize, BaseRun, Normalize
from data_collector.utils import deco_retry, get_calendar_list


class BinanceCollector(BaseCollector):
    """Binance数字货币数据收集器"""
    
    retry = 5  # 重试次数
    
    def __init__(
        self,
        save_dir: Union[str, Path],
        start=None,
        end=None,
        interval="1d",
        max_workers=1,
        max_collector_count=2,
        delay=1,  # 增加延迟避免API限制
        check_data_length: int = None,
        limit_nums: int = None,
        api_key: str = None,
        api_secret: str = None,
    ):
        """
        初始化Binance收集器
        
        Parameters
        ----------
        save_dir: str
            数据保存目录
        start: str
            开始时间
        end: str
            结束时间
        interval: str
            时间间隔，支持 "1d", "1h", "4h", "1m"
        max_workers: int
            工作进程数，默认1（避免API限制）
        max_collector_count: int
            最大收集器数量
        delay: float
            请求间隔，默认1秒
        check_data_length: int
            数据长度检查
        limit_nums: int
            限制数量（调试用）
        api_key: str
            Binance API Key
        api_secret: str
            Binance API Secret
        """
        # 先初始化binance对象
        load_dotenv()
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_SECRET")
        
        if not self.api_key or not self.api_secret:
            logger.warning("未设置Binance API Key和Secret，将使用公开API（功能受限）")
            self.binance = Binance()
        else:
            self.binance = Binance(api_key=self.api_key, api_secret=self.api_secret)
        
        # 保存limit_nums以便在get_instrument_list中使用
        self._limit_nums = limit_nums
        
        # 然后调用父类初始化（会调用get_instrument_list）
        super(BinanceCollector, self).__init__(
            save_dir=save_dir,
            start=start,
            end=end,
            interval=interval,
            max_workers=max_workers,
            max_collector_count=max_collector_count,
            delay=delay,
            check_data_length=check_data_length,
            limit_nums=limit_nums,
        )
        
        self.init_datetime()
    
    def init_datetime(self):
        """初始化时间参数"""
        if self.interval in [self.INTERVAL_1min, "1m", "1h", "4h"]:
            # 确保类型一致
            min_start = pd.Timestamp(self.DEFAULT_START_DATETIME_1MIN)
            self.start_datetime = max(self.start_datetime, min_start)
        elif self.interval == self.INTERVAL_1d:
            pass
        else:
            raise ValueError(f"不支持的间隔: {self.interval}")
    
    def get_instrument_list(self):
        """获取交易对列表"""
        logger.info("获取Binance交易对列表...")
        
        try:
            # 获取所有交易对信息
            exchange_info = self.binance.spot.market.get_exchangeInfo()
            
            if exchange_info["code"] != 200:
                logger.error(f"获取交易对信息失败: {exchange_info}")
                return []
            
            symbols = []
            # 优先选择主流交易对
            priority_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]
            
            for symbol in priority_symbols:
                if any(s["symbol"] == symbol and s["status"] == "TRADING" 
                      for s in exchange_info["data"]["symbols"]):
                    symbols.append(symbol)
            
            # 添加其他USDT交易对
            for symbol_info in exchange_info["data"]["symbols"]:
                symbol = symbol_info["symbol"]
                if (symbol.endswith("USDT") and symbol_info["status"] == "TRADING" 
                    and symbol not in symbols):
                    symbols.append(symbol)
            
            logger.info(f"获取到 {len(symbols)} 个USDT交易对")
            # 如果设置了limit_nums，只返回前N个
            if hasattr(self, '_limit_nums') and self._limit_nums:
                symbols = symbols[:self._limit_nums]
            return symbols
            
        except Exception as e:
            logger.error(f"获取交易对列表失败: {e}")
            return []
    
    def normalize_symbol(self, symbol: str):
        """标准化交易对符号"""
        return symbol.lower()
    
    def get_data(
        self, symbol: str, interval: str, start_datetime: pd.Timestamp, end_datetime: pd.Timestamp
    ) -> pd.DataFrame:
        """获取K线数据"""
        
        @deco_retry(retry_sleep=self.delay, retry=self.retry)
        def _get_simple(start_, end_):
            self.sleep()
            
            # 转换时间格式
            start_time = int(start_.timestamp() * 1000)
            end_time = int(end_.timestamp() * 1000)
            
            # 转换间隔格式
            binance_interval = self._convert_interval(interval)
            
            # 获取K线数据
            result = self.binance.spot.market.get_klines(
                symbol=symbol,
                interval=binance_interval,
                startTime=start_time,
                endTime=end_time,
                limit=1000  # 每次最多1000条
            )
            
            if result["code"] != 200:
                raise ValueError(f"获取数据失败: {result}")
            
            klines = result["data"]
            if not klines:
                raise ValueError(f"没有获取到数据: {symbol}")
            
            # 转换为DataFrame
            df = self._klines_to_dataframe(klines, symbol)
            return df
        
        try:
            if interval == self.INTERVAL_1d:
                return _get_simple(start_datetime, end_datetime)
            elif interval in [self.INTERVAL_1min, "1m", "1h", "4h"]:
                # 分钟和小时数据需要分批获取
                _res = []
                _start = start_datetime
                while _start < end_datetime:
                    if interval in ["1m", self.INTERVAL_1min]:
                        # 1分钟数据，每次获取1天
                        _tmp_end = min(_start + pd.Timedelta(days=1), end_datetime)
                    else:
                        # 小时数据，每次获取7天
                        _tmp_end = min(_start + pd.Timedelta(days=7), end_datetime)
                    
                    try:
                        _resp = _get_simple(_start, _tmp_end)
                        _res.append(_resp)
                    except ValueError as e:
                        logger.warning(f"获取数据失败: {e}")
                    _start = _tmp_end
                
                if _res:
                    return pd.concat(_res, sort=False).sort_values(["symbol", "date"])
                else:
                    return pd.DataFrame()
            else:
                raise ValueError(f"不支持的间隔: {interval}")
                
        except Exception as e:
            logger.error(f"获取数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def _convert_interval(self, interval: str) -> str:
        """转换间隔格式"""
        interval_map = {
            "1d": "1d",
            "1h": "1h", 
            "4h": "4h",
            "1min": "1m",
            "1m": "1m"
        }
        return interval_map.get(interval, "1d")
    
    def _klines_to_dataframe(self, klines: list, symbol: str) -> pd.DataFrame:
        """将K线数据转换为DataFrame"""
        if not klines:
            return pd.DataFrame()
        
        # K线数据格式: [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, 收盘时间, 成交额, 成交笔数, 主动买入成交量, 主动买入成交额, 忽略]
        columns = [
            "open_time", "open", "high", "low", "close", "volume", 
            "close_time", "quote_volume", "count", "taker_buy_volume", 
            "taker_buy_quote_volume", "ignore"
        ]
        
        df = pd.DataFrame(klines, columns=columns)
        
        # 转换数据类型
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        df["quote_volume"] = df["quote_volume"].astype(float)
        
        # 转换时间
        df["date"] = pd.to_datetime(df["open_time"], unit="ms")
        df["symbol"] = symbol
        
        # 选择需要的列
        df = df[["date", "symbol", "open", "high", "low", "close", "volume"]]
        
        return df


class BinanceNormalize(BaseNormalize):
    """Binance数据标准化器"""
    
    COLUMNS = ["open", "close", "high", "low", "volume"]
    DAILY_FORMAT = "%Y-%m-%d"
    
    def _get_calendar_list(self) -> Iterable[pd.Timestamp]:
        """获取交易日历"""
        # 数字货币7x24交易，使用连续日历
        return get_calendar_list("US_ALL")
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据"""
        if df.empty:
            return df
        
        df = df.copy()
        df.set_index("date", inplace=True)
        # 处理日期格式，支持多种格式
        df.index = pd.to_datetime(df.index, format='mixed')
        df.index = df.index.tz_localize(None)
        
        # 去重
        df = df[~df.index.duplicated(keep="first")]
        
        # 排序
        df.sort_index(inplace=True)
        
        # 处理异常数据
        df.loc[(df["volume"] <= 0) | np.isnan(df["volume"]), self.COLUMNS] = np.nan
        
        # 计算涨跌幅
        df["change"] = df["close"].pct_change()
        
        # 设置因子为1（数字货币通常不需要复权）
        df["factor"] = 1.0
        
        # 重置索引
        df = df.reset_index()
        
        return df


class BinanceNormalize1d(BinanceNormalize):
    """Binance日线数据标准化器"""
    
    def _get_calendar_list(self) -> Iterable[pd.Timestamp]:
        """获取交易日历"""
        # 数字货币7x24交易，使用连续日历
        return get_calendar_list("US_ALL")  # 使用美国日历作为参考


class BinanceNormalize1min(BinanceNormalize):
    """Binance分钟数据标准化器"""
    
    def _get_calendar_list(self) -> Iterable[pd.Timestamp]:
        """获取交易日历"""
        # 数字货币7x24交易，使用连续日历
        return get_calendar_list("US_ALL")


class Run(BaseRun):
    """Binance数据收集运行器"""
    
    def __init__(self, source_dir=None, normalize_dir=None, max_workers=1, interval="1d"):
        """
        初始化运行器
        
        Parameters
        ----------
        source_dir: str
            原始数据保存目录
        normalize_dir: str
            标准化数据保存目录
        max_workers: int
            并发数，建议为1避免API限制
        interval: str
            时间间隔，支持 "1d", "1h", "4h", "1m"
        """
        super().__init__(source_dir, normalize_dir, max_workers, interval)
    
    @property
    def collector_class_name(self):
        return "BinanceCollector"
    
    @property
    def normalize_class_name(self):
        if self.interval == "1d":
            return "BinanceNormalize1d"
        elif self.interval in ["1min", "1m", "1h", "4h"]:
            return "BinanceNormalize1min"
        else:
            return "BinanceNormalize"
    
    @property
    def default_base_dir(self) -> Union[Path, str]:
        return CUR_DIR
    
    def download_data(
        self,
        max_collector_count=2,
        delay=1,
        start=None,
        end=None,
        check_data_length=None,
        limit_nums=None,
        api_key=None,
        api_secret=None,
    ):
        """下载数据
        
        Parameters
        ----------
        max_collector_count: int
            最大收集器数量
        delay: float
            请求延迟，默认1秒
        start: str
            开始时间
        end: str
            结束时间
        check_data_length: int
            数据长度检查
        limit_nums: int
            限制数量
        api_key: str
            Binance API Key
        api_secret: str
            Binance API Secret
            
        Examples
        --------
        # 下载日线数据
        $ python collector.py download_data --source_dir ~/.qlib/crypto_data/source --start 2023-01-01 --end 2023-12-31 --interval 1d --limit_nums 10
        
        # 下载分钟数据
        $ python collector.py download_data --source_dir ~/.qlib/crypto_data/source --start 2023-12-01 --end 2023-12-02 --interval 1m --limit_nums 5
        """
        # 创建collector实例并传递额外参数
        collector_class = getattr(self._cur_module, self.collector_class_name)
        collector = collector_class(
            save_dir=self.source_dir,
            max_workers=self.max_workers,
            max_collector_count=max_collector_count,
            delay=delay,
            start=start,
            end=end,
            interval=self.interval,
            check_data_length=check_data_length,
            limit_nums=limit_nums,
            api_key=api_key,
            api_secret=api_secret,
        )
        collector.collector_data()
    
    def normalize_data(
        self,
        date_field_name: str = "date",
        symbol_field_name: str = "symbol",
        end_date: str = None,
    ):
        """标准化数据
        
        Parameters
        ----------
        date_field_name: str
            日期字段名
        symbol_field_name: str
            交易对字段名
        end_date: str
            结束日期
            
        Examples
        --------
        $ python collector.py normalize_data --source_dir ~/.qlib/crypto_data/source --normalize_dir ~/.qlib/crypto_data/normalize --interval 1d
        """
        super(Run, self).normalize_data(
            date_field_name, symbol_field_name, end_date=end_date
        )


if __name__ == "__main__":
    fire.Fire(Run)

