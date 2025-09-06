#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验收测试 - 验证Binance数据收集器的完整功能
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime

# 添加路径
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent))

def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("最终验收测试 - Binance数据收集器")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"测试目录: {temp_dir}")
        
        # 测试1: 日线数据收集
        print("\n1. 测试日线数据收集...")
        cmd = f"""
        cd {CUR_DIR.parent.parent.parent} && 
        python scripts/data_collector/binance/collector.py download_data \
            --source_dir {temp_dir}/daily \
            --start 2024-12-01 \
            --end 2024-12-02 \
            --interval 1d \
            --limit_nums 3 \
            --delay 2
        """
        
        result = os.system(cmd)
        if result == 0:
            print("✓ 日线数据收集成功")
            
            # 检查文件
            daily_files = list(Path(temp_dir).joinpath("daily").glob("*.csv"))
            print(f"  生成了 {len(daily_files)} 个文件")
            
            if daily_files:
                df = pd.read_csv(daily_files[0])
                print(f"  数据形状: {df.shape}")
                print(f"  列名: {list(df.columns)}")
                print(f"  时间范围: {df['date'].min()} 到 {df['date'].max()}")
        else:
            print("✗ 日线数据收集失败")
            return False
        
        # 测试2: 小时数据收集
        print("\n2. 测试小时数据收集...")
        cmd = f"""
        cd {CUR_DIR.parent.parent.parent} && 
        python scripts/data_collector/binance/collector.py download_data \
            --source_dir {temp_dir}/hourly \
            --start 2024-12-01 \
            --end 2024-12-02 \
            --interval 1h \
            --limit_nums 2 \
            --delay 2
        """
        
        result = os.system(cmd)
        if result == 0:
            print("✓ 小时数据收集成功")
            
            # 检查文件
            hourly_files = list(Path(temp_dir).joinpath("hourly").glob("*.csv"))
            print(f"  生成了 {len(hourly_files)} 个文件")
            
            if hourly_files:
                df = pd.read_csv(hourly_files[0])
                print(f"  数据形状: {df.shape}")
                print(f"  时间范围: {df['date'].min()} 到 {df['date'].max()}")
        else:
            print("✗ 小时数据收集失败")
            return False
        
        # 测试3: 分钟数据收集
        print("\n3. 测试分钟数据收集...")
        cmd = f"""
        cd {CUR_DIR.parent.parent.parent} && 
        python scripts/data_collector/binance/collector.py download_data \
            --source_dir {temp_dir}/minute \
            --start 2024-12-01 \
            --end 2024-12-01 \
            --interval 1m \
            --limit_nums 2 \
            --delay 2
        """
        
        result = os.system(cmd)
        if result == 0:
            print("✓ 分钟数据收集成功")
            
            # 检查文件
            minute_files = list(Path(temp_dir).joinpath("minute").glob("*.csv"))
            print(f"  生成了 {len(minute_files)} 个文件")
            
            if minute_files:
                df = pd.read_csv(minute_files[0])
                print(f"  数据形状: {df.shape}")
                print(f"  时间范围: {df['date'].min()} 到 {df['date'].max()}")
        else:
            print("✗ 分钟数据收集失败")
            return False
        
        # 测试4: 数据标准化
        print("\n4. 测试数据标准化...")
        for interval in ["1d", "1h", "1m"]:
            source_dir = Path(temp_dir) / interval
            normalize_dir = Path(temp_dir) / f"normalize_{interval}"
            
            if source_dir.exists() and list(source_dir.glob("*.csv")):
                cmd = f"""
                cd {CUR_DIR.parent.parent.parent} && 
                python scripts/data_collector/binance/collector.py normalize_data \
                    --source_dir {source_dir} \
                    --normalize_dir {normalize_dir} \
                    --interval {interval}
                """
                
                result = os.system(cmd)
                if result == 0:
                    print(f"✓ {interval} 数据标准化成功")
                    
                    # 检查标准化文件
                    if normalize_dir.exists():
                        files = list(normalize_dir.glob("*.csv"))
                        if files:
                            df = pd.read_csv(files[0])
                            required_cols = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'change', 'factor']
                            if all(col in df.columns for col in required_cols):
                                print(f"  ✓ 包含所有必需字段: {required_cols}")
                            else:
                                print(f"  ✗ 缺少字段: {set(required_cols) - set(df.columns)}")
                else:
                    print(f"✗ {interval} 数据标准化失败")
                    return False
        
        # 测试5: Python API使用
        print("\n5. 测试Python API...")
        try:
            from collector import BinanceCollector
            
            collector = BinanceCollector(
                save_dir=temp_dir + "/api_test",
                start="2024-12-01",
                end="2024-12-02",
                interval="1h",
                limit_nums=1,
                delay=1
            )
            
            # 获取交易对列表
            symbols = collector.get_instrument_list()
            print(f"✓ 获取到 {len(symbols)} 个交易对")
            
            if symbols:
                # 获取数据
                df = collector.get_data(
                    symbols[0], 
                    "1h", 
                    pd.Timestamp("2024-12-01"), 
                    pd.Timestamp("2024-12-02")
                )
                
                if not df.empty:
                    print(f"✓ 成功获取 {symbols[0]} 数据，形状: {df.shape}")
                else:
                    print(f"✗ 未获取到 {symbols[0]} 数据")
                    return False
            else:
                print("✗ 未获取到交易对列表")
                return False
                
        except Exception as e:
            print(f"✗ Python API测试失败: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        return False
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_data_quality():
    """测试数据质量"""
    print("\n" + "=" * 60)
    print("数据质量验证")
    print("=" * 60)
    
    try:
        from pbinance import Binance
        
        binance = Binance()
        
        # 测试主流币种的数据质量
        test_coins = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        start_time = int(pd.Timestamp("2024-12-01").timestamp() * 1000)
        end_time = int(pd.Timestamp("2024-12-02").timestamp() * 1000)
        
        for coin in test_coins:
            print(f"\n验证 {coin} 数据质量...")
            
            result = binance.spot.market.get_klines(
                symbol=coin,
                interval="1h",
                startTime=start_time,
                endTime=end_time
            )
            
            if result["code"] == 200 and result["data"]:
                klines = result["data"]
                
                # 解析数据
                data = []
                for kline in klines:
                    data.append({
                        'timestamp': pd.to_datetime(kline[0], unit='ms'),
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                
                df = pd.DataFrame(data)
                
                # 数据质量检查
                checks = {
                    "数据完整性": df.isnull().sum().sum() == 0,
                    "价格逻辑性": (df['high'] >= df['low']).all() and (df['high'] >= df['open']).all() and (df['high'] >= df['close']).all(),
                    "成交量逻辑性": (df['volume'] >= 0).all(),
                    "时间连续性": df['timestamp'].is_monotonic_increasing
                }
                
                print(f"  ✓ 数据条数: {len(df)}")
                for check_name, result in checks.items():
                    status = "✓" if result else "✗"
                    print(f"  {status} {check_name}")
                
                if all(checks.values()):
                    print(f"  ✓ {coin} 数据质量良好")
                else:
                    print(f"  ✗ {coin} 数据质量有问题")
                    return False
            else:
                print(f"  ✗ {coin} 数据获取失败")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ 数据质量验证失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始最终验收测试...")
    
    # 测试基本功能
    basic_success = test_basic_functionality()
    
    # 测试数据质量
    quality_success = test_data_quality()
    
    print("\n" + "=" * 60)
    print("验收测试结果")
    print("=" * 60)
    
    if basic_success and quality_success:
        print("🎉 验收测试通过！")
        print("✓ 所有核心功能正常")
        print("✓ 数据质量良好")
        print("✓ 支持多种时间间隔")
        print("✓ 支持主流数字货币")
        print("✓ CLI和Python API都可用")
        print("\nBinance数据收集器已准备就绪！")
    else:
        print("❌ 验收测试失败！")
        if not basic_success:
            print("✗ 基本功能测试失败")
        if not quality_success:
            print("✗ 数据质量验证失败")
    
    return basic_success and quality_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
