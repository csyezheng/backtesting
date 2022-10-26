from datetime import date
from backtesting.strategy.base import BaseStrategy
from backtesting.indicators.zigzag import ZigZag


class ZigZagStrategy(BaseStrategy):
    params = (
        ('dev_threshold', 5),
        ('depth', 10),
        ('mode', 'strict uptrend and downtrend'),
    )

    def __init__(self):
        super(ZigZagStrategy, self).__init__()
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.zigzag = ZigZag(dev_threshold=self.params.dev_threshold, depth=self.params.depth)
        # self.crossover = bt.ind.CrossOver(self.zigzag.trough, self.data.close)

    @classmethod
    def run_once(cls):
        return True

    @classmethod
    def optimize(cls):
        return cls.config['ZIGZAG STRATEGY PARAMETERS']['OPTIMIZATION']

    def log(self, txt, dt=None):
        """
        Logging function for this strategy
        """
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    @classmethod
    def params_list(cls):
        dev_threshold = cls.config['ZIGZAG STRATEGY PARAMETERS']['DEV THRESHOLD']
        depth = cls.config['ZIGZAG STRATEGY PARAMETERS']['DEPTH']
        # return {'dev_threshold': dev_threshold, 'depth': depth}
        mode = cls.config['ZIGZAG STRATEGY PARAMETERS']['MODE']
        return {'dev_threshold': dev_threshold, 'depth': depth, 'mode': mode}

    def operate(self, from_open):
        close_price = self.data.close[0]
        previous_peak = self.zigzag.previous_peak[0]
        peak = self.zigzag.peak[0]
        previous_trough = self.zigzag.previous_trough[0]
        trough = self.zigzag.trough[0]

        if not previous_peak or not peak or not previous_trough or not trough:
            return

        if self.params.mode == 'strict uptrend and downtrend':
            uptrend = previous_peak < peak and previous_trough < trough
            downtrend = previous_peak > peak and previous_trough > trough
        elif self.params.mode == 'strict uptrend':
            uptrend = previous_peak < peak and previous_trough < trough
            downtrend = not (uptrend)
        elif self.params.mode == 'not downtrend':
            downtrend = previous_peak > peak and previous_trough > trough
            uptrend = not (downtrend)
        elif self.params.mode == 'strict price with previous trough and trough':
            uptrend = close_price > previous_trough and close_price > trough
            downtrend = close_price < previous_trough and close_price < trough
        elif self.params.mode == 'above previous swing low and swing low':
            uptrend = close_price > previous_trough and close_price > trough
            downtrend = not (uptrend)
        elif self.params.mode == 'above previous swing low':
            uptrend = close_price > previous_trough
            downtrend = close_price < previous_trough
        elif self.params.mode == 'above swing low':
            uptrend = close_price > trough
            downtrend = close_price < trough

        if self.start_date <= self.data.datetime.date() <= self.end_date:
            if not self.position:
                if uptrend > 0:
                    print(' {} submit Buy, from open {}, close {}'.format(
                        self.data.datetime.date(),
                        from_open, self.data.close[0])
                    )
                    order = self.buy()
            elif downtrend:
                self.close()
        if self.data.datetime.date() > self.end_date and self.position:
            order = self.close()
