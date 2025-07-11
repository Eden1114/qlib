# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent))

from data_collector.yahoo.collector import YahooCollectorUS, Run


class CustomYahooCollectorUS1d(YahooCollectorUS):
    """
    Custom Yahoo Data Collector for US stocks that reads symbols from a stock_list.txt file
    Daily frequency (1d)
    """
    
    def __init__(
        self,
        save_dir,
        stock_list_path,
        start=None,
        end=None,
        interval="1d",
        max_workers=4,
        max_collector_count=2,
        delay=0,
        check_data_length=None,
        limit_nums=None,
    ):
        """
        Parameters
        ----------
        save_dir: str
            stock save dir
        stock_list_path: str
            path to the stock list file, each line contains one stock symbol
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
        self.stock_list_path = stock_list_path
        super(CustomYahooCollectorUS1d, self).__init__(
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
    
    def get_instrument_list(self):
        """
        Read stock symbols from the stock_list.txt file
        """
        logger.info(f"Reading stock symbols from {self.stock_list_path}...")
        
        if not os.path.exists(self.stock_list_path):
            raise FileNotFoundError(f"Stock list file not found: {self.stock_list_path}")
        
        with open(self.stock_list_path, "r") as f:
            raw_symbols = [line.strip() for line in f.readlines() if line.strip()]
        
        # 处理股票代码格式，将SOXL.US转换为SOXL
        symbols = []
        for symbol in raw_symbols:
            if symbol.endswith(".US"):
                symbol = symbol[:-3]
            symbols.append(symbol)
        
        logger.info(f"Loaded {len(symbols)} symbols from stock list file.")
        return symbols
    
    def init_datetime(self):
        """Override init_datetime to handle type comparison issues"""
        if self.interval == "1min":
            # Convert both to pd.Timestamp for comparison
            default_start = pd.Timestamp(self.DEFAULT_START_DATETIME_1MIN)
            self.start_datetime = max(self.start_datetime, default_start)
        elif self.interval == "1d":
            pass
        else:
            raise ValueError(f"interval error: {self.interval}")

        self.start_datetime = self.convert_datetime(self.start_datetime, self._timezone)
        self.end_datetime = self.convert_datetime(self.end_datetime, self._timezone)


class CustomYahooCollectorUS1min(YahooCollectorUS):
    """
    Custom Yahoo Data Collector for US stocks that reads symbols from a stock_list.txt file
    Minute frequency (1min)
    """
    
    def __init__(
        self,
        save_dir,
        stock_list_path,
        start=None,
        end=None,
        interval="1min",
        max_workers=4,
        max_collector_count=2,
        delay=0,
        check_data_length=None,
        limit_nums=None,
    ):
        """
        Parameters
        ----------
        save_dir: str
            stock save dir
        stock_list_path: str
            path to the stock list file, each line contains one stock symbol
        max_workers: int
            workers, default 4
        max_collector_count: int
            default 2
        delay: float
            time.sleep(delay), default 0
        interval: str
            freq, value from [1min, 1d], default 1min
        start: str
            start datetime, default None
        end: str
            end datetime, default None
        check_data_length: int
            check data length, by default None
        limit_nums: int
            using for debug, by default None
        """
        self.stock_list_path = stock_list_path
        super(CustomYahooCollectorUS1min, self).__init__(
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
    
    def get_instrument_list(self):
        """
        Read stock symbols from the stock_list.txt file
        """
        logger.info(f"Reading stock symbols from {self.stock_list_path}...")
        
        if not os.path.exists(self.stock_list_path):
            raise FileNotFoundError(f"Stock list file not found: {self.stock_list_path}")
        
        with open(self.stock_list_path, "r") as f:
            raw_symbols = [line.strip() for line in f.readlines() if line.strip()]
        
        # 处理股票代码格式，将SOXL.US转换为SOXL
        symbols = []
        for symbol in raw_symbols:
            if symbol.endswith(".US"):
                symbol = symbol[:-3]
            symbols.append(symbol)
        
        logger.info(f"Loaded {len(symbols)} symbols from stock list file.")
        return symbols
    
    def init_datetime(self):
        """Override init_datetime to handle type comparison issues"""
        if self.interval == "1min":
            # Convert both to pd.Timestamp for comparison
            default_start = pd.Timestamp(self.DEFAULT_START_DATETIME_1MIN)
            self.start_datetime = max(self.start_datetime, default_start)
        elif self.interval == "1d":
            pass
        else:
            raise ValueError(f"interval error: {self.interval}")

        self.start_datetime = self.convert_datetime(self.start_datetime, self._timezone)
        self.end_datetime = self.convert_datetime(self.end_datetime, self._timezone)


class CustomRun(Run):
    """
    Custom Run class for CustomYahooCollectorUS
    """
    
    def __init__(
        self, 
        source_dir=None, 
        normalize_dir=None, 
        max_workers=1, 
        interval="1d", 
        region="US",
        stock_list_path=None
    ):
        """
        Parameters
        ----------
        source_dir: str
            The directory where the raw data collected from the Internet is saved
        normalize_dir: str
            Directory for normalize data
        max_workers: int
            Concurrent number, default is 1
        interval: str
            freq, value from [1min, 1d], default 1d
        region: str
            region, value from ["CN", "US", "BR"], default "US"
        stock_list_path: str
            path to the stock list file
        """
        super(CustomRun, self).__init__(source_dir, normalize_dir, max_workers, interval, region)
        self.stock_list_path = stock_list_path
    
    @property
    def collector_class_name(self):
        return f"CustomYahooCollector{self.region.upper()}{self.interval}"
        
    @property
    def normalize_class_name(self):
        return f"YahooNormalize{self.region.upper()}{self.interval}"
    
    def download_data(
        self,
        max_collector_count=2,
        delay=0.5,
        start=None,
        end=None,
        check_data_length=None,
        limit_nums=None,
        stock_list_path=None,
    ):
        """
        Download data using CustomYahooCollector
        
        Parameters
        ----------
        max_collector_count: int
            default 2
        delay: float
            time.sleep(delay), default 0.5
        start: str
            start datetime, default None
        end: str
            end datetime, default None
        check_data_length: int
            check data length, by default None
        limit_nums: int
            using for debug, by default None
        stock_list_path: str
            path to the stock list file, if None, use the one from __init__
        """
        logger.info(f"Download data: {self.source_dir}")
        
        # Use stock_list_path from parameter or from __init__
        stock_list_path = stock_list_path or self.stock_list_path
        if stock_list_path is None:
            raise ValueError("stock_list_path must be provided either in __init__ or as parameter")
            
        # Import the collector class
        collector_class = globals()[self.collector_class_name]
        
        # Create collector instance
        collector = collector_class(
            save_dir=self.source_dir,
            stock_list_path=stock_list_path,
            max_workers=self.max_workers,
            max_collector_count=max_collector_count,
            delay=delay,
            start=start,
            end=end,
            interval=self.interval,
            check_data_length=check_data_length,
            limit_nums=limit_nums,
        )
        
        # Collect data
        collector.collector_data()
        
    def normalize_data(
        self,
        date_field_name: str = "date",
        symbol_field_name: str = "symbol",
        end_date: str = None,
        qlib_data_1d_dir: str = None,
        stock_list_path=None,
    ):
        """
        Normalize data for custom Yahoo data
        
        Parameters
        ----------
        date_field_name: str
            date field name, default "date"
        symbol_field_name: str
            symbol field name, default "symbol"
        end_date: str
            end date, default None
        qlib_data_1d_dir: str
            qlib data 1d dir, default None
        stock_list_path: str
            path to the stock list file, if None, use the one from __init__
        """
        logger.info(f"Normalize data from {self.source_dir} to {self.normalize_dir}")
        
        # Use stock_list_path from parameter or from __init__
        stock_list_path = stock_list_path or self.stock_list_path
        
        # Import the normalize class from the collector module
        from data_collector.yahoo.collector import YahooNormalizeUS1d, YahooNormalizeUS1min
        
        if self.normalize_class_name == "YahooNormalizeUS1d":
            normalize_class = YahooNormalizeUS1d
        elif self.normalize_class_name == "YahooNormalizeUS1min":
            normalize_class = YahooNormalizeUS1min
        else:
            raise ValueError(f"Unsupported normalize class: {self.normalize_class_name}")
        
        # Create normalizer instance
        kwargs = {}
        if self.interval == "1min":
            kwargs["qlib_data_1d_dir"] = qlib_data_1d_dir
        
        normalizer = normalize_class(date_field_name=date_field_name, symbol_field_name=symbol_field_name, **kwargs)
        
        # Create normalize object
        from data_collector.base import Normalize
        
        normal_obj = Normalize(
            source_dir=self.source_dir,
            target_dir=self.normalize_dir,
            normalize_class=normalize_class,
            max_workers=self.max_workers,
            date_field_name=date_field_name,
            symbol_field_name=symbol_field_name,
            **kwargs,
        )
        
        # Normalize data
        normal_obj.normalize()


if __name__ == "__main__":
    import fire
    fire.Fire(CustomRun) 