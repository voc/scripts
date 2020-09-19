#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#==============================================================================
# Script export sync new complete subtitles to 
# voctoweb/media.ccc.de as recordings of type SRT
#==============================================================================

import os
import csv
import requests
from contextlib import closing
import time

dry_run = False


def main():
    last_run = load_last_run_timestamp()
    timestamp = None

    try:
        url = 'https://media_export:{}@c3subtitles.de/media_export/{}'.format(os.environ['PASSWORD'], last_run)
        with closing(requests.get(url, stream=True)) as r:
            reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter=';')
            for item in reader:
                timestamp = item['touched']
                print(item['touched'])
                print(dict(item))
                process_item(item)
                print()
    except KeyboardInterrupt:
        pass

    if timestamp:
        print('previous timestamp: {} new timestamp: {}'.format(last_run, timestamp))
        store_last_run_timestamp(timestamp[0:-1] + ".99Z")
    else:
        #print('did not yield results, please check manually')
        pass

def process_item(item):
    # ([('GUID', '60936beb-b15d-44ec-a9ca-9dc0807fd889'), ('complete', 'True'), ('media_language', 'deu'), ('srt_language', 'de'), 
    #   ('last_changed_on_amara', '2020-01-08T19:50:25Z'), ('revision', '16'), ('url', 'https://mirror.selfnet.de/c3subtitles/congress/36c3/36c3-10766-deu-eng-spa-Digitalisierte_Migrationskontrolle.de.srt')])

    guid = item['GUID']

    if item['complete']:
        filename = os.path.basename(item['url'])
        #print(guid, filename)

        #print(guid, item['media_language'], 'would be created on media')
        create_recording(guid, {
            "filename": filename,
            "language": item['media_language']
        })
    else:
        # TODO check if recording already exists on media, and then delete if necessary
        # extend
        print(guid, item['media_language'], 'has to be depublished manually')
        print(item)
        pass

def create_recording(guid, data):
    data = {
        "api_key": os.environ['VOCTOWEB_API_KEY'],
        "guid": guid,
        "recording": {
            **data,
            "mime_type": "application/x-subrip",
            "folder": ""
        } 
    }
    if not(dry_run):
        r = requests.post('https://media.ccc.de/api/recordings', headers={'CONTENT-TYPE': 'application/json'}, json=data)
        if r.status_code == 422:
            print("  " + r.json()['event'][0])
            return False
        if r.status_code != 201:
            print("  {}".format(r.status_code))
            print("  " + r.text)
            return False
        print('  created recording successfully')
        return True
    print('…')
    time.sleep(0.1)


def load_last_run_timestamp():
    if os.path.isfile(".last_media_sync_run"):
        with open(".last_media_sync_run", "r") as fp:
            return fp.read()

    return '2020-01-01T0:00:00Z'

def store_last_run_timestamp(last_run):
    with open(".last_media_sync_run", "w") as fp:
        fp.write(last_run)

if __name__ == '__main__':
    main()
