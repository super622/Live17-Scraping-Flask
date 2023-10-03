import re
import sys
import time
import requests
import asyncio
import json
import datetime
import gspread
import pytz
import mysql.connector
import logging

import config

from gspread_formatting import *
from googleapiclient.discovery import build  # Added
from google.oauth2 import service_account

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class Chating:

    # Init
    def __init__(self, end_date_month, end_date_day, end_time_hour, end_time_minute, nick_url, start_time_hour, start_time_minute):
        self.name = nick_url
        self.end_date_month = end_date_month
        self.end_date_day = end_date_day
        self.end_time_hour = end_time_hour
        self.end_time_minute = end_time_minute
        self.start_time_hour = start_time_hour
        self.start_time_minute = start_time_minute
        self.start_year = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).year
        self.start_month = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).month
        self.start_day = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).day
        self.started_flag = False
        self.temp_result = []

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
                    user['Coin'] = int(res['Coin']) + int(user['Coin'])
                    user['Gif_Count'] = int(res['Gif_Count']) + int(user['Gif_Count'])
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
                hex = bytes(user_name, 'utf-8')
                print(f"gif users => {user['UserName']}, {user_name}")
                print(f"hex => {user['Hex']}, {hex}")
                if(user['Hex'] == hex):
                    return user
            res = {
                "UserName": '',
                "GifType": '',
                "Gif_Count": 0,
                "Coin": 0
            }
            return res
        
        # add all gif users
        async def append_to_total_gif_users(total_users, sub_users, type):
            temp = total_users
            flag = False
            for sub in sub_users:
                for total in temp:
                    if(total['Hex'] == sub['Hex'] and total['GifType'] == sub['GifType']):
                        total['Coin'] = int(sub['Coin']) + int(total['Coin'])
                        total['Gif_Count'] = int(total['Gif_Count']) + int(sub['Gif_Count'])
                        flag = True

                if(flag != True):
                    temp.append(sub)
                else:
                    flag = False
            if(type):
                total_users = temp
            else:
                return temp

        # add all snack users
        async def append_to_total_snack_users(total_users, sub_users, type):
            temp = total_users
            flag = False
            for sub in sub_users:
                for total in temp:
                    if(total['UserName'] == sub['UserName']):
                        total['Gif_Count'] = int(sub['Gif_Count']) + int(total['Gif_Count'])
                        total['Coin'] = int(sub['Coin']) + int(total['Coin'])
                        total['Snack_Count'] = int(sub['Snack_Count']) + int(total['Snack_Count'])
                        flag = True
            
                if(flag):
                    flag = False
                else:
                    temp.append(sub)

            if(type):
                total_users = temp
            else:
                return temp

        # add all result
        async def append_to_total_result(total_result, gif_users, snack_users, type):
            max_len = len(gif_users) if len(gif_users) > len(snack_users) else len(snack_users)
            temp_arr = None
            result_array = []
            if max_len == len(gif_users):
                temp_arr = gif_users
            else:
                temp_arr = snack_users
            
            for i in range(len(temp_arr)):
                res_arr = None

                if(i < len(gif_users) and i < len(snack_users)):
                    res_arr = [gif_users[i]['UserName'], gif_users[i]['GifType'], gif_users[i]['Gif_Count'], gif_users[i]['Coin'], snack_users[i]['UserName'], snack_users[i]['Snack_Count'], snack_users[i]['Gif_Count'], snack_users[i]['Coin']]
                elif(i >= len(gif_users)):
                    res_arr = ['', '', '', '', snack_users[i]['UserName'], snack_users[i]['Snack_Count'], snack_users[i]['Gif_Count'], snack_users[i]['Coin']]
                elif(i >= len(snack_users)):
                    res_arr = [gif_users[i]['UserName'], gif_users[i]['GifType'], gif_users[i]['Gif_Count'], gif_users[i]['Coin'], '','','','']
                
                result_array.append(res_arr)
            total_result = result_array
            if(type == False):
                return total_result

        # add git and snack user
        async def append_to_snack_gifusers(snack_gifs_users, gifs_user, username, snack_cnt):
            flag = False
            for user in snack_gifs_users:
                if(user['UserName'] == username):
                    user['Gif_Count'] = gifs_user['Gif_Count']
                    user['Coin'] = int(gifs_user['Coin'])
                    user['Snack_Count'] = int(snack_cnt) + int(user['Snack_Count'])
                    flag = True

            if flag:
                return snack_gifs_users
            else:
                res = {
                    "UserName": username,
                    "Gif_Count": gifs_user['Gif_Count'],
                    "Snack_Count": int(snack_cnt),
                    "Coin": int(gifs_user['Coin'])
                }
                snack_gifs_users.append(res)
                return snack_gifs_users

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

            results = drive_service.files().list(q="name='" + file_name + "' and mimeType='application/vnd.google-apps.spreadsheet' ", pageSize=10, fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])
            if not items:
                return ''
            else:
                return items[0]['id']

        # format cell type
        async def format_cell_format(worksheet):
            fmt = CellFormat(
                    backgroundColor=Color(173, 168, 168),
                    textFormat=TextFormat(bold=False, foregroundColor=Color(0, 0, 0)),
                    horizontalAlignment='CENTER'
                )

            format_cell_range(worksheet, 'A5:H5', fmt)
            format_cell_range(worksheet, 'E1:E5', fmt)

        # init content of worksheet
        async def init_content_of_worksheet(worksheet):
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

        # add data into database
        def result_response(value):
            result = ''
            if value == 1:
                result = '現在進行中の配信者のリストが見つかりません。'
            elif value == 2:
                result = '入力した配信者に関する情報が見つかりません。'
            
            try:
                with mysql.connector.connect(
                    host='127.0.0.1',
                    user='root',
                    password=config.DB_PASS,
                    database='live_db'
                ) as cnx:
                    cursor = cnx.cursor()
                    query = "SELECT * FROM history WHERE url='" + self.name + "'"
                    cursor.execute(query)
                    rows = cursor.fetchall()

                    if len(rows) > 0:
                        for row in rows:
                            cursor.execute(f"DELETE FROM history WHERE id={row[0]}")
                    
                    query = 'INSERT INTO history (url, start_date, end_date, type, status) VALUES (%s, %s, %s, %s, %s)'
                    cursor.execute(query, (self.name, f"{self.start_year}-{self.start_month}-{self.start_day} {self.start_time_hour}:{self.start_time_minute}", f"{self.start_year}-{self.end_date_month}-{self.end_date_day} {self.end_time_hour}:{self.end_time_minute}", 'C', result,))
                    cnx.commit()
                    print('db disconnect')
            except Exception as e:
                print(e)

        url = 'https://wap-api.17app.co/api/v1/cells?count=0&cursor=&paging=1&region=JP&tab=hot'

        liveStreamIDs = None
        try:
            liveStreamIDs = await send_request(url)
            liveStreamIDs = json.loads(liveStreamIDs)
            liveStreamIDs = liveStreamIDs['cells']
        except Exception as e:
            print(f"An error occurred while fetching JSON for {url}: {e}")
        
        if(liveStreamIDs == None):
            result_response(1)
            return 'Not exist'
        
        live_stream_id_arr = []
        for i in range(len(liveStreamIDs)):
            if('stream' in liveStreamIDs[i]):
                if liveStreamIDs[i]['stream']['userInfo']['displayName'] == self.name:
                    live_stream_id_arr.append(liveStreamIDs[i]['stream']['liveStreamID'])

        if len(live_stream_id_arr) == 0:
            result_response(2)
            return 'failure - not exist live stream id'
        
        if(self.started_flag != True):
            result_response(0)
            self.started_flag = True

        print(len(live_stream_id_arr))
        logging.basicConfig(level=logging.INFO)
        for live_room_id in live_stream_id_arr:
            url = f'https://17.live/ja/live/{live_room_id}'
            print(url)

            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')

            # options.add_argument('--no-sandbox') 
            # options.add_argument('--disable-dev-shm-usage') 
            # options.add_argument('--headless')
            # options.add_argument('--disable-gpu')
            # options.add_argument('--disable-extensions')
            # options.add_argument('--remote-debugging-port=9222')
            # options.add_argument('--log-level=DEBUG')
            # options.add_argument('--enable-logging')
            # options.add_argument('--disable-software-rasterizer')
            # options.binary_location = '/usr/bin/google-chrome'

            browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

            browser.get(url)

            total_snack_cnt = 0
            total_coin_cnt = 0
            total_score = 0
            total_gif_man_cnt = 0
            total_gifs_user = []
            total_snack_user = []
            total_results = []

            while True:
                chating_panel = browser.find_elements('css selector', '.ChatList__ListWrapper-sc-733d46-1')
                print('start')
                if(len(chating_panel) > 0):
                    snack_cnt = 0
                    gif_man_cnt = 0
                    coin_cnt = 0
                    score = ''
                    gifs_users = []
                    snack_gifs_users = []
                    gifs_list = []
                    sub_result = []

                    chating_elements = browser.find_elements('css selector', '.Chat__ChatWrapper-sc-clenhv-0')
                    for chat_element in chating_elements:
                        name_element = chat_element.find_elements('css selector', '.ChatUserName__NameWrapper-sc-1ca2hpy-0')
                        user_name = name_element[0].text
                        if len(chat_element.find_elements('css selector', '.GiftItem__GiftIcon-sc-g419cs-0')) > 0:
                            gif_element = chat_element.find_elements('css selector', '.Chat__ContentWrapper-sc-clenhv-1')
                            gif_type = gif_element[0].text
                            coin_element = re.search(r'\((\d+)\)', gif_type)
                            coin = 0
                            if coin_element:
                                coin = coin_element.group(1)

                            res = {
                                "UserName": user_name,
                                "Hex": bytes(user_name, "utf-8"),
                                "GifType": gif_type,
                                "Gif_Count": 1,
                                "Coin": coin
                            }
                            gifs_list = await append_to_gif(gifs_list, gif_type, coin)
                            gifs_users = await append_to_gifusers(gifs_users, res)

                        if len(chat_element.find_elements('css selector', '.LaborReward__ControlledText-sc-cxndew-0')) > 0:
                            gif_state = await find_in_gifusers(gifs_users, user_name)
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

                    length = len(gifs_users) if len(gifs_users) > len(snack_gifs_users) else len(snack_gifs_users)
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
                        sub_result.append(res_arr)
                    
                    score_elements = browser.find_elements(By.XPATH, "//*[@style='transform: rotateX(0deg) translateZ(28px);']")
                    for element in score_elements:
                        while element.text == '':
                            time.sleep(1)
                        score += element.text
                    print(f"coin = {coin_cnt}, score = {score}")

                    # total_gifs_user
                    temp_total_gifs_user = await append_to_total_gif_users(total_gifs_user, gifs_users, False)

                    # total_snack_user
                    temp_total_snack_user = await append_to_total_snack_users(total_snack_user, snack_gifs_users, False)

                    # total result
                    temp_total_results = await append_to_total_result(total_results, temp_total_gifs_user, temp_total_snack_user, False)

                    print("-----------------------------------")
                    print(f"result => {sub_result}")
                    print("-----------------------------------")
                    print(f"total => {temp_total_results}")

                    current_month = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).month
                    current_day = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).day

                    if(self.start_day != current_day):
                        print('date==================')
                        self.start_day = current_day

                        total_snack_cnt += snack_cnt
                        total_gif_man_cnt += gif_man_cnt
                        total_coin_cnt = coin_cnt
                        total_score = score

                        # total_gifs_user
                        await append_to_total_gif_users(total_gifs_user, gifs_users, True)

                        # total_snack_user
                        await append_to_total_snack_users(total_snack_user, snack_gifs_users, True)

                        # total result
                        await append_to_total_result(total_results, total_gifs_user, total_snack_user, True)

                        # refresh
                        browser.refresh()
                        
                    # create google sheet
                    SCOPES = ['https://www.googleapis.com/auth/drive']
                    SERVICE_ACCOUNT_FILE = 'service-account.json'

                    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
                    client = gspread.authorize(creds)
                    service = build('sheets', 'v4', credentials=creds)

                    tab_position = 0
                    filename = f"{self.name}"
                    folder_name = '1IkovXnPZ8y-aIgR6MnbykOVfXC34CJhT'
                    sheetID = await get_sheet_by_name(filename, folder_name)
                    print(sheetID)
                    create_flag = False
                    if(sheetID == ''):
                        create_flag = True
                        sheetID = await createGoogleSheet(filename)
                        tab_position = 3
                    else:
                        spreadsheet = client.open_by_key(sheetID)
                        sheets_list = spreadsheet.worksheets()
                        tab_position = len(sheets_list)

                    # write content into google sheet (init column name)
                    spreadsheet = client.open_by_key(sheetID)

                    if(create_flag or tab_position == 1):
                        worksheet = spreadsheet.sheet1

                        await format_cell_format(worksheet)

                        try:
                            worksheet.resize(rows=5000, cols=8)

                            worksheet.update_title(f"{current_month}-{current_day}")

                            await init_content_of_worksheet(worksheet)
                        except:
                            print('quota <')

                        worksheet = spreadsheet.add_worksheet(title="total", rows='5000', cols='8')

                        await format_cell_format(worksheet)

                        try:
                            await init_content_of_worksheet(worksheet)
                        except:
                            print('quota <')

                        worksheet = spreadsheet.add_worksheet(title="ギフト内訳", rows='5000', cols='3')

                        fmt = CellFormat(
                                backgroundColor=Color(173, 168, 168),
                                textFormat=TextFormat(bold=False, foregroundColor=Color(0, 0, 0)),
                                horizontalAlignment='CENTER'
                            )

                        format_cell_range(worksheet, 'A1:C1', fmt)

                        try:
                            worksheet.update("A1", [["ギフト名"]], value_input_option="USER_ENTERED")
                            worksheet.update("B1", [["ギフト個数"]], value_input_option="USER_ENTERED")
                            worksheet.update("C1", [["コイン数"]], value_input_option="USER_ENTERED")
                        except:
                            print('quota <')

                    worksheet = None
                    try:
                        worksheet = spreadsheet.get_worksheet(tab_position - 3)
                    except:
                        worksheet = None
                    
                    if(worksheet == None):
                        worksheet = spreadsheet.add_worksheet(title=f"{current_month}-{current_day}", rows='5000', cols='8')

                        try:
                            await init_content_of_worksheet(worksheet)
                        except:
                            print('quota <')

                    # clear content in google sheet
                    try:
                        sheet_range = f'{current_month}-{current_day}!A6:Z'  # Adjust the range as needed
                        service.spreadsheets().values().clear(spreadsheetId=sheetID, range=sheet_range).execute()
                        sheet_range = f'total!A6:Z'
                        service.spreadsheets().values().clear(spreadsheetId=sheetID, range=sheet_range).execute()
                        sheet_range = f'ギフト内訳!A2:Z'  # Adjust the range as needed
                        service.spreadsheets().values().clear(spreadsheetId=sheetID, range=sheet_range).execute()
                    except:
                        print('quota <')

                    # write content into google sheet
                    worksheet = spreadsheet.get_worksheet(tab_position - 3)

                    try:
                        worksheet.update("F1", [[str(coin_cnt)]], value_input_option="USER_ENTERED")
                        worksheet.update("F2", [[str(snack_cnt)]], value_input_option="USER_ENTERED")
                        worksheet.update("F3", [[str(gif_man_cnt)]], value_input_option="USER_ENTERED")
                        worksheet.update("F4", [[str(score)]], value_input_option="USER_ENTERED")
                    except:
                        print('quota <')
                    
                    try:
                        print('----------------------------')
                        print(sub_result)
                        print('----------------------------')
                        worksheet.insert_rows(sub_result, row=6)
                    except:
                        print('quota <')

                    worksheet = spreadsheet.worksheet("total")

                    try:
                        worksheet.update("F1", [[str(total_coin_cnt)]], value_input_option="USER_ENTERED")
                        worksheet.update("F2", [[str(total_snack_cnt + snack_cnt)]], value_input_option="USER_ENTERED")
                        worksheet.update("F3", [[str(total_gif_man_cnt + gif_man_cnt)]], value_input_option="USER_ENTERED")
                        worksheet.update("F4", [[str(total_score)]], value_input_option="USER_ENTERED")
                    except:
                        print('quota <')

                    try:
                        worksheet.insert_rows(temp_total_results, row=6)
                    except:
                        print('quota <')

                    worksheet = spreadsheet.worksheet("ギフト内訳")

                    try:
                        worksheet.insert_rows(gifs_list, row=2)
                    except:
                        print('quota <')

                    current_hour = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).hour
                    current_minute = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).minute

                    if self.start_time_hour == current_hour and self.start_time_minute == current_minute:
                        total_results = self.temp_result
                    
                    if current_month == self.end_date_month and current_day == self.end_date_day and current_hour == self.end_time_hour and current_minute == self.end_time_minute:
                        sys.exit(1)

                else:
                    result_response(2)
                    return 'Failure'

    async def main(self):
        result = await self.scanData()
        return result

    def run(self):
        result = asyncio.run(self.main)
        return result