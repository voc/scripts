#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
export/sync subtitles to voctoweb/media.ccc.de as recordings of type SRT / WebVTT

'''

import os
import csv
import requests
import logging
from contextlib import closing
import time
import paramiko
import urllib

dry_run = False
no_upload = True
slow_down = False
ssh = None
sftp = None

config = {
    'upload_host': 'koeln.media.ccc.de',
    'upload_user': 'cdn-app',
}

mapping = {
     2: 'todo',
     7: 'draft',
     8: 'complete',
    11: 'todo',
    12: 'translated',
}

VOCTOWEB_API_URL = 'https://media.ccc.de/api'
VOCTOWEB_API_URL = 'https://media.test.c3voc.de/api'


def main():
    last_run = load_last_run_timestamp()
    timestamp = None
    logging.info(' applying changes on c3subtitles.de since {} to {}'.format(last_run, VOCTOWEB_API_URL))

    try:
        url = 'https://media_export:{}@c3subtitles.de/media_export/{}'.format(os.environ['PASSWORD'], last_run)
        logging.info('loading c3subtitles.de/media_export/')
        with closing(requests.get(url, stream=True)) as r:
            reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter=';')
            for item in reader:
                print(dict(item))
                timestamp = item['touched']
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

    r = None
    target = None
    if item['complete'] == 'True' or item['released_as_draft'] == 'True':
        filename = os.path.basename(item['url'])
        #print(guid, item['media_language'], 'would be created on media')
        r = create_recording(guid, {
            "filename": filename,
            "language": item['media_language'],
            "state": mapping.get(int(item['state']), 'state-' + item['state'])
        })
        target = os.path.dirname(r['public_url']).replace('http://cdn.media.ccc.de/', '/static.media.ccc.de/') + '/{}-{}.vtt'.format(guid, item['media_language'])
    else:
        #print(guid, amara_url)
        filename = '{}-{}.vtt'.format(guid, item['media_language'])

        # print(guid, item['media_language'], 'would be created on media')
        r = create_recording(guid, {
            "filename": filename,
            "mime_type": "text/vtt",
            "language": item['media_language'],
            "state": mapping.get(int(item['state']), 'state-' + item['state'])
        })
        target = r['public_url'].replace('https://static.media.ccc.de/media/', '/static.media.ccc.de/')

    amara_url = "https://amara.org/api/videos/{}/languages/{}/subtitles/?format=vtt".format(item['amara_key'], item['amara_language'])
    if target and not(dry_run) and not(no_upload):
        if not target.startswith('/static.media.ccc.de/'):
            raise Exception('unexpected target path ' + target)
        process_and_upload_vtt(amara_url, target)

    #time.sleep(1)


def create_recording(guid, data):
    data = {
        "api_key": os.environ['VOCTOWEB_API_KEY'],
        "guid": guid,
        "recording": {
            "mime_type": "application/x-subrip",
            "folder": "",
            **data
        } 
    }
    if not(dry_run):
        r = requests.post(VOCTOWEB_API_URL + '/recordings', headers={'CONTENT-TYPE': 'application/json'}, json=data)
        #if r.status_code == 422:
        #    print(r.json())
        #    print("  " + r.json()['event'][0])
        #    r = requests.patch(VOCTOWEB_API_URL + '/recordings/' + r.json()['event'][0], headers={'CONTENT-TYPE': 'application/json'}, json=data)
        if r.status_code not in [200, 201]:
            print("  {}".format(r.status_code))
            print("  " + r.text.split('\n')[0])
            slow_down and time.sleep(5)
            return False
        print('  {} recording successfully'.format('created' if r.status_code == 201 else 'updated'))
        print("    " + r.text)
        return r.json()
    print('…')
    slow_down and time.sleep(0.1)


def load_last_run_timestamp():
    if os.path.isfile(".last_media_sync_run"):
        with open(".last_media_sync_run", "r") as fp:
            return fp.read()

    return '2020-01-01T0:00:00Z'


def store_last_run_timestamp(last_run):
    with open(".last_media_sync_run", "w") as fp:
        fp.write(last_run)


def process_and_upload_vtt(url, target):
    # check if ssh connection is open
    if ssh is None:
        connect_ssh()

    try:
        with urllib.request.urlopen(url) as df:
            print('  uploading {} to {}'.format(url, target))
            with sftp.open(target, 'w', 32768) as fh:
                while True:
                    chunk = df.read(32768)
                    if not chunk:
                        break
                    fh.write(chunk)
    except paramiko.SSHException as e:
        raise Exception('could not upload WebVTT because of SSH problem ' + str(e)) from e
    except IOError as e:
        raise Exception('could not upload WebVTT because of ' + str(e)) from e


def connect_ssh():
    global ssh, sftp
    logging.info('Establishing SSH connection')
    ssh = paramiko.SSHClient()
    logging.getLogger("paramiko").setLevel(logging.ERROR)
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(config['upload_host'], username=config['upload_user'], )
    except paramiko.AuthenticationException as e:
        raise Exception('Authentication failed. Please check credentials ' + str(e)) from e
    except paramiko.BadHostKeyException:
        raise Exception('Bad host key. Check your known_hosts file')
    except paramiko.SSHException as e:
        raise Exception('SSH negotiation failed ' + str(e)) from e

    sftp = ssh.open_sftp()
    logging.info('SSH connection established to ' + config['upload_host'])




if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    main()
