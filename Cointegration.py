import pandas as pd
import numpy as np
from itertools import combinations


def pair_selection_MSD(prices_df:pd.DataFrame) -> pd.DataFrame:
    normalized_prices_df = (prices_df-prices_df.mean())/prices_df.std()
    pair_list = []
    MSD_list  = []
    for pair in combinations(normalized_prices_df.columns,2):
        pair_list.append(str(pair))
        MSD_list.append(sum((normalized_prices_df.loc[:,pair[0]] - normalized_prices_df.loc[:,pair[1]]) ** 2))

    selection = pd.DataFrame({'pair':pair_list, 'MSD':MSD_list})
    selection_ranked = selection.set_index('pair').sort_values('MSD')
    
    return selection_ranked

def log_return(df:pd.DataFrame) -> pd.DataFrame:
    rtn_df = pd.DataFrame()
    for crypto in list(df.columns):
        rtn_df['crypto'] = np.log(df.loc[:,crypto] / df.loc[:,crypto].shift(1))

    return rtn_df