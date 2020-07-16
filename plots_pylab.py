###########################################################################
# Functions for graphing (matplotlib)

########################################
## Daily new cases and 14-day moving average
def new_case_plot(df, label, days=14, centered=False, output=None):

    if centered:
        date_field = f'Centered_Date_{days}'
    else:
        date_field='Last_Update'
        
    g = sns.lineplot(df['Last_Update'], df['New_Cases'], label="Daily new cases")
    sns.lineplot(df[date_field], df[f'day_avg_{days}'], ax=g, label=f"{days} day moving average")
    g.set(xlabel="\nDate", ylabel="New Cases", title=f"New Cases Per Day\n{label}")
    leg = g.legend(loc='upper left', frameon=False)
    plt.xticks(rotation=90)
    if output == 'inline':
        plt.show()
    else:
        output = output.replace("'","").replace('.png', '_new_cases.png')
        plt.savefig(output, bbox_inches='tight')

########################################
## Yellow target: 50 new cases over 14 days per 100K people
def newcase_sum(df, days, perpop=1):
    """ 
    compute the sum of {days} days and {days}_sum to the df 
    if perpop is not 1, calculate the same weighted by the population pop
    """
    field = f'sum_{days}'
    df[field] = df.New_Cases.rolling(window=days, min_periods=1).sum()
    df[field] *= perpop

def yellow_target(df, label, output=None):
    population = set(df.Population).pop()
    newcase_sum(df, 14, perpop=100000/population)
    target = 50
    
    g = sns.lineplot(df['Last_Update'], df['sum_14'], label="14 day caseload per 100K")
    sns.lineplot(df['Last_Update'], [target]*len(df), label="Yellow Target", ax=g)
    g.set(xlabel="\nDate", ylabel="14 days cases per 100K", title=f"Progress towards yellow target\n{label}")
    leg = g.legend(loc='lower right', frameon=False)
    plt.xticks(rotation=90)
    if output == 'inline':
        plt.show()
    else:
        output = output.replace("'","").replace('.png', '_yellow_target.png')
        plt.savefig(output, bbox_inches='tight')

########################################
## Days trending downward in 14 days
def limit_xticks(labels, num=5):
    """
    For some reason I can't limit the number of xticks so here I'm
    just doing it myself by erasing the text of the xticks I don't want
    """
        
    target_ticks = set([0, len(labels)-1])
    for i in range(1, num-1):
        pos= int(round(len(labels)/(num-1)*i,0))
        target_ticks.add(pos)

    for i, lab in enumerate(labels):
        if i not in target_ticks:
            labels[i].set_text("")
    return labels

def trending(df, label, days=14, output=None):
    tfield = f'trend_{days}'
    sfield = f'slope_{days}'
    
    formatted_dates = df['Last_Update'].apply(lambda x: x.strftime('%Y-%m-%d'))
    g=sns.barplot(formatted_dates, df[tfield], label="increasing trends", color='red')
    sns.barplot(formatted_dates, df[tfield]-14, label="decreasing trends", color='green')
    t = g.twinx()
    
    sns.lineplot(np.arange(len(df)), df[sfield], color="black", label="14-day slope", ax=t)
    #slopes = np.where(df['trend_14'].isnull(), 0, df['slope_14'])
    #sns.lineplot(np.arange(len(df)), slopes, color="black", label="14-day slope", ax=t)

    labels = limit_xticks(g.get_xticklabels())
    g.set_xticklabels(labels,rotation=90)

    g.set_ylim(-14,14)
    title=f"Number of days in the past two weeks with a positive or negative trend\n{label}"
    g.set(xlabel="\nDate", ylabel="Number of days", title=title)
    t.set(ylabel="slope of 14-day trend")
    slope_lim = max(abs(df[df[sfield].notna()][sfield]))*1.1
    t.set_ylim(-slope_lim,slope_lim)
    leg = t.legend(loc='lower left', frameon=False)

    if output == 'inline':
        plt.show()
    else:
        output = output.replace("'","").replace('.png', '_trend.png')
        plt.savefig(output, bbox_inches='tight')
    
