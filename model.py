from arch import arch_model
import pandas as pd

def garch(returns:pd.Series()):
    am = arch_model(returns, mean='AR', dist= 'skewstudent', p=1, o=0, q=1)
    res = am.fit()
    return res