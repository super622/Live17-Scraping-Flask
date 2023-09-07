import asyncio
import json
import datetime

from flask import Flask, request
from flask_cors import CORS
# from crontab import CronTab
from getContents import ContentSCraping

app = Flask(__name__)
CORS(app)
# cron = CronTab(user='root')

@app.route('/')
def hello_world():
   return 'Server is running...'

@app.route('/start')
def start():
   current_month = datetime.datetime.now().month
   current_day = datetime.datetime.now().day
   start_minute = request.args.get('start_minute')
   start_hours = request.args.get('start_hours')
   # end_month = request.args.get('end_month')
   # end_day = request.args.get('end_day')

   # cmd = f"python Scraping.py {current_month} {current_day}"
   # job = cron.new(command=cmd)

   # time = f"{start_minute} {start_hours} * * *"
   # job.setall(time)
   # cron.write()
   # print('a')
   
   getData = ContentSCraping(current_month, current_day)
   response = asyncio.run(getData.main())
   return json.dumps(response)

@app.route('/stop')
def stop():
   # cron.remove_all()
   print('stop')

if __name__ == '__main__':
   app.run()