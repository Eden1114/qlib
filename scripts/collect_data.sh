#!/bin/bash

# 默认参数值
START_DATE="2020-01-01"
END_DATE="2020-12-31"
END_DATE_QLIB="2025-07-09"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --start_date)
      START_DATE="$2"
      shift 2
      ;;
    --end_date)
      END_DATE="$2"
      shift 2
      ;;
    --end_date_qlib)
      END_DATE_QLIB="$2"
      shift 2
      ;;
    *)
      echo "未知参数: $1"
      exit 1
      ;;
  esac
done

python scripts/get_data.py qlib_data \
    --target_dir ~/.qlib/qlib_data/us_data \
    --region us \
    --version v3 \
    --interval 1d

python data_collector/yahoo/collector.py download_data \
    --source_dir ~/.qlib/stock_data/source/us_data \
    --start ${START_DATE} \
    --end ${END_DATE} \
    --delay 1 \
    --interval 1d \
    --region US

python data_collector/yahoo/collector.py normalize_data \
    --source_dir ~/.qlib/stock_data/source/us_data \
    --normalize_dir ~/.qlib/stock_data/source/us_data_nor \
    --max_workers 16 \
    --region US \
    --qlib_data_1d_dir ~/.qlib/qlib_data/qlib/us_data \
    --interval 1d \
    --end_date ${END_DATE_QLIB}