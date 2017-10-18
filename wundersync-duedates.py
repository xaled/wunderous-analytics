#!/usr/bin/python

import requests
import json
import utils
import argparse
import time
import os

import logging
logger = logging.getLogger(__name__)

TASKS_DATA = os.path.join(os.path.dirname(__file__), "tasks.json")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "wunderous.config.json")
CSV_HEADER = ['timestamp', 'date', 'created', 'completed', 'inbox_count']
DAY = 24 * 3600
MAX_FUTURE_DAYS = 100
RESEARCH_LIST_ID = 320002049
MAX_INBOX_TASKS = 1
MAX_RESEARCH_TASKS = 1
MODIFY_DUEDATES = True


def load_old_entries(sheet_data):
    if os.path.exists(sheet_data):
        with open(sheet_data) as fin:
            return json.load(fin)
    return []


def parse_day(date):
    return int(utils.iso8601_to_epoch(date)) / (86400) * (86400)


def parse_tasks(tasks):
    data_obj = dict()
    for task in tasks:
        created_day = parse_day(task["created_at"])
        if not created_day in data_obj:
            data_obj[created_day] = [0, 0]
        data_obj[created_day][0] += 1
        if "completed_at" in task:
            completed_day = parse_day(task["completed_at"])
            if not completed_day in data_obj:
                data_obj[completed_day] = [0, 0]
            data_obj[completed_day][1] += 1
    # lst = [[d, utils.epoch_to_iso8601(d)[:10], v[0],v[1]] for d,v in data_obj.items()]
    lst = sorted(data_obj.keys())  # sorted days from
    lst2 = list()
    inbox_count = 0
    for d in range(lst[0], int(time.time()), 86400):
        if d in data_obj:
            v = data_obj[d]
            inbox_count = inbox_count + v[0] - v[1]
            lst2.append([d, utils.epoch_to_iso8601(d)[:10], v[0], v[1], inbox_count])
        else:
            lst2.append([d, utils.epoch_to_iso8601(d)[:10], 0, 0, inbox_count])
    return lst2


def get_list_id(list_title):
    logging.debug('getting list_id of: %s', list_title)
    f = requests.get('https://a.wunderlist.com/api/v1/lists', headers=headers)
    lists = json.loads(f.content)
    for l in lists:
        if l['title'] == list_title:
            return l['id']
    return None


def print_list_ids():
    logging.debug('getting list_ids')
    f = requests.get('https://a.wunderlist.com/api/v1/lists', headers=headers)
    lists = json.loads(f.content)
    for l in lists:
        print l['title'], ':', l['id']


def get_inbox_list_id():
    if "inbox_id" in config:
        return config["inbox_id"]
    return get_list_id('inbox')


def get_tasks(list_id, completed=None):
    if completed is None:
        params = {'list_id': list_id}
    else:
        params = {'list_id': list_id, 'completed': completed}
    f = requests.get('https://a.wunderlist.com/api/v1/tasks', headers=headers, params=params)
    ret = json.loads(f.content)
    logging.debug('got %d %s tasks from list: %d', len(ret), ("completed" if completed else "not completed"), list_id)
    return ret


def get_all_tasks(list_id=None):
    if list_id is None:
        list_id = get_inbox_list_id()
    new_tasks = get_tasks(list_id)
    completed_tasks = get_tasks(list_id, completed=True)
    return new_tasks + completed_tasks


def load_configs(config_file):
    global headers, config
    fin = open(config_file)
    config = json.load(fin)['wunderlist']
    access_token = config['access_token']
    client_id = config['client_id']
    headers = {'X-Access-Token': access_token, 'X-Client-ID': client_id, 'Content-Type': 'application/json'}


def filter_routines(tasks):
    routines_set = set()
    to_remove = list()
    for task in tasks:
        if task['completed'] and '#routine' in task['title'].split():
            key_ = task['title'] + '.' + task['completed_at'][:10]
            if key_ in routines_set:
                to_remove.append(task)
            else:
                routines_set.add(key_)
    res = list(tasks)
    print len(res)
    for task in to_remove:
        res.remove(task)
    logging.info("removed %d duplicate routine entry from data" % len(to_remove))
    print len(res)
    return res


def _merge(tasks1, tasks2):
    tasks = list(tasks1)
    ids = [t['id'] for t in tasks]
    for task in tasks2:
        if not task['id'] in ids:
            tasks.append(task)
    return tasks


def main(args):
    data = load_old_entries(args.json_output)
    load_configs(args.config_file)
    if not args.no_download:
        logging.info("getting tasks")
        tasks = get_all_tasks()
        logging.info("got %d task", len(tasks))
    else:
        tasks = []
    tasks = _merge(data, tasks)
    tasks = filter_routines(tasks)
    list_day = parse_tasks(tasks)
    if not args.json_output is None:
        utils.save_json(tasks, args.json_output)
    if not args.csv_output is None:
        utils.save_csv(list_day, args.csv_output, CSV_HEADER)
    else:
        utils.output_list(list_day, CSV_HEADER)


"""
if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Wunderlist parse and export')
    parser.add_argument('-C', '--config-file', default=CONFIG_FILE,  action='store', help='Config file')
    parser.add_argument('-j', '--json-output', default=TASKS_DATA, action='store', help='json output')
    parser.add_argument('-c', '--csv-output', action='store', help='csv output')
    parser.add_argument('-d', '--debug', action="store_true", help='debugging logs')
    parser.add_argument('--no-download', action="store_true", help='don\'t download rewire export from drive')
    args = parser.parse_args()
    print args
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    main(args)
"""

def get_capacities(inbox_tasks, research_tasks, min_date, max_date):
    dates = [utils.epoch_to_iso8601date(d) for d in range(min_date, max_date+1, DAY)]
    capacities = {d:[MAX_INBOX_TASKS, MAX_RESEARCH_TASKS] for d in dates}
    for task in inbox_tasks:
        if "due_date" in task and task["due_date"] in capacities:
            capacities[task["due_date"]][0] -= 1
    for task in research_tasks:
        if "due_date" in task and task["due_date"] in capacities:
            capacities[task["due_date"]][1] -= 1
    for d in capacities:
        if capacities[d][0]< 0:
            capacities[d][0] = 0
        if capacities[d][1] < 0:
            capacities[d][1] = 0
    return capacities


def get_operations(inbox_tasks, research_tasks, min_date, max_date):
    capacities = get_capacities(inbox_tasks, research_tasks, min_date, max_date)
    inbox_tasks_sorted = sorted([task for task in inbox_tasks  if not "due_date" in task], key=lambda x:x['created_at'][:10])
    research_tasks_sorted = sorted([task for task in research_tasks  if not "due_date" in task], key=lambda x:x['created_at'][:10])
    inbox_tasks_index = 0
    research_tasks_index = 0
    operations = list()
    for d in capacities:
        ci, cr  = capacities[d][0], capacities[d][1]
        for i in range(ci):
            if inbox_tasks_index < len(inbox_tasks_sorted):
                operations.append((d, inbox_tasks_sorted[inbox_tasks_index],))
                inbox_tasks_index+=1
        for i in range(cr):
            if research_tasks_index < len(research_tasks_sorted):
                operations.append((d, research_tasks_sorted[research_tasks_index],))
                research_tasks_index+=1
    return operations


def update_duedate(task, new_duedate):
    logger.debug("updating duedate for task_id=%d, new duedate=%s", task['id'], new_duedate)
    if MODIFY_DUEDATES:
        data = {'revision': task['revision'], 'due_date': new_duedate}
        res = requests.patch('https://a.wunderlist.com/api/v1/tasks/%d'%task['id'], headers=headers, json=data)
        logger.debug("res.status_code=%d,  res.content=%s", res.status_code, res.content)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    load_configs(CONFIG_FILE)
    inbox_tasks = get_tasks(get_inbox_list_id())
    research_tasks = get_tasks(RESEARCH_LIST_ID)
    due_dates = dict()
    for task in inbox_tasks+research_tasks:
        if "due_date" in task:
            if not task["due_date"] in due_dates:
                due_dates[task["due_date"]] = 0
            due_dates[task["due_date"]] += 1

    # adding empty days to the list
    due_dates_epoch = sorted([int(utils.iso8601date_to_epoch(dd)) for dd in due_dates.keys()])
    min_date = due_dates_epoch[0]
    today = (int(time.time()) / DAY) * DAY
    max_date = today + MAX_FUTURE_DAYS * DAY
    for d in range(min_date, max_date + 1, DAY):
        isod = utils.epoch_to_iso8601date(d)
        if not isod in due_dates:
            due_dates[isod] = 0

    # Printing due dates
    due_dates_sorted = sorted(due_dates.items(), key=lambda x: x[0])
    for date, count in due_dates_sorted:
        print date, ":", count

    #print "--"
    #print_list_ids()

    # apply operations

    operations = get_operations(inbox_tasks, research_tasks, today, max_date)
    for op in operations:
        dd, task = op
        #print "change due date for task_id=%d, title=%s, created_at=%s, new_due_date=%s"%(task['id'], task['title'][:20], task['created_at'][:20], dd)
        update_duedate(task, dd)


    # due dates spreadsheet
    inbox_tasks = get_tasks(get_inbox_list_id())
    research_tasks = get_tasks(RESEARCH_LIST_ID)
    print "----------------DUE-DATES"
    print "-----------------------------------"
    print "due date\ttitle"
    for task in inbox_tasks+research_tasks:
        if "due_date" in task:
            print "%s\t%s" % (task["due_date"], task["title"])