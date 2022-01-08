import pandas as pd
import numpy as np

def log_return(series:pd.Series) -> pd.Series:
    rtn = np.log(series / series.shift(1))

    return rtn