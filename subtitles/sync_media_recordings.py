#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
export/sync subtitles to voctoweb/media.ccc.de as recordings of type SRT / WebVTT

'''

from os import path, environ
import csv
import requests
import logging
from contextlib import closing
import time
import paramiko
import urllib

dry_run = False
no_upload = False
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
#VOCTOWEB_API_URL = 'https://media.test.c3voc.de/api'


def main():
    last_run = load_last_run_timestamp()
    timestamp = None
    logging.info(f' applying changes on c3subtitles.de since {last_run} to {VOCTOWEB_API_URL}')

    try:
        url = f'https://media_export:{environ['PASSWORD']}@c3subtitles.de/media_export/{last_run}'
        logging.info(' loading c3subtitles.de/media_export/ ')
        with closing(requests.get(url, stream=True)) as r:
            reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter=';')
            for item in reader:
                print(dict(item))
                timestamp = item['touched']
                process_item(item)
                print()
    except KeyboardInterrupt:
        pass
    finally:
        if timestamp:
            print(f'previous timestamp: {last_run} new timestamp: {timestamp}')
            store_last_run_timestamp(timestamp[0:-1] + ".99Z")
        else:
            print('did not yield results, please check manually')
            pass

def process_item(item):
    # ([('GUID', '60936beb-b15d-44ec-a9ca-9dc0807fd889'), ('complete', 'True'), ('media_language', 'deu'), ('srt_language', 'de'), 
    #   ('last_changed_on_amara', '2020-01-08T19:50:25Z'), ('revision', '16'), ('url', 'https://mirror.selfnet.de/c3subtitles/congress/36c3/36c3-10766-deu-eng-spa-Digitalisierte_Migrationskontrolle.de.srt')
    # ])

    guid = item['GUID']
    r = None

    # when flags 'complete' or 'released_as_draft' are true, create SRT recording on media  
    if item['complete'] == 'True' or item['released_as_draft'] == 'True':
        # logging.debug(guid, item['media_language'], 'would be created on media')

        filename = path.basename(item['url']) # e.g. '36c3-10766-deu-eng-spa-Digitalisierte_Migrationskontrolle.de.srt'
        
        # upsert subtitle recording, will update subtitle recording from previous else due to unique constraint on language
        r = upsert_recording(guid, {
            "filename": filename,
            "mime_type": "application/x-subrip",
            "language": item['media_language'],
            "state": mapping.get(int(item['state']), 'state-' + item['state'])
        })
        # download vtt file from amara for new player (which does not support srt)
        if r and not(dry_run) and not(no_upload):
            target = path.dirname(r['public_url']).replace('https://cdn.media.ccc.de/', '/static.media.ccc.de/') + f'/{guid}-{item['media_language']}.vtt'
            amara_url = f"https://amara.org/api/videos/{item['amara_key']}/languages/{item['amara_language']}/subtitles/?format=vtt"
            if not target.startswith('/static.media.ccc.de/'):
                raise Exception('unexpected target path ' + target)
            
            process_and_upload_vtt(amara_url, target)

    # otherwise create placeholder VTT recording to display current status
    else:
        # logging.debug(guid, item['media_language'], 'would be created on media')

        filename = f'{guid}-{item['media_language']}.vtt' # e.g. '60936beb-b15d-44ec-a9ca-9dc0807fd889-deu.vtt'

        # create placeholder recording with the current state
        r = upsert_recording(guid, {
            "filename": filename,
            "mime_type": "text/vtt",
            "language": item['media_language'],
            "state": mapping.get(int(item['state']), 'state-' + item['state'])
        })
        # target = r['public_url'].replace('https://static.media.ccc.de/media/', '/static.media.ccc.de/')

    # time.sleep(1)


def upsert_recording(guid, data):
    data = {
        "api_key": environ['VOCTOWEB_API_KEY'],
        "guid": guid,
        "recording": {
            "folder": "",
            **data
        } 
    }
    if not(dry_run):
        # create or update recording in voctoweb
        r = requests.post(VOCTOWEB_API_URL + '/recordings', headers={'CONTENT-TYPE': 'application/json'}, json=data)
        if r.status_code not in [200, 201]:
            print("  {}".format(r.status_code))
            print("  " + r.text.split('\n')[0])
            slow_down and time.sleep(5)
            if r.status_code == 422:
                return r.json()
            return False
        print(f"  {'created' if r.status_code == 201 else 'updated'} recording successfully")
        print(f"    {r.text}")
        return r.json()
    print('…')
    slow_down and time.sleep(0.1)


def load_last_run_timestamp():
    if path.isfile(".last_media_sync_run"):
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
            try:
                sftp.mkdir(path.dirname(target))
            except:
                pass
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
