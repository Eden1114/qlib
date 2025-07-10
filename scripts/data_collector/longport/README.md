# Longport 数据收集器

这个数据收集器使用 [Longport API](https://open.longportapp.com/) 来获取股票数据，并将其转换为 QLib 可用的格式。

## 安装依赖

首先需要安装 Longport API：

```bash
pip install longport
pip install python-dotenv
```

## 环境配置

在使用数据收集器前，需要创建一个 `.env` 文件，包含以下内容：

```
LONGPORT_APP_KEY=你的APP_KEY
LONGPORT_APP_SECRET=你的APP_SECRET
LONGPORT_ACCESS_TOKEN=你的ACCESS_TOKEN
LONGPORT_DEBUG_ACCESS_TOKEN=你的调试ACCESS_TOKEN（可选）
LONGPORT_DEBUG=False  # 设置为True使用调试模式
```

可以从 Longport 开发者平台获取这些凭证。

## 使用方法

### 下载数据

```bash
# 下载美股日线数据
python collector.py download_data --source_dir ~/.qlib/stock_data/source/us_data --region US --start 2022-01-01 --end 2022-12-31 --delay 0.5 --interval 1d

# 下载港股日线数据
python collector.py download_data --source_dir ~/.qlib/stock_data/source/hk_data --region HK --start 2022-01-01 --end 2022-12-31 --delay 0.5 --interval 1d

# 下载美股分钟线数据
python collector.py download_data --source_dir ~/.qlib/stock_data/source/us_data_1min --region US --start 2022-01-01 --end 2022-01-07 --delay 0.5 --interval 1min
```

### 标准化数据

```bash
# 标准化美股日线数据
python collector.py normalize_data --source_dir ~/.qlib/stock_data/source/us_data --normalize_dir ~/.qlib/stock_data/normalize/us_data --region US --interval 1d

# 标准化港股日线数据
python collector.py normalize_data --source_dir ~/.qlib/stock_data/source/hk_data --normalize_dir ~/.qlib/stock_data/normalize/hk_data --region HK --interval 1d
```

### 转换为 QLib 格式

使用 QLib 的 `dump_bin.py` 脚本将标准化的数据转换为 QLib 的二进制格式：

```bash
# 转换美股数据
python scripts/dump_bin.py dump_all --csv_path ~/.qlib/stock_data/normalize/us_data --qlib_dir ~/.qlib/qlib_data/us_data --freq day --date_field_name date --symbol_field_name symbol

# 转换港股数据
python scripts/dump_bin.py dump_all --csv_path ~/.qlib/stock_data/normalize/hk_data --qlib_dir ~/.qlib/qlib_data/hk_data --freq day --date_field_name date --symbol_field_name symbol
```

## 支持的市场和频率

- 市场：
  - US（美股）
  - HK（港股）

- 频率：
  - 1d（日线）
  - 1min（分钟线）

## 数据字段

收集的数据包含以下字段：

- date：日期
- open：开盘价
- high：最高价
- low：最低价
- close：收盘价
- volume：成交量
- turnover：成交额
- change：价格变化率（标准化后计算）

## 注意事项

1. Longport API 有请求频率限制，建议设置适当的延迟（delay）
2. 对于大量数据的下载，建议分批次进行
3. 确保 `.env` 文件中的凭证正确且有效
