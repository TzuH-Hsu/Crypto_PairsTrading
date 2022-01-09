from arch.typing import DateLike
from numpy.lib.function_base import append
import pandas as pd
import numpy as np
from itertools import combinations
from arch.univariate import *

def log_return(prices_df:pd.DataFrame) -> pd.DataFrame:
    rtn_df = pd.DataFrame()
    for crypto in prices_df.columns:
        rtn_df[f'{crypto}'] = np.log(prices_df.loc[:,crypto] / prices_df.loc[:,crypto].shift(1))

    return rtn_df

def return_spreads(return_df:pd.DataFrame) -> pd.DataFrame:
    dfs = []
    pair_list=[]
    for pair in combinations(return_df.columns, 2):
        spread_tmp = return_df.loc[:, pair[0]] - return_df.loc[:, pair[1]]
        dfs.append(spread_tmp)
        pair_list.append(str(pair))
    return_spreads_df = pd.concat(dfs, axis='columns', keys=pair_list)

    return return_spreads_df

class ForecastModel:
    def __init__(self, return_spreads_df:pd.DataFrame) -> None:
        self.rtn_df = return_spreads_df
        self.pair_spread = []
        for pair in self.rtn_df.columns:
            self.pair_spread.append(self.rtn_df.loc[:, pair])
    
    def modelspec(self, spread:pd.Series, vol:GARCH|EGARCH, dist:Normal|StudentsT|SkewStudent):
        self.am = ARX(spread, lags=1)
        self.am.volatility = vol
        self.am.distribution = dist
    
    def rollingForecasting(self, window:int, date_start:DateLike, VaR_alpha:list[float,float]) -> pd.DataFrame:
        forecast_df = pd.DataFrame()
        for i in []:
            res = self.am.fit(first_obs=i, last_obs=i, disp='off')
            forecast = res.forecast(reindex=False)
            cond_mean = forecast.mean
            cond_var = forecast.variance
            
            q = self.am.distribution.ppf(VaR_alpha, res.params[-2:])
            VaR = -cond_mean.values - np.sqrt(cond_var).values * q[None, :]
            
            tmp = {'datetime':'', 'cond_mean':cond_mean, 'cond_var':cond_var, f'VaR-{VaR_alpha[0]*100}%':VaR[0], f'VaR-{VaR_alpha[1]*100}%':VaR[1]}
            forecast_df.append(tmp)

        return forecast_df.set_index('datetime')
