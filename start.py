#!/usr/bin/env python
# coding: utf-8

import os
import importlib
from concurrent.futures import ProcessPoolExecutor as Pool

import pandas as pd
from backtesting.task import Task
from backtesting.utils import read_config, index_stock_cons, df_to_csv

config = read_config()


def start():
    start_date = config.get('START_DATE')
    end_date = config.get('END_DATE')
    days = (end_date - start_date).days
    summary_list = []
    strategies = config.get('STRATEGIES')
    for strategy_cls_name, module in strategies.items():
        strategy_cls = getattr(importlib.import_module(module), strategy_cls_name)
        detail_report = backtest_symbols(strategy_cls)
        if detail_report is None or detail_report.empty:
            continue
        df = detail_report.groupby(by=['strategy', 'params'], axis=0).agg(
            {'won_total': 'sum', 'total_closed': 'sum', 'pnl_net_total': 'sum',
             'net_profit_percentage': 'mean', 'max_drawdown': 'max',
             'sharpe_ratio_a': 'mean'})
        df['strike_rate'] = (df['won_total'].astype(float) / df['total_closed'].astype(float)).fillna(0)
        df['annualized_return_percentage'] = df['net_profit_percentage'] / days * 365
        summary_list.append(df)
    if summary_list:
        summary_report = pd.concat(summary_list)
        summary_report.reset_index(inplace=True)
        report_dir = config.get('REPORT_DIR')
        df_to_csv(summary_report, report_dir, 'summary')


def backtest_symbols(strategy_cls):
    symbols = index_stock_cons('000300')

    workers = os.cpu_count()
    with Pool(max_workers=workers) as outer_pool:
        engine = Engine(config, strategy_cls)
        results = outer_pool.map(engine, symbols.items())

    record_list = []
    try:
        for sublist in results:
            if sublist:
                for record in sublist:
                    record_list.append(record)
    except Exception as e:
        print(e)
    if not record_list:
        return None

    df = pd.DataFrame(record_list)
    report_dir = config.get('REPORT_DIR')
    strategy_dir = os.path.join(report_dir, 'strategy')
    prefix = strategy_cls.__name__
    df_to_csv(df, strategy_dir, prefix)
    return df


class Engine(object):

    def __init__(self, conf, strategy_cls):
        self.task = Task(conf, strategy_cls)

    def __call__(self, pairs):
        metrics_record = self.task.run(pairs[0], pairs[1])
        return metrics_record


if __name__ == '__main__':
    start()
