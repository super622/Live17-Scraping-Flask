import re
import sys
import time
import requests
import asyncio
import json
import datetime
import gspread
import pytz

from googleapiclient.discovery import build  # Added
from google.oauth2 import service_account

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class Chating:

    # Init
    def __init__(self, end_date_month, end_date_day, end_time_hour, end_time_minute, nick_url):

        self.name = nick_url
        self.end_date_month = end_date_month
        self.end_date_day = end_date_day
        self.end_time_hour = end_time_hour
        self.end_time_minute = end_time_minute
        self.start_year = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).year
        self.start_month = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).month
        self.start_day = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).day

    # Get Data from Chating panel
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
            
        # Add gif user
        async def append_to_gifusers(gifs_users, res):
            flag = False
            for user in gifs_users:
                if(user['UserName'] == res['UserName'] and user['GifType'] == res['GifType']):
                    user['Coin'] = int(res['Coin']) * int(user['Gif_Count'] + 1)
                    user['Gif_Count'] += 1
                    flag = True

            if flag:
                return gifs_users
            else:
                gifs_users.append(res)
                return gifs_users
            
        # add gif list
        async def append_to_gif(gif_list, gif_type, coin):
            flag = False
            for gif in gif_list:
                if(gif[0] == gif_type):
                    gif[2] = int(gif[2]) + int(coin)
                    gif[1] = int(gif[1]) + 1
                    flag = True
                
            if(flag):
                return gif_list
            else:
                gif_list.append([gif_type, 1, coin])
                return gif_list

        # find special gif user
        async def find_in_gifusers(gifs_users, user_name):
            for user in gifs_users:
                if(user['UserName'] == user_name):
                    return user
            res = {
                "UserName": '',
                "GifType": '',
                "Gif_Count": 0,
                "Coin": 0
            }
            return res
        
        # Create New Google Sheet
        async def createGoogleSheet(filename):
            SCOPES = ['https://www.googleapis.com/auth/drive']  # Modified
            credentials = service_account.Credentials.from_service_account_file('service-account.json', scopes=SCOPES)

            drive = build('drive', 'v3', credentials=credentials)
            file_metadata = {
                'name': filename,
                'parents': ['1IkovXnPZ8y-aIgR6MnbykOVfXC34CJhT'],
                'mimeType': 'application/vnd.google-apps.spreadsheet'
            }
            res = drive.files().create(body=file_metadata).execute()
            permission_body = {
                'role': 'writer',  # Set the desired role ('reader', 'writer', 'commenter', 'owner')
                'type': 'anyone',  # Share with anyone
            }
            drive.permissions().create(fileId=res['id'], body=permission_body).execute()

            return res['id']

        # Get Sheet ID by file name in special folder
        async def get_sheet_by_name(file_name, folder_name):
            SCOPES = ['https://www.googleapis.com/auth/drive']  # Modified
            credentials = service_account.Credentials.from_service_account_file('service-account.json', scopes=SCOPES)
            drive_service = build('drive', 'v3', credentials=credentials)

            results = drive_service.files().list(q="name='" + file_name + "' and mimeType='application/vnd.google-apps.spreadsheet' ",
                                    pageSize=10, fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])
            if not items:
                return ''
            else:
                return items[0]['id']

        # add git and snack user
        async def append_to_snack_gifusers(snack_gifs_users, gifs_user, username, snack_cnt):
            flag = False
            x = 1
            for user in snack_gifs_users:
                if(user['UserName'] == username):
                    user['Gif_Count'] = gifs_user['Gif_Count']
                    user['Coin'] = ((int(user['Snack_Count']) + int(snack_cnt)) * x) + int(gifs_user['Coin'])
                    user['Snack_Count'] = int(snack_cnt) + int(user['Snack_Count'])
                    flag = True

            if flag:
                return snack_gifs_users
            else:
                res = {
                    "UserName": username,
                    "Gif_Count": gifs_user['Gif_Count'],
                    "Snack_Count": int(snack_cnt),
                    "Coin": (int(snack_cnt) * x) + int(gifs_user['Coin'])
                }
                snack_gifs_users.append(res)
                return snack_gifs_users

        url = 'https://wap-api.17app.co/api/v1/cells?count=0&cursor=&paging=1&region=JP&tab=hot'

        liveStreamIDs = None
        try:
            liveStreamIDs = await send_request(url)
            liveStreamIDs = json.loads(liveStreamIDs)
            liveStreamIDs = liveStreamIDs['cells']
        except Exception as e:
            print(f"An error occurred while fetching JSON for {url}: {e}")
        
        if(liveStreamIDs == None):
            return 'Not exist'
        
        live_stream_id_arr = []
        for i in range(len(liveStreamIDs)):
            if('stream' in liveStreamIDs[i]):
                if liveStreamIDs[i]['stream']['userInfo']['displayName'] == self.name:
                    live_stream_id_arr.append(liveStreamIDs[i]['stream']['liveStreamID'])

        if len(live_stream_id_arr) == 0:
            return 'failure - not exist live stream id'
        print(live_stream_id_arr)
        for live_room_id in live_stream_id_arr:
            url = f'https://17.live/ja/live/{live_room_id}'

            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            # # Maximize the browser window
            # browser.maximize_window()

            # # Bring the browser window to the front
            # browser.execute_script("window.focus();")
            # time.sleep(3)
            
            browser.get(url)
            time.sleep(10)

            while True:
                time.sleep(5)
                chating_panel = browser.find_elements('css selector', '.ChatList__ListWrapper-sc-733d46-1')
                if(len(chating_panel) > 0):
                    snack_cnt = 0
                    gif_man_cnt = 0
                    coin_cnt = 0
                    score = ''
                    gifs_users = []
                    snack_gifs_users = []
                    gifs_list = []
                    total_result = []

                    chating_elements = browser.find_elements('css selector', '.Chat__ChatWrapper-sc-clenhv-0')
                    for chat_element in chating_elements:
                        if len(chat_element.find_elements('css selector', '.GiftItem__GiftIcon-sc-g419cs-0')) > 0:
                            name_element = chat_element.find_elements('css selector', '.ChatUserName__NameWrapper-sc-1ca2hpy-0')
                            user_name = name_element[0].text
                            gif_element = chat_element.find_elements('css selector', '.Chat__ContentWrapper-sc-clenhv-1')
                            gif_type = gif_element[0].text
                            coin_element = re.search(r'\((\d+)\)', gif_type)
                            coin = 0
                            if coin_element:
                                coin = coin_element.group(1)

                            res = {
                                "UserName": user_name,
                                "GifType": gif_type,
                                "Gif_Count": 1,
                                "Coin": coin
                            }
                            gifs_list = await append_to_gif(gifs_list, gif_type, coin)
                            gifs_users = await append_to_gifusers(gifs_users, res)

                            gif_man_cnt = len(gifs_users)

                        if len(chat_element.find_elements('css selector', '.LaborReward__ControlledText-sc-cxndew-0')) > 0:
                            name_element = chat_element.find_elements('css selector', '.ChatUserName__NameWrapper-sc-1ca2hpy-0')
                            user_name = name_element[0].text
                            gif_state = await find_in_gifusers(gifs_users, user_name)
                            print(gif_state)
                            snack_cnt_element = chat_element.find_elements('css selector', '.LaborReward__ControlledText-sc-cxndew-0')
                            snack_cnt_element = snack_cnt_element[0].text
                            snack_cnt = re.findall(r'\d+', snack_cnt_element)
                            snack_cnt = snack_cnt[0]
                            snack_gifs_users = await append_to_snack_gifusers(snack_gifs_users, gif_state, user_name, snack_cnt)

                            gif_man_cnt = len(gifs_users)
                            snack_cnt = len(snack_gifs_users)

                    for user in gifs_users:
                        coin_cnt += int(user['Coin'])

                    for user in snack_gifs_users:
                        if(int(user['Gif_Count']) == 0):
                            coin_cnt += int(user['Coin'])

                    length = len(gifs_list) if len(gifs_list) > len(snack_gifs_users) else len(snack_gifs_users)
                    temp_arr = None

                    if(length == len(gifs_users)):
                        temp_arr = gifs_users
                    else:
                        temp_arr = snack_gifs_users

                    i = 0
                    for i in range(len(temp_arr)):
                        res_arr = None
                        if(i >= len(gifs_users)):
                            res_arr = ['', '', '', '', snack_gifs_users[i]['UserName'], snack_gifs_users[i]['Snack_Count'], snack_gifs_users[i]['Gif_Count'], snack_gifs_users[i]['Coin']]
                        elif(i >= len(snack_gifs_users)):
                            res_arr = [gifs_users[i]['UserName'], gifs_users[i]['GifType'], gifs_users[i]['Gif_Count'], gifs_users[i]['Coin'], '','','','']
                        elif(i < len(gifs_users) and i < len(snack_gifs_users)):
                            res_arr = [gifs_users[i]['UserName'], gifs_users[i]['GifType'], gifs_users[i]['Gif_Count'], gifs_users[i]['Coin'], snack_gifs_users[i]['UserName'], snack_gifs_users[i]['Snack_Count'], snack_gifs_users[i]['Gif_Count'], snack_gifs_users[i]['Coin']]
                        
                        total_result.append(res_arr)
                        i += 1
                    
                    score_elements = browser.find_elements(By.XPATH, "//*[@style='transform: rotateX(0deg) translateZ(28px);']")
                    for element in score_elements:
                        while element.text == '':
                            time.sleep(2)
                        score += element.text
                    print(f"coin = {coin_cnt}, score = {score}")
                    time.sleep(5)

                    # create google sheet
                    filename = f"Test_{self.name}__{self.start_year}_{self.start_month}_{self.start_day}"
                    folder_name = '1IkovXnPZ8y-aIgR6MnbykOVfXC34CJhT'
                    sheetID = await get_sheet_by_name(filename, folder_name)
                    create_flag = False
                    if(sheetID == ''):
                        create_flag = True
                        sheetID = await createGoogleSheet(filename)
                    print(sheetID)

                    # write content into google sheet (init column name)
                    SCOPES = ['https://www.googleapis.com/auth/drive']
                    SERVICE_ACCOUNT_FILE = 'service-account.json'

                    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
                    client = gspread.authorize(creds)
                    service = build('sheets', 'v4', credentials=creds)

                    spreadsheet = client.open_by_key(sheetID)

                    if(create_flag):
                        worksheet = spreadsheet.sheet1
                        worksheet.update_title('チャット履歴')

                        worksheet.update("E1", [["コイン数"]], value_input_option="USER_ENTERED")
                        worksheet.update("E2", [["ギフト人数"]], value_input_option="USER_ENTERED")
                        worksheet.update("E3", [["スナック数"]], value_input_option="USER_ENTERED")
                        worksheet.update("E4", [["スコア"]], value_input_option="USER_ENTERED")

                        worksheet.update("A5", [["リスナー名"]], value_input_option="USER_ENTERED")
                        worksheet.update("B5", [["ギフト名"]], value_input_option="USER_ENTERED")
                        worksheet.update("C5", [["ギフト個数"]], value_input_option="USER_ENTERED")
                        worksheet.update("D5", [["コイン数"]], value_input_option="USER_ENTERED")
                        worksheet.update("E5", [["リスナー名"]], value_input_option="USER_ENTERED")
                        worksheet.update("F5", [["スナック"]], value_input_option="USER_ENTERED")
                        worksheet.update("G5", [["ギフト個数"]], value_input_option="USER_ENTERED")
                        worksheet.update("H5", [["合計コイン"]], value_input_option="USER_ENTERED")

                        worksheet = spreadsheet.add_worksheet(title="ギフト内訳", rows='1000', cols='20')

                        worksheet.update("A1", [["ギフト名"]], value_input_option="USER_ENTERED")
                        worksheet.update("B1", [["ギフト個数"]], value_input_option="USER_ENTERED")
                        worksheet.update("C1", [["コイン数"]], value_input_option="USER_ENTERED")

                    # clear content in google sheet
                    sheet_range = f'チャット履歴!A6:Z'  # Adjust the range as needed
                    service.spreadsheets().values().clear(spreadsheetId=sheetID, range=sheet_range).execute()
                    sheet_range = f'ギフト内訳!A2:Z'  # Adjust the range as needed
                    service.spreadsheets().values().clear(spreadsheetId=sheetID, range=sheet_range).execute()

                    # write content into google sheet
                    worksheet = spreadsheet.worksheet("チャット履歴")

                    worksheet.update("F1", [[str(coin_cnt)]], value_input_option="USER_ENTERED")
                    worksheet.update("F2", [[str(snack_cnt)]], value_input_option="USER_ENTERED")
                    worksheet.update("F3", [[str(gif_man_cnt)]], value_input_option="USER_ENTERED")
                    worksheet.update("F4", [[str(score)]], value_input_option="USER_ENTERED")
                    try:
                        worksheet.insert_rows(total_result, row=6)
                    except:
                        print('quota <')

                    worksheet = spreadsheet.worksheet("ギフト内訳")
                    worksheet.insert_rows(gifs_list, row=2)

                    current_month = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).month
                    current_day = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).day
                    current_hour = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).hour
                    current_minute = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).minute

                    if current_month == self.end_date_month and current_day == self.end_date_day and current_hour == self.end_time_hour and current_minute == self.end_time_minute:
                        sys.exit(1)

                else:
                    return 'Failure'

    async def main(self):
        result = await self.scanData()
        return result
    
    def run(self):
        result = asyncio.run(self.main)
        return result