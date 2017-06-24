# coding=utf-8

media_private_api_key = "foobar42"
allowed_keys = ["subtitle-key1", "subtitle-key2"]

'''
Testfall für Commandline gegen media-api

curl -v -H "CONTENT-TYPE: application/json" -d '{
    "api_key":"foobar32",
    "guid":"654331ae-1710-42e5-bdf4-65a03a80c614",
    "recording":{
      "filename":"32c3-7550-en-Opening_Event_hd.fr.srt",
      "language":"fra",
      "mime_type":"application/x-subrip",
      "length":"3600",
      "folder":"h264-hd/subtitles"
      }
  }' "https://api.media.ccc.de/api/recordings"
'''
