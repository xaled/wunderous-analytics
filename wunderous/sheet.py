from __future__ import print_function
import os
import json
import time
import re
import logging
from kutils.json_min_db import JsonMinConnexion

from wunderous.config import WEEK_OFFSET, DAY, WEEK, MONTHES, CSV_HEADER, config
from wunderous.drive import get_sheet_values, get_sheet_metadata, get_sheet_value, update_sheet_values, \
    append_sheet_values
from wunderous.utils import save_csv, output_list, weeksheet_to_epoch, epoch_to_iso8601, epoch_to_how_ods, \
    epoch_to_reward, rewire_to_epoch, epoch_to_iso8601date, iso8601date_to_epoch
from wunderous.rewire import get_rewire_data
from wunderous.git import get_git_dates
logger = logging.getLogger(__name__)


def load_configs():
    work_hours_sheet_id = config['drive']['work_hours_sheet_id']
    sheet_regex = config['drive']['sheet_regex']
    return work_hours_sheet_id, sheet_regex


def load_old_entries(sheet_data):
    if os.path.exists(sheet_data):
        with open(sheet_data) as fin:
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
            lst.append([d, epoch_to_iso8601(d)[:10], data[str(d)]])
        else:
            lst.append([d, epoch_to_iso8601(d)[:10], 0.0])
    return lst


def get_work_hours(work_hours_sheet_id, sheet_regex, data):
    sheets = [ str(sh['properties']['title']) for sh in get_sheet_metadata(work_hours_sheet_id)['sheets'] ]
    logger.debug("sheets: %s", sheets)
    for sheet in sheets:
        #w = w0 - i * WEEK
        #week = _format_week(w)
        match_ = re.match(sheet_regex, sheet)
        if match_:
            logger.debug("trying to extract sheet: %s", sheet)
            try:
                range_ = "'%s'!B2:O2" % sheet
                w = int(weeksheet_to_epoch(match_.group(1)))
                ret = get_sheet_values(work_hours_sheet_id, range_)
                values = ret['values'][0]
                for j in range(7):
                    try:
                        data['work_hours'][str(w + j * DAY)] = float(values[j * 2 + 1])
                    except:
                        data['work_hours'][str(w + j * DAY)] = 0.0
            except Exception as e:
                logger.error("Error trying to get data from sheet %s : %s", sheet, str(e), exc_info=True)

    return data


def get_sheet_action(sheet_date, sheet_sync_msg):
    if sheet_sync_msg == '' or time.time() - weeksheet_to_epoch(sheet_date) < 2*WEEK:
        return 'sync'
    elif sheet_sync_msg == 'synced':
        return 'delete'
    elif sheet_sync_msg == 'deleted':
        return 'ignore'


def parse_week_sheet(spreadsheet_id, sheet_regex):
    sheets = [ str(sh['properties']['title']) for sh in get_sheet_metadata(spreadsheet_id)['sheets'] ]
    logger.debug("sheets: %s", sheets)
    work_hours = dict()
    rewards = list()
    for sheet in sheets:
        #w = w0 - i * WEEK
        #week = _format_week(w)
        match_ = re.match(sheet_regex, sheet)
        if match_:
            action = get_sheet_action(get_sheet_value(spreadsheet_id, "'%s'!A1" % sheet),
                                      get_sheet_value(spreadsheet_id, "'%s'!D20" % sheet))
            logger.debug("action for sheet:%s is %s", sheet, action)
            if action == 'sync':
                work_hours_, rewards_, how_ods = sync_sheet(spreadsheet_id, sheet, match_.group(1))
                logger.debug("len(work_hours_)=%d, len(rewards_)=%d", len(work_hours_), len(rewards_))
                # logger.debug("workhours_=%s", work_hours_)
                # logger.debug("rewards_=%s", rewards_)
                # logger.debug("how_ods=%s", how_ods)
                update_sheet_values(spreadsheet_id, "'%s'!A23" % sheet, how_ods)
                work_hours.update(work_hours_)
                rewards.extend(rewards_)
                update_sheet_values(spreadsheet_id, "'%s'!D20" % sheet,
                                    [['synced','','last synced: %s' % epoch_to_how_ods(time.time())]])
            elif action == 'delete':
                update_sheet_values(spreadsheet_id, "'%s'!D20" % sheet, [['delete']])
    return work_hours, rewards


def sync_sheet(spreadsheet_id, sheet, sheet_date):
    work_hours = dict()
    rewards = list()
    how_ods = list()
    logger.debug("trying to extract sheet: %s", sheet)
    try:
        range_ = "'%s'!B2:O2" % sheet
        w = int(weeksheet_to_epoch(sheet_date))
        ret = get_sheet_values(spreadsheet_id, range_)
        values = ret['values'][0]
        for j in range(7):
            try:
                work_hours[str(w + j * DAY)] = float(values[j * 2 + 1])
            except:
                work_hours[str(w + j * DAY)] = 0.0
    except Exception as e:
        logger.error("Error trying to get data from sheet %s : %s", sheet, str(e), exc_info=True)
    try:
        range_ = "'%s'!B3:O19" % sheet
        w = int(weeksheet_to_epoch(sheet_date))
        ret = get_sheet_values(spreadsheet_id, range_)
        values = ret['values']
        for di in range(7):
            day = str(w + di * DAY)
            how_ods_work_hours, how_ods_home_hours, how_ods_done = 0,0,''
            for hi in range(17):
                is_home = _is_home(di, hi)
                try: task = values[hi][di*2]
                except: task = ''
                try: period = float(values[hi][di*2 +1])
                except: period = 0
                if task == '' or period == 0:
                    continue
                if is_home:
                    how_ods_home_hours += period
                else:
                    how_ods_work_hours += period
                how_ods_done += task + ', '
                if check_task_for_reward(task):
                    rewards.append(_work_reward(int(day), hi, task, period))

            how_ods_entry = [epoch_to_how_ods(int(day)), how_ods_work_hours, how_ods_home_hours, how_ods_done]
            how_ods.append(how_ods_entry)

    except Exception as e:
        logger.error("Error trying to get data from sheet %s : %s", sheet, str(e), exc_info=True)
    return work_hours, rewards, how_ods


def _work_reward(timestamp, hi, task, period):
    return [task + '_' + epoch_to_iso8601date(timestamp) + '#' + str(hi), epoch_to_reward(timestamp), 'hour_reward',
            str(period*config['rewards']['multiplicator']), "automatically added by wunderous.sheet"]


def _habit_reward(timestamp, habitname, value, count=1, unit='times'):
    return ["%s_%s#%s%s" % (habitname, epoch_to_iso8601date(timestamp), str(count), unit), epoch_to_reward(timestamp),
            'habit_reward', str(value), "automatically added by wunderous.sheet"]

def _git_reward(date, timestamp):
    return ["git_%s" % (date), epoch_to_reward(timestamp), 'git_reward', config['rewards']['git']['multiplicator'],
            "automatically added by wunderous.sheet"]


def _is_home(di, hi): # home or work
    if 0 < di < 6 and 1 < hi < 10:
        return False
    return True


def check_task_for_reward(task):
    if task in config['rewards']['projects']:
        return True
    return False


def get_git_rewards():
    rewards = list()
    t0 = time.time()
    dates_lines = get_git_dates()
    for date in dates_lines:
        date_epoch = iso8601date_to_epoch(date)
        if t0 - date_epoch < WEEK:
            rewards.append(_git_reward(date, date_epoch))
    return rewards


def _get_habit_type(habit):
    try:
        if habit['Name'] in config['rewards']['rewire']['custom']:
            return config['rewards']['rewire']['custom'][habit['Name']]['process_status'], \
                   config['rewards']['rewire']['custom'][habit['Name']]['multiplicator']
    except:
        pass

    try:
        if habit['Unit Name'] in config['rewards']['rewire']['custom_unit']:
            return config['rewards']['rewire']['custom_unit'][habit['Unit Name']]['process_status'], \
                   config['rewards']['rewire']['custom_unit'][habit['Unit Name']]['multiplicator']
    except:
        pass
    multiplicator = config['rewards']['rewire']['multiplicator']
    target_count = float(habit['Target Count'])
    if target_count > 0.0:
        return False, multiplicator / target_count
    else:
        return True, multiplicator


def get_rewire_rewards():
    rewards = list()
    rewire_data = get_rewire_data(True)
    t0 = time.time()
    #list_day = parse_daily(data)
    for habit in rewire_data:
        name = habit['Name']
        unit = habit['Unit Name']
        process_status, multiplicator = _get_habit_type(habit)
        for entry in habit['entries']:
            date_epoch = int(rewire_to_epoch(entry['Date']))
            if process_status:
                # if DAY < t0 - date_epoch < WEEK and entry['Status'] == 'DONE':
                if t0 - date_epoch < WEEK and entry['Status'] == 'DONE':
                    rewards.append(_habit_reward(date_epoch, name, multiplicator))
            else:
                count = float(entry['Actual Count'])
                # if 2*DAY < t0 - date_epoch < WEEK and count > 0.0:
                if 0 < t0 - date_epoch < WEEK and count > 0.0:
                    rewards.append(_habit_reward(date_epoch, name, multiplicator * count, count=count, unit=unit))
    return rewards


def get_new_rewards(rewards, old_rewards):
    new_rewards = list()
    for reward in rewards:
        entry = reward[0]
        if not entry in old_rewards:
            new_rewards.append(reward)

    return new_rewards


def process_rewards(rewards, old_rewards, spreadsheet_id):
    new_rewards = get_new_rewards(rewards, old_rewards)
    logger.info("appending %d rewards", len(new_rewards))
    # append_sheet_values(spreadsheet_id, "'rewards_log'!A3",  [['aaa', 'bbb', 'cccc', '12.5']])
    append_sheet_values(spreadsheet_id, "'rewards_log'!A3", new_rewards)
    for reward in new_rewards:
        old_rewards.append(reward[0])


def main(args):
    # data = load_old_entries(args.json_output)
    conn = JsonMinConnexion(args.sheet_db, create=True, template={'work_hours': {}, 'rewards':[]})
    data = conn.db
    logger.debug("there is already %d entries.", len(data))
    work_hours_sheet_id, sheet_regex = load_configs()
    if not args.no_download:
        # data = get_work_hours(work_hours_sheet_id, sheet_regex, data)
        work_hours, rewards_ = parse_week_sheet(work_hours_sheet_id, sheet_regex)
        data['work_hours'].update(work_hours)
        rewards = list(rewards_)

        # other rewards:
        rewards.extend(get_git_rewards())
        rewards.extend(get_rewire_rewards())

        logger.debug("rewards: %s", rewards)
        process_rewards(rewards, data['rewards'], work_hours_sheet_id)

    list_day = parse_work_hours_daily(data['work_hours'])
    # if not args.json_output is None:
    #    save_json(data, args.json_output)
    conn.save()
    if not args.csv_output is None:
        save_csv(list_day, args.csv_output, CSV_HEADER)
    else:
        output_list(list_day, CSV_HEADER)