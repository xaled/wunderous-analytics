#!/usr/bin/python
import os
import json
from drive import download_file


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "wunderous.config.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "out")


def load_configs(config_file):
    global headers, config
    fin = open(config_file)
    config = json.load(fin)['drive']
    file_id = config['file_id']
    filename = config['filename']
    return file_id, filename





def get_rewire_data():
    file_id, filename = load_configs(CONFIG_FILE)
    outfile = os.path.join(OUT_DIR, filename)
    download_file(outfile, file_id)

def main():
    get_rewire_data()

main()