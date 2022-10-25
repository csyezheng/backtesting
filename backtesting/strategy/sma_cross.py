import backtrader as bt
from backtesting.strategy.base import BaseStrategy


class SMACrossStrategy(BaseStrategy):

    params = (
        ('fast_period', 20),
        ('slow_period', 50),
    )

    def __init__(self):
        super(SMACrossStrategy, self).__init__()
        self.sma_fast = bt.ind.SMA(period=self.params.fast_period)
        self.sma_slow = bt.ind.SMA(period=self.params.slow_period)
        self.crossover = bt.ind.CrossOver(self.sma_fast, self.sma_slow)

    @classmethod
    def run_once(cls):
        return False

    @classmethod
    def optimize(cls):
        return cls.config['SMA CROSS STRATEGY PARAMETERS']['OPTIMIZATION']

    @classmethod
    def params_list(cls):
        fast_period = cls.config['SMA CROSS STRATEGY PARAMETERS']['FAST_PERIOD']
        slow_period = cls.config['SMA CROSS STRATEGY PARAMETERS']['SLOW_PERIOD']
        step = cls.config['SMA CROSS STRATEGY PARAMETERS']['STEP']
        if step:
            param1 = range(int(fast_period['MINIMUN']), int(fast_period['MAXIMIUM']) + 1, int(fast_period['STEP']))
            param2 = range(int(slow_period['MINIMUN']), int(slow_period['MAXIMIUM']) + 1, int(slow_period['STEP']))
            return {'fast_period': param1, 'slow_period': param2}
        else:
            return {'fast_period': fast_period, 'slow_period': slow_period}

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
