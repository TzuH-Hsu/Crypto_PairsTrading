from datetime import timedelta
from itertools import combinations

import numpy as np
import pandas as pd
from arch.univariate import *


def log_return(prices_df: pd.DataFrame) -> pd.DataFrame:
    rtn_df = pd.DataFrame()
    for crypto in prices_df.columns:
        rtn_df[f'{crypto}'] = np.log(
            prices_df.loc[:, crypto] / prices_df.loc[:, crypto].shift(1))

    return rtn_df


def return_spreads(return_df: pd.DataFrame) -> pd.DataFrame:
    dfs = []
    pair_list = []
    for pair in combinations(return_df.columns, 2):
        spread_tmp = return_df.loc[:, pair[0]] - return_df.loc[:, pair[1]]
        dfs.append(spread_tmp)
        pair_list.append(str(pair))
    return_spreads_df = pd.concat(dfs, axis='columns', keys=pair_list)

    return return_spreads_df


class ForecastModel:
    def __init__(self, spread: pd.Series) -> None:
        self.spread = spread

    def modelspec(self, vol: GARCH | EGARCH, dist: Normal | StudentsT | SkewStudent):
        self.am = ARX(self.spread, lags=1, rescale=False)
        self.am.volatility = vol
        self.am.distribution = dist

    def rollingForecasting(self, window: int, VaR_alpha: list[float, float]) -> pd.DataFrame:
        data_total_days = self.spread.shape[0]
        data_start_date = self.spread.index[0]

        forecast_df = pd.DataFrame(columns=[
                                   'datetime', 'cond_mean', 'cond_var', f'VaR-{VaR_alpha[0]*100}%', f'VaR-{VaR_alpha[1]*100}%'])
        for i in range(data_total_days-window):
            res = self.am.fit(first_obs=data_start_date+timedelta(days=i),
                              last_obs=data_start_date+timedelta(days=window+i), disp='off')
            forecast = res.forecast(reindex=False, align='target')
            datetime = forecast.mean.iloc[1].name
            cond_mean = forecast.mean.iloc[1, 0]
            cond_var = forecast.variance.iloc[1, 0]

            q = self.am.distribution.ppf(VaR_alpha, res.params[-2:])
            VaR = cond_mean + np.sqrt(cond_var) * q
            tmp = {'datetime': datetime, 'cond_mean': cond_mean, 'cond_var': cond_var,
                   f'VaR-{VaR_alpha[0]*100}%': VaR[0], f'VaR-{VaR_alpha[1]*100}%': VaR[1]}
            forecast_df = forecast_df.append(tmp, ignore_index=True)

        return forecast_df.set_index('datetime')
