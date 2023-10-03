import asyncio
import json
import math
import datetime
import threading
import time
import schedule
import pytz
import config
import mysql.connector

from multiprocessing import Process
from flask import Flask, request
from flask_cors import CORS
from EventSide import EventScraping
from ChatSide import Chating

app = Flask(__name__)
CORS(app)

# Dictionary to store scheduled jobs
scheduled_jobs = {}

# Check if the server is working
@app.route('/')
def hello_world():
   return 'Server is running...'

# Add 0 to one digit of the hour or minute
def change_string(value):
   value = str(value)
   if(len(value) == 1):
      return f"0{value}"
   return value

# Store scraping status into database
def result_response(url, type, start_date_year, start_date_month, start_date_day, start_time_hour, start_time_minute):
   try:
         with mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password=config.DB_PASS,
            database='live_db'
         ) as cnx:
            cursor = cnx.cursor()
            query = "SELECT * FROM history WHERE url='" + url + "'"
            cursor.execute(query)
            rows = cursor.fetchall()

            if len(rows) > 0:
               for row in rows:
                  cursor.execute(f"DELETE FROM history WHERE id={row[0]}")

            query = 'INSERT INTO history (url, start_date, end_date, type, status) VALUES (%s, %s, %s, %s, %s)'
            cursor.execute(query, (url, f"{start_date_year}-{start_date_month}-{start_date_day} {start_time_hour}:{start_time_minute}", "", type, '-',))
            cnx.commit()
            print('db disconnect')
   except Exception as e:
         print(e)

# Start scraping about chating side
def chating_scraping(end_date_month, end_date_day, end_time_hour, end_time_minute, nick_url, start_date_year, start_date_month, start_date_day, start_time_hour, start_time_minute):
   result_response(nick_url, 'C', start_date_year, start_date_month, start_date_day, start_time_hour, start_time_minute)
   getChatingData = Chating(end_date_month, end_date_day, end_time_hour, end_time_minute, nick_url, start_time_hour, start_time_minute)
   response = asyncio.run(getChatingData.main())
   return json.dumps(response)

# Start scraping about event side
def event_scraping(start_date_year, start_date_month, start_date_day, start_time_hour, start_time_minute, end_date_month, end_date_day, end_time_hour, end_time_minute, event):
   result_response(event, 'C', start_date_year, start_date_month, start_date_day, start_time_hour, start_time_minute)
   getData = EventScraping(start_date_month, start_date_day, start_time_hour, start_time_minute, end_date_month, end_date_day, end_time_hour, end_time_minute, event)
   response = asyncio.run(getData.main())
   return json.dumps(response)

# Start Scraping about live site
@app.route('/start', methods=['POST'])
def start():
   url_type = request.values.get('type')
   start_date_year = int(request.values.get('start_date_year'))
   start_date_month = int(request.values.get('start_date_month'))
   start_date_day = int(request.values.get('start_date_day'))
   start_time_hour = int(request.values.get('start_time_hour'))
   start_time_minute = int(request.values.get('start_time_minute'))
   end_date_year = int(request.values.get('end_date_year'))
   end_date_month = int(request.values.get('end_date_month'))
   end_date_day = int(request.values.get('end_date_day'))
   end_time_hour = int(request.values.get('end_time_hour'))
   end_time_minute = int(request.values.get('end_time_minute'))
   purpose_url = request.values.get('purpose_url')

   current_year = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).year

   if(start_date_year > current_year):
      current_year = start_date_year

   # Create datetime objects for start and end times
   japan_timezone = pytz.timezone('Asia/Tokyo')
   start_datetime = japan_timezone.localize(datetime.datetime(current_year, start_date_month, start_date_day, start_time_hour, start_time_minute, 0))
   end_datetime = japan_timezone.localize(datetime.datetime(end_date_year, end_date_month, end_date_day, end_time_hour, end_time_minute, 0))


   # # Convert start_date and end_date to datetime objects
   # start_datetime = datetime.datetime.strptime(f"{current_year}-{start_date_month}-{start_date_day} {start_time_hour}:{start_time_minute}:0", '%Y-%m-%d %H:%M:%S')
   # end_datetime = datetime.datetime.strptime(f"{end_date_year}-{end_date_month}-{end_date_day} {start_time_hour}:{start_time_minute}:0", '%Y-%m-%d %H:%M:%S')

   # Convert current time to Japan time zone and make it offset-aware
   cur_time = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))

   # Calculate the delay in seconds until the scheduled time
   delay = (start_datetime - cur_time).total_seconds()
   delay = math.floor(delay)
   print(delay)

   # url_type true: event, false: chat 
   if(url_type != 'false'):
      if(purpose_url.find(';') > -1):
         event_url_arr = purpose_url.split(';')
         for event in event_url_arr:
            job = schedule.every().day.at(f"{change_string(start_time_hour)}:{change_string(start_time_minute)}", "Asia/Tokyo").do(event_scraping, start_date_year, start_date_month, start_date_day, start_time_hour, start_time_minute, end_date_month, end_date_day, end_time_hour, end_time_minute, event)
            print(job)
            scheduled_jobs[job] = {'start_datetime': start_datetime, 'end_datetime': end_datetime}
      else:
         job = schedule.every().day.at(f"{change_string(start_time_hour)}:{change_string(start_time_minute)}", "Asia/Tokyo").do(event_scraping, start_date_year, start_date_month, start_date_day, start_time_hour, start_time_minute, end_date_month, end_date_day, end_time_hour, end_time_minute, purpose_url)
         print(job)
         scheduled_jobs[job] = {'start_datetime': start_datetime, 'end_datetime': end_datetime}
      while True:
         schedule.run_pending()
         time.sleep(1000)
   else:
      if(purpose_url.find(';') > -1):
         nick_name_arr = purpose_url.split(';')
         for nick_name in nick_name_arr:
            res = threading.Timer(delay, chating_scraping, args=(end_date_month, end_date_day, end_time_hour, end_time_minute, nick_name, start_date_year, start_date_month, start_date_day, start_time_hour, start_time_minute)).start()
      else:
         print(purpose_url)
         res = threading.Timer(delay, chating_scraping, args=(end_date_month, end_date_day, end_time_hour, end_time_minute, purpose_url, start_date_year, start_date_month, start_date_day, start_time_hour, start_time_minute)).start()


   return json.dumps([{"type": "success", "msg": "リクエストが受け付けられました。"}])

# Cron job stop
@app.route('/stop', methods=['POST'])
def stop():
   job = list(scheduled_jobs.keys())[0]
   job.cancel()
   del scheduled_jobs[job]
   return json.dumps({'message': 'Cron job canceled successfully'})

if __name__ == '__main__':
    for _ in range(50):  # Run 50 processes
        p = Process(target=app.run)
        p.start()
