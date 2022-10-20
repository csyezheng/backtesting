import backtrader as bt


class TradeList(bt.Analyzer):
    """
    Records closed trades and returns dictionary containing the following
    keys/values:
      - ``ref``: reference number (from backtrader)
      - ``ticker``: data name
      - ``direction``: direction (long or short)
      - ``datein``: entry date/time
      - ``pricein``: entry price (considering multiple entries)
      - ``dateout``: exit date/time
      - ``priceout``: exit price (considering multiple exits)
      - ``chng%``: price change in %s during trade
      - ``pnl``: profit/loss
      - ``pnl%``: profit/loss in % to broker value
      - ``size``: size
      - ``value``: value
      - ``cumpnl``: cumulative profit/loss for trades shown before this trade
      - ``nbars``: average trade duration in price bars
      - ``pnl/bar``: average profit/loss per bar
      - ``mfe``: max favorable excursion in $s from entry price
      - ``mae``: max adverse excursion in $s from entry price
      - ``mfe%``: max favorable excursion in % of entry price
      - ``mae%``: max adverse excursion in % of entry price
    """

    def __init__(self):
        self.trades = []
        self.cumprofit = 0.0

    def notify_trade(self, trade):

        if trade.isclosed:
            if trade.isclosed:

                brokervalue = self.strategy.broker.getvalue()

                direction = 'short'
                if trade.history[0].event.size > 0:
                    direction = 'long'

                pricein = trade.history[len(trade.history) - 1].status.price
                priceout = trade.history[len(trade.history) - 1].event.price
                datein = bt.num2date(trade.history[0].status.dt)
                dateout = bt.num2date(trade.history[len(trade.history) - 1].status.dt)
                if trade.data._timeframe >= bt.TimeFrame.Days:
                    datein = datein.date()
                    dateout = dateout.date()

                pcntchange = 100 * priceout / pricein - 100
                pnl = trade.history[len(trade.history) - 1].status.pnlcomm
                pnlpcnt = 100 * pnl / brokervalue
                barlen = trade.history[len(trade.history) - 1].status.barlen
                pbar = pnl / barlen
                self.cumprofit += pnl

                size = value = 0.0
                for record in trade.history:
                    if abs(size) < abs(record.status.size):
                        size = record.status.size
                        value = record.status.value

                highest_in_trade = max(trade.data.high.get(ago=0, size=barlen + 1))
                lowest_in_trade = min(trade.data.low.get(ago=0, size=barlen + 1))
                hp = highest_in_trade - pricein
                lp = lowest_in_trade - pricein
                mfe0 = 0.0
                mae0 = 0.0
                mfe = 0.0
                mae = 0.0
                if direction == 'long':
                    mfe0 = hp
                    mae0 = lp
                    mfe = 100 * hp / pricein
                    mae = 100 * lp / pricein
                if direction == 'short':
                    mfe0 = -lp
                    mae0 = -hp
                    mfe = -100 * lp / pricein
                    mae = -100 * hp / pricein

                self.trades.append({
                    'ref': trade.ref,
                    'ticker': trade.data._name,
                    'direction': direction,
                    'datein': datein,
                    'pricein': pricein,
                    'dateout': dateout,
                    'priceout': priceout,
                    'chng%': round(pcntchange, 2),
                    'pnl': pnl,
                    'pnl%': round(pnlpcnt, 2),
                    'size': size, 'value': value,
                    'cumpnl': self.cumprofit,
                    'nbars': barlen,
                    'pnl/bar': round(pbar, 2),
                    'mfe': round(mfe0, 2),
                    'mae': round(mae0, 2),
                    'mfe%': round(mfe, 2),
                    'mae%': round(mae, 2)
                })

    def get_analysis(self):
        return self.trades
