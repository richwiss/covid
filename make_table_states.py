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
        assert color in ['red', 'yellow', 'green']
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

def make_row(state, statefiles, out):
    f1, f2, f3 = [name for name in statefiles if name.endswith('.png')]

    statename = state.replace('_',' ')
    location = f'{state}/{state}_State'
    plotly_page = f'graphs.php?location={location}'

    print(f"""
    <tr>
        <td><a href="/covid/states/{state}">{statename}</a></td>
        <td><a href="{plotly_page}"><img src="{state}/{f1}" style="width: 55vw; max-width: 100px;"></a></td>
        <td><a href="{plotly_page}"><img src="{state}/{f2}" style="width: 55vw; max-width: 100px;"></a></td>
        <td><a href="{plotly_page}"><img src="{state}/{f3}" style="width: 55vw; max-width: 100px;"></a></td>
        </tr>
    """, file=out)


def main():

    # Get the name of the state from the command-line arguments
    parser = argparse.ArgumentParser(description='Make an HTML table for all states.')
    parser.add_argument("-t", "--template", default="web/sindex.php", help="template for the table")
    args = parser.parse_args()
    template = args.template

    # Get list of PNG files
    statedir=pathlib.Path(f'states/')
    suffixes = ['_trend', '_yellow_target', '_new_cases']
    endings = [f'{suffix}.png' for suffix in suffixes]

    states = [path.name for path in statedir.iterdir() if path.is_dir()]
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
    output=open(f'states/{tableout}', 'w')

    # Create index.php for the state by using the template
    phpout=open(f'states/index.php', 'w')
    for line in open(template):
        line = re.sub(r"TABLE_HTML", f"{tableout}", line)
        line = re.sub(r'PAGE_TITLE', f'SARS-CoV-2: USA', line) 
        print(line, file=phpout, end='')

    ####
    # Create the table.html file for the country
    ####
    # Make row for each state
    for state in sorted(all_files):
        statefiles = all_files[state]
        make_row(state, statefiles, output)


if __name__=='__main__':
    main()
