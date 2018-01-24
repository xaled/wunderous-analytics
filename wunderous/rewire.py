#!/usr/bin/python3
from __future__ import print_function
import os
import json
import csv
import argparse
import logging
import time
from wunderous.config import config, OUT_DIR
from wunderous.drive import download_file
from wunderous.utils import save_csv, save_json, output_list, rewire_to_epoch, epoch_to_iso8601



logger = logging.getLogger(__name__)
HABBIT_HEADER = ['Name', 'Description', 'Current Streak', 'Longest Streak', 'Schedule', 'Unit Name', 'Target Count', 'Category', 'Target Days', 'Archived']
ROW_HEADER = ['Habit', 'Date', 'Status', 'Unit Name', 'Actual Count', 'Target Count', 'Note']
CSV_HEADER = ['timestamp','date','score']


def _get_csv_rows(csvfile):
    rows = list()
    with open(csvfile) as fin:
        reader = csv.reader(fin)
        for row in reader:
            rows.append(row)
        return rows


def _parse_csv_rows(rows):
    i =0
    while i < len(rows):
        i+=1
        if  i >= len(rows): break
        habbit_row = rows[i]
        entry_rows = list()
        i+=3
        while len(rows[i]) !=1:
            entry_rows.append(rows[i])
            i+=1
        i+=2
        yield habbit_row, entry_rows


def parse_file(csvfile):
    csv_rows = _get_csv_rows(csvfile)
    habbits = list()
    for habbit_row, entry_rows in _parse_csv_rows(csv_rows):
        habbit = dict(zip(HABBIT_HEADER, habbit_row))
        entries = [dict(zip(ROW_HEADER, entry_row)) for entry_row in entry_rows]
        habbit['entries'] = entries
        habbits.append(habbit)
    return habbits

def process_dates(data):
    earlier_day = (int(time.time())/86400)*86400
    for habbit in data:
        for entry in habbit['entries']:
            entry['date_timestamp'] = int(rewire_to_epoch(entry['Date']))
            if entry['date_timestamp'] < earlier_day:
                earlier_day = entry['date_timestamp']
    return data, earlier_day


def get_weights(habbit):
    return 1, -1


def parse_daily(data):
    data, earlier_day = process_dates(data)
    dates = dict()
    for d in range(earlier_day, int(time.time()), 86400):
        dates[d] = [d, epoch_to_iso8601(d)[:10], 0]
    for habbit in data:
        pos, neg = get_weights(habbit)
        for entry in habbit['entries']:
            if   entry["Status"] == "DONE": v = pos
            elif entry["Status"] == "FAIL": v = neg
            else: v = 0
            dates[entry['date_timestamp']][2] += v
    lst = sorted(dates.values(), key=lambda x:x[0])
    return lst


def get_rewire_data(download):
    # file_id, filename = load_configs(CONFIG_FILE)
    outfile = os.path.join(OUT_DIR, config['drive']['filename'])
    if download:
        download_file(outfile, config['drive']['file_id'])
    data = parse_file(outfile)
    return data


def main(args):
    data = get_rewire_data(not args.no_download)
    list_day = parse_daily(data)
    if not args.json_output is None:
        save_json(data, args.json_output)
    if not args.csv_output is None:
        save_csv(list_day, args.csv_output, CSV_HEADER)
    else:
        output_list(list_day, CSV_HEADER)