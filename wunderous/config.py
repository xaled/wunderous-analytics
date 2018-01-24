import json
import os, sys


def load_configs(config_file):
    global headers, config
    fin = open(config_file)
    config = json.load(fin)['drive']
    return config


if sys.argv[0] == '':
    CONFIG_FILE = os.path.join(os.path.abspath(sys.argv[0]), "wunderous.config.json")
else:
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "wunderous.config.json")
print(CONFIG_FILE)
config = load_configs(CONFIG_FILE)