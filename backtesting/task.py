import os

import pandas as pd
import matplotlib.pyplot as plt
import backtrader as bt

from backtesting.comminfo import StampDutyCommissionScheme
from backtesting.analyzer import TradeList
from backtesting.feeds.akshare import load_data_from_akshare
from backtesting.utils import keys_exists, df_to_csv, strategy_params_repr
from backtesting.metrics import DetailMetric
from backtesting.sizer import AllInSizerInt


class Task:

    def __init__(self, config, strategy_cls):
        self.config = config
        self.start_date = self.config.get('START_DATE')
        self.end_date = self.config.get('END_DATE')
        self.data_dir = self.config.get('DATA_DIR')

        self.symbol = None
        self.name = None
        self.strategy_cls = strategy_cls
        self.strategy_name = self.strategy_cls.__name__
        self.optimization = strategy_cls.optimize()
        self.params = strategy_cls.params_list()
        self.run_once = strategy_cls.run_once()

        self.cheat_on_open = self.config.get('CHEAT_ON_OPEN')
        self.trade_history = self.config.get('TRADE_HISTORY')

        self.cerebro = bt.Cerebro()

        if self.optimization:
            self.cerebro.optstrategy(self.strategy_cls, **self.params)
        else:
            self.cerebro.addstrategy(self.strategy_cls, **self.params)

        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
        self.cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns', tann=365)
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio', riskfreerate=0.0, annualize=True,
                                 timeframe=bt.TimeFrame.Days)
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='sharpe_ratio_a')
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
        self.cerebro.addanalyzer(bt.analyzers.Transactions, _name='transactions')
        self.cerebro.addanalyzer(TradeList, _name='tradelist')

        start_cash = self.config.get('START_CASH', 1000000)
        self.cerebro.broker.setcash(start_cash)

        # order_size = self.config.get('ORDER_SIZE', 100)
        stamp_duty = self.config.get('STAMP_DUTY', 0.001)
        buy_commission_rate = self.config.get('BUY_COMMISSION_RATE', 0.0005)
        sell_commission_rate = self.config.get('SELL_COMMISSION_RATE', 0.0015)
        minimum_commission = self.config.get('MINIMUM_COMMISSION', 5)
        comminfo = StampDutyCommissionScheme(buy_commission_rate, sell_commission_rate, minimum_commission, stamp_duty)
        self.cerebro.broker.addcommissioninfo(comminfo)

        # Configure the Cheat-On-Open method to buy the close on order bar
        self.cerebro.broker.set_coo(True)

        # self.cerebro.addsizer(AllInSizerRoundLot, cheat_on_open=self.cheat_on_open)
        self.cerebro.addsizer(AllInSizerInt, cheat_on_open=self.cheat_on_open)

        self.portfolio_startvalue = self.cerebro.broker.getvalue()

    def performance(self, strategy):

        metrics = DetailMetric()
        metrics.symbol = self.symbol
        metrics.name = self.name
        metrics.strategy = self.strategy_name
        metrics.params = strategy_params_repr(strategy)

        analyzers = strategy.analyzers
        if hasattr(analyzers, 'trade_analyzer'):
            ta = strategy.analyzers.trade_analyzer.get_analysis()

            metrics.total_open = ta.total.open if keys_exists(ta, 'total', 'open') else None
            metrics.total_closed = ta.total.closed if keys_exists(ta, 'total', 'closed') else None
            metrics.won_total = ta.won.total if keys_exists(ta, 'won', 'total') else None
            metrics.lost_total = ta.lost.total if keys_exists(ta, 'lost', 'total') else None

            metrics.streak_won_longest = ta.streak.won.longest if keys_exists(ta, 'streak', 'won',
                                                                              'longest') else None
            metrics.streak_lost_longest = ta.streak.lost.longest if keys_exists(ta, 'streak', 'lost',
                                                                                'longest') else None

            metrics.pnl_net_total = ta.pnl.net.total if keys_exists(ta, 'pnl', 'net', 'total') else None
            metrics.pnl_net_average = ta.pnl.net.average if keys_exists(ta, 'pnl', 'net', 'average') else None

            metrics.strike_rate = (metrics.won_total / metrics.total_closed) * 100 \
                if metrics.won_total and metrics.total_closed else None

            metrics.net_profit_percentage = metrics.pnl_net_total / self.portfolio_startvalue if metrics.pnl_net_total else None
            days = (self.end_date - self.start_date).days
            # metrics.annualized_return_percentage = (1.0 + metrics.net_profit_percentage) ** (
            #         365 / days) - 1.0 if metrics.net_profit_percentage else None
            metrics.annualized_return_percentage = metrics.net_profit_percentage / (
                    days / 365) if metrics.net_profit_percentage else None

        if hasattr(analyzers, 'drawdown'):
            dd = strategy.analyzers.drawdown.get_analysis()
            metrics.max_drawdown = dd.max.drawdown
            metrics.max_moneydown = dd.max.moneydown

        if hasattr(analyzers, 'sqn'):
            sqn_analyzer = strategy.analyzers.sqn.get_analysis()
            metrics.sqn = sqn_analyzer.sqn

        if hasattr(analyzers, 'sharpe_ratio'):
            sharpe_analyzer = strategy.analyzers.sharpe_ratio.get_analysis()
            metrics.sharpe_ratio = sharpe_analyzer['sharperatio']

        if hasattr(analyzers, 'sharpe_ratio_a'):
            sharpe_analyzer = strategy.analyzers.sharpe_ratio_a.get_analysis()
            metrics.sharpe_ratio_a = sharpe_analyzer['sharperatio']

        if hasattr(analyzers, 'tradelist'):
            trade_list = strategy.analyzers.tradelist.get_analysis()
            df = pd.DataFrame(trade_list)
            report_dir = self.config.get('REPORT_DIR')
            trade_list_dir = os.path.join(report_dir, r'trade_list')
            prefix = ' '.join([
                metrics.strategy,
                metrics.params,
                self.symbol,
                'trade_list '
            ])
            df_to_csv(df, trade_list_dir, prefix)

        # Designate the rows
        h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
        h2 = ['Strike Rate', 'Win Streak', 'Losing Streak', 'PnL Net']
        h3 = ['DrawDown Pct', 'MoneyDown', '', '']
        r1 = [metrics.total_open, metrics.total_closed, metrics.won_total, metrics.lost_total]
        r2 = [('%.2f%%' % metrics.strike_rate) if metrics.strike_rate else '',
              metrics.streak_won_longest, metrics.streak_lost_longest, metrics.pnl_net_total]
        r3 = [('%.2f%%' % metrics.max_drawdown) if metrics.max_drawdown else '', metrics.max_moneydown,
              '', '']

        # Check which set of headers is the longest.
        header_length = max(len(h1), len(h2), len(h3))
        # Print the rows
        print_list = [h1, r1, h2, r2, h3, r3]
        row_format = "{:<15}" * (header_length + 1)
        try:
            print("Trade Analysis Results:")
            for row in print_list:
                if row:
                    print(row_format.format('', *row))
            print('[SQN:%.2f, Sharpe Ratio:%.2f, Final Portfolio:%.2f, Total PnL:%.2f]' % (
                metrics.sqn, metrics.sharpe_ratio, self.cerebro.broker.getvalue(),
                metrics.pnl_net_total))
        except Exception as e:
            pass

        if 'CHART' in self.config and self.config['CHART'] is True and not self.optimization:
            figs = self.cerebro.plot(style='candlestick')
            plt.rcParams["figure.figsize"] = [16, 9]
            chart_dir = os.path.join(self.config.get('REPORT_DIR'), 'chart')
            if not os.path.exists(chart_dir):
                os.mkdir(chart_dir)
            for fig in figs:
                fig.savefig(os.path.join(chart_dir, '{}.png'.format(metrics.strategy + ' ' + metrics.symbol)))

        return metrics

    def run(self, symbol, name):
        self.symbol = symbol
        self.name = name
        data = load_data_from_akshare(self.data_dir, symbol)
        self.cerebro.adddata(data, name=symbol)
        strategies = self.cerebro.run(cheat_on_open=self.cheat_on_open, tradehistory=self.trade_history,
                                      runonce=self.run_once)
        metrics_record = []
        if self.optimization:
            for strategy_group in strategies:
                for strategy in strategy_group:
                    metrics = self.performance(strategy)
                    metrics_record.append(metrics.asdict())
        else:
            for strategy in strategies:
                metrics = self.performance(strategy)
                metrics_record.append(metrics.asdict())
        return metrics_record
