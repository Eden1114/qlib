#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta

# 添加路径以导入collector模块
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR))

from collector import Run, LongportCollectorUS1d, LongportNormalizeUS1d

def download_example():
    """下载数据示例"""
    print("=== 开始下载数据示例 ===")
    
    # 创建数据目录
    source_dir = Path.home() / ".qlib" / "stock_data" / "source" / "longport_us_example"
    source_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置下载参数
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)  # 下载最近30天的数据
    
    # 初始化运行器并下载数据
    runner = Run(
        source_dir=source_dir,
        interval="1d",
        region="US",
        max_workers=1
    )
    
    # 下载特定股票数据，而不是全部股票
    symbols = ["AAPL.US", "MSFT.US", "GOOGL.US", "AMZN.US", "TSLA.US"]
    
    # 创建一个自定义的收集器实例
    collector = LongportCollectorUS1d(
        save_dir=source_dir,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        interval="1d",
        max_workers=1,
    )
    
    # 覆盖默认的股票列表
    collector.instrument_list = symbols
    
    # 收集数据
    collector.collector_data()
    
    print(f"数据已下载到: {source_dir}")
    return source_dir

def normalize_example(source_dir):
    """标准化数据示例"""
    print("=== 开始标准化数据示例 ===")
    
    # 创建标准化数据目录
    normalize_dir = Path.home() / ".qlib" / "stock_data" / "normalize" / "longport_us_example"
    normalize_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化运行器并标准化数据
    runner = Run(
        source_dir=source_dir,
        normalize_dir=normalize_dir,
        interval="1d",
        region="US",
        max_workers=1
    )
    
    # 标准化数据
    runner.normalize_data()
    
    print(f"标准化数据已保存到: {normalize_dir}")
    return normalize_dir

def visualize_data(source_dir, normalize_dir):
    """可视化原始数据和标准化数据"""
    print("=== 开始可视化数据示例 ===")
    
    # 选择一个股票进行可视化
    symbol = "AAPL.US"
    symbol_file = f"{symbol.split('.')[0]}.csv"
    
    # 读取原始数据
    source_file = source_dir / symbol_file
    if source_file.exists():
        source_df = pd.read_csv(source_file)
        print(f"原始数据示例 ({symbol}):")
        print(source_df.head())
        
        # 绘制原始数据
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.plot(pd.to_datetime(source_df['date']), source_df['close'], label='Close Price')
        plt.title(f"{symbol} 原始收盘价")
        plt.xlabel('日期')
        plt.ylabel('价格')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.legend()
    
    # 读取标准化数据
    normalize_file = normalize_dir / symbol_file
    if normalize_file.exists():
        normalize_df = pd.read_csv(normalize_file)
        print(f"\n标准化数据示例 ({symbol}):")
        print(normalize_df.head())
        
        # 绘制标准化数据
        plt.subplot(1, 2, 2)
        plt.plot(pd.to_datetime(normalize_df['date']), normalize_df['close'], label='Close Price')
        plt.plot(pd.to_datetime(normalize_df['date']), normalize_df['change'], label='Price Change')
        plt.title(f"{symbol} 标准化数据")
        plt.xlabel('日期')
        plt.ylabel('价格/变化率')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(normalize_dir.parent / "longport_data_visualization.png")
        print(f"可视化图表已保存到: {normalize_dir.parent / 'longport_data_visualization.png'}")
        plt.show()

def main():
    """主函数"""
    # 下载数据
    source_dir = download_example()
    
    # 标准化数据
    normalize_dir = normalize_example(source_dir)
    
    # 可视化数据
    visualize_data(source_dir, normalize_dir)
    
    print("\n=== 示例运行完成 ===")
    print("您可以使用以下命令将标准化数据转换为QLib格式:")
    print(f"python scripts/dump_bin.py dump_all --csv_path {normalize_dir} --qlib_dir ~/.qlib/qlib_data/longport_us_example --freq day --date_field_name date --symbol_field_name symbol")

if __name__ == "__main__":
    main() 