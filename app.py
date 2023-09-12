import asyncio
import json
import os
import datetime

from flask import Flask, request
from flask_cors import CORS
from crontab import CronTab
from getContents import ContentSCraping
from Chating import Chating

app = Flask(__name__)
CORS(app)
# cron = CronTab(user='Holly')

@app.route('/')
def hello_world():
   return 'Server is running...'

@app.route('/start')
def start():
   start_date_month = request.args.get('start_date_month')
   start_date_day = request.args.get('start_date_day')
   start_time_hour = request.args.get('start_time_hour')
   start_time_minute = request.args.get('start_time_minute')
   end_date_month = request.args.get('end_date_month')
   end_date_day = request.args.get('end_date_day')
   event_url = request.args.get('event_url')
   nick_url = request.args.get('nick_url')

   # script_directory = os.path.dirname(os.path.abspath(__file__))

   # script_path = os.path.join(script_directory, 'Scraping.py')

   # end_month = request.args.get('end_month')
   # end_day = request.args.get('end_day')

   # cmd = f"python {script_path}"
   # job = cron.new(command=cmd)

   # time = f"{start_minute} {start_hours} * * *"
   # job.setall(time)
   # cron.write()
   # print('a')
   # return ''

   # getData = ContentSCraping(start_date_month, start_date_day, event_url)
   # response = asyncio.run(getData.main())
   # return json.dumps(response)

   getChatingData = Chating(nick_url)
   response = asyncio.run(getChatingData.main())
   return json.dumps(response)

@app.route('/stop')
def stop():
   # cron.remove_all()
   print('stop')

if __name__ == '__main__':
   app.run()
