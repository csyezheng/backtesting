#!/usr/bin/env python
# coding: utf-8

import os
import importlib
from datetime import datetime
import pandas as pd
from backtesting.task import Task
from backtesting.utils import read_config, index_stock_cons
from backtesting.metrics import SummaryMetric

config = read_config()


def backtest_strategies():
    summary_list = []
    strategies = {
        'backtesting.strategy.sma_cross': 'SMACrossStrategy',
    }
    for module, strategy_cls_name in strategies.items():
        strategy_cls = getattr(importlib.import_module(module), strategy_cls_name)
        params_list = strategy_cls.params_list()
        for params in params_list:
            detail_report = backtest_symbols(strategy_cls, *params)
            summary_metric = SummaryMetric()
            summary_metric.strategy = strategy_cls.__name__
            summary_metric.params = ', '.join([str(i) for i in params])
            summary_metric.won_total = detail_report.won_total.sum()
            summary_metric.total_closed = detail_report.total_closed.sum()
            summary_metric.strike_rate = summary_metric.won_total / summary_metric.total_closed
            summary_metric.pnl_net_total = detail_report.pnl_net_total.sum()
            summary_metric.net_profit_percentage = detail_report.net_profit_percentage.mean()
            summary_metric.annualized_return_percentage = detail_report.annualized_return_percentage.mean()
            summary_metric.max_drawdown = detail_report.max_drawdown.max()
            summary_metric.sharpe_ratio_a = detail_report.sharpe_ratio_a.mean()
            summary_list.append(summary_metric.asdict())
    summary_report = pd.DataFrame(summary_list)
    save(summary_report, 'summary')


def backtest_symbols(strategy_cls, *args):
    metrics_record = []
    symbols = index_stock_cons('000300')
    for symbol, name in symbols.items():
        task = Task(config, strategy_cls, *args)
        task.feed_data(symbol, name)
        metrics = task.run()
        metrics_record.append(metrics)
    detail_report = pd.DataFrame(metrics_record)
    save(detail_report, 'detail')
    return detail_report


def save(df, report_type):
    report_dir = os.path.join(os.getcwd(), 'report')
    if not os.path.exists(report_dir):
        os.mkdir(report_dir)
    file_path = os.path.join(report_dir, report_type + datetime.now().strftime(' %d-%H%M%S') + '.csv')
    df.to_csv(file_path, index=False)


if __name__ == '__main__':
    backtest_strategies()
