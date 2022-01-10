from ast import literal_eval
from datetime import timedelta
from itertools import combinations

import numpy as np
import pandas as pd
from arch.typing import DateLike
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
    def __init__(self, spread_df: pd.DataFrame, pair: str) -> None:
        self.pair = pair
        self.spread = spread_df[pair]

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

        self.result = forecast_df.set_index('datetime')


class Strategy:
    def __init__(self, price_df: pd.DataFrame, model: ForecastModel) -> None:
        self.pair = literal_eval(model.pair)
        self.spread = model.spread
        self.priceA = price_df[self.pair[0]]
        self.priceB = price_df[self.pair[1]]
        self.forecast_len = len(model.result)
        self.upperVaR = model.result.iloc[:, -1]
        self.lowerVaR = model.result.iloc[:, -2]

    def performance(self, date_start: DateLike):
        spread = self.spread[date_start:]
        priceA = self.priceA[date_start:]
        priceB = self.priceB[date_start:]
        money = 0
        countA = 1
        countB = 1
        ratios = priceA/priceB
        trade_countA = 0
        trade_countB = 0

        for i in range(self.forecast_len):
            if (spread[i] > self.upperVaR[i]) and (countA > 0):
                money += priceA[i] - priceB[i] * ratios[i]
                countA -= 1
                countB += ratios[i]
                trade_countA += 1

            if (spread[i] < self.lowerVaR[i]) and (countB > 0):
                money -= priceA[i] - priceB[i] * ratios[i]
                countA += 1
                countB -= ratios[i]
                trade_countB += 1

        money = countA * priceA[-1] + countB * priceB[-1]
        returnA = ((priceA[-1] - priceA[0])/priceA[0])*100
        returnB = ((priceB[-1] - priceB[0])/priceB[0])*100
        pair_return = ((money - (priceA[0]+priceB[0]))/(priceA[0]+priceB[0]))*100

        tmp_dict = {'Currency A': [self.pair[0]], 'A Return%': returnA,
                    'Currency B': [self.pair[1]], 'B Return%': returnB,
                    'trades': trade_countA+trade_countB,
                    'trades A->B': trade_countA, 
                    'trades B->A': trade_countB,
                    'Pair Return%': pair_return}

        result = pd.DataFrame(tmp_dict)

        return result
