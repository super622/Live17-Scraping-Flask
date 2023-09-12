import time
import requests
import asyncio
import json
import datetime
import gspread

from datetime import date
from openpyxl.styles import Alignment
from googleapiclient.discovery import build  # Added
from google.oauth2 import service_account

from selenium import webdriver
from selenium.webdriver.common.by import By

class Chating:

    # Init
    def __init__(self, name):
        self.name = name

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
            
        
        url = 'https://wap-api.17app.co/api/v1/cells?count=0&cursor=&paging=1&region=JP&tab=hot'

        liveStreamIDs = None
        try:
            liveStreamIDs = await send_request(url)
            liveStreamIDs = json.loads(liveStreamIDs)
            liveStreamIDs = liveStreamIDs['cells']
        except Exception as e:
            print(f"An error occurred while fetching JSON for {url}: {e}")

        live_stream_id_arr = []
        for i in range(len(liveStreamIDs)):
            if('stream' in liveStreamIDs[i]):
                if liveStreamIDs[i]['stream']['userInfo']['displayName'] == self.name:
                    live_stream_id_arr.append(liveStreamIDs[i]['stream']['liveStreamID'])

        for live_room_id in live_stream_id_arr:
            data = []
            url = f'https://17.live/ja/live/{live_room_id}'

            chrome_options = webdriver.ChromeOptions()
            browser = webdriver.Chrome(options=chrome_options)

            # Maximize the browser window
            browser.maximize_window()

            # Bring the browser window to the front
            browser.execute_script("window.focus();")
            time.sleep(3)
            
            browser.get(url)
            time.sleep(5)

            chating_panel = browser.find_elements('css selector', '.ChatList__ListWrapper-sc-733d46-1')
            if(len(chating_panel) > 0):
                snack_cnt = len(chating_panel[0].find_elements('css selector', '.LaborReward__ControlledText-sc-cxndew-0'))
                gif_man_cnt = len(chating_panel[0].find_elements('css selector', '.GiftItem__GiftIcon-sc-g419cs-0'))
                coin_cnt = 0
                score = 0
                gifs_users = []
                snack_gifs_users = []
                print(f"snack => {snack_cnt},   gif man => {gif_man_cnt}")

                chating_elements = browser.find_elements('css selector', '.Chat__ChatWrapper-sc-clenhv-0')
                for chat_element in chating_elements:
                    if len(chat_element.find_elements('css selector', '.GiftItem__GiftIcon-sc-g419cs-0')) > 0:
                        name_element = chat_element.find_elements('css selector', '.ChatUserName__NameWrapper-sc-1ca2hpy-0')
                        user_name = name_element[0].text
                        gif_element = chat_element.find_elements('css selector', '.Chat__ContentWrapper-sc-clenhv-1')
                        gif_type = gif_element[0].text
                        print(gif_type)

            else:
                return 'Failure'

    async def main(self):
        result = await self.scanData()
        return result
    
    def run(self):
        result = asyncio.run(self.main)
        return result