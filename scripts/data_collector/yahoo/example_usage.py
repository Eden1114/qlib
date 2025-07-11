#!/usr/bin/env python3
"""
CustomYahooDataCollector使用示例
"""

import os
import sys
from pathlib import Path

# 添加路径
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent))

from custom_yahoo_collector import CustomRun

def main():
    """主函数"""
    
    # 配置参数
    config = {
        "source_dir": "~/.qlib/stock_data/source",
        "normalize_dir": "~/.qlib/stock_data/normalize", 
        "qlib_dir": "~/.qlib/qlib_data/my_us_data",
        "stock_list_path": "my_stocks.txt",
        "start_date": "2020-01-01",
        "end_date": "2023-01-01"
    }
    
    print("=== CustomYahooDataCollector使用示例 ===\n")
    
    # 1. 创建股票列表文件
    print("1. 创建股票列表文件...")
    stocks = ["AAPL.US", "TSLA.US", "NVDA.US", "MSFT.US", "GOOGL.US"]
    
    with open(config["stock_list_path"], "w") as f:
        for stock in stocks:
            f.write(f"{stock}\n")
    
    print(f"   创建了股票列表文件: {config['stock_list_path']}")
    print(f"   包含股票: {', '.join(stocks)}")
    
    # 2. 创建CustomRun实例
    print("\n2. 初始化CustomRun...")
    custom_run = CustomRun(
        source_dir=config["source_dir"],
        normalize_dir=config["normalize_dir"],
        max_workers=1,
        interval="1d",
        region="US",
        stock_list_path=config["stock_list_path"]
    )
    
    # 3. 下载数据
    print("\n3. 下载数据...")
    print("   这可能需要几分钟时间，请耐心等待...")
    
    try:
        custom_run.download_data(
            start=config["start_date"],
            end=config["end_date"],
            delay=0.5
        )
        print("   数据下载完成！")
    except Exception as e:
        print(f"   数据下载失败: {e}")
        return
    
    # 4. 标准化数据
    print("\n4. 标准化数据...")
    try:
        custom_run.normalize_data()
        print("   数据标准化完成！")
    except Exception as e:
        print(f"   数据标准化失败: {e}")
        return
    
    # 5. 转换为qlib格式
    print("\n5. 转换为qlib格式...")
    print("   请手动运行以下命令:")
    print(f"   python -m scripts.dump_bin --csv_path {config['normalize_dir']} --qlib_dir {config['qlib_dir']} --include_fields open,close,high,low,volume,change,adjclose")
    
    # 6. 使用数据示例
    print("\n6. 使用数据示例:")
    print("   请在转换完成后运行以下Python代码:")
    print(f"""
   import qlib
   from qlib.data import D
   
   # 初始化qlib
   qlib.init(provider_uri="{config['qlib_dir']}")
   
   # 获取数据
   df = D.features(["AAPL"], ["$close"], start_time="{config['start_date']}", end_time="{config['end_date']}")
   print(df.head())
   """)
    
    print("\n=== 完成！ ===")

if __name__ == "__main__":
    main() 