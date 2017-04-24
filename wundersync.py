import requests
import json

AUTH_CONFIG_FILE = "auth.config.json"
TASKS_FILE = "tasks.data.json"
DAY_CSV_FILE = "day.data.csv"
WEEK_CSV_FILE = "week.data.csv"
fin = open(AUTH_CONFIG_FILE)
authconfig = json.load(fin)
access_token = authconfig['access_token']
client_id = authconfig['client_id']
headers={'X-Access-Token': access_token, 'X-Client-ID': client_id, 'Content-Type' : 'application/json'}

def save_json(data, filepath):
    with open(filepath,'w') as fou:
        json.dump(data, fou, indent=3)
def save_csv(lst, filepath, headers=None):
    with open(filepath,'w') as fou:
        if not headers is None:
            fou.write(",".join(['"'+('%s'%h).replace("\\","\\\\").replace("\"","\\\"")+'"' for h in headers]) + "\n")
        for row in lst:
            fou.write(",".join(['"'+('%s'%cell).replace("\\","\\\\").replace("\"","\\\"")+'"' for cell in row]) + "\n")
def parse_day(date):
    return date[:10]



def parse_tasks(tasks, span="day"):
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
    lst = [[d,v[0],v[1]] for d,v in data_obj.items()]
    # TODO: sort and fill gap
    return lst

def get_inbox_list_id():
    if "inbox_id" in authconfig:
        return authconfig["inbox_id"]
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
    return json.loads(f.content)

def get_all_tasks(list_id=None, all_lists=False):
    if list_id is None:
        list_id = get_inbox_list_id()
    new_tasks = get_tasks(list_id)
    completed_tasks = get_tasks(list_id, completed=True)
    return new_tasks  + completed_tasks

def main():
    tasks = get_all_tasks()
    save_json(tasks, TASKS_FILE)
    list_day = parse_tasks(tasks, span="day")
    save_csv(list_day, DAY_CSV_FILE)
    #list_week = parse_tasks(tasks, span="week")
    #save_csv(list_week, WEEK_CSV_FILE)


if __name__=="__main__":
    main()