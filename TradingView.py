from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

class Datafeed:
    def __init__(self) -> None:
        self.tv = TvDatafeed()
        
    def Binance_daily_close(self, symbol:str, date_start_str:str, date_end_str:str):
        
        date_start = datetime.strptime(date_start_str, '%Y/%m/%d')
        date_end   = datetime.strptime(date_end_str  , '%Y/%m/%d')
        delta = date_end - date_start
        data = self.tv.get_hist(symbol=symbol, exchange='BINANCE', interval=Interval.in_daily, n_bars=delta.days)

        return data.close
