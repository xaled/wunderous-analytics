#!/usr/bin/python3
import argparse
import logging
from wunderous.config import SHEETS_DATA
from wunderous.sheet import main



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='rewire parse and export')
    # parser.add_argument('-C', '--config-file', default=CONFIG_FILE, action='store', help='Config file')
    # parser.add_argument('-j', '--json-output', default=SHEETS_DATA, action='store', help='json output')
    parser.add_argument('-S', '--sheet-db', default=SHEETS_DATA, action='store', help='json output')
    parser.add_argument('-c', '--csv-output', action='store', help='csv output')
    parser.add_argument('-d', '--debug', action="store_true", help='debugging logs')
    parser.add_argument('--no-download', action="store_true", help='don\'t download rewire export from drive')
    args = parser.parse_args()
    print(args)
    # SHEETS_DATA = args.json_output
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    main(args)
