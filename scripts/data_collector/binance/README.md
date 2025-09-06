# Binance 数字货币数据收集器

基于 qlib 框架的 Binance 数字货币交易数据收集器，支持获取开高收低交易量等 K 线数据。

## 功能特性

- 支持多种时间间隔：日线(1d)、小时线(1h)、4 小时线(4h)、分钟线(1m)
- 自动获取所有 USDT 交易对，优先选择主流币种
- 支持 API Key 认证（可选）
- 符合 qlib 数据格式标准
- 内置重试机制和 API 限制处理

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

### 环境变量配置（可选）

创建 `.env` 文件并配置 Binance API 信息：

```bash
# .env
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET=your_api_secret_here
```

**注意**：即使不配置 API Key，收集器也可以使用公开 API 获取基础数据。

## 使用方法

### 1. 下载数据

#### 下载日线数据

```bash
python collector.py download_data \
    --source_dir ~/.qlib/crypto_data/source \
    --start 2024-01-01 \
    --end 2024-01-31 \
    --interval 1d \
    --limit_nums 10 \
    --delay 1
```

#### 下载小时数据

```bash
python collector.py download_data \
    --source_dir ~/.qlib/crypto_data/source \
    --start 2024-01-01 \
    --end 2024-01-02 \
    --interval 1h \
    --limit_nums 5 \
    --delay 2
```

#### 下载分钟数据

```bash
python collector.py download_data \
    --source_dir ~/.qlib/crypto_data/source \
    --start 2024-01-01 \
    --end 2024-01-01 \
    --interval 1m \
    --limit_nums 3 \
    --delay 2
```

### 2. 标准化数据

```bash
python collector.py normalize_data \
    --source_dir ~/.qlib/crypto_data/source \
    --normalize_dir ~/.qlib/crypto_data/normalize \
    --interval 1d
```

## 参数说明

### download_data 参数

- `--source_dir`: 原始数据保存目录
- `--start`: 开始时间，格式：YYYY-MM-DD
- `--end`: 结束时间，格式：YYYY-MM-DD
- `--interval`: 时间间隔，支持：1d, 1h, 4h, 1m
- `--limit_nums`: 限制交易对数量（调试用）
- `--delay`: 请求间隔（秒），建议 1 秒以上避免 API 限制
- `--api_key`: Binance API Key（可选）
- `--api_secret`: Binance API Secret（可选）

## 数据格式

### 原始数据格式

- `date`: 时间戳
- `symbol`: 交易对符号（如：BTCUSDT）
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量

### 标准化数据格式

- `date`: 时间戳
- `symbol`: 交易对符号
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `change`: 涨跌幅
- `factor`: 复权因子（数字货币通常为 1.0）

## 支持的交易对

收集器会自动获取所有 USDT 交易对，包括但不限于：

- 主流币：BTCUSDT, ETHUSDT, BNBUSDT
- 山寨币：ADAUSDT, DOTUSDT, LINKUSDT, XRPUSDT
- 其他：根据 Binance 交易所实时更新

## 测试

运行测试脚本验证功能：

```bash
# 测试小时和分钟数据获取
python test_hourly_minute.py

# 测试功能总结
python test_summary.py
```

## 注意事项

1. **API 限制**：Binance API 有请求频率限制，建议设置适当的延迟时间
2. **数据量**：数字货币 7x24 交易，数据量较大，建议合理设置时间范围
3. **存储空间**：确保有足够的磁盘空间存储数据
4. **网络稳定性**：建议在网络稳定的环境下运行

## 示例用法

### 完整的数据收集流程

```bash
# 1. 下载最近一周的小时数据
python collector.py download_data \
    --source_dir ~/.qlib/crypto_data/source \
    --start 2024-12-01 \
    --end 2024-12-08 \
    --interval 1h \
    --limit_nums 10 \
    --delay 2

# 2. 标准化数据
python collector.py normalize_data \
    --source_dir ~/.qlib/crypto_data/source \
    --normalize_dir ~/.qlib/crypto_data/normalize \
    --interval 1h

# 3. 查看数据
ls ~/.qlib/crypto_data/normalize/
```

### 使用 Python API

```python
from collector import BinanceCollector
import pandas as pd

# 创建收集器
collector = BinanceCollector(
    save_dir="./data",
    start="2024-01-01",
    end="2024-01-31",
    interval="1h",
    limit_nums=5
)

# 获取交易对列表
symbols = collector.get_instrument_list()
print(f"获取到 {len(symbols)} 个交易对")

# 获取单个交易对数据
df = collector.get_data("BTCUSDT", "1h",
                       pd.Timestamp("2024-01-01"),
                       pd.Timestamp("2024-01-02"))
print(df.head())
```
