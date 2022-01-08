import pandas as pd
import numpy as np

def log_return(df:pd.DataFrame) -> pd.DataFrame:
    rtn_df = pd.DataFrame()
    for crypto in list(df.columns):
        rtn_df['crypto'] = np.log(df.loc[:,crypto] / df.loc[:,crypto].shift(1))

    return rtn_df