import os
import sys
import re
import pandas
from datetime import date
from collections import defaultdict

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

def makerow(labels, files, out):
    f1, f2, f3 = [f'{dir}/{name}' for name in files]
    labels = [label.replace('_',' ') for label in labels]
    county = labels[2]
    if county in phases:
        phase = phases[county]
        tdcolor = f'<td class="{phase.color}">'
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


# Read data from phases
regions = defaultdict(set)
phases = dict()
df = pandas.read_csv('phases.csv', parse_dates=['Effective_Date'])
for _, row in df.iterrows():
    (county, region, color, date) = row.values
    region = region.replace(' ', '_')
    regions[region].add(county)
    phases[county] = Phase(color, date)

# Load list of generated .png files
dir='png'
files=sorted(os.listdir(dir))

# Make state row
state = [x for x in files if x.startswith('Pennsylvania_')]
makerow(['Pennyslvania', '', ''], state, sys.stdout)

# Get counties
counties = [f for f in files if '_County_' in f]
rgx = re.compile(r'^(.*?)_County_.*$')
data = {}
for i in range(0, len(counties), 3):
    name = rgx.search(counties[i]).group(1)
    data[name] = counties[i:i+3]

# Make region rows
regionfiles = [f for f in files if '_Region_' in f]
rgx = re.compile(r'^(.*?)_Region_.*$')
for i in range(0, len(regionfiles), 3):
    match = rgx.search(regionfiles[i])
    region = match.group(1)
    makerow(['Pennsylvania', region, ''], regionfiles[i:i+3], sys.stdout)

    # Make country rows
    rgx2 = re.compile(r'^(.*?)_County_.*$')
    for county in sorted(regions[region]):
        countyfiles = data[county]
        match = rgx2.search(countyfiles[0])
        makerow(['Pennsylvania', region, match.group(1)], countyfiles, sys.stdout)
