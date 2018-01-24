import json
import os, sys


def load_configs(config_file):
    global headers, config
    fin = open(config_file)
    config = json.load(fin)
    return config


if sys.argv[0] == '':
    SCRIPT_DIR = os.path.abspath(sys.argv[0])
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

CONFIG_FILE = os.path.join(SCRIPT_DIR, "wunderous.config.json")
SHEETS_DATA = os.path.join(SCRIPT_DIR, "sheets.data.json")
OUT_DIR = os.path.join(SCRIPT_DIR, "out")
CSV_HEADER = ['timestamp', 'date', 'work_hours']

MONTHES = {'11': 'Nov', '10': 'Oct', '12': 'Dec', '1': 'Jan', '3': 'Mar', '2': 'Feb', '5': 'May', '4': 'Apr',
           '7': 'Jul', '6': 'Jun', '9': 'Sep', '8': 'Aug'}
DAY = 86400
WEEK = DAY * 7
WEEK_OFFSET = 3
MAX_ERROR = 4
# print(CONFIG_FILE)
config = load_configs(CONFIG_FILE)