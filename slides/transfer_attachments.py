#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
 
import sys, os
import time
import urllib
import requests
from datetime import datetime
from lxml import etree
import shutil

import configparser
import argparse
import pysftp


cp = configparser.ConfigParser()
cp.read('attachments.conf')
config = cp

parser = argparse.ArgumentParser(description="Transfer slide pdf's from frab to voctoweb")
parser.add_argument('--since', action='store', default=0, type=int)
parser.add_argument('--verbose', '-v', action='store_true', default=False)
parser.add_argument('--offline', action='store_true', default=True)

args = parser.parse_args()


offline = args.offline # True -> Schedules nicht von frab.cccv.de herunterladen (benötigt Account)


LOGIN_HOST = "https://frab.cccv.de"

conference = "35c3"


LANG_MAP = {
    "en" : "eng",
    "de" : "deu"
}

dry_run = False

base_folder = "/cdn.media.ccc.de/congress/2018/slides-pdf/"

if __name__ == '__main__':
    schedule = None
    if offline:
        with open("data/schedule_" + conference + ".xml", "r", encoding='utf-8') as f:
            schedule = etree.parse(f)
    else:
        r = requests.get("http://events.ccc.de/congress/2018/Fahrplan/schedule.xml")
        schedule = etree.fromstring(r.content)

    if not dry_run:
        sftp = pysftp.Connection('koeln.media.ccc.de', username='cdn-app', private_key='~/.ssh/id_cdn-app_media')
        sftp.cd('cdn.media.ccc.de/congress/2018/slides-pdf/')

    count = 0
    count_missing = 0
    max_time = 0

    for attachments in schedule.xpath('.//event/attachments[count(*)>=1]'):
        count += 1

        event = attachments.xpath('..')[0]
        slug = event.find('slug').text

        if args.verbose: print(slug)

        pdf_count = 0
        pdfs = []
        for attachment in attachments:
            basename = os.path.basename(attachment.attrib['href']).split('?')[0]
            ext = os.path.splitext(basename)[1][1:].lower()

            # skip specific files
            if ext == "torrent" or basename == "missing.png":
                #if args.verbose: print('   ignoring: ' + basename)
                count_missing += 1
                continue

            title = attachment.text

            str =  (title + basename).lower()
            if 'abstract' in str or 'paper' in str or 'bierzerlegung' in str:
                if args.verbose: print('   ignoring: ' + basename)
                continue

            file_path, time  = attachment.attrib['href'].split('?')
            time = int(time)
            if time > max_time:
                max_time = time


            if ext == "pdf" and time > args.since:
                pdf_count += 1
                # presentation, slide, folien
                if args.verbose: print("   " + ", ".join([ext, title, basename]))

                file_url = LOGIN_HOST + file_path

                with urllib.request.urlopen(file_url) as u:

                    if u.getcode() != 200:
                        sys.stderr.write(" \033[91mERROR: file is not accesible \033[0m\n")
                        continue

                    file_size = int(u.getheader("Content-Length"))
                    target_file_name = slug + ".pdf"
                    target_file_path = os.path.join(base_folder, target_file_name)

                    if not dry_run:
                        with sftp.open(target_file_path, "wb") as f:
                            shutil.copyfileobj(u, f)

                    url = 'https://media.ccc.de/api/recordings'
                    data = {
                        "api_key": "xxx",
                        "guid": event.attrib['guid'],
                        "recording": {
                            "filename": target_file_name,
                            "language": LANG_MAP[event.find('language').text],
                            "mime_type": "application/pdf",
                            "size": int(file_size / 1024 / 1024),
                            "folder": "slides-pdf"
                    } }

                    r = requests.post(url, headers={'CONTENT-TYPE': 'application/json'}, json=data)
                    if r.status_code != 201:
                        print("  " + r.status_code)
                        print("  " + r.text)
            else:
                print('   ignoring: ' + basename)
                continue



    if args.verbose: print('')
    print("{}: {} events with attachments, and {} missing.png".format(conference, count, count_missing))
    print("  max_time: {}, {}".format(max_time, datetime.fromtimestamp(max_time)))
    if args.verbose: print('')