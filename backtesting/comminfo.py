import backtrader as bt


class StampDutyCommissionScheme(bt.CommInfoBase):
    '''
    This commission scheme uses a fixed commission and stamp duty for share
    purchases. Share sales are subject only to the fixed commission.

    The scheme is intended for trading China equities on the main market.

    commtype (def: None): Supported values are CommInfoBase.COMM_PERC
        (commission to be understood as %) and CommInfoBase.COMM_FIXED
        (commission to be understood as monetary units)

    if commtype == self.COMM_PERC, the commission will be devide by 100.0，
    so the commission should be multiply 100, custom param `sell_commission_rate`
    not necessary multiply 100.
    '''

    params = (
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_PERC),
        ('percabs', True),
    )

    def __init__(self, buy_commission_rate, sell_commission_rate, minimum_commission, stamp_duty):
        super(StampDutyCommissionScheme, self).__init__()
        self.buy_commission_rate = buy_commission_rate
        self.sell_commission_rate = sell_commission_rate
        self.minimum_commission = minimum_commission
        self.stamp_duty = stamp_duty

    def _getcommission(self, size, price, pseudoexec):
        '''
        If size is greater than 0, this indicates a long / buying of shares.
        If size is less than 0, it idicates a short / selling of shares.
        '''

        if size > 0:
            return size * price * self.buy_commission_rate
        elif size < 0:
            # return - size * price * (self.p.stamp_duty + self.p.commission * self.p.mult)
            return abs(size) * price * self.sell_commission_rate
        else:
            return 0  # just in case for some reason the size is 0.
