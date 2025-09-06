# rm -rf ~/.qlib/stock_data/source

SOURCE_DIR=~/.qlib/stock_data/source
NORMALIZE_DIR=~/.qlib/stock_data/normalize
QLIB_DIR=~/.qlib/qlib_data/normalize

STOCK_LIST_PATH=stock_list.txt
START_DATE=2025-06-30
END_DATE=2025-08-31
DELAY=0.5
MAX_WORKERS=16
MAX_COLLECTOR_COUNT=2
INTERVAL=1d

python3 custom_yahoo_collector.py \
    download_data \
    --source_dir $SOURCE_DIR \
    --stock_list_path $STOCK_LIST_PATH \
    --start $START_DATE \
    --end $END_DATE \
    --delay $DELAY \
    --max_workers $MAX_WORKERS \
    --max_collector_count $MAX_COLLECTOR_COUNT \
    --interval $INTERVAL

python3 collector.py \
    normalize_data \
    --source_dir $SOURCE_DIR \
    --normalize_dir $NORMALIZE_DIR

python3 ../../dump_bin.py \
    dump_all \
    --csv_path $SOURCE_DIR \
    --qlib_dir $QLIB_DIR \
    --freq day \
    --exclude_fields date,symbol
