import os
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import backtrader as bt

from backtesting.comminfo import StampDutyCommissionScheme
from backtesting.analyzer import TradeList
from backtesting.feeds.akshare import load_data_from_akshare
from backtesting.utils import keys_exists
from backtesting.metrics import DetailMetric
from backtesting.sizer import AllInSizerInt

CHART_DIR = os.path.join(os.getcwd(), 'chart')


class Task:

    def __init__(self, config, strategy_cls, *args):
        self.config = config
        self.start_date = self.config.get('START_DATE')
        self.end_date = self.config.get('END_DATE')

        self.cheat_on_open = self.config.get('CHEAT_ON_OPEN')

        self.cerebro = bt.Cerebro()
        self.strategy_cls = strategy_cls

        self.cerebro.addstrategy(self.strategy_cls, *args)

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

        self.metrics = DetailMetric()
        self.metrics.strategy = self.strategy_cls.__name__
        self.metrics.params = self.strategy_cls.params_list()

    def feed_data(self, symbol, name):
        self.metrics.symbol = symbol
        self.metrics.name = name
        data = load_data_from_akshare(symbol)
        self.cerebro.adddata(data, name=symbol)

    def performance(self, strategy):
        analyzers = strategy.analyzers
        if hasattr(analyzers, 'trade_analyzer'):
            ta = strategy.analyzers.trade_analyzer.get_analysis()

            self.metrics.total_open = ta.total.open if keys_exists(ta, 'total', 'open') else None
            self.metrics.total_closed = ta.total.closed if keys_exists(ta, 'total', 'closed') else None
            self.metrics.won_total = ta.won.total if keys_exists(ta, 'won', 'total') else None
            self.metrics.lost_total = ta.lost.total if keys_exists(ta, 'lost', 'total') else None

            self.metrics.streak_won_longest = ta.streak.won.longest if keys_exists(ta, 'streak', 'won',
                                                                                   'longest') else None
            self.metrics.streak_lost_longest = ta.streak.lost.longest if keys_exists(ta, 'streak', 'lost',
                                                                                     'longest') else None

            self.metrics.pnl_net_total = ta.pnl.net.total if keys_exists(ta, 'pnl', 'net', 'total') else None
            self.metrics.pnl_net_average = ta.pnl.net.average if keys_exists(ta, 'pnl', 'net', 'average') else None

            self.metrics.strike_rate = (self.metrics.won_total / self.metrics.total_closed) * 100 \
                if self.metrics.won_total and self.metrics.total_closed else None

            self.metrics.net_profit_percentage = self.metrics.pnl_net_total / self.portfolio_startvalue if self.metrics.pnl_net_total else None
            days = (self.end_date - self.start_date).days
            # self.metrics.annualized_return_percentage = (1.0 + self.metrics.net_profit_percentage) ** (
            #         365 / days) - 1.0 if self.metrics.net_profit_percentage else None
            self.metrics.annualized_return_percentage = self.metrics.net_profit_percentage / (
                    days / 365) if self.metrics.net_profit_percentage else None

        if hasattr(analyzers, 'drawdown'):
            dd = strategy.analyzers.drawdown.get_analysis()
            self.metrics.max_drawdown = dd.max.drawdown
            self.metrics.max_moneydown = dd.max.moneydown

        if hasattr(analyzers, 'sqn'):
            sqn_analyzer = strategy.analyzers.sqn.get_analysis()
            self.metrics.sqn = sqn_analyzer.sqn

        if hasattr(analyzers, 'sharpe_ratio'):
            sharpe_analyzer = strategy.analyzers.sharpe_ratio.get_analysis()
            self.metrics.sharpe_ratio = sharpe_analyzer['sharperatio']

        if hasattr(analyzers, 'sharpe_ratio_a'):
            sharpe_analyzer = strategy.analyzers.sharpe_ratio_a.get_analysis()
            self.metrics.sharpe_ratio_a = sharpe_analyzer['sharperatio']

        if hasattr(analyzers, 'tradelist'):
            trade_list = strategy.analyzers.tradelist.get_analysis()
            df = pd.DataFrame(trade_list)
            report_dir = os.path.join(os.getcwd(), 'report/detail')
            if not os.path.exists(report_dir):
                os.mkdir(report_dir)
            file_name = ' '.join([self.metrics.strategy, self.metrics.strategy, 'trade_list ',
                                  datetime.now().strftime('%d-%H%M%S') + '.csv'])
            file_path = os.path.join(report_dir, file_name)
            df.to_csv(file_path, index=False)

        # Designate the rows
        h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
        h2 = ['Strike Rate', 'Win Streak', 'Losing Streak', 'PnL Net']
        h3 = ['DrawDown Pct', 'MoneyDown', '', '']
        r1 = [self.metrics.total_open, self.metrics.total_closed, self.metrics.won_total, self.metrics.lost_total]
        r2 = [('%.2f%%' % self.metrics.strike_rate) if self.metrics.strike_rate else '',
              self.metrics.streak_won_longest, self.metrics.streak_lost_longest, self.metrics.pnl_net_total]
        r3 = [('%.2f%%' % self.metrics.max_drawdown) if self.metrics.max_drawdown else '', self.metrics.max_moneydown,
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
                self.metrics.sqn, self.metrics.sharpe_ratio, self.cerebro.broker.getvalue(),
                self.metrics.pnl_net_total))
        except Exception as e:
            pass

        # plot
        chart = False
        if 'chart' in self.config and self.config['chart'] == 'true':
            chart = True
        if chart:
            # fig = self.cerebro.plot()
            plt.rcParams["figure.figsize"] = [16, 9]
            if not os.path.exists(CHART_DIR):
                os.mkdir(CHART_DIR)
            plt.savefig(os.path.join(CHART_DIR, '{}.png'.format(self.metrics.symbol)))

    def run(self):
        strategies = self.cerebro.run(cheat_on_open=self.cheat_on_open, tradehistory=True, runonce=False)
        strategy = strategies[0]
        self.performance(strategy)
        return self.metrics.asdict()
