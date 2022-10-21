import backtrader as bt
from backtesting.strategy.base import BaseStrategy


class PriceSMACrossStrategy(BaseStrategy):

    params = (
        ('period', 50),
    )

    def __init__(self):
        super(PriceSMACrossStrategy, self).__init__()
        self.period = self.params.period
        self.sma = bt.ind.SMA(period=self.period)
        self.crossover = bt.ind.CrossOver(self.data.close, self.sma)

    @classmethod
    def optimize(cls):
        return cls.config['PRICE SMA CROSS STRATEGY PARAMETERS']['OPTIMIZATION']

    @classmethod
    def params_list(cls):
        period = cls.config['PRICE SMA CROSS STRATEGY PARAMETERS']['PERIOD']
        param = range(int(period['MINIMUN']), int(period['MAXIMIUM']) + 1, int(period['STEP']))
        return {'period': param}

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
