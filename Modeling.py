import pandas as pd
import numpy as np

def log_return(prices_df:pd.DataFrame) -> pd.DataFrame:
    rtn_df = pd.DataFrame()
    for crypto in prices_df.columns:
        rtn_df[f'{crypto}'] = np.log(prices_df.loc[:,crypto] / prices_df.loc[:,crypto].shift(1))

    return rtn_df