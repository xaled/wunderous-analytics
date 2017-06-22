#!/usr/bin/python
import os
import json
from drive import get_sheet_values, get_sheet_metadata
import csv
import argparse
import logging
import utils
import time

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "wunderous.config.json")
SHEETS_DATA = os.path.join(os.path.dirname(__file__), "sheets.data.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
CSV_HEADER = ['timestamp', 'date', 'work_hours']

MONTHES = {'11': 'Nov', '10': 'Oct', '12': 'Dec', '1': 'Jan', '3': 'Mar', '2': 'Feb', '5': 'May', '4': 'Apr',
           '7': 'Jul', '6': 'Jun', '9': 'Sep', '8': 'Aug'}
DAY = 86400
WEEK = DAY * 7
WEEK_OFFSET = 3
MAX_ERROR = 4


def load_configs(config_file):
    global headers, config
    fin = open(config_file)
    config = json.load(fin)['drive']
    work_hours_sheet_id = config['work_hours_sheet_id']
    return work_hours_sheet_id


def load_old_entries():
    if os.path.exists(SHEETS_DATA):
        with open(SHEETS_DATA) as fin:
            return json.load(fin)
    return {'work_hours': {}}


def _get_week(timestamp):
    return int(timestamp - WEEK_OFFSET * DAY) / WEEK * WEEK + WEEK_OFFSET * DAY


def _format_week(week):
    str1 = time.strftime('%-d/%-m/%Y', time.gmtime(week))
    d, m, y = str1.split('/')
    m = MONTHES[m]
    return d + m + y


def parse_work_hours_daily(data):
    earlier_day =  sorted([int(k) for k in data.keys()])[0]
    lst= []
    for d in range(earlier_day, int(time.time()), DAY):
        if str(d) in data:
            lst.append([d, utils.epoch_to_iso8601(d)[:10], data[str(d)]])
        else:
            lst.append([d, utils.epoch_to_iso8601(d)[:10], 0])
    return lst



def get_work_hours(work_hours_sheet_id, data):
    w0 = _get_week(time.time())
    error = 0
    i = 0
    sheets = [ str(sh['properties']['title']) for sh in get_sheet_metadata(work_hours_sheet_id)['sheets'] ]
    logging.debug("sheets: %s", sheets)
    while error < MAX_ERROR:
        w = w0 - i * WEEK
        week = _format_week(w)
        range_ = "'%s'!B2:O2" % week

        if week in sheets:
            ret = get_sheet_values(work_hours_sheet_id, range_)
            values = ret['values'][0]
            for j in range(7):
                try:
                    data['work_hours'][str(w + j * DAY)] = int(values[j * 2 + 1])
                except:
                    data['work_hours'][str(w + j * DAY)] = 0
            error = 0
        else:
            error += 1
        i += 1
    return data


def main(args):
    data = load_old_entries()
    work_hours_sheet_id = load_configs(CONFIG_FILE)

    data = get_work_hours(work_hours_sheet_id, data)
    print data
    list_day = parse_work_hours_daily(data['work_hours'])
    if not args.json_output is None:
        utils.save_json(data, args.json_output)
    if not args.csv_output is None:
        utils.save_csv(list_day, args.csv_output, CSV_HEADER)
    else:
        utils.output_list(list_day, CSV_HEADER)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='rewire parse and export')
    parser.add_argument('-C', '--config-file', default=CONFIG_FILE, action='store', help='Config file')
    parser.add_argument('-j', '--json-output', default=SHEETS_DATA, action='store', help='json output')
    parser.add_argument('-c', '--csv-output', action='store', help='csv output')
    parser.add_argument('-d', '--debug', action="store_true", help='debugging logs')
    args = parser.parse_args()
    print args
    SHEETS_DATA = args.json_output
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    main(args)
