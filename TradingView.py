from datetime import datetime
from pandas import Series
from tvDatafeed import TvDatafeed, Interval

class Datafeed:
    def __init__(self) -> None:
        self.tv = TvDatafeed()
        
    def daily_close(self, symbol:str, exchange:str, date_start_str:str, date_end_str:str) -> Series:
        
        date_start = datetime.strptime(date_start_str, '%Y/%m/%d')
        date_end   = datetime.strptime(date_end_str  , '%Y/%m/%d')
        delta = datetime.now() - date_start
        data_extended = self.tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_daily, n_bars=(delta.days + 90))
        data = data_extended[date_start:date_end]

        return data.close
