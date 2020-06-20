import os
import pathlib
import sys
import re
import pandas as pd
from datetime import date
from collections import defaultdict
import argparse

class Phase(object):
    def __init__(self, color, effective_date):
        assert color in ['red', 'yellow', 'green', 'blue']
        self.color = color
        self.effective_date = effective_date
        if self.color == 'red':
            self.emoji='🔴'
        elif self.color == 'yellow':
            self.emoji='🟡'
        elif self.color == 'green':
            self.emoji='🟢'
        elif self.color == 'blue':
            self.emoji='🔵'

    def __repr__(self):
        return f'Phase({self.color}, "{self.effective_date}")'

def make_row(labels, directory, files, out, phases, has_regions):
    f1, f2, f3 = [name for name in files if name.endswith('.png')]

    location = f1.replace('_new_cases.png','')
    labels = [label.replace('_',' ') for label in labels]
    county = labels[2]
    plotly_page = f'graphs.php?location={location}'

    if county in phases:
        phase = phases[county]
        edate = phase.effective_date.strftime('%m/%d/%Y')
        emoji = f'<BR /><div style="font-size: 75%;">{phase.emoji} {edate}</div>'
    else:
        emoji = ''

    if has_regions:
        region_info = f'<td>{labels[1]}</td>'
    else:
        region_info = ''
    print(f"""
    <tr>
        <td>{labels[0]}</td>
        {region_info}
        <td>{labels[2]}{emoji}</td>
          <td><a href="{plotly_page}"><img src="{f1}" style="width: 55vw; max-width: 100px;"></a></td>
          <td><a href="{plotly_page}"><img src="{f2}" style="width: 55vw; max-width: 100px;"></a></td>
          <td><a href="{plotly_page}"><img src="{f3}" style="width: 55vw; max-width: 100px;"></a></td>
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


def get_files(statepath, extension='png', suffixes=None):
    """ 
    Load list of generated .png files 
    
    statepath: location of files
    extension: files must end with this extension
    suffixes: a list of suffixes that each file must end with, prior to the
      extension (e.g. ['_trend', '_yellow_target', '_new_cases']) 
    """
    filenames=[path.name for path in statepath.iterdir()]
    endings = [f'{suffix}.{extension}' for suffix in suffixes]
    valid = []
    for filename in sorted(filenames):
        for ending in endings:
            if filename.endswith(ending):
                valid.append(filename)
                break
    return valid

def main():

    # Get the name of the state from the command-line arguments
    parser = argparse.ArgumentParser(description='Make an HTML table for a state.')
    parser.add_argument("-s", "--state", required=True, help="state name")
    parser.add_argument("-t", "--template", default="web/index.php", help="template for the table")
    args = parser.parse_args()
    statename = args.state
    template = args.template

    # Read the phases and regions
    regions = load_regions(statename) # map region name -> set of county names
    phases = load_phases(statename)   # map county name -> Phase
    has_regions = (len(regions) > 0)

    # Get list of PNG files
    coviddir = os.environ.get('COVIDDIR', None)
    if not coviddir:
        coviddir = '~/Desktop/covid'
    statedir = f'{coviddir}/states'
            
    statedirlocal=pathlib.Path(f'{statedir}/{statename}')
    suffixes = ['_trend', '_yellow_target', '_new_cases']
    files = get_files(statedirlocal, extension='png', suffixes=suffixes)
    assert len(files) % len(suffixes) == 0

    # Setup output directories
    tableout=f'{statename}_table.html'
    output=open(f'{statedir}/{statename}/{tableout}', 'w')

    county_rgx = re.compile(r'(<th>)County(</th>)')
    footer = defaultdict(str)
    footer['New_York'] = 'Region status from the <a href="https://forward.ny.gov/regional-monitoring-dashboard">New York regional monitoring</a> website.<br/>'
    footer['Pennsylvania'] = 'Region status from the <a href="https://www.health.pa.gov/topics/disease/coronavirus/Pages/Coronavirus.aspx">Pennsylvania Dept of Health</a> website.<br/>'

    # Create index.php for the state by using the template
    phpout=open(f'{statedir}/{statename}/index.php', 'w')
    for line in open(template):
        statedisplay = statename.replace('_',' ')
        line = re.sub(r"TABLE_HTML", f"{tableout}", line)
        line = re.sub(r'PAGE_TITLE', f'SARS-CoV-2: {statedisplay}', line) 
        line = re.sub(r'FOOTER_INFO', footer[statename], line)
        if not has_regions: line = re.sub(r'<th>Region</th>','', line)

        if statename == 'Louisiana': re.sub(r'(<th>)County(</th>)', r'\1Parrish\2', line)
        print(line, file=phpout, end='')

    ####
    # Create the table.html file for the state
    ####
    # Make state row
    statefiles = [x for x in files if x.startswith(f'{statename}_State')]
    (state, region, county) = (statename, '', '')
    make_row([state, region, county], statedirlocal, statefiles, output, phases, has_regions)

    # Get the images for the counties so we can insert into regions as we go
    county_files = [f for f in files if '_County_' in f]
    county_rgx = re.compile(r'^(.*?)_County_.*.png$')
    data = {}
    for i in range(0, len(county_files), 3):
        name = county_rgx.search(county_files[i]).group(1)
        data[name] = county_files[i:i+3]

    nyc_boroughs = ['Bronx', 'Queens', 'New_York_City', 'New_York', 'Kings', 'Richmond']
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
        make_row([state, region, county], dir, regionfiles[i:i+3], output, phases, has_regions)

        # Make country rows in the correct regions, if possible
        for county in sorted(regions[region.replace('_', ' ')]):
            county = county.replace(' ', '_')
            if not (statename == 'New_York' and county in nyc_boroughs):
                countyfiles = data[county]
                match = county_rgx.search(countyfiles[0])
                countyname = match.group(1)
                make_row([statename, region, countyname], dir, countyfiles, output, phases, has_regions)
                data.pop(county)

    # Make country rows that weren't in regions
    for county in sorted(data.keys()):
        countyfiles = data[county]
        region = "&nbsp;"
        match = county_rgx.search(countyfiles[0])
        countyname = match.group(1)
        make_row([statename, region,countyname], dir, countyfiles, output, phases, has_regions)

if __name__=='__main__':
    main()
