#!/usr/bin/python

import requests
import json
import utils
import argparse
import logging
import csv
import time
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "wunderous.config.json")
CSV_HEADER = ['timestamp','date','created','completed', 'inbox_count']



def save_json(data, filepath):
    with open(filepath,'w') as fou:
        json.dump(data, fou, indent=3)

def save_csv(lst, filepath, headers=CSV_HEADER):
    with open(filepath,'w') as fou:
        csvwriter = csv.writer(fou)
        csvwriter.writerow(headers)
        for row in lst:
            csvwriter.writerow([str(item) for item in row])
def output_list(lst, headers=CSV_HEADER):
    print '\t'.join(headers)
    for row in lst:
        print '\t'.join([str(item) for item in row])

def parse_day(date):
    return int(utils.iso8601_to_epoch(date))/(86400)*(86400)



def parse_tasks(tasks):
    data_obj = dict()
    for task in tasks:
        created_day = parse_day(task["created_at"])
        if not created_day in data_obj:
            data_obj[created_day] = [0, 0]
        data_obj[created_day][0]+=1
        if "completed_at" in task:
            completed_day = parse_day(task["completed_at"])
            if not completed_day in data_obj:
                data_obj[completed_day] = [0, 0]
            data_obj[completed_day][1]+=1
    #lst = [[d, utils.epoch_to_iso8601(d)[:10], v[0],v[1]] for d,v in data_obj.items()]
    lst = sorted(data_obj.keys()) # sorted days from
    lst2 = list()
    inbox_count = 0
    for d in range(lst[0],int(time.time()), 86400):
        if d in data_obj:
            v = data_obj[d]
            inbox_count = inbox_count+v[0]-v[1]
            lst2.append([d, utils.epoch_to_iso8601(d)[:10], v[0], v[1], inbox_count])
        else:
            lst2.append([d, utils.epoch_to_iso8601(d)[:10], 0, 0, inbox_count])
    return lst2

def get_inbox_list_id():

    if "inbox_id" in config:
        return config["inbox_id"]
    logging.debug('getting inbox list_id')
    f = requests.get('https://a.wunderlist.com/api/v1/lists', headers=headers)
    lists = json.load(f.content)
    for l in lists:
        if l['title']=='inbox':
            return l['id']

def get_tasks(list_id, completed=None):
    if completed is None:
        params={'list_id':list_id}
    else:
        params={'list_id':list_id, 'completed':completed}
    f = requests.get('https://a.wunderlist.com/api/v1/tasks', headers=headers, params=params )
    ret = json.loads(f.content)
    logging.debug('got %d %s tasks from list: %d', len(ret), ("completed" if completed else "not completed"), list_id)
    return ret

def get_all_tasks(list_id=None):
    if list_id is None:
        list_id = get_inbox_list_id()
    new_tasks = get_tasks(list_id)
    completed_tasks = get_tasks(list_id, completed=True)
    return new_tasks  + completed_tasks

def load_configs(config_file):
    global headers, config
    fin = open(config_file)
    config = json.load(fin)['wunderlist']
    access_token = config['access_token']
    client_id = config['client_id']
    headers = {'X-Access-Token': access_token, 'X-Client-ID': client_id, 'Content-Type': 'application/json'}

def main(args):
    load_configs(args.config_file)
    logging.info("getting tasks")
    tasks = get_all_tasks()
    logging.info("got %d task", len(tasks))
    list_day = parse_tasks(tasks)
    if not args.json_output is None:
        save_json(tasks, args.json_output)
    if not args.csv_output is None:
        save_csv(list_day, args.csv_output)
    else:
        output_list(list_day)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Wunderlist parse and export')
    parser.add_argument('-C', '--config-file', default=CONFIG_FILE,  action='store', help='Config file')
    parser.add_argument('-j', '--json-output', action='store', help='json output')
    parser.add_argument('-c', '--csv-output', action='store', help='csv output')
    parser.add_argument('-d', '--debug', action="store_true", help='debugging logs')
    args = parser.parse_args()
    print args
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    main(args)