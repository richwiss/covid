#!/usr/bin/env python
# coding: utf-8

import re
from bs4 import BeautifulSoup
import sys
import os
import csv
import argparse

## Parse the command line
def parse_cmdline():
    """ Get command-line arguments """
    parser = argparse.ArgumentParser(description='Parse Chester County Health Dept page')
    parser.add_argument('html', help="HTML file to read", type=argparse.FileType('r'))
    parser.add_argument('--csv', help="write CSV otuput", action='store_true')
    pargs = parser.parse_args()
    args = vars(pargs)
    return args


def clean_labels(labels, basetext, dates=False):
    rgx = re.compile(r'^' + basetext + r' (... \d\d, 202\d) ([\d,]+)$')

    first = True
    data = []
    for (i, label) in enumerate(labels):
        m = rgx.search(label)
        if m:
            (date, value) = m.groups()
            # In at least one file (2020-08-13), Feb 29 was the first date.
            if first and date != 'Mar 01, 2020':
                #print(f'Skipping {date}')
                continue
            first = False
            #print(f'Processing {date}')
            if dates:
                data.append(date)
            else:
                data.append(int(value.replace(',','')))
        else:
            print(f'ERROR: {label}')
    assert first == False
    return data


def main():
    args = parse_cmdline()
    filename = args['html'].name
    txtfile = filename.replace('.html', '.txt')

    soup=BeautifulSoup(open(filename), features="lxml")
    gs = soup.findAll('g', class_='amcharts-graph-column')
    labeled = [x for x in gs if x.has_attr('aria-label')]

    negatives = [l['aria-label'] for l in labeled if 'Total Negatives' in l['aria-label']]
    positives = [l['aria-label'] for l in labeled if 'Total All Positives' in l['aria-label']]
    deaths    = [l['aria-label'] for l in labeled if 'Total Deaths' in l['aria-label']]

    neg = clean_labels(negatives, 'Total Negatives')
    pos = clean_labels(positives, 'Total All Positives')
    rip = clean_labels(deaths, 'Total Deaths')
    dates = clean_labels(negatives, 'Total Negatives', dates=True)

    if args['csv']:
        csvfile = filename.replace('.html', '.csv')
        fh = open(csvfile,'w')
        writer = csv.writer(fh)
        header = ['Date', '#', 'Positives', 'Negatives', 'Deaths']
        writer.writerow(header)    

    ft = open(txtfile,'w')
    for i, (dt,p,n,d) in enumerate(zip(dates,pos, neg, rip)):
        row = [dt, i+1, p, n, d]
        if args['csv']:
            writer.writerow(row)
        print(f'{p}\t{n}\t{d}', file=ft)
    ft.close()

    if args['csv']:
        fh.close()


if __name__=='__main__':
    main()
