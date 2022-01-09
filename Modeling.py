from numpy.lib.function_base import append
import pandas as pd
import numpy as np
from itertools import combinations

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