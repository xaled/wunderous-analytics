import os
import httplib2
from oauth2client.file import Storage
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
import json




OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
CREDS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "wunderous.config.json")


def load_configs(config_file):
    global headers, config
    fin = open(config_file)
    config = json.load(fin)['drive']
    client_secret = config['client_secret']
    client_id = config['client_id']
    return client_id, client_secret

def init_service():
    storage = Storage(CREDS_FILE)
    credentials = storage.get()

    if credentials is None:
        # Run through the OAuth flow and retrieve credentials
        client_id, client_secret = load_configs(CONFIG_FILE)
        flow = OAuth2WebServerFlow(client_id, client_secret, OAUTH_SCOPE, REDIRECT_URI)
        authorize_url = flow.step1_get_authorize_url()
        print 'Go to the following link in your browser: ' + authorize_url
        code = raw_input('Enter verification code: ').strip()
        credentials = flow.step2_exchange(code)
        storage.put(credentials)

    # Create an httplib2.Http object and authorize it with our credentials
    http = httplib2.Http()
    http = credentials.authorize(http)

    drive_service = build('drive', 'v2', http=http)
    return drive_service


def list_files(service):
    page_token = None
    while True:
        param = {}
        if page_token:
            param['pageToken'] = page_token
        files = service.files().list(**param).execute()
        for item in files['items']:
            yield item
        page_token = files.get('nextPageToken')
        if not page_token:
            break
def _download_file(drive_service, download_url, outfile):
    resp, content = drive_service._http.request(download_url)
    if resp.status == 200:
        with open(outfile, 'wb') as f:
            f.write(content)
        print "OK"
        return
    else:
        raise Exception("ERROR downloading %s, response code is not 200!" % outfile)

def download_file(outfile, fileid):
    drive_service = init_service()
    for item in list_files(drive_service):
        if fileid == item.get('id'):
            if 'downloadUrl' in item:
                _download_file(drive_service, item['downloadUrl'], outfile)
                return
            else:
                raise Exception("No download link is found for file:  %s"%item['title'])
    raise Exception("No file with id: %s is found "%fileid)