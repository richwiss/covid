import os
import sys
import re
import pandas as pd
from datetime import date
from collections import defaultdict
import argparse

class Phase(object):
    def __init__(self, color, effective_date):
        assert color in ['red', 'yellow', 'green']
        self.color = color
        self.effective_date = effective_date
        if self.color == 'red':
            self.emoji='🔴'
        elif self.color == 'yellow':
            self.emoji='🟡'
        elif self.color == 'green':
            self.emoji='🟢'

    def __repr__(self):
        return f'Phase({self.color}, "{self.effective_date}")'


def makerow(labels, directory, files, out):
    f1, f2, f3 = [name for name in files]
    labels = [label.replace('_',' ') for label in labels]
    county = labels[2]
    #if county == 'New_York_City':
    #    print(f'PHASE: {phases[county]}')
    if county in phases:
        phase = phases[county]
        edate = phase.effective_date.strftime('%m/%d/%Y')
        emoji = f'<BR /><div style="font-size: 75%;">{phase.emoji} {edate}</div>'
    else:
        tdcolor='<td>'
        emoji = ''
    print(f"""
    <tr>
        <td>{labels[0]}</td>
        <td>{labels[1]}</td>
        <td>{labels[2]}{emoji}</td>
          <td><a href="{f1}"><img src="{f1}" style="width: 55vw; max-width: 100px;"></a></td>
          <td><a href="{f2}"><img src="{f2}" style="width: 55vw; max-width: 100px;"></a></td>
          <td><a href="{f3}"><img src="{f3}" style="width: 55vw; max-width: 100px;"></a></td>
        </tr>
    """, file=out)




def load_regions(statename):
    """ load population and region data for counties if applicable"""

    population_loc = 'resources'
    df = pd.read_csv(f'{population_loc}/county-populations.csv')

    regions = defaultdict(set)
    sstate = statename.replace('_', ' ')

    def f(row):
        if row.State == sstate:
            regions[row.Region].add(row.County)

    df[df.Region.notnull()].apply(f, axis=1)

    return regions

def load_phases(statename):
    """ read designated phases (PA only) """
    phases = dict()
    phases_loc = '.'
    df = pd.read_csv(f'{phases_loc}/phases.csv', parse_dates=['Effective_Date'])
    sstate = statename.replace('_', ' ')

    def f(row):
        if row.State == sstate:
            phases[row.County] = Phase(row.Phase, row.Effective_Date)

    df.apply(f, axis=1)
    return phases


def get_png_files(statedir):
    """ Load list of generated .png files """
    files=sorted(os.listdir(statedir))
    return files

coviddir = os.environ.get('COVIDDIR', None)
if not coviddir:
    coviddir = '~/Desktop/covid'
statedir = f'{coviddir}/states'    

# Choose the state
parser = argparse.ArgumentParser(description='Make an HTML table for a state.')
parser.add_argument("-s", "--state", required=True, help="state name")
args = parser.parse_args()
statename = args.state

# Read the phases and regions
regions = load_regions(statename)
phases = load_phases(statename)

# Get list of PNG files
statedir=f'{statedir}/{statename}'
files = get_png_files(statedir)

# Setup output directories
tableout=f'{statename}_table.html'
output=open(f'{statedir}/{statename}/{tableout}', 'w')

# create index for the state
phpout=open(f'{statedir}/{statename}/index.php', 'w')

for line in open('web/index.php'):
    line = re.sub(r"'table.html'", f"'{tableout}'", line)
    print(line, file=phpout, end='')
    if 'Data from the' in line:
        phase_data = ''
        if statename=="New_York":
            phase_data = 'Region status from the <a href="https://forward.ny.gov/regional-monitoring-dashboard">New York regional monitoring</a> website.<br/>'
        elif statename=='Pennsylvania':
            phase_data = 'Region status from the <a href="https://www.health.pa.gov/topics/disease/coronavirus/Pages/Coronavirus.aspx">Pennsylvania Dept of Health</a> website.<br/>'
        print(phase_data, file=phpout)

# Make state row
statefiles = [x for x in files if x.startswith(f'{statename}_State')]
(state, region, county) = (statename, '', '')
makerow([state, region, county], statedir, statefiles, output)

# Get counties
counties = [f for f in files if '_County_' in f]
county_rgx = re.compile(r'^(.*?)_County_.*.png$')
data = {}
for i in range(0, len(counties), 3):
    name = county_rgx.search(counties[i]).group(1)
    data[name] = counties[i:i+3]

# Make region rows
regionfiles = sorted([f for f in files if '_Region_' in f])
rgx = re.compile(r'^(.*?)_Region_.*.png$')
for i in range(0, len(regionfiles), 3):
    match = rgx.search(regionfiles[i])
    region = match.group(1)
    (state, county) = (statename, '')
    if region == 'New_York_City':
        region = 'New York City<BR/>(all boroughs)'
        county = 'New York City'

    makerow([state, region, county], dir, regionfiles[i:i+3], output)

    # Make country rows in the correct regions, if possible
    for county in sorted(regions[region.replace('_', ' ')]):
        county = county.replace(' ', '_')
        if statename == 'New_York' and county in ['Bronx', 'Queens', 'New_York_City', 'New_York', 'Kings', 'Richmond']:
            pass
        else:
            countyfiles = data[county]
            match = county_rgx.search(countyfiles[0])
            countyname = match.group(1)
            makerow([f'{statename}', region, countyname], dir, countyfiles, output)
            data.pop(county)

# Make country rows that weren't in regions
for county in sorted(data.keys()):
    countyfiles = data[county]
    match = county_rgx.search(countyfiles[0])
    makerow([f'{statename}', '&nbsp;', match.group(1)], dir, countyfiles, output)

