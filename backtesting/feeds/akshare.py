import os
from datetime import datetime
import pandas as pd
import backtrader as bt
import akshare as ak


class AkshareData(bt.feed.DataBase):
    """
    AkshareData base on akshare to fetch history data
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.iter = None
        self.data = None

    def start(self):
        if self.data is None:
            df = ak.stock_zh_a_hist(symbol=self.p.dataname, adjust="qfq").iloc[:, :6]
            df.columns = [
                'trade_date',
                'open',
                'close',
                'high',
                'low',
                'volume',
            ]
            df.index = pd.to_datetime(df['trade_date'])
            self.data = df
            assert (self.data is not None)
        # set the iterator anyway
        self.iter = self.data.sort_index(ascending=False).iterrows()

    def stop(self):
        pass

    def _load(self):
        if self.iter is None:
            # if no data ... no parsing
            return False
        # try to get 1 row of data from iterator
        try:
            row = next(self.iter)
        except StopIteration:
            # end of the list
            return False
        # fill the lines
        self.lines.datetime[0] = self.date2num(datetime.strptime(row[1]['trade_date'], '%Y-%m-%d'))
        self.lines.open[0] = row[1]['open']
        self.lines.high[0] = row[1]['high']
        self.lines.low[0] = row[1]['low']
        self.lines.close[0] = row[1]['close']
        self.lines.volume[0] = row[1]['volume']
        self.lines.openinterest[0] = -1
        # Say success
        return True


def load_data_from_akshare(symbol):
    data_dir = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    file_path = os.path.join(data_dir, symbol + '.csv')
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = ak.stock_zh_a_hist(symbol=symbol, adjust="qfq").iloc[:, :6]
        df.columns = [
            'date',
            'open',
            'close',
            'high',
            'low',
            'volume',
        ]
        df.to_csv(file_path, index=False)
    df.index = pd.to_datetime(df['date'])
    data = bt.feeds.PandasData(dataname=df)
    return data
