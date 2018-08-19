"""
commons.py
    Funzioni e dati condivisi fra gli script.
"""
import datetime
import pathlib
import pandas as pd
import numpy as np

# Prima data disponibile
# CoinMarketCap's historical data only goes back to 28/04/2013
FIRST_DATE = datetime.date(2013, 4, 28)
# Percentage factor
PERC_FACTOR = 100

def annualized_sharpe(returns, N=52):
    """
    Calculate the annualised Sharpe ratio of a returns stream 
    based on a number of trading periods, N. N defaults to 52,
    which then assumes a stream of weekly returns.

    The function assumes that the returns are the excess of 
    those compared to a benchmark.
    """
    return np.sqrt(N) * returns.expanding().mean() / returns.expanding().std()

def daterange(start_date, end_date, step = 1):
    """
        Generatore di tutte le date comprese in un intervallo specificato.
    """
    for n in range(0, int ((end_date - start_date).days) + 1, step):
        yield start_date + datetime.timedelta(n)

  
def make_dir_if_not_exists(dir):
    """
        Crea la directory specificata se non esiste già.
        [Makes a directory if it doesn't already exist.]
    """
    path = pathlib.Path(dir)
    if not path.exists():
        path.mkdir(parents=True)

class Config(dict):
    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError

    def __setattr__(self, key, value):
        if key in self.__dict__:
            self.__dict__[key] = value
        else:
            self[key] = value
