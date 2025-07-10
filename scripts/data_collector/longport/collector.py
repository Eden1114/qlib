# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import abc
import sys
import copy
import time
import datetime
from abc import ABC
from pathlib import Path
from typing import Iterable

import fire
import pandas as pd
from loguru import logger
from dateutil.tz import tzlocal
from dotenv import load_dotenv
import os

from longport.openapi import (
    QuoteContext,
    Config,
    Market,
    AdjustType,
    SecurityListCategory,
    Period,
)

import qlib
from qlib.data import D
from qlib.utils import code_to_fname, fname_to_code, exists_qlib_data
from qlib.constant import REG_CN as REGION_CN

CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent))

from dump_bin import DumpDataUpdate
from data_collector.base import BaseCollector, BaseNormalize, BaseRun, Normalize
from data_collector.utils import (
    deco_retry,
    get_calendar_list,
    get_hs_stock_symbols,
    get_us_stock_symbols,
    generate_minutes_calendar_from_daily,
    calc_adjusted_price,
)


class LongportCollector(BaseCollector):
    retry = 5  # Configuration attribute. How many times will it try to re-request the data if the network fails.

    def __init__(
        self,
        save_dir: [str, Path],
        start=None,
        end=None,
        interval="1d",
        max_workers=4,
        max_collector_count=2,
        delay=0,
        check_data_length: int = None,
        limit_nums: int = None,
    ):
        """
        Parameters
        ----------
        save_dir: str
            stock save dir
        max_workers: int
            workers, default 4
        max_collector_count: int
            default 2
        delay: float
            time.sleep(delay), default 0
        interval: str
            freq, value from [1min, 1d], default 1d
        start: str
            start datetime, default None
        end: str
            end datetime, default None
        check_data_length: int
            check data length, by default None
        limit_nums: int
            using for debug, by default None
        """
        self.init_config()
        super(LongportCollector, self).__init__(
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
        # 初始化配置必须在初始化日期时间之前
        self.init_datetime()

    def init_config(self):
        """Initialize Longport API config"""
        load_dotenv(override=True)
        debug = os.getenv("LONGPORT_DEBUG", "False").lower() == "true"
        
        self.config = Config(
            app_key=os.getenv("LONGPORT_APP_KEY"),
            app_secret=os.getenv("LONGPORT_APP_SECRET"),
            access_token=os.getenv("LONGPORT_DEBUG_ACCESS_TOKEN")
            if debug
            else os.getenv("LONGPORT_ACCESS_TOKEN"),
        )
        

    def init_datetime(self):
        if self.interval == self.INTERVAL_1min:
            self.start_datetime = max(self.start_datetime, self.DEFAULT_START_DATETIME_1MIN)
        elif self.interval == self.INTERVAL_1d:
            pass
        else:
            raise ValueError(f"interval error: {self.interval}")

        self.start_datetime = self.convert_datetime(self.start_datetime, self._timezone)
        self.end_datetime = self.convert_datetime(self.end_datetime, self._timezone)

    @staticmethod
    def convert_datetime(dt: [pd.Timestamp, datetime.date, str], timezone):
        try:
            dt = pd.Timestamp(dt, tz=timezone).timestamp()
            dt = pd.Timestamp(dt, tz=tzlocal(), unit="s")
        except ValueError:
            pass
        return dt

    @property
    @abc.abstractmethod
    def _timezone(self):
        raise NotImplementedError("rewrite get_timezone")

    def get_data_from_remote(self, symbol, interval, start_date, end_date):
        """Get data from Longport API"""
        error_msg = f"{symbol}-{interval}-{start_date}-{end_date}"
        
        try:
            ctx = QuoteContext(self.config)
            
            # Convert to Python date objects for the API
            if isinstance(start_date, pd.Timestamp):
                start_date = start_date.date()
            if isinstance(end_date, pd.Timestamp):
                end_date = end_date.date()
                
            # Map interval to Longport Period
            period = Period.Day if interval in ["1d"] else Period.Min_1
            adjust_type = AdjustType.ForwardAdjust  # Default to no adjustment
            
            # Call the API
            resp = ctx.history_candlesticks_by_date(
                symbol, period, adjust_type, start_date, end_date
            )
            
            if resp:
                # Convert to DataFrame
                data = []
                for candle in resp:
                    data.append({
                        'symbol': symbol,
                        'date': candle.timestamp,
                        'open': candle.open,
                        'high': candle.high,
                        'low': candle.low,
                        'close': candle.close,
                        'volume': candle.volume,
                        'turnover': getattr(candle, 'turnover', 0)
                    })
                
                return pd.DataFrame(data)
            else:
                logger.warning(f"No data returned for {error_msg}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.warning(f"Get data error: {symbol}--{start_date}--{end_date}: {str(e)}")
            return pd.DataFrame()

    def get_data(
        self, symbol: str, interval: str, start_datetime: pd.Timestamp, end_datetime: pd.Timestamp
    ) -> pd.DataFrame:
        @deco_retry(retry_sleep=self.delay, retry=self.retry)
        def _get_simple(start_, end_):
            self.sleep()
            resp = self.get_data_from_remote(
                symbol,
                interval=interval,
                start_date=start_,
                end_date=end_,
            )
            if resp is None or resp.empty:
                raise ValueError(
                    f"get data error: {symbol}--{start_}--{end_}" + "The stock may be delisted, please check"
                )
            return resp

        _result = None
        if interval == self.INTERVAL_1d:
            try:
                _result = _get_simple(start_datetime, end_datetime)
            except ValueError as e:
                pass
        elif interval == self.INTERVAL_1min:
            _res = []
            _start = self.start_datetime
            while _start < self.end_datetime:
                _tmp_end = min(_start + pd.Timedelta(days=7), self.end_datetime)
                try:
                    _resp = _get_simple(_start, _tmp_end)
                    _res.append(_resp)
                except ValueError as e:
                    pass
                _start = _tmp_end
            if _res:
                _result = pd.concat(_res, sort=False).sort_values(["symbol", "date"])
        else:
            raise ValueError(f"cannot support {self.interval}")
        return pd.DataFrame() if _result is None else _result

    def collector_data(self):
        """collector data"""
        super(LongportCollector, self).collector_data()
        self.download_index_data()

    @abc.abstractmethod
    def download_index_data(self):
        """download index data"""
        raise NotImplementedError("rewrite download_index_data")


class LongportCollectorUS(LongportCollector, ABC):
    def get_instrument_list(self):
        """Get US stock symbols"""
        try:
            ctx = QuoteContext(self.config)
            resp = ctx.security_list(Market.US, SecurityListCategory.Overnight)
            symbols = [security.symbol for security in resp]
            # symbols = ['TSLA.US', "SOXL.US", "AAPL.US"]
            return symbols
        except Exception as e:
            logger.warning(f"Failed to get US stock symbols: {str(e)}")
            # Fallback to built-in method
            return get_us_stock_symbols()

    def download_index_data(self):
        """Download US index data"""
        # Common US indices
        indices = ["SPY.US", "QQQ.US", "DIA.US"]
        for index_symbol in indices:
            try:
                df = self.get_data(index_symbol, self.interval, self.start_datetime, self.end_datetime)
                if not df.empty:
                    self.save_instrument(index_symbol, df)
            except Exception as e:
                logger.warning(f"Failed to download index data for {index_symbol}: {str(e)}")

    def normalize_symbol(self, symbol):
        """Normalize US stock symbols"""
        # Ensure US suffix
        if not symbol.endswith(".US"):
            symbol = f"{symbol}.US"
        return symbol

    @property
    def _timezone(self):
        """US stock market timezone"""
        return "America/New_York"


class LongportCollectorUS1d(LongportCollectorUS):
    """US daily data collector"""
    pass


class LongportCollectorUS1min(LongportCollectorUS):
    """US minute data collector"""
    pass


class LongportCollectorHK(LongportCollector, ABC):
    def get_instrument_list(self):
        """Get HK stock symbols"""
        try:
            ctx = QuoteContext(self.config)
            resp = ctx.security_list(Market.HK, SecurityListCategory.All)
            symbols = [security.symbol for security in resp]
            return symbols
        except Exception as e:
            logger.warning(f"Failed to get HK stock symbols: {str(e)}")
            # Return an empty list as fallback
            return []

    def download_index_data(self):
        """Download HK index data"""
        # Common HK indices
        indices = ["HSI.HK", "HSCEI.HK"]
        for index_symbol in indices:
            try:
                df = self.get_data(index_symbol, self.interval, self.start_datetime, self.end_datetime)
                if not df.empty:
                    self.save_instrument(index_symbol, df)
            except Exception as e:
                logger.warning(f"Failed to download index data for {index_symbol}: {str(e)}")

    def normalize_symbol(self, symbol):
        """Normalize HK stock symbols"""
        # Ensure HK suffix
        if not symbol.endswith(".HK"):
            symbol = f"{symbol}.HK"
        return symbol

    @property
    def _timezone(self):
        """HK stock market timezone"""
        return "Asia/Hong_Kong"


class LongportCollectorHK1d(LongportCollectorHK):
    """HK daily data collector"""
    pass


class LongportCollectorHK1min(LongportCollectorHK):
    """HK minute data collector"""
    pass


class LongportNormalize(BaseNormalize):
    COLUMNS = ["open", "close", "high", "low", "volume", "turnover"]
    DAILY_FORMAT = "%Y-%m-%d"

    @staticmethod
    def calc_change(df: pd.DataFrame, last_close: float) -> pd.Series:
        df = df.copy()
        df["change"] = df["close"] / df["close"].shift(1) - 1
        if last_close is not None and len(df) > 0:
            df["change"].iloc[0] = df["close"].iloc[0] / last_close - 1
        return df

    @staticmethod
    def normalize_longport(
        df: pd.DataFrame,
        calendar_list: list = None,
        date_field_name: str = "date",
        symbol_field_name: str = "symbol",
        last_close: float = None,
    ):
        if df.empty:
            return df

        # Convert date format
        df[date_field_name] = pd.to_datetime(df[date_field_name])
        
        # Filter by calendar
        if calendar_list is not None:
            df = df[df[date_field_name].isin(calendar_list)]
        
        # Calculate change
        if last_close is not None and len(df) > 0:
            df = LongportNormalize.calc_change(df, last_close)
        
        # Sort by date
        df = df.sort_values(by=[date_field_name])
        
        return df

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        # normalize
        df = self.adjusted_price(df)
        df = self.normalize_longport(
            df, self._calendar_list, self._date_field_name, self._symbol_field_name, None
        )
        return df

    @abc.abstractmethod
    def adjusted_price(self, df: pd.DataFrame) -> pd.DataFrame:
        # adjusted price
        raise NotImplementedError("rewrite adjusted_price")


class LongportNormalize1d(LongportNormalize, ABC):
    DAILY_FORMAT = "%Y-%m-%d"

    def adjusted_price(self, df: pd.DataFrame) -> pd.DataFrame:
        # Use adjusted price
        if df.empty:
            return df
        return df

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        # normalize
        df = df.copy()
        df = self.adjusted_price(df)
        df = self.normalize_longport(
            df, self._calendar_list, self._date_field_name, self._symbol_field_name, self._get_first_close(df)
        )
        return df

    def _get_first_close(self, df: pd.DataFrame) -> float:
        if df.empty:
            return None
        return df["close"].iloc[0]


class LongportNormalizeUS:
    def _get_calendar_list(self) -> Iterable[pd.Timestamp]:
        # Get US market calendar
        return get_calendar_list("US_ALL")


class LongportNormalizeUS1d(LongportNormalizeUS, LongportNormalize1d):
    pass


class LongportNormalizeHK:
    def _get_calendar_list(self) -> Iterable[pd.Timestamp]:
        # Get HK market calendar - use CSI300 as a fallback since HKEX is not available
        try:
            # 尝试使用自定义日历
            ctx = QuoteContext(Config.from_env())
            symbol = "HSI.HK"  # 使用恒生指数作为参考
            start_date = date(2000, 1, 1)
            end_date = datetime.datetime.now().date()
            resp = ctx.history_candlesticks_by_date(
                symbol, Period.Day, AdjustType.NoAdjust, start_date, end_date
            )
            
            if resp:
                # 提取日期
                dates = [pd.Timestamp(candle.timestamp) for candle in resp]
                return sorted(dates)
        except Exception as e:
            logger.warning(f"Failed to get HK calendar: {str(e)}, using CSI300 as fallback")
            
        # 使用CSI300作为备用
        return get_calendar_list("CSI300")


class LongportNormalizeHK1d(LongportNormalizeHK, LongportNormalize1d):
    pass


class Run(BaseRun):
    def __init__(self, source_dir=None, normalize_dir=None, max_workers=1, interval="1d", region="US"):
        """
        Parameters
        ----------
        source_dir: str
            The directory where the raw data collected from the Internet is saved, default "Path(__file__).parent/source"
        normalize_dir: str
            Directory for normalize data, default "Path(__file__).parent/normalize"
        max_workers: int
            Concurrent number, default is 1; when collecting data, it is recommended that max_workers be set to 1
        interval: str
            freq, value from [1min, 1d], default 1d
        region: str
            region, value from ["US", "HK"], default "US"
        """
        super().__init__(source_dir, normalize_dir, max_workers, interval)
        self.region = region

    @property
    def collector_class_name(self):
        return f"LongportCollector{self.region.upper()}{self.interval}"

    @property
    def normalize_class_name(self):
        return f"LongportNormalize{self.region.upper()}{self.interval}"

    @property
    def default_base_dir(self) -> [Path, str]:
        return CUR_DIR

    def download_data(
        self,
        max_collector_count=2,
        delay=0.5,
        start=None,
        end=None,
        check_data_length=None,
        limit_nums=None,
    ):
        """download data from Longport API

        Parameters
        ----------
        max_collector_count: int
            default 2
        delay: float
            time.sleep(delay), default 0.5
        start: str
            start datetime, default "2000-01-01"; closed interval(including start)
        end: str
            end datetime, default ``pd.Timestamp(datetime.datetime.now() + pd.Timedelta(days=1))``; open interval(excluding end)
        check_data_length: int
            check data length, if not None and greater than 0, each symbol will be considered complete if its data length is greater than or equal to this value, otherwise it will be fetched again, the maximum number of fetches being (max_collector_count). By default None.
        limit_nums: int
            using for debug, by default None

        Examples
        ---------
            # get daily data
            $ python collector.py download_data --source_dir ~/.qlib/stock_data/source --region US --start 2020-11-01 --end 2020-11-10 --delay 0.1 --interval 1d
            # get 1m data
            $ python collector.py download_data --source_dir ~/.qlib/stock_data/source --region US --start 2020-11-01 --end 2020-11-10 --delay 0.1 --interval 1m
        """
        if self.interval == "1d" and pd.Timestamp(end) > pd.Timestamp(datetime.datetime.now().strftime("%Y-%m-%d")):
            raise ValueError(f"end_date: {end} is greater than the current date.")

        super(Run, self).download_data(max_collector_count, delay, start, end, check_data_length, limit_nums)

    def normalize_data(
        self,
        date_field_name: str = "date",
        symbol_field_name: str = "symbol",
        end_date: str = None,
    ):
        """normalize data

        Parameters
        ----------
        date_field_name: str
            date field name, default date
        symbol_field_name: str
            symbol field name, default symbol
        end_date: str
            end date, default None

        Examples
        ---------
            # normalize US 1d data
            $ python collector.py normalize_data --source_dir ~/.qlib/stock_data/source --normalize_dir ~/.qlib/stock_data/normalize --region US --interval 1d
            # normalize HK 1d data
            $ python collector.py normalize_data --source_dir ~/.qlib/stock_data/source --normalize_dir ~/.qlib/stock_data/normalize --region HK --interval 1d
        """
        super(Run, self).normalize_data(date_field_name, symbol_field_name, end_date=end_date)


if __name__ == "__main__":
    fire.Fire(Run)
