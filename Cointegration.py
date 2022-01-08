import pandas as pd
import numpy as np
from itertools import combinations
from statsmodels.tsa.stattools import coint

def pair_selection_MSD(prices_df:pd.DataFrame) -> pd.DataFrame:
    normalized_prices_df:pd.DataFrame = (prices_df-prices_df.mean())/prices_df.std()
    pair_list = []
    MSD_list  = []
    for pair in combinations(normalized_prices_df.columns,2):
        pair_list.append(str(pair))
        MSD_list.append(sum((normalized_prices_df.loc[:,pair[0]] - normalized_prices_df.loc[:,pair[1]]) ** 2))

    selection = pd.DataFrame({'pair':pair_list, 'MSD':MSD_list})
    selection_ranked = selection.set_index('pair').sort_values('MSD')
    
    return selection_ranked

def cointegration_test(prices_df: pd.DataFrame, alpha: float=0.05) -> pd.DataFrame:
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