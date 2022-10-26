import math
from collections import deque
from datetime import date
import backtrader as bt


class ZigZag(bt.Indicator):
    """
    The Zig Zag indicator is used to describe the peaks and troughs.
    Peaks and troughs are patterns that are developed by the price action experienced by all securities.
    The easiest way to determine whether or not a trendline has been broken is to witness the breakdown and then replacement of either rising or falling peaks and troughs.
    The Zig Zag indicator is used to help identify price trends and changes in price trends.
    """

    lines = ('zigzag', 'previous_peak', 'peak', 'previous_trough', 'trough')

    plotinfo = dict(subplot=False, plotlinelabels=True, plotlinevalues=True, plotvaluetags=True, )

    plotlines = dict(
        zigzag=dict(_name='zigzag', color='blue', ls='-', _skipnan=True),
        previous_peak=dict(_plotskip=True),
        peak=dict(_plotskip=True),
        previous_trough=dict(_plotskip=True),
        trough=dict(_plotskip=False, color='green', ls='--', ),
    )

    params = (
        ('dev_threshold', 5),  # Deviation (%)
        ('depth', 10),
    )

    def __init__(self):
        super(ZigZag, self).__init__()
        self.dev_threshold = self.params.dev_threshold
        self.depth = self.params.depth
        self.bar_index = 0
        # last pivot index
        self.index_last = 0
        # last pivot price
        self.price_last = 0
        self.is_high_last = True  # otherwise the last pivot is a low pivot
        self.is_replaced_last = False  # the last pivot is a replace
        self.nan = float('nan')
        init_pair = (0, self.nan)
        self.peak_deque = deque([init_pair, init_pair, init_pair], maxlen=3)
        self.trough_deque = deque([init_pair, init_pair, init_pair], maxlen=3)

    def pivots(self, length, is_high):
        try:
            src = self.data.high if is_high else self.data.low
            price = src[length] if src[length] else 0.0
            if length == 0:
                return length, price
            else:
                is_found = True
                for i in range(abs(length)):
                    if is_high and src[i] > price:
                        is_found = False
                    if not is_high and src[i] < price:
                        is_found = False
                for i in range(length + 1, 2 * length + 1):
                    if is_high and src[i] >= price:
                        is_found = False
                    if not is_high and src[i] <= price:
                        is_found = False
                if is_found and length * 2 <= self.bar_index:
                    return length, price
                else:
                    return None, None
        except Exception as e:
            # TODO
            print('The last data access out of range')
            return None, None

    def pivot_found(self, dev, is_high, index, price):
        """
        :param dev:
        :param is_high:
        :param index:
        :param price:
        :return: A pair of bool
            1. Bool: The last pivot is is high or low
            2. Bool: Create new pivot or not
            3. Bool: Replace previous pivot or not
        """
        if self.is_high_last == is_high:
            # same direction: higher high or lower low
            same_direction = price > self.price_last if self.is_high_last else price < self.price_last
            if same_direction:
                # remove previous pivot and set new pivot for higher high or lower low
                bars_arg = self.index_last - self.bar_index
                self.lines.zigzag[bars_arg] = self.nan
                self.lines.zigzag[index] = price
                self.is_replaced_last = True
                if is_high:
                    self.peak_deque.pop()
                    self.peak_deque.append((self.bar_index + index, price))
                else:
                    self.trough_deque.pop()
                    self.trough_deque.append((self.bar_index + index, price))
                return self.is_high_last, True, True
            else:
                return None, False, False
        else:
            # reverse the direction (or create the very first line)
            if abs(dev) >= self.dev_threshold:
                self.lines.zigzag[index] = price
                self.is_replaced_last = False
                if is_high:
                    self.peak_deque.append((self.bar_index + index, price))
                else:
                    self.trough_deque.append((self.bar_index + index, price))
                return is_high, True, False
            else:
                return None, False, False

    def calc_dev(self, base_price, price):
        return 100 * (price - base_price) / base_price if base_price else 100

    def next(self):
        index_high, price_high = self.pivots(math.floor(self.depth / 2), True)
        index_low, price_low = self.pivots(math.floor(self.depth / 2), False)

        if index_high and index_low and index_high == index_low:
            dev1 = self.calc_dev(self.price_last, price_high)
            is_high2, is_new2, replaced = self.pivot_found(dev1, True, index_high, price_high)
            if is_new2:
                self.index_last = self.bar_index + index_high
                self.price_last = price_high
                self.is_high_last = is_high2
            dev2 = self.calc_dev(self.price_last, price_low)
            is_high1, is_new1, replaced = self.pivot_found(dev2, False, index_low, price_low)
            if is_new1:
                self.index_last = self.bar_index + index_low
                self.price_last = price_low
                self.is_high_last = is_high1
        else:
            if index_high:
                dev1 = self.calc_dev(self.price_last, price_high)
                is_high, is_new, replaced = self.pivot_found(dev1, True, index_high, price_high)
                if is_new:
                    self.index_last = self.bar_index + index_high
                    self.price_last = price_high
                    self.is_high_last = is_high
            else:
                if index_low:
                    dev2 = self.calc_dev(self.price_last, price_low)
                    is_high, is_new, replaced = self.pivot_found(dev2, False, index_low, price_low)
                    if is_new:
                        self.index_last = self.bar_index + index_low
                        self.price_last = price_low
                        self.is_high_last = is_high
        self.set_peak_trough()
        self.bar_index += 1

    def set_peak_trough(self):
        index_high = self.peak_deque[2][0]
        index_low = self.trough_deque[2][0]
        if index_high <= self.bar_index:
            self.lines.previous_peak[0] = self.peak_deque[1][1]
            self.lines.peak[0] = self.peak_deque[2][1]
        else:
            self.lines.previous_peak[0] = self.peak_deque[0][1]
            self.lines.peak[0] = self.peak_deque[1][1]
        if index_low <= self.bar_index:
            self.lines.previous_trough[0] = self.trough_deque[1][1]
            self.lines.trough[0] = self.trough_deque[2][1]
        else:
            self.lines.previous_trough[0] = self.trough_deque[0][1]
            self.lines.trough[0] = self.trough_deque[1][1]
