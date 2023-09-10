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
    def __init__(self) -> None:
        pass

    # Get Data from Chating panel
    async def scanData(self):
        
        print('start')

    async def main(self):
        result = await self.scanData()
        return result
    
    def run(self):
        result = asyncio.run(self.main)
        return result