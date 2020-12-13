import pandas as pd
import seaborn as sns
import numpy as np
from matplotlib import pyplot as plt
from plots_pylab import limit_xticks
import common
from plots_plotly import posNeg_rate_plotly

path='data/covidtracking'

def get_data(trim=False, clip_date=None):
    tracking_loc=f'{path}/states'
    csv_file='daily.csv'
    df = pd.read_csv(f'{tracking_loc}/{csv_file}')
    df = df.rename(columns={"date": "Last_Update", "state": "Province_State"})
    df['Province_State'] = df['Province_State'].apply(lambda x: common.merged_d[x])

    df.Last_Update = pd.to_datetime(df.Last_Update, format='%Y%m%d')
    if clip_date:
        # remove data before this date
        df = df[df.Last_Update > clip_date]
    if trim:
        df = df[['Last_Update', 'Province_State', 'positive', 'negative']]

    return df
    
def filter_by_state(df, state):
    state_df = pd.DataFrame(df[df.Province_State==state].sort_values(by='Last_Update'))
    state_df.reset_index(inplace=True)
    return state_df
    
def augment(state_df, window=7):
    """ add daily and average values to the data """

    # replace "NaN" values with zeros
    state_df['positive'].fillna(0, inplace=True)
    state_df['negative'].fillna(0, inplace=True)
    
    # cumulative
    state_df['positive_rate'] = state_df.positive / (state_df.positive + state_df.negative)

    # daily
    state_df['daily_positive'] = state_df.positive.subtract(state_df.positive.shift(1), fill_value=0)
    state_df['daily_negative'] = state_df.negative.subtract(state_df.negative.shift(1), fill_value=0)
    
    # {window}-day daily test rate
    dp = f'daily_positive_{window}'
    dn = f'daily_negative_{window}'
    dpr= f'daily_positive_rate_{window}'
    state_df[dp] = state_df.daily_positive.rolling(window=window, min_periods=1, center=False).sum()
    state_df[dn] = state_df.daily_negative.rolling(window=window, min_periods=1, center=False).sum()
    state_df[dpr]= state_df[dp]/(state_df[dp] + state_df[dn])
    
    # {window}-day daily number of tests average
    state_df['tests'] = state_df.positive + state_df.negative
    state_df['daily_tests'] = state_df.tests.subtract(state_df.tests.shift(1), fill_value=0)
    nt = f'daily_tests_{window}'
    state_df[nt] = state_df.daily_tests.rolling(window=window, min_periods=1, center=False).mean()

    return state_df

if __name__ == '__main__':
    ct_df = get_data(clip_date='2020-03-15')
    days = 7
    pngScale=0.25
    output = 'inline'
    for state in ['Delaware']:
        state_df = filter_by_state(ct_df, state)
        augment(state_df, window=days)
        posNeg_rate_plotly(state_df, label=state, days=days, output=output, pngScale=pngScale)    
