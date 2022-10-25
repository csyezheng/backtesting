import backtrader as bt
from backtesting.utils import read_config


class BaseStrategy(bt.Strategy):
    config = read_config()

    def __init__(self):
        self.cheating = self.cerebro.p.cheat_on_open
        self.start_date = BaseStrategy.config.get('START_DATE')
        self.end_date = BaseStrategy.config.get('END_DATE')

    @classmethod
    def run_once(cls):
        pass

    @classmethod
    def optimize(cls):
        pass

    @classmethod
    def params_list(cls):
        pass

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        dt = self.datas[0].datetime.datetime(0)
        if order.status == order.Margin:
            if order.isbuy():
                print(
                    '[%s] order was not executed, not enough cash. Price: %.2f, PNL: %.2f, Cash: %.2f' %
                    (dt, order.executed.price, order.executed.pnl, self.broker.getvalue()))

        elif order.status == order.Completed:
            if order.isbuy():
                print(
                    '[%s] BUY EXECUTED, Price: %.2f, PNL: %.2f, Cash: %.2f' %
                    (dt, order.executed.price, order.executed.pnl, self.broker.getvalue()))
            else:  # Sell
                print('[%s] SELL EXECUTED, Price: %.2f, PNL: %.2f, Cash: %.2f' %
                      (dt, order.executed.price, order.executed.pnl, self.broker.getvalue()))
        else:
            print('order status: {}'.format(order.status))

    def operate(self, from_open):
        pass

    def next(self):
        if self.cheating:
            return
        self.operate(from_open=False)

    def next_open(self):
        if not self.cheating:
            return
        self.operate(from_open=True)
