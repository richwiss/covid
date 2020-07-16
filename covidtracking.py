# # Covid Tracking
# #### Requires: imports from above as well as limit_xticks() function
"""
abbrevs = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 
           'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'DC': 'District of Columbia', 
           'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 
           'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 
           'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 
           'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 
           'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 
           'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 
           'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 
           'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 
           'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'}
rabbrevs = dict([(v,k) for (k,v) in abbrevs.items()])
"""




def get_covidtracking():
    tracking_loc='covidtracking/states'
    csv_file='daily.csv'
    df = pd.read_csv(f'{tracking_loc}/{csv_file}')
    df.date = pd.to_datetime(df.date, format='%Y%m%d')
    return df
    
def filter_covidtracking(df, state):
    state_df = pd.DataFrame(df[df.state==state].sort_values(by='date'))
    state_df.reset_index(inplace=True)
    return state_df
    
def augment_covidtracking(state_df, window=7):
    """ 
    only works for a single state at a time
    """
    state_df['positive'].fillna(0, inplace=True)
    state_df['negative'].fillna(0, inplace=True)
    state_df['pending'].fillna(0, inplace=True)
    

    # cumulative
    state_df['positive_rate'] = state_df.positive / (state_df.positive + state_df.negative)
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
    state_df['new_tests'] = state_df.tests.subtract(state_df.tests.shift(1), fill_value=0)
    nt = f'new_tests_{window}'
    state_df[nt] = state_df.new_tests.rolling(window=window, min_periods=1, center=False).mean()
    return state_df





def positive_test_rate(df, label, window=7, mindate="2020-04-01", output=None):
    """
    run on covidtracking data
    """    
    
    if mindate is not None:
        df = df[df.date > mindate]
        
    dpr = f'daily_positive_rate_{window}'
    g = sns.lineplot(df['date'], df[dpr], label=f"positive test rate: {window} day average")
    #sns.lineplot(df['date'], df['positive_rate'], label="cumulative positive test rate", ax=g)
    g.set(xlabel="\nDate", ylabel="Positive test rate", title=f"Positive test rate over time\n{label}")

    ymax = max(0.5, max(df.daily_positive_rate_7))
    g.set_ylim(0, ymax)

    leg = g.legend(loc='best', frameon=False)
    plt.xticks(rotation=90)
    if output == 'inline':
        plt.show()
    #else:
    #    output = output.replace("'","").replace('.png', '_yellow_target.png')
    #    plt.savefig(output, bbox_inches='tight')





def ptr_plus(df, label, window=7, mindate="2020-04-01", output=None):
    dpr = f'daily_positive_rate_{window}'
    nt = f'new_tests_{window}'

    if mindate is not None:
        df = df[df.date > mindate]
    
    formatted_dates = df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    g=sns.barplot(formatted_dates, df[nt], label="number of tests", color='green')
    t = g.twinx()
    
    sns.lineplot(np.arange(len(df)), df[dpr], color="black", label="positive test rate", ax=t)
    #slopes = np.where(df['trend_14'].isnull(), 0, df['slope_14'])
    #sns.lineplot(np.arange(len(df)), slopes, color="black", label="14-day slope", ax=t)

    labels = limit_xticks(g.get_xticklabels())
    g.set_xticklabels(labels,rotation=90)

    #g.set_ylim(-14,14)
    
    title=f"Number of tests and positive test rate: {window}-day average\n{label}"
    g.set(xlabel="\nDate", ylabel="Number of tests", title=title)
    t.set(ylabel="Positive test rate")

    ymax = max(0.5, max(df.daily_positive_rate_7))
    t.set_ylim(0, ymax)
    
    leg = t.legend(loc='best', frameon=False)

    if output == 'inline':
        plt.show()
    else:
        output = output.replace("'","").replace('.png', '_trend.png')
        plt.savefig(output, bbox_inches='tight')
    

#state = 'Oregon'
#ct_df = get_covidtracking()
#state_df = filter_covidtracking(ct_df, rabbrevs[state])
#augment_covidtracking(state_df)
#ptr_plus(state_df, state, output='inline')







