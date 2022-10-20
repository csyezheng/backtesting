import backtrader as bt


class AllInSizerRoundLot(bt.Sizer):
    params = (
        ('a_round_lot', 100),
    )

    def __init__(self, cheat_on_open=False):
        super(AllInSizerRoundLot, self).__init__()
        self.cheat_on_open = cheat_on_open

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if not position:
            price = data.open[0] if self.cheat_on_open else data.open[1]
            size = int(cash // price // self.params.a_round_lot * self.params.a_round_lot)
            while size > 0:
                order_value = size * price
                commission = comminfo.getcommission(size, price)
                if order_value + commission >= cash:
                    size -= self.params.a_round_lot
                else:
                    break
        else:
            size = position.size

        return size


class AllInSizerInt(AllInSizerRoundLot):
    params = (
        ('a_round_lot', 1),
    )
