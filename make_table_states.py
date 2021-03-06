import os
import pathlib
import sys
import re
import pandas as pd
from datetime import date
from collections import defaultdict
import argparse
import common

def make_row(state, statefiles, out):
    pngs = [name for name in statefiles if name.endswith('.png')]
    #print(pngs)
    assert len(pngs) == 4
    f1, f2, f3, f4 = pngs

    statename = state.replace('_',' ')
    location = f'{state}_State'
    plotly_page = f'{state}/graphs.php?location={location}'

    print(f"""
    <tr>
        <td><a href="/covid/states/{state}">{statename}</a></td>
        <td><a href="{plotly_page}"><img src="{state}/{f1}" style="width: 55vw; max-width: 100px;"></a></td>
        <td><a href="{plotly_page}"><img src="{state}/{f3}" style="width: 55vw; max-width: 100px;"></a></td>
        <td><a href="{plotly_page}"><img src="{state}/{f4}" style="width: 55vw; max-width: 100px;"></a></td>
        <td><a href="{plotly_page}"><img src="{state}/{f2}" style="width: 55vw; max-width: 100px;"></a></td>
        </tr>
    """, file=out)


def main():
    coviddir = os.environ.get('COVIDDIR', None)
    if not coviddir:
        home = os.environ.get('HOME', '.') # fallback to cwd
        coviddir = f'{home}/Desktop/covid'
    statedir = f'{coviddir}/states'

    parser = argparse.ArgumentParser(description='Make an HTML table for all states.')
    parser.add_argument("-t", "--template", default="web/sindex.php", help="template for the table")
    args = parser.parse_args()
    template = args.template

    # Get list of PNG files
    statedir=pathlib.Path(f'{statedir}/')
    suffixes = ['_trend', '_yellow_target', '_new_cases', '_posneg']
    endings = [f'{suffix}.png' for suffix in suffixes]
    graphed_states = set([path.name for path in statedir.iterdir() if path.is_dir()])

    all_states = set([x.replace(' ','_') for x in common.state_d.values()])
    all_territories = set([x.replace(' ','_') for x in common.territory_d.values()])

    states = sorted(graphed_states.intersection(all_states))
    territories = sorted(graphed_states.intersection(all_territories))
    usa = 'United_States'
    states.extend(territories)
    states.insert(0, usa)

    all_files = {}
    for state in states:
        statepath = statedir.joinpath(state)
        statefiles = sorted([path.name for path in statepath.iterdir() \
            if path.name.startswith(f'{state}_State_')])
        valid = []
        for filename in statefiles:
            for ending in endings:
                if filename.endswith(ending):
                    valid.append(filename)
                    break
        all_files[state] = valid

    # Setup output directories
    tableout=f'table.html'
    output=open(f'{statedir}/{tableout}', 'w')

    # Create index.php for the state by using the template
    phpout=open(f'{statedir}/index.php', 'w')
    for line in open(template):
        line = re.sub(r"TABLE_HTML", f"{tableout}", line)
        line = re.sub(r'PAGE_TITLE', f'SARS-CoV-2: USA', line) 
        print(line, file=phpout, end='')

    ####
    # Create the table.html file for the country
    ####
    # Make row for each state
    for state in all_files:
        statefiles = all_files[state]
        make_row(state, statefiles, output)


if __name__=='__main__':
    main()
