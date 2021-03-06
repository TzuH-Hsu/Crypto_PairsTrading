from ast import literal_eval
from datetime import timedelta
from itertools import combinations

import numpy as np
import pandas as pd
from arch.typing import DateLike
from arch.univariate import *
from arch.univariate.base import ARCHModelResult
from scipy.stats import jarque_bera
from statsmodels.tsa.stattools import coint


def price_normalization(prices_df: pd.DataFrame) -> pd.DataFrame:
    normalized_prices_df: pd.DataFrame = (
        prices_df-prices_df.mean())/prices_df.std()
    return normalized_prices_df


def descriptive_statistics(return_df: pd.DataFrame) -> pd.DataFrame:
    df_tmp = pd.concat([return_df.kurtosis(), return_df.apply(jarque_bera).iloc[1]], keys=[
                       'Fisher’s kurtosis', 'jarque bera test(p-value)'], axis='columns')
    return_df = pd.concat([return_df.describe(include='all').T, df_tmp], axis='columns')
    return return_df


def pair_selection_MSD(prices_df: pd.DataFrame) -> pd.DataFrame:
    normalized_prices_df = price_normalization(prices_df)
    pair_list = []
    MSD_list = []
    for pair in combinations(normalized_prices_df.columns, 2):
        pair_list.append(str(pair))
        MSD_list.append(sum(
            (normalized_prices_df.loc[:, pair[0]] - normalized_prices_df.loc[:, pair[1]]) ** 2))

    selection = pd.DataFrame({'pair': pair_list, 'MSD': MSD_list})
    selection_ranked = selection.set_index('pair').sort_values('MSD')

    return selection_ranked


def cointegration_test(prices_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    pair_list = []
    score_list = []
    pvalue_list = []
    cointegration_list = []
    for pair in combinations(prices_df.columns, 2):
        pair_list.append(str(pair))
        score, pvalue, _ = coint(
            prices_df.loc[:, pair[0]], prices_df.loc[:, pair[1]])
        cointegration = True if (pvalue <= alpha) else False
        score_list.append(score)
        pvalue_list.append(pvalue)
        cointegration_list.append(cointegration)
    result_df = pd.DataFrame({'pair': pair_list, 'score': score_list,
                             'p-value': pvalue_list, 'cointegration': cointegration_list})
    result_df_ranked = result_df.set_index('pair').sort_values('p-value')

    return result_df_ranked


def cal_return(prices_df: pd.DataFrame, log:bool=False) -> pd.DataFrame:
    rtn_df = pd.DataFrame()
    if log:
        for crypto in prices_df.columns:
            rtn_df[f'{crypto}'] = np.log(prices_df.loc[:, crypto] / prices_df.loc[:, crypto].shift(1))
    else:
        for crypto in prices_df.columns:
            rtn_df[f'{crypto}'] = prices_df.loc[:, crypto] - prices_df.loc[:, crypto].shift(1)
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
    def __init__(self, spread_df: pd.DataFrame, pair: tuple[str, str]) -> None:
        self.pair = pair
        self.spread = spread_df[str(pair)]

    def modelspec(self, vol: GARCH | EGARCH, dist: Normal | StudentsT | SkewStudent):
        # self.am = ARX(self.spread, lags=1, rescale=False)
        self.am = ZeroMean(self.spread, rescale=False)
        self.am.volatility = vol
        self.am.distribution = dist

    def rollingForecasting(self, window: int, VaR_alpha: list[float, float]) -> ARCHModelResult:
        data_total_days = self.spread.shape[0]
        data_start_date = self.spread.index[0]

        forecast_df = pd.DataFrame(columns=[
                                   'datetime', 'cond_mean', 'cond_var', f'VaR-{VaR_alpha[0]*100}%', f'VaR-{VaR_alpha[1]*100}%'])
        for i in range(data_total_days-window):
            self.res = self.am.fit(first_obs=data_start_date + timedelta(days=i),
                                   last_obs=data_start_date + timedelta(days=window+i),
                                   disp='off', options={'maxiter': 300}, tol=1e-04)
            forecast = self.res.forecast(reindex=False, align='target')
            datetime = forecast.mean.iloc[1].name
            cond_mean = forecast.mean.iloc[1, 0]
            cond_var = forecast.variance.iloc[1, 0]

            if type(self.am.distribution) == StudentsT:
                params = self.res.params[-1:]
            elif type(self.am.distribution) == SkewStudent:
                params = self.res.params[-2:]
            else:
                params = None

            q = self.am.distribution.ppf(VaR_alpha, params)
            VaR = cond_mean + np.sqrt(cond_var) * q
            tmp = {'datetime': datetime, 'cond_mean': cond_mean, 'cond_var': cond_var,
                   f'VaR-{VaR_alpha[0]*100}%': VaR[0], f'VaR-{VaR_alpha[1]*100}%': VaR[1]}
            forecast_df = forecast_df.append(tmp, ignore_index=True)

        self.result = forecast_df.set_index('datetime')


class Strategy:
    def __init__(self, price_df: pd.DataFrame, model: ForecastModel) -> None:
        self.pair = model.pair
        self.spreadall = model.spread
        self.priceA = price_df[self.pair[0]]
        self.priceB = price_df[self.pair[1]]
        self.forecast_len = len(model.result)
        self.upperVaR = model.result.iloc[:, -1]
        self.lowerVaR = model.result.iloc[:, -2]


    def performance(self, date_start: DateLike) -> pd.DataFrame:
        self.spread = self.spreadall[date_start:]
        priceA = self.priceA[date_start:]
        priceB = self.priceB[date_start:]
        money = 0
        countA = 1
        countB = 1
        trades = 0

        for i in range(self.forecast_len):
            if (self.spread[i] > self.upperVaR[i]) and (countA > 0):
                money += priceA[i] - priceB[i]
                countA -= 1
                countB += 1
                trades += 1

            if (self.spread[i] < self.lowerVaR[i]) and (countB > 0):
                money -= priceA[i] - priceB[i]
                countA += 1
                countB -= 1
                trades += 1

        money = money + countA * priceA[-1] + countB * priceB[-1]
        returnA = ((priceA[-1] - priceA[0])/priceA[0])*100
        returnB = ((priceB[-1] - priceB[0])/priceB[0])*100
        pair_return = ((money - (priceA[0]+priceB[0]))/(priceA[0]+priceB[0]))*100

        tmp_dict = {'Currency A': [self.pair[0]], 'A Return%': returnA,
                    'Currency B': [self.pair[1]], 'B Return%': returnB,
                    'trades': trades, 'Pair Return%': pair_return}

        result = pd.DataFrame(tmp_dict)

        return result
