from easilyb.os_ops.desktop import get_mouse_location, get_active_window
import logging
import time
logger = logging.getLogger(__name__)
import datetime

SLEEP_INTERVAL = 10 #10
INACTIVITY_THRESHOLD = 60 # 60
SYNC_INTERVAL = 600 # 600
TIMEDATE_FORMAT = "%d/%m/%Y %H:%M:%S"


class WindowActivityTracker:
    def __init__(self):
        self.last_mouse_mouvement = time.time()
        self.last_mouse_location = -1, -1
        self.current_activity = None
        self.current_activity_start = 0.0
        self.active = False

    def finished_activity(self, t):
        return self.current_activity[0], self.current_activity[1], \
               self.current_activity_start, t, t - self.current_activity_start

    def track(self):
        try:
            logger.info('starting window activity tracking')
            while True:
                t = time.time()
                mouse_location = get_mouse_location()
                if mouse_location != self.last_mouse_location:
                    self.last_mouse_mouvement = t
                    self.last_mouse_location = mouse_location
                    active = True
                elif not self.active or t - self.last_mouse_mouvement > INACTIVITY_THRESHOLD:
                    active = False
                    activity = None

                if active:
                    active_window = get_active_window()
                    activity = active_window['cmd'], active_window['title']

                    if activity != self.current_activity:
                        if self.current_activity is not None:
                            yield self.finished_activity(t)
                        self.current_activity = activity
                        self.current_activity_start = t
                elif self.current_activity is not None:
                    yield self.finished_activity(t)
                    self.current_activity = None
                self.active = active

                time.sleep(SLEEP_INTERVAL)
        except:
            logger.error('Exception while tracking windows activity', exc_info=True)
            raise
        finally:
            logger.info('stopping window activity tracking')


def get_hostname():
    import socket
    return socket.gethostname()


def sync(entries, spreadsheet_id):
    print("syncing to google")
    from wunderous.drive import append_sheet_values
    append_sheet_values(spreadsheet_id, "'current'!A2" , entries)


def main(spreadsheet_id):
    from easilyb.time_ops import format_utc_time
    hostname = get_hostname()
    tracker = WindowActivityTracker()
    entries = list()
    last_sync = time.time()
    for activity in tracker.track():
        entries.append([hostname, activity[0], activity[1],
                        format_utc_time(activity[2], TIMEDATE_FORMAT), format_utc_time(activity[3], TIMEDATE_FORMAT),
                        str(datetime.timedelta(seconds=int(activity[4])))])
        print(entries[-1])
        if time.time() - last_sync > SYNC_INTERVAL:
            sync(entries, spreadsheet_id)
            entries.clear()
            last_sync = time.time()