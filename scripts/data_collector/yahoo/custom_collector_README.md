# 自定义Yahoo数据收集器

这个自定义收集器允许您从指定的股票列表文件中读取股票代码，并只收集这些特定股票的数据，而不是收集所有美股股票的数据。

## 特性

- 支持从文件中读取自定义股票列表
- 支持日线数据（1d）和分钟线数据（1min）
- 完全兼容qlib的数据格式
- 大幅提高数据收集效率（只收集需要的股票）

## 使用方法

### 1. 创建股票列表文件

创建一个股票列表文件（例如`stock_list.txt`），每行一个股票代码，例如：

```
SOXL.US
TSLA.US
MSTR.US
AAPL.US
NVDA.US
```

### 2. 下载数据

```bash
# 下载日线数据
python custom_yahoo_collector.py download_data --source_dir ~/.qlib/stock_data/source --stock_list_path stock_list.txt --start 2020-01-01 --end 2023-01-01

# 下载分钟线数据（注意：Yahoo Finance分钟线数据只有最近几天的数据）
python custom_yahoo_collector.py download_data --source_dir ~/.qlib/stock_data/source --stock_list_path stock_list.txt --interval 1min --start 2025-07-07 --end 2025-07-11
```

### 3. 标准化数据

```bash
# 标准化日线数据
python custom_yahoo_collector.py normalize_data --source_dir ~/.qlib/stock_data/source --normalize_dir ~/.qlib/stock_data/normalize

# 标准化分钟线数据（需要提供1d数据目录）
python custom_yahoo_collector.py normalize_data --source_dir ~/.qlib/stock_data/source --normalize_dir ~/.qlib/stock_data/normalize --interval 1min --qlib_data_1d_dir ~/.qlib/qlib_data/us_data
```

### 4. 转换为qlib格式

```bash
# 转换日线数据
python -m scripts.dump_bin --csv_path ~/.qlib/stock_data/normalize --qlib_dir ~/.qlib/qlib_data/custom_us_data --include_fields open,close,high,low,volume,change,adjclose

# 转换分钟线数据
python -m scripts.dump_bin --csv_path ~/.qlib/stock_data/normalize --qlib_dir ~/.qlib/qlib_data/custom_us_data_1min --include_fields open,close,high,low,volume,change,adjclose --freq 1min
```

### 5. 使用数据

```python
import qlib
from qlib.data import D

# 初始化qlib（日线数据）
qlib.init(provider_uri="~/.qlib/qlib_data/custom_us_data")

# 使用数据
df = D.features(["SOXL", "TSLA", "MSTR"], ["$close", "$volume"], start_time="2020-01-01", end_time="2023-01-01")
print(df)

# 获取单个股票数据
aapl_data = D.features(["AAPL"], ["$open", "$high", "$low", "$close", "$volume"], start_time="2020-01-01", end_time="2023-01-01")
print(aapl_data)
```

## 参数说明

- `--source_dir`: 原始数据保存目录
- `--normalize_dir`: 标准化数据保存目录
- `--stock_list_path`: 股票列表文件路径
- `--start`: 开始日期，格式为YYYY-MM-DD
- `--end`: 结束日期，格式为YYYY-MM-DD
- `--max_workers`: 并行工作进程数，默认为1
- `--interval`: 数据频率，可选值为"1d"（日线）或"1min"（分钟线），默认为"1d"
- `--region`: 地区，默认为"US"

## 完整示例

以下是一个完整的使用示例：

```bash
# 1. 创建股票列表文件
cat > my_stocks.txt << EOF
AAPL.US
TSLA.US
NVDA.US
MSFT.US
GOOGL.US
EOF

# 2. 下载数据
python custom_yahoo_collector.py download_data \
    --source_dir ~/.qlib/stock_data/source \
    --stock_list_path my_stocks.txt \
    --start 2020-01-01 \
    --end 2023-01-01 \
    --delay 0.5

# 3. 标准化数据
python custom_yahoo_collector.py normalize_data \
    --source_dir ~/.qlib/stock_data/source \
    --normalize_dir ~/.qlib/stock_data/normalize

# 4. 转换为qlib格式
python -m scripts.dump_bin \
    --csv_path ~/.qlib/stock_data/normalize \
    --qlib_dir ~/.qlib/qlib_data/my_us_data \
    --include_fields open,close,high,low,volume,change,adjclose

# 5. 使用数据
python -c "
import qlib
from qlib.data import D

qlib.init(provider_uri='~/.qlib/qlib_data/my_us_data')
df = D.features(['AAPL'], ['\$close'], start_time='2020-01-01', end_time='2023-01-01')
print(df.head())
"
```

## 参数说明

### download_data参数

- `--source_dir`: 原始数据保存目录
- `--stock_list_path`: 股票列表文件路径
- `--start`: 开始日期，格式为YYYY-MM-DD
- `--end`: 结束日期，格式为YYYY-MM-DD
- `--interval`: 数据频率，可选值为"1d"（日线）或"1min"（分钟线），默认为"1d"
- `--max_workers`: 并行工作进程数，默认为1
- `--delay`: 请求间隔时间（秒），默认为0.5
- `--max_collector_count`: 失败重试次数，默认为2

### normalize_data参数

- `--source_dir`: 原始数据目录
- `--normalize_dir`: 标准化数据保存目录
- `--interval`: 数据频率，需要与下载时保持一致
- `--qlib_data_1d_dir`: 1d数据目录（仅在处理1min数据时需要）

## 注意事项

1. **股票代码格式**: 股票列表文件中的代码格式应为"AAPL.US"，程序会自动转换为Yahoo Finance需要的格式
2. **网络访问**: 如果遇到网络问题，可能需要使用代理访问Yahoo Finance
3. **数据质量**: 数据质量依赖于Yahoo Finance，可能存在异常值或缺失值
4. **qlib使用**: 在qlib中使用时，股票代码不需要".US"后缀（如使用"AAPL"而不是"AAPL.US"）
5. **分钟线数据限制**: Yahoo Finance的分钟线数据只有最近几天的数据（通常不超过7天）
6. **请求频率**: 建议设置适当的delay参数，避免请求过于频繁被限制

## 故障排除

1. **KeyError**: 确保股票列表文件存在且格式正确
2. **网络超时**: 增加delay参数或使用代理
3. **数据缺失**: 检查股票代码是否正确，以及时间范围是否合理
4. **内存不足**: 减少max_workers参数或分批处理数据 