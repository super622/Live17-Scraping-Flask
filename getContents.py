import requests
import asyncio
import json
import datetime

from datetime import date
from bs4 import BeautifulSoup
from googleapiclient.discovery import build  # Added
from google.oauth2 import service_account

class ContentSCraping:
    # Init
    def __init__(self, month, day):
        self.month = month
        self.day = day

    # Get Data from purpose site
    async def scanData(self):
        # Send get request
        async def send_request(p_url):
            url = p_url
            headers = {
                'Content-Type': 'application/json',
                "Accept": "application/json",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                json_response = response.text
                return json_response
            else:
                return ''

        # Append to array
        async def append_to_arr(store, data):
            for i in range(len(data)):
                store.append({
                    "UserID": data[i]['userInfo']['displayName'],
                    "Score": data[i]['score']
                })
            return store

        # Get Ranking List
        async def getRankingList(containerID):
            result = []
            url = f'https://api-dsa.17app.co/api/v1/leaderboards/eventory?containerID={containerID}&cursor=&count=100'
            nextCursor = 'init'
            while nextCursor != '':
                ranking_list = await send_request(url)
                ranking_list = json.loads(ranking_list)
                if 'data' in ranking_list:
                    await append_to_arr(result, ranking_list['data'])
                nextCursor = ranking_list['nextCursor']
                url = f'https://api-dsa.17app.co/api/v1/leaderboards/eventory?containerID={containerID}&cursor={nextCursor}&count=100'

            return result

        # Create New Google Sheet
        async def createGoogleSheet(filename):
            SCOPES = ['https://www.googleapis.com/auth/drive']  # Modified
            credentials = service_account.Credentials.from_service_account_file('elite-thunder-397502-23b91197a948.json', scopes=SCOPES)

            drive = build('drive', 'v3', credentials=credentials)
            file_metadata = {
                'name': filename,
                'parents': '11seQXAOIxXozPsCy7rG_CgJW0L8rdPmM',
                # 'parents': ['1EO1rQPYbTRGUQl4mGvkFAY2cm0zn947w'],
                'mimeType': 'application/vnd.google-apps.spreadsheet'
            }
            res = drive.files().create(body=file_metadata).execute()

            permission_body = {
                'role': 'reader',  # Set the desired role ('reader', 'writer', 'commenter', 'owner')
                'type': 'anyone',  # Share with anyone
            }
            drive.permissions().create(fileId=res['id'], body=permission_body).execute()
            return res['id']

        # Get Sheet ID by file name
        async def get_sheet_by_name(file_name, folder_name):
            drive_service = build('drive', 'v3', credentials=creds)
            sheet_id = None

            results = drive_service.files().list(q="name='" + file_name + "' and mimeType='application/vnd.google-apps.spreadsheet' and '" + folder_name + "' in parents",
                                                pageSize=10, fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])
            if not items:
                return ''
            else:
                sheet_id = items[0]['id']

            return sheet_id

        # Get Calculate result
        def calculate_date(year, month, day):
            date1 = datetime.strptime(f'{year}-{month}-{day}', '%Y-%m-%d')
            if(self.month > month):
                start_year = year - 1
            else:
                start_year = year
            date2 = datetime.strptime(f'{start_year}-{self.month}-{self.day}', '%Y-%m-%d')
            delta = date1 - date2
            return delta.days

        # Get event all url
        url = 'https://wap-api.17app.co/api/v1/event?region=JP&status=1'
        
        event_urls = None
        try:
            event_urls = await send_request(url)
        except Exception as e:
            print(f"An error occurred while fetching JSON for {url}: {e}")

        event_urls = json.loads(event_urls)
        event_urls = event_urls['events']['inProgress']

        event_url_arr = []
        if (len(event_urls) > 1):
            for i in range(len(event_urls)):
                event_url_arr.append(event_urls[i]['descriptionURL'])

        # Get containerID from event refrence api
        event_json_data = []
        for i in range(len(event_url_arr)):
            event_id = event_url_arr[i].split('/')[-1]
            json_url = f'https://webcdn.17app.co/campaign/projects/{event_id}/references.json'
            try:
                event_json_response = await send_request(json_url)
                if(event_json_response != ''):
                    data = json.loads(event_json_response)
                    data = data['fetcher']
                    # Get Current Date
                    current_date = date.today()
                    formatted_date = current_date.strftime("%Y-%m-%d")

                    # count of day from start date to cur date
                    cnt = 0

                    # Get event data.
                    event_data = []
                    for i in range(len(data)):
                        event_data.append({
                            "EventID": data[i]['id'][12:],
                            "ContainerID": data[i]['value']['args'][0],
                            "List": []
                        })

                    res = {
                        "ID": event_id,
                        "Date": formatted_date,
                        "Data": event_data,
                        "Count": cnt
                    }
                    event_json_data.append(res)
            except Exception as e:
                print(f"An error occurred while fetching JSON for {json_url}: {e}")

        # for i in range(len(event_json_data)):
        #     data = event_json_data[i]['Data']
        #     for j in range(len(data)):
        #         event_json_data[i]['Data'][j]['List'] = await getRankingList(data[j]['ContainerID'])

        for i in range(len(event_json_data)):
            current_year = datetime.datetime.now().year
            current_month = datetime.datetime.now().month
            current_day = datetime.datetime.now().day

            filename = f"Ranking_{event_json_data[i]['ID']}_{current_year}_{self.month}_{self.day}"

            if(self.month == current_month and self.day == current_day):
                # create new sheet
                sheetID = await createGoogleSheet(filename)
                event_json_data[i]['Count'] == 0
            else:
                folder_name = '11seQXAOIxXozPsCy7rG_CgJW0L8rdPmM'
                sheetID = await get_sheet_by_name(filename, folder_name)
                event_json_data[i]['Count'] = calculate_date(current_year, current_month, current_day)
        return event_json_data
    async def main(self):
        result = await self.scanData()
        return result

    # Run the main coroutine
    def run(self):
        result = asyncio.run(self.main())
        return result
