from __future__ import print_function
from time import gmtime, time, strptime, strftime, mktime, timezone
import json, csv


def epoch_to_iso8601(timestamp):
    try:
        mlsec = str(timestamp).split('.')[1][:3]
    except:
        mlsec = "000"
    mlsec = mlsec + "0" * (3 - len(mlsec))
    iso_str = strftime("%Y-%m-%dT%H:%M:%S.{}Z".format(mlsec), gmtime(timestamp))
    return iso_str


def iso8601_to_epoch(iso_str):
    str_time, mlsec = iso_str.split('.')
    mlsec = float(mlsec[:-1]) / 1000
    time_tuple = strptime(str_time + "UTC", "%Y-%m-%dT%H:%M:%S%Z")
    return mktime(time_tuple) - timezone + mlsec


def iso8601date_to_epoch(iso_str):
    time_tuple = strptime(iso_str, "%Y-%m-%d")
    return mktime(time_tuple) - timezone


def epoch_to_iso8601date(timestamp):
    iso_str = strftime("%Y-%m-%d", gmtime(timestamp))
    return iso_str


def epoch_to_how_ods(timestamp):
    iso_str = strftime("%a, %d, %b %Y", gmtime(timestamp))
    return iso_str


def epoch_to_reward(timestamp):
    iso_str = strftime("%d-%b-%Y", gmtime(timestamp))
    return iso_str


def rewire_to_epoch(str_time):
    time_tuple = strptime(str_time + "/UTC", "%d/%m/%Y/%Z")
    return mktime(time_tuple) - timezone


def weeksheet_to_epoch(str_date):
    time_tuple = strptime(str_date + "/UTC", "%d%b%Y/%Z")
    return mktime(time_tuple) - timezone


def save_json(data, filepath):
    with open(filepath, 'w') as fou:
        json.dump(data, fou, indent=3)


def save_csv(lst, filepath, headers):
    with open(filepath, 'w') as fou:
        csvwriter = csv.writer(fou)
        csvwriter.writerow(headers)
        for row in lst:
            csvwriter.writerow([str(item) for item in row])


def output_list(lst, headers):
    print('\t'.join(headers))
    for row in lst:
        print('\t'.join([str(item) for item in row]))
