#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的小时和分钟级别数据测试
"""

import sys
from pathlib import Path
import pandas as pd
from pbinance import Binance

# 添加路径
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent))

def test_hourly_data():
    """测试小时级别数据"""
    print("=" * 50)
    print("测试小时级别数据获取")
    print("=" * 50)
    
    binance = Binance()
    
    # 测试币种
    test_coins = ["BNBUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "DOTUSDT"]
    
    # 测试时间范围
    start_date = "2024-12-01"
    end_date = "2024-12-02"
    
    start_time = int(pd.Timestamp(start_date).timestamp() * 1000)
    end_time = int(pd.Timestamp(end_date).timestamp() * 1000)
    
    print(f"时间范围: {start_date} 到 {end_date}")
    print(f"时间戳: {start_time} 到 {end_time}")
    
    for coin in test_coins:
        print(f"\n测试 {coin} 小时数据...")
        
        try:
            result = binance.spot.market.get_klines(
                symbol=coin,
                interval="1h",
                startTime=start_time,
                endTime=end_time
            )
            
            if result["code"] == 200:
                klines = result["data"]
                print(f"✓ {coin} 获取到 {len(klines)} 条小时数据")
                
                if klines:
                    # 解析第一条数据
                    first_kline = klines[0]
                    open_price = float(first_kline[1])
                    high_price = float(first_kline[2])
                    low_price = float(first_kline[3])
                    close_price = float(first_kline[4])
                    volume = float(first_kline[5])
                    timestamp = pd.to_datetime(first_kline[0], unit='ms')
                    
                    print(f"  第一条数据时间: {timestamp}")
                    print(f"  开盘价: {open_price}")
                    print(f"  最高价: {high_price}")
                    print(f"  最低价: {low_price}")
                    print(f"  收盘价: {close_price}")
                    print(f"  成交量: {volume}")
                    
                    # 显示前3条数据
                    print("  前3条数据:")
                    for i, kline in enumerate(klines[:3]):
                        timestamp = pd.to_datetime(kline[0], unit='ms')
                        close_price = float(kline[4])
                        volume = float(kline[5])
                        print(f"    {i+1}. {timestamp}: 收盘价={close_price}, 成交量={volume}")
                else:
                    print(f"  ✗ {coin} 没有数据")
            else:
                print(f"✗ {coin} API错误: {result}")
                
        except Exception as e:
            print(f"✗ {coin} 请求失败: {e}")

def test_minute_data():
    """测试分钟级别数据"""
    print("\n" + "=" * 50)
    print("测试分钟级别数据获取")
    print("=" * 50)
    
    binance = Binance()
    
    # 测试币种
    test_coins = ["BNBUSDT", "ETHUSDT", "XRPUSDT"]
    
    # 测试时间范围（1小时）
    start_date = "2024-12-01 10:00:00"
    end_date = "2024-12-01 11:00:00"
    
    start_time = int(pd.Timestamp(start_date).timestamp() * 1000)
    end_time = int(pd.Timestamp(end_date).timestamp() * 1000)
    
    print(f"时间范围: {start_date} 到 {end_date}")
    print(f"时间戳: {start_time} 到 {end_time}")
    
    for coin in test_coins:
        print(f"\n测试 {coin} 分钟数据...")
        
        try:
            result = binance.spot.market.get_klines(
                symbol=coin,
                interval="1m",
                startTime=start_time,
                endTime=end_time
            )
            
            if result["code"] == 200:
                klines = result["data"]
                print(f"✓ {coin} 获取到 {len(klines)} 条分钟数据")
                
                if klines:
                    # 解析第一条数据
                    first_kline = klines[0]
                    open_price = float(first_kline[1])
                    high_price = float(first_kline[2])
                    low_price = float(first_kline[3])
                    close_price = float(first_kline[4])
                    volume = float(first_kline[5])
                    timestamp = pd.to_datetime(first_kline[0], unit='ms')
                    
                    print(f"  第一条数据时间: {timestamp}")
                    print(f"  开盘价: {open_price}")
                    print(f"  最高价: {high_price}")
                    print(f"  最低价: {low_price}")
                    print(f"  收盘价: {close_price}")
                    print(f"  成交量: {volume}")
                    
                    # 显示前5条数据
                    print("  前5条数据:")
                    for i, kline in enumerate(klines[:5]):
                        timestamp = pd.to_datetime(kline[0], unit='ms')
                        close_price = float(kline[4])
                        volume = float(kline[5])
                        print(f"    {i+1}. {timestamp}: 收盘价={close_price}, 成交量={volume}")
                else:
                    print(f"  ✗ {coin} 没有数据")
            else:
                print(f"✗ {coin} API错误: {result}")
                
        except Exception as e:
            print(f"✗ {coin} 请求失败: {e}")

def test_4hour_data():
    """测试4小时级别数据"""
    print("\n" + "=" * 50)
    print("测试4小时级别数据获取")
    print("=" * 50)
    
    binance = Binance()
    
    # 测试币种
    test_coins = ["BNBUSDT", "ETHUSDT", "XRPUSDT"]
    
    # 测试时间范围（2天）
    start_date = "2024-12-01"
    end_date = "2024-12-03"
    
    start_time = int(pd.Timestamp(start_date).timestamp() * 1000)
    end_time = int(pd.Timestamp(end_date).timestamp() * 1000)
    
    print(f"时间范围: {start_date} 到 {end_date}")
    print(f"时间戳: {start_time} 到 {end_time}")
    
    for coin in test_coins:
        print(f"\n测试 {coin} 4小时数据...")
        
        try:
            result = binance.spot.market.get_klines(
                symbol=coin,
                interval="4h",
                startTime=start_time,
                endTime=end_time
            )
            
            if result["code"] == 200:
                klines = result["data"]
                print(f"✓ {coin} 获取到 {len(klines)} 条4小时数据")
                
                if klines:
                    # 解析第一条数据
                    first_kline = klines[0]
                    open_price = float(first_kline[1])
                    high_price = float(first_kline[2])
                    low_price = float(first_kline[3])
                    close_price = float(first_kline[4])
                    volume = float(first_kline[5])
                    timestamp = pd.to_datetime(first_kline[0], unit='ms')
                    
                    print(f"  第一条数据时间: {timestamp}")
                    print(f"  开盘价: {open_price}")
                    print(f"  最高价: {high_price}")
                    print(f"  最低价: {low_price}")
                    print(f"  收盘价: {close_price}")
                    print(f"  成交量: {volume}")
                    
                    # 显示所有数据
                    print("  所有4小时数据:")
                    for i, kline in enumerate(klines):
                        timestamp = pd.to_datetime(kline[0], unit='ms')
                        close_price = float(kline[4])
                        volume = float(kline[5])
                        print(f"    {i+1}. {timestamp}: 收盘价={close_price}, 成交量={volume}")
                else:
                    print(f"  ✗ {coin} 没有数据")
            else:
                print(f"✗ {coin} API错误: {result}")
                
        except Exception as e:
            print(f"✗ {coin} 请求失败: {e}")

def main():
    """主测试函数"""
    print("开始测试多个数字货币的小时和分钟级别数据获取...")
    
    # 测试小时数据
    test_hourly_data()
    
    # 测试分钟数据
    test_minute_data()
    
    # 测试4小时数据
    test_4hour_data()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
