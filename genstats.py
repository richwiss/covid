import time
import numpy as np

###########################################################################
# Generate various statistics on the data
def gen_statistics(rowdf, groupby, no_trends=False):
    """
    Purpose: One-stop shopping for adding various statistics such as
    daily new cases, 7-day rolling average, cases per 100K, etc.
    """
    # generate new case counts
    gen_new_cases(rowdf, groupby)

    # Add {days}-day moving average
    days = 7
    gen_average_new_cases(rowdf, groupby, days)

    # Add {days}-day/per 100K
    rowdf[f'percap_{days}'] = rowdf[f'day_avg_{days}']/rowdf['Population']*100000*days

    # Generate 14-day trendlines the original way -- won't do counties by without force
    gen_trend_original(rowdf, groupby, days=14, force=(no_trends==False))

    # Generate 14-day trendlines -- won't do counties by without force
    #gen_trend_alternate(rowdf, groupby)


###########################################################################
def gen_new_cases(rowdf, groupby):
    """
    Purpose: Add the new_cases column to the dataframe
    Inputs: row dataframe (rowdf) and how to groupby (state, county, region)
    Side effect: Mutates the existing dataframe
    """
    rowdf['New_Cases'] = rowdf.groupby(groupby)['Confirmed'].diff()
    rowdf['New_Cases'].fillna(0, inplace=True)

def gen_average_new_cases(rowdf, groupby, days):
    """
    Purpose: Add the day_avg_{days} column to the dataframe
    Inputs: row dataframe (rowdf), days to average over (days),
            and how to groupby (state, county, region)
    Side effect: Mutates the existing dataframe
    """
    field = f'day_avg_{days}'
    rollfn = lambda x: x.rolling(window=days, min_periods=1).mean()
    rowdf[field] = rowdf.groupby(groupby)['New_Cases'].transform(rollfn)

def fit(period):
    """ A function to find the best-fit line for a period of data """
    if len(period) == 1:
        return 0
    else:
        m, _ = np.polyfit(np.arange(len(period)), period, 1)
        return m


def gen_trend_original(rowdf, groupby, days=14, force=False):
    """ 
    **** Warning: this function is quite slow for counties ****

    Purpose: compute the trendline for the past {days} days as slope_{days}
    and the number of days within those {days} that the trend is worsening
    (positive) or improving (negative) as trend_{days}
    Side effect: Mutates the df to include slope_{days} and trend_{days}
    """
    if (not force) and ('Admin2' in rowdf): return

    # Get the slope of the trend line for the past {days} days.
    sfield=f'slope_{days}'
    rollfn = lambda x: x.rolling(window=days, min_periods=1).apply(fit)
    rowdf[sfield] = rowdf.groupby(groupby)['New_Cases'].transform(rollfn)

    # Get the number of times the slope was positive in last {days} days.
    tfield = f'trend_{days}'
    rollfn1 = lambda x: x.rolling(window=days, min_periods=days).apply(lambda x: (x>0).sum())
    #rollfn2 = lambda x: x.rolling(window=days, min_periods=days).apply(lambda x: x.gt(0).sum())

    if 'Admin2' in rowdf: print(f'Generating county trends')
    s = time.time()
    rowdf[tfield] = rowdf.groupby(groupby)[sfield].transform(rollfn1)
    e = time.time()
    if 'Admin2' in rowdf: print(f'Elapsed: {e-s}s')

def gen_trend_alternate(rowdf, groupby, days=14, force=False):
    """ 
    Purpose: compute the number of days within {days} days that
    the trend is worsening (positive) or improving (negative) as trend_{days}
    Side effect: Mutates the df to include trend_{days}
    """
    # Get the number of times the slope was positive in last {days} days.
    if (not force) and ('Admin2' in rowdf): return

    # Fake it for now
    # Get the number of times the slope was positive in last {days} days.
    tfield = f'trend_{days}'
    sfield = f'day_avg_7_diff'
    # hard code 7 bc day_avg_14 prob doesn't exist. we could make it if needed
    rowdf[sfield] = rowdf.groupby(groupby)['day_avg_7'].diff(periods=7)
    rollfn1 = lambda x: x.rolling(window=days, min_periods=days).apply(lambda x: (x>0).sum())
    s = time.time()
    rowdf[tfield] = rowdf.groupby(groupby)[sfield].transform(rollfn1)
    e = time.time()
    print(f'Elapsed: {e-s}s')

