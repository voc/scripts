#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
 
import sys, os
import time
import urllib
import requests
from datetime import datetime

import getpass
import pycurl
from lxml import etree
from cStringIO import StringIO

import configparser
import argparse

reload(sys)
sys.setdefaultencoding('utf-8')

cp = configparser.ConfigParser()
cp.read('attachments.conf')
config = cp

parser = argparse.ArgumentParser(description='Download slide pdfs directly from frab')
parser.add_argument('--since', action='store', default=0, type=int)
parser.add_argument('--verbose', '-v', action='store_true', default=False)
parser.add_argument('--offline', action='store_true', default=True)
parser.add_argument('--published', action='store_true', default=False)

args = parser.parse_args()


offline = args.offline # True -> Schedules nicht von frab.cccv.de herunterladen (benötigt Account)


LOGIN_HOST = "https://frab.cccv.de"

ACRONYMS = [
#            "17c3", "18c3",
#            "19c3", "20c3", "21c3",
#            "22c3", "23c3", "24c3", "25c3", "26c3", "27c3", "28c3",
#            "29c3", "30c3", "31c3", "32c3",
#            "camp2011", "camp2015",
#            "33c3",
             "34c3"
            ][::-1]


LANG_MAP = {
    "en" : "eng",
    "de" : "deu"
}


LOGIN_URL = "%s/users/sign_in" % (LOGIN_HOST)
LOGIN_SUBMIT = "%s/users/sign_in?locale=en" % (LOGIN_HOST)
# https://frab.cccv.de/en/17c3/public/schedule.xml
SCHEDULE_URL = "%s/en/%s/public/schedule.xml"


dry_run = True


'''
frab login code kommt von fahrplan deploy skript von nexus
  TODO von pycurl auf requests lib umstellen

TODO: frab code in eigene datei auslagern
TODO: public media.ccc.de api mit einbinden um an die conference acronyyms zu kommen

'''


def setupCurl(curl, url):
    '''
    Common ration for curl instances.
    
    @type curl: pycurl.Curl
    @type url: str
    @rtype StringIO
    '''
    buf = StringIO()
    curl.setopt(pycurl.TIMEOUT, 1)
    curl.setopt(pycurl.COOKIEFILE, './temp.txt') # Turn on cookies
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.WRITEFUNCTION, buf.write)
    # curl.setopt(pycurl.HEADERFUNCTION, header)
    curl.setopt(pycurl.CONNECTTIMEOUT, 0)
    curl.setopt(pycurl.TIMEOUT, 0)
    # curl.setopt(pycurl.SSL_VERIFYPEER, 0)
    curl.setopt(pycurl.POST, 0)
    return buf

def acquireToken(curl):
    '''
    Acquires a login token.
    
    @type curl: pycurl.Curl
    '''
    print("acquire token")
    buf = setupCurl(curl, LOGIN_URL)
    print("GET %s" % (LOGIN_URL))
    curl.perform()
    assert curl.getinfo(pycurl.HTTP_CODE) == 200, "failed to acquire token"
    parser = etree.HTMLParser()
    buf.reset()
    tree = etree.parse(buf, parser=parser, base_url=LOGIN_URL)
    token = tree.xpath(".//meta[@name='csrf-token']")
    return token[0].attrib["content"]
    
def login(curl, token, username, password):
    '''
    Perform login on website.
    
    @type username: str
    @type password: str
    @type curl: pycurl.Curl
    '''
        
    print "login with token %s" % token
    setupCurl(curl, LOGIN_SUBMIT)
    curl.setopt(pycurl.POST, 1)
    curl.setopt(pycurl.POSTFIELDS, "authenticity_token=%s&user[email]=%s&user[password]=%s" % (token, username, password))
    print "POST %s" % (LOGIN_SUBMIT)
    curl.perform()
    assert curl.getinfo(pycurl.HTTP_CODE) == 302, "failed to login"

def download(curl, conference_acronym):
    '''
    Perform download of fahrplan.
    
    @type curl: pycurl.Curl
    '''
    
    #url = "https://frab.cccv.de/en/17c3/public/schedule.xml"
    url = SCHEDULE_URL % (LOGIN_HOST, conference_acronym)

    
    print"download %s schedule" % (conference_acronym)
    buf = setupCurl(curl, url)
    curl.setopt(pycurl.TIMEOUT, 6000)
    print "GET %s" % (url)
    curl.perform()
    if curl.getinfo(pycurl.HTTP_CODE) != 200:
        print buf.getvalue()
    assert curl.getinfo(pycurl.HTTP_CODE) == 200, "failed to download schedule"
    
    #print "store schedule to disk"
    dumpfile = open("data/schedule_" + conference_acronym + ".xml", "w")   
    dumpfile.write(buf.getvalue())
    dumpfile.close()
    buf.reset()
    
    return buf

    

    print("done")


if __name__ == '__main__':
    curl = pycurl.Curl()
    if not args.published and not offline:
        token = acquireToken(curl)
        time.sleep(3)
        USERNAME = raw_input("Username: ")
        PASSWORD = getpass.getpass()
        login(curl, token, USERNAME, PASSWORD)
        time.sleep(6)
        
    ul = urllib.URLopener()
    
    for conference in ACRONYMS:
        schedule = None
        if offline:
            with open("data/schedule_" + conference + ".xml") as f:
                buf = f.read()
                schedule = etree.fromstring(buf).getroottree()
        elif args.published:

            schedule = etree.fromstring(requests.get("http://events.ccc.de/congress/2017/Fahrplan/schedule.xml").content)
        else:
            # download current (probably not published version) from frab
            buf = download(curl, conference)
            schedule = etree.parse(buf)

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


                else:
                    if args.verbose: print('   ignoring: ' + basename)
                    continue



        if args.verbose: print('')
        print("{}: {:3d} events with attachments, and {:3d} missing.png – last change {}".format(conference, count, count_missing, datetime.fromtimestamp(max_time)))
        if args.verbose: print('')