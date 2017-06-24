# coding=utf-8

import config
from flask import Flask, Response, request, json
#from flask.ext.cors import CORS
import requests
import ssl

app = Flask(__name__)
#cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

debug=False

'''
Ziele:

* Media Private API so beschränken, dass damit nur noch Untertitel angelegt und geändert werden können
* Adapter soll transparent sein:
      Implementation auf Subtitle Seite so geschrieben sein,
      dass man den Adpaper einfach raus nehmen kann wenn die normale API irgendwann mal selbst
      Berechtigung können sollte

Testfall für Commandline

curl -v -H "CONTENT-TYPE: application/json" -d '{
    "api_key":"34170cc4-0a3d-11e6-823b-6c400891b752",
    "guid":"654331ae-1710-42e5-bdf4-65a03a80c614",
    "recording":{
      "filename":"32c3-7550-en-Opening_Event_hd.fr.srt",
      "language":"fra",
      "mime_type":"application/x-subrip",
      "length":"3600",
      "folder":"h264-hd/subtitles"
      }
  }' "http://localhost:5000/api/recordings"
'''


def error(msg):
    return Response(json.dumps({'msg': msg}), mimetype='application/json', status=500)


@app.route("/api/recordings", methods = ['POST'])
def recordings():
    if not request.json['api_key']:
        return error('api key missing')
    
    if request.json['api_key'] not in config.allowed_keys:
        return error('wrong api key')


    recording = request.json['recording']

    if recording['mime_type'] != "application/x-subrip":
        return error('only mime_type "application/x-subrip" is allowed')

    if 'subtitles' not in recording['folder']:
        return error("folder has to contain string 'subtitles'")
    
    if not recording['filename'].endswith('.srt'):
        return error('filename has to end with .srt')

    payload = request.json
    payload['api_key'] = config.media_private_api_key

    r = requests.post(
        "https://api.media.ccc.de/api/recordings",
        headers={'CONTENT-TYPE' : 'application/json'},
        data=json.dumps(payload), verify=False
    )

    return Response(r.text, mimetype='application/json', status=r.status_code)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=debug)
