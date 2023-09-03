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
   month = request.args.get("month")
   day = request.args.get("day")
   
   getData = ContentSCraping(month, day)
   response = asyncio.run(getData.main())
   return json.dumps(response)

@app.route('/stop').




def stop():
   return 'stop ...'

if __name__ == '__main__':
   app.run()