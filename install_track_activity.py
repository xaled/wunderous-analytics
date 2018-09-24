from wunderous.drive import init_sheet_service, SHEETS_CREDS_FILE
import os
import sys
service_file_content = """[Unit]
Description=Track Activity Service

[Service]
Type=oneshot
ExecStart=/bin/bash {start_script_path}

[Install]
WantedBy=multi-user.target"""

start_script_content = """#!/bin/bash
su {user} -c 'python3 {script_path} {ssid}'
"""


def _system(cmd):
    print(cmd)
    os.system(cmd)


if __name__ == "__main__":
    path = os.path.dirname(os.path.realpath(sys.argv[0]))
    if not os.path.exists(SHEETS_CREDS_FILE):
        init_sheet_service()

    user = os.getenv('USER')
    ssid = input("What is the spreadsheet id?")
    script_path = os.path.join(path, 'track_activity.py')

    start_script_path = os.path.join(path, 'out/track_activity.start.sh')
    with open(start_script_path, 'w') as fou:
        fou.write(start_script_content.format(user=user, script_path=script_path, ssid=ssid))
    _system('chmod +x "%s"' %  start_script_path)

    service_file_path = os.path.join(path, 'out/track_activity.service')
    with open(service_file_path, 'w') as fou:
        fou.write(service_file_content.format(start_script_path=start_script_path))

    _system('sudo systemctl enable %s' % service_file_path)
    _system('sudo systemctl start track_activity.service' )


