import backtrader as bt
from backtesting.strategy.base import BaseStrategy


class SMACrossStrategy(BaseStrategy):

    def __init__(self, fast_period, slow_period):
        super(SMACrossStrategy, self).__init__()
        self.sma_fast = bt.ind.SMA(period=fast_period)
        self.sma_slow = bt.ind.SMA(period=slow_period)
        self.crossover = bt.ind.CrossOver(self.sma_fast, self.sma_slow)

    @classmethod
    def params_list(cls):
        fast_period = cls.config['SMA CROSS STRATEGY PARAMETERS']['FAST_PERIOD']
        slow_period = cls.config['SMA CROSS STRATEGY PARAMETERS']['SLOW_PERIOD']
        param1 = range(int(fast_period['MINIMUN']), int(fast_period['MAXIMIUM']) + 1, int(fast_period['STEP']))
        param2 = range(int(slow_period['MINIMUN']), int(slow_period['MAXIMIUM']) + 1, int(slow_period['STEP']))
        return [(i, v) for i in param1 for v in param2]

    def operate(self, from_open):
        if self.start_date <= self.data.datetime.date() <= self.end_date:
            if not self.position:  # not in the market
                if self.crossover > 0:  # if fast crosses slow to the upside
                    print(' {} submit Buy, from open {}, close {}'.format(
                        self.data.datetime.date(),
                        from_open, self.data.close[0])
                    )
                    order = self.buy()  # enter long
            elif self.crossover < 0:  # in the market & cross to the downside
                self.close()  # close long position
        if self.data.datetime.date() > self.end_date and self.position:
            order = self.close()  # close position
