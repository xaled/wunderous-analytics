import os
import sys
import httplib2
from oauth2client.file import Storage
from apiclient import discovery
from oauth2client.client import OAuth2WebServerFlow
from wunderous.config import config

OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
SHEETS_OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/spreadsheets.readonly'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
CREDS_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'credentials.json')
SHEETS_CREDS_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'sheets_credentials.json')
# CONFIG_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "wunderous.config.json")
sheet_service = None
drive_service = None


def load_configs():
    client_secret = config['client_secret']
    client_id = config['client_id']
    return client_id, client_secret


def init_drive_service():
    global drive_service
    if drive_service:
        return drive_service
    storage = Storage(CREDS_FILE)
    credentials = storage.get()

    if credentials is None:
        # Run through the OAuth flow and retrieve credentials
        client_id, client_secret = load_configs()
        flow = OAuth2WebServerFlow(client_id, client_secret, OAUTH_SCOPE, REDIRECT_URI)
        authorize_url = flow.step1_get_authorize_url()
        print('Go to the following link in your browser: ' + authorize_url)
        code = input('Enter verification code: ').strip()
        credentials = flow.step2_exchange(code)
        storage.put(credentials)

    # Create an httplib2.Http object and authorize it with our credentials
    http = httplib2.Http()
    http = credentials.authorize(http)

    drive_service = discovery.build('drive', 'v2', http=http)
    return drive_service


def init_sheet_service():
    global sheet_service
    if sheet_service:
        return sheet_service
    storage = Storage(SHEETS_CREDS_FILE)
    credentials = storage.get()

    if credentials is None:
        # Run through the OAuth flow and retrieve credentials
        client_id, client_secret = load_configs()
        flow = OAuth2WebServerFlow(client_id, client_secret, SHEETS_OAUTH_SCOPE, REDIRECT_URI)
        authorize_url = flow.step1_get_authorize_url()
        print('Go to the following link in your browser: ' + authorize_url)
        code = input('Enter verification code: ').strip()
        credentials = flow.step2_exchange(code)
        storage.put(credentials)

    # Create an httplib2.Http object and authorize it with our credentials
    http = httplib2.Http()
    http = credentials.authorize(http)

    sheet_service = discovery.build('sheets', 'v4', http=http)
    return sheet_service


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
        print("OK")
        return
    else:
        raise Exception("ERROR downloading %s, response code is not 200!" % outfile)


def download_file(outfile, fileid):
    drive_service = init_sheet_service()
    for item in list_files(drive_service):
        if fileid == item.get('id'):
            if 'downloadUrl' in item:
                _download_file(drive_service, item['downloadUrl'], outfile)
                return
            else:
                raise Exception("No download link is found for file:  %s" % item['title'])
    raise Exception("No file with id: %s is found " % fileid)


def get_sheet_metadata(spreadsheet_id):
    sheet_service = init_sheet_service()
    sheet_metadata = sheet_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return sheet_metadata


def get_sheet_values(spreadsheet_id, range_):
    sheet_service = init_sheet_service()
    request = sheet_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_,
                                                        valueRenderOption='FORMATTED_VALUE',
                                                        dateTimeRenderOption='SERIAL_NUMBER')
    response = request.execute()
    return response


def update_sheet_values(spreadsheet_id, range_, value_input_option, body):
    sheet_service = init_sheet_service()
    result = sheet_service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_,
                                                          valueInputOption=value_input_option, body=body).execute()
    return result.get('updatedCells')

