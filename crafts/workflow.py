import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from pprint import pprint
warnings.filterwarnings('ignore')

import qlib
from qlib.data import D
from qlib.utils import flatten_dict
from qlib.utils.time import Freq
from qlib.contrib.data.handler import Alpha158, Alpha360
from qlib.contrib.model.gbdt import LGBModel
from qlib.contrib.strategy import TopkDropoutStrategy
from qlib.contrib.evaluate import risk_analysis
from qlib.backtest import backtest, executor
from qlib.workflow import R
from qlib.workflow.record_temp import SignalRecord, PortAnaRecord
from qlib.utils import init_instance_by_config

def main():
    # 初始化 qlib
    print("正在初始化 qlib...")
    qlib.init(provider_uri='~/.qlib/qlib_data/us_data')
    
    print(
        D.list_instruments(instruments=D.instruments("all"), as_list=True)
    )
    
    # 定义您的10支股票池
    stock_pool = ['AAPL', 'AMD', 'AMZN', 'GOOGL', 'META', 'MSFT', 'MSTR', 'NVDA', 'SOXL', 'TSLA']
    
    print(f"股票池: {stock_pool}")
    
    # 检查股票数据可用性
    print("\n检查股票数据可用性...")
    available_stocks = []
    for stock in stock_pool:
        try:
            data = D.features(
                instruments=[stock],
                start_time="2025-01-01",
                end_time="2025-12-31",
                freq="day",
                fields=["$close"]
            )
            if not data.empty:
                available_stocks.append(stock)
                print(f"✓ {stock}: 可用")
            else:
                print(f"✗ {stock}: 无数据")
        except Exception as e:
            print(f"✗ {stock}: 错误 - {e}")
    
    if len(available_stocks) < 5:
        print(f"警告: 只有 {len(available_stocks)} 支股票有数据，建议至少5支股票")
        if len(available_stocks) == 0:
            print("错误: 没有可用的股票数据")
            return
    
    print(f"\n使用 {len(available_stocks)} 支股票进行回测: {available_stocks}")
    
    config = {
        "market": available_stocks,
        "benchmark": available_stocks[0],  # 使用第一支股票作为基准
        "start_time": "2025-01-02",  # 调整开始时间
        "end_time": "2025-07-08",    # 调整结束时间，确保在数据范围内
        "freq": "day",
        "topk": min(5, len(available_stocks)),  # 持有股票数量
        "n_drop": 1,  # 每日调整股票数量
        "account": 1000000,  # 初始资金
    }
    
    # 选择因子集 (Alpha158 或 Alpha360)
    factor_set = "Alpha158"  # 可以改为 "Alpha360"
    print(f"\n使用因子集: {factor_set}")
    
    # 构建数据集
    print("\n构建数据集...")
    if factor_set == "Alpha158":
        data_handler = Alpha158(
            start_time=config["start_time"],
            end_time=config["end_time"],
            fit_start_time=config["start_time"],
            fit_end_time="2025-06-30",  # 训练集结束时间
            instruments=config["market"]
        )
    else:  # Alpha360
        data_handler = Alpha360(
            start_time=config["start_time"],
            end_time=config["end_time"],
            fit_start_time=config["start_time"],
            fit_end_time="2025-06-30",
            instruments=config["market"]
        )
    
    # 获取特征数据
    features = data_handler.fetch()
    print(f"特征数据形状: {features.shape}")
    print(f"特征列数: {len(features.columns)}")
    print(f"特征数据索引:\n{features.index}")
    print(f"特征数据前5行:\n{features.head()}")
    
    # 创建标签 (未来收益率)
    print("\n创建标签...")
    label_data = D.features(
        instruments=config["market"],
        start_time=config["start_time"],
        end_time=config["end_time"],
        freq=config["freq"],
        fields=["Ref($close, -2)/Ref($close, -1) - 1"]  # 未来2日收益率
    )
    
    print(f"标签数据形状: {label_data.shape}")
    print(f"标签数据索引:\n{label_data.index}")
    print(f"标签数据前5行:\n{label_data.head()}")
    
    # 检查索引匹配情况
    print(f"\n特征数据索引类型: {type(features.index)}")
    print(f"标签数据索引类型: {type(label_data.index)}")
    print(f"特征数据索引级别数: {features.index.nlevels}")
    print(f"标签数据索引级别数: {label_data.index.nlevels}")
    
    # 检查时间范围
    if features.index.nlevels >= 2:
        feature_dates = features.index.get_level_values(0).unique()
        print(f"特征数据日期范围: {feature_dates.min()} 到 {feature_dates.max()}")
    
    if label_data.index.nlevels >= 2:
        label_dates = label_data.index.get_level_values(0).unique()
        print(f"标签数据日期范围: {label_dates.min()} 到 {label_dates.max()}")
    
    # 修复索引顺序问题
    print("\n修复索引顺序...")
    # 将标签数据的索引顺序调整为与特征数据一致 (datetime, instrument)
    label_data = label_data.swaplevel().sort_index()
    print(f"调整后标签数据索引:\n{label_data.index[:10]}")
    
    # 现在可以直接合并了
    print("\n合并数据...")
    dataset = features.join(label_data, how="inner")
    print(f"合并后形状: {dataset.shape}")
    
    # 检查NaN值情况
    print(f"\n数据质量检查:")
    print(f"总行数: {len(dataset)}")
    print(f"总列数: {len(dataset.columns)}")
    print(f"每列NaN数量:")
    nan_counts = dataset.isnull().sum()
    print(nan_counts[nan_counts > 0].head(10))  # 显示前10个有NaN的列
    
    print(f"\n每行NaN数量:")
    row_nan_counts = dataset.isnull().sum(axis=1)
    print(f"完全无NaN的行数: {(row_nan_counts == 0).sum()}")
    print(f"有NaN的行数: {(row_nan_counts > 0).sum()}")
    print(f"平均每行NaN数量: {row_nan_counts.mean():.2f}")
    
    # 尝试不同的NaN处理策略
    print(f"\n尝试不同的NaN处理策略...")
    
    # 策略1: 只删除完全为NaN的行
    dataset_strategy1 = dataset.dropna(how='all')
    print(f"策略1 - 删除完全NaN行后形状: {dataset_strategy1.shape}")
    
    # 策略2: 删除任何包含NaN的行
    dataset_strategy2 = dataset.dropna()
    print(f"策略2 - 删除任何NaN行后形状: {dataset_strategy2.shape}")
    
    # 策略3: 用前值填充
    dataset_strategy3 = dataset.fillna(method='ffill').dropna()
    print(f"策略3 - 前值填充后形状: {dataset_strategy3.shape}")
    
    # 策略4: 用均值填充
    dataset_strategy4 = dataset.fillna(dataset.mean()).dropna()
    print(f"策略4 - 均值填充后形状: {dataset_strategy4.shape}")
    
    # 选择最佳策略
    if not dataset_strategy2.empty:
        dataset = dataset_strategy2
        print(f"使用策略2: 删除任何NaN行")
    elif not dataset_strategy3.empty:
        dataset = dataset_strategy3
        print(f"使用策略3: 前值填充")
    elif not dataset_strategy4.empty:
        dataset = dataset_strategy4
        print(f"使用策略4: 均值填充")
    else:
        dataset = dataset_strategy1
        print(f"使用策略1: 只删除完全NaN行")
    
    print(f"最终数据集形状: {dataset.shape}")
    
    if dataset.empty:
        print("错误: 数据集为空，请检查数据时间范围或股票代码")
        return None, None
    
    # 分割训练和测试集
    train_end = "2025-06-30"
    train_data = dataset[dataset.index.get_level_values(0) <= train_end]
    test_data = dataset[dataset.index.get_level_values(0) > train_end]
    
    print(f"训练集大小: {train_data.shape}")
    print(f"测试集大小: {test_data.shape}")
    
    if train_data.empty or test_data.empty:
        print("错误: 训练集或测试集为空，请调整时间分割点")
        return None, None
    
    # 准备训练数据
    feature_cols = [col for col in dataset.columns if col != "Ref($close, -2)/Ref($close, -1) - 1"]
    X_train = train_data[feature_cols]
    y_train = train_data["Ref($close, -2)/Ref($close, -1) - 1"]
    X_test = test_data[feature_cols]
    y_test = test_data["Ref($close, -2)/Ref($close, -1) - 1"]
    
    print(f"训练特征形状: {X_train.shape}")
    print(f"训练标签形状: {y_train.shape}")
    
    # 使用sklearn的LightGBM进行训练
    print("\n训练LightGBM模型...")
    try:
        from lightgbm import LGBMRegressor
        
        # 创建LightGBM模型
        lgb_model = LGBMRegressor(
            objective='regression',
            colsample_bytree=0.8879,
            learning_rate=0.0421,
            subsample=0.8789,
            reg_alpha=205.6999,
            reg_lambda=580.9768,
            max_depth=8,
            num_leaves=210,
            n_jobs=20,
            random_state=42
        )
        
        # 训练模型
        lgb_model.fit(X_train, y_train)
        
        # 生成预测
        print("生成预测...")
        pred_train = lgb_model.predict(X_train)
        pred_test = lgb_model.predict(X_test)
        
        # 创建预测分数DataFrame
        pred_scores = pd.concat([
            pd.Series(pred_train, index=train_data.index, name="score"),
            pd.Series(pred_test, index=test_data.index, name="score")
        ]).sort_index()
        
    except ImportError:
        print("LightGBM未安装，使用简化的线性回归模型...")
        from sklearn.linear_model import LinearRegression
        
        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        
        pred_train = lr_model.predict(X_train)
        pred_test = lr_model.predict(X_test)
        
        pred_scores = pd.concat([
            pd.Series(pred_train, index=train_data.index, name="score"),
            pd.Series(pred_test, index=test_data.index, name="score")
        ]).sort_index()
    
    print(f"预测分数形状: {pred_scores.shape}")
    
    # 配置回测策略
    print("\n配置回测策略...")
    strategy_config = {
        "topk": config["topk"],
        "n_drop": config["n_drop"],
        "signal": pred_scores,
    }
    
    executor_config = {
        "time_per_step": "day",
        "generate_portfolio_metrics": True,
    }
    
    backtest_config = {
        "start_time": config["start_time"],
        "end_time": config["end_time"],
        "account": config["account"],
        "benchmark": config["benchmark"],
        "exchange_kwargs": {
            "freq": config["freq"],
            "limit_threshold": 0.095,
            "deal_price": "close",
            "open_cost": 0.0005,
            "close_cost": 0.0015,
            "min_cost": 5,
        },
    }
    
    # 执行回测
    print("执行回测...")
    strategy_obj = TopkDropoutStrategy(**strategy_config)
    executor_obj = executor.SimulatorExecutor(**executor_config)
    
    portfolio_metric_dict, indicator_dict = backtest(
        executor=executor_obj, 
        strategy=strategy_obj, 
        **backtest_config
    )
    
    # 分析结果
    print("\n=== 回测结果分析 ===")
    analysis_freq = "1day"
    report_normal, positions_normal = portfolio_metric_dict.get(analysis_freq)
    
    # 计算超额收益
    analysis = dict()
    analysis["excess_return_without_cost"] = risk_analysis(
        report_normal["return"] - report_normal["bench"], freq=analysis_freq
    )
    analysis["excess_return_with_cost"] = risk_analysis(
        report_normal["return"] - report_normal["bench"] - report_normal["cost"], 
        freq=analysis_freq
    )
    
    analysis_df = pd.concat(analysis)
    
    # 打印结果
    print(f"\n基准收益分析 ({analysis_freq}):")
    pprint(risk_analysis(report_normal["bench"], freq=analysis_freq))
    
    print(f"\n超额收益分析 (不含成本) ({analysis_freq}):")
    pprint(analysis["excess_return_without_cost"])
    
    print(f"\n超额收益分析 (含成本) ({analysis_freq}):")
    pprint(analysis["excess_return_with_cost"])
    
    # 计算IC指标
    print("\n=== IC指标分析 ===")
    ic_analysis = {}
    for date in pred_scores.index.get_level_values(0).unique():
        if date in y_test.index.get_level_values(0):
            pred_scores_date = pred_scores.loc[date]
            y_test_date = y_test.loc[date]
            common_stocks = pred_scores_date.index.intersection(y_test_date.index)
            if len(common_stocks) > 0:
                ic = pred_scores_date[common_stocks].corr(y_test_date[common_stocks])
                ic_analysis[date] = ic
    
    if ic_analysis:
        ic_series = pd.Series(ic_analysis)
        print(f"平均IC: {ic_series.mean():.4f}")
        print(f"IC标准差: {ic_series.std():.4f}")
        print(f"ICIR: {ic_series.mean() / ic_series.std():.4f}")
    
    print("\n=== 回测完成 ===")
    return analysis_df, portfolio_metric_dict

if __name__ == "__main__":
    main()
