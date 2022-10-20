class DetailMetric:

    def __init__(self):
        self.symbol = None
        self.name = None
        self.strategy = None
        self.params = None
        self.total_open = None
        self.total_closed = None
        self.won_total = None
        self.lost_total = None
        self.streak_won_longest = None
        self.streak_lost_longest = None
        self.pnl_net_total = None
        self.pnl_net_average = None
        self.strike_rate = None
        self.net_profit_percentage = None
        self.annualized_return_percentage = None
        self.max_drawdown = None
        self.max_moneydown = None
        self.sqn = None
        self.sharpe_ratio = None
        self.sharpe_ratio_a = None

    def asdict(self):
        return {
            'symbol': self.symbol,
            'name': self.name,
            'strategy': self.strategy,
            'params': self.params,
            'total_open': self.total_open,
            'total_closed': self.total_closed,
            'won_total': self.won_total,
            'lost_total': self.lost_total,
            'streak_won_longest': self.streak_won_longest,
            'streak_lost_longest': self.streak_lost_longest,
            'pnl_net_total': self.pnl_net_total,
            'pnl_net_average': self.pnl_net_average,
            'strike_rate': self.strike_rate,
            'net_profit_percentage': self.net_profit_percentage,
            'annualized_return_percentage': self.annualized_return_percentage,
            'max_drawdown': self.max_drawdown,
            'max_moneydown': self.max_moneydown,
            'sqn': self.sqn,
            'sharpe_ratio': self.sharpe_ratio,
            'sharpe_ratio_a': self.sharpe_ratio_a,
        }

    def __repr__(self):
        return self.asdict().__repr__()


class SummaryMetric:

    def __init__(self):
        self.strategy = None
        self.params = None
        self.won_total = None
        self.total_closed = None
        self.strike_rate = None
        self.pnl_net_total = None
        self.net_profit_percentage = None
        self.annualized_return_percentage = None
        self.max_drawdown = None
        self.sharpe_ratio_a = None

    def asdict(self):
        return {
            'strategy': self.strategy,
            'params': self.params,
            'won_total': self.won_total,
            'total_closed': self.total_closed,
            'strike_rate': self.strike_rate,
            'pnl_net_total': self.pnl_net_total,
            'net_profit_percentage': self.net_profit_percentage,
            'annualized_return_percentage': self.annualized_return_percentage,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio_a': self.sharpe_ratio_a,
        }

    def __repr__(self):
        return self.asdict().__repr__()
