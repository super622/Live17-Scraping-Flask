import asyncio
import json
import math
import datetime
import threading
import schedule

from flask import Flask, request
from flask_cors import CORS
from getContents import ContentSCraping
from Chating import Chating

app = Flask(__name__)
CORS(app)

# Dictionary to store scheduled jobs
scheduled_jobs = {}

@app.route('/')
def hello_world():
   return 'Server is running...'

def change_string(value):
   value = str(value)
   if(len(value) == 1):
      print(f"0{value}")
      return f"0{value}"

def chating_scraping(end_date_month, end_date_day, start_time_hour, start_time_minute, nick_url):
   getChatingData = Chating(end_date_month, end_date_day, start_time_hour, start_time_minute, nick_url)
   response = asyncio.run(getChatingData.main())
   return json.dumps(response)

def event_scraping(start_date_month, start_date_day, event_url):
   print('start')
   getData = ContentSCraping(start_date_month, start_date_day, event_url)
   response = asyncio.run(getData.main())
   return json.dumps(response)

@app.route('/start', methods=['POST'])
def start():
   start_date_year = int(request.values.get('start_date_year'))
   start_date_month = int(request.values.get('start_date_month'))
   start_date_day = int(request.values.get('start_date_day'))
   start_time_hour = int(request.values.get('start_time_hour'))
   start_time_minute = int(request.values.get('start_time_minute'))
   end_date_year = int(request.values.get('end_date_year'))
   end_date_month = int(request.values.get('end_date_month'))
   end_date_day = int(request.values.get('end_date_day'))
   event_url = request.values.get('event_url')
   nick_url = request.values.get('nick_url')

   current_year = datetime.datetime.now().year
   current_month = datetime.datetime.now().month
   current_day = datetime.datetime.now().day
   current_hour = datetime.datetime.now().hour
   current_minute = datetime.datetime.now().minute

   if(start_date_year == current_year):
      print('')
      # if((start_date_day == current_day and start_time_hour < current_hour) or (start_date_day == current_day and start_time_hour == current_hour and start_time_minute < current_minute)):
      #    return json.dumps([{"type": "warning", "msg": "選択した開始日と時刻が現在の時刻より遅れてはいけません。"}])
   elif(start_date_year > current_year):
      current_year = start_date_year

   # Create a datetime object for the specified start date and time
   start_datetime = datetime.datetime(current_year, start_date_month, start_date_day, start_time_hour, start_time_minute, 0)
   end_datetime = datetime.datetime(end_date_year, end_date_month, end_date_day, start_time_hour, start_time_minute, 0)

   # Calculate the delay in seconds until the scheduled time
   delay = (start_datetime - datetime.datetime.now()).total_seconds()
   delay = math.floor(delay)
   print(delay)

   # Create a new thread to call the scheduled function after the delay
   res = threading.Timer(delay, chating_scraping, args=(end_date_month, end_date_day, start_time_hour, start_time_minute, nick_url)).start()

   # Convert start_date and end_date to datetime objects
   start_datetime = datetime.datetime.strptime(f"{current_year}-{start_date_month}-{start_date_day} {start_time_hour}:{start_time_minute}:0", '%Y-%m-%d %H:%M:%S')
   end_datetime = datetime.datetime.strptime(f"{end_date_year}-{end_date_month}-{end_date_day} {start_time_hour}:{start_time_minute}:0", '%Y-%m-%d %H:%M:%S')
   
   # Schedule the cron job
   job = schedule.every().day.at(f"{change_string(start_time_hour)}:{change_string(start_time_minute)}:00").do(event_scraping, start_date_month, start_date_day, event_url)

   print(job)

   # Store the scheduled job in a dictionary
   scheduled_jobs[job] = {'start_datetime': start_datetime, 'end_datetime': end_datetime}

   return json.dumps([{"type": "success", "msg": "リクエストが受け付けられました。"}])

@app.route('/stop', methods=['POST'])
def stop():
   job = list(scheduled_jobs.keys())[0]
   job.cancel()
   del scheduled_jobs[job]
   return json.dumps({'message': 'Cron job canceled successfully'})

if __name__ == '__main__':
   app.run()
