import asyncio
import json

from flask import Flask, request
from flask_cors import CORS
from getContents import ContentSCraping

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
   return 'Server is running...'

@app.route('/start')
def start():
   start_month = request.args.get("start_month")
   start_day = request.args.get("start_day")
   # start_time = request.args.get('start_time')
   # end_month = request.args.get('end_date')
   # end_day = request.args.get('end_day')
   
   getData = ContentSCraping(start_month, start_day)
   response = asyncio.run(getData.main())
   return json.dumps(response)

@app.route('/stop')
def stop():
   return 'stop ...'

if __name__ == '__main__':
   app.run()