import os
import sys
import re
import pandas
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

def makerow(labels, directory, files, out):
    f1, f2, f3 = [name for name in files]
    labels = [label.replace('_',' ') for label in labels]
    county = labels[2]
    if county in phases:
        phase = phases[county]
        #tdcolor = f'<td class="{phase.color}">'
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


# Choose the state
parser = argparse.ArgumentParser(description='Make an HTML table for a state.')
parser.add_argument("-s", "--state", required=True, help="state name")
args = parser.parse_args()
statename = args.state

# Load list of generated .png files
dir=f'states/{statename}'
files=sorted(os.listdir(dir))
tableout=f'{statename}_table.html'
output=open(f'states/{statename}/{tableout}', 'w')

# create index for the state if it doesn't exist
phpout=open(f'states/{statename}/index.php', 'w')

for line in open('web/index.php'):
    line = re.sub(r"'table.html'", f"'{tableout}'", line)
    line = re.sub(r'"mystyle.css"', '../../mystyle.css', line)
    print(line, file=phpout, end='')


# Read data from phases
if statename=='Pennyslvania':
    regions = defaultdict(set)
    phases = dict()
    df = pandas.read_csv('phases.csv', parse_dates=['Effective_Date'])
    for _, row in df.iterrows():
        (county, region, color, date) = row.values
        region = region.replace(' ', '_')
        regions[region].add(county)
        phases[county] = Phase(color, date)
else:
    regions = defaultdict(set)
    phases = dict()


# Make state row
state = [x for x in files if x.startswith(f'{statename}_State')]
makerow([f'{statename}', '', ''], dir, state, output)

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
    makerow([f'{statename}', region, ''], dir, regionfiles[i:i+3], output)

    # Make country rows in the correct regions, if possible
    for county in sorted(regions[region]):
        countyfiles = data[county]
        match = county_rgx.search(countyfiles[0])
        makerow([f'{statename}', region, match.group(1)], dir, countyfiles, output)
        data.pop(county)

# Make country rows that weren't in regions
for county in sorted(data.keys()):
    countyfiles = data[county]
    match = county_rgx.search(countyfiles[0])
    makerow([f'{statename}', '&nbsp;', match.group(1)], dir, countyfiles, output)

