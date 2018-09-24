#!/usr/bin/python3
from wunderous.drive import init_sheet_service, SHEETS_CREDS_FILE
import os
import sys

start_script_content = "#!/bin/bash\npython3 {script_path} {ssid};\n"


def _system(cmd):
    print(cmd)
    os.system(cmd)


if __name__ == "__main__":
    path = os.path.dirname(os.path.realpath(sys.argv[0]))
    if not os.path.exists(SHEETS_CREDS_FILE):
        init_sheet_service()

    # user = os.getenv('USER')
    ssid = input("What is the spreadsheet id?")
    script_path = os.path.join(path, 'track_activity.py')

    out_path = os.path.join(path, 'out')
    if not os.path.exists(out_path):
        os.mkdir(out_path)
    start_script_path = os.path.join(path, 'out/track_activity.start.sh')
    with open(start_script_path, 'w') as fou:
        fou.write(start_script_content.format(script_path=script_path, ssid=ssid))
    _system('chmod +x "%s"' %  start_script_path)

