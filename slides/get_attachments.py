 # -*- coding: UTF-8 -*-
 
import sys
import time
import urllib
import os

import getpass
import pycurl
from lxml import etree
from cStringIO import StringIO
from matplotlib.cbook import Null

reload(sys)
sys.setdefaultencoding('utf-8')


offline = True # True -> Schedules nicht von frab.cccv.de herunterladen (benötigt Account)
LOGIN_HOST = "https://frab.cccv.de"

ACRONYMS = [
#            "17c3", "18c3",
#            "19c3", "20c3", "21c3", 
#            "22c3", "23c3", "24c3", "25c3", "26c3", "27c3", "28c3",
#            "29c3", "30c3", "31c3",
#            "camp2011", "camp2015",
            "32c3"
            ]



LOGIN_URL = "%s/en/session/new" % (LOGIN_HOST)
LOGIN_SUBMIT = "%s/en/session" % (LOGIN_HOST)
# https://frab.cccv.de/en/17c3/public/schedule.xml
SCHEDULE_URL = "%s/en/%s/public/schedule.xml"


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
    curl.setopt(pycurl.COOKIEFILE, '')
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
    print "acquire token"
    buf = setupCurl(curl, LOGIN_URL)
    print "GET %s" % (LOGIN_URL)
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
    print "GET %s" % (LOGIN_SUBMIT)
    curl.perform()
    assert curl.getinfo(pycurl.HTTP_CODE) == 302, "failed to login"


def download(curl, conference_acronym):
    '''
    Perform download of fahrplan.
    
    @type curl: pycurl.Curl
    '''
    
    #url = "https://frab.cccv.de/en/17c3/public/schedule.xml"
    url = SCHEDULE_URL % (LOGIN_HOST, conference_acronym)

    
    print "download %s schedule" % (conference_acronym)
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

    

    print "done"



if __name__ == '__main__':
    if not offline:
        curl = pycurl.Curl()
        token = acquireToken(curl)
        time.sleep(2)
        USERNAME = raw_input("Username: ")
        PASSWORD = getpass.getpass()
        login(curl, token, USERNAME, PASSWORD)
        time.sleep(4)
        
    ul = urllib.URLopener()
    
    for conference in ACRONYMS:
        schedule = Null
        if offline:
            with open("data/schedule_" + conference + ".xml") as f:
                buf = f.read()
                schedule = etree.fromstring(buf).getroottree()
        else:    
            buf = download(curl, conference)
            schedule = etree.parse(buf)
        
        for attachments in schedule.xpath('.//event/attachments[count(*)>1]'):
            #print etree.tostring(attachment)
            #print attachment.xpath('../../slug')[0].text
            
            slug = attachments.xpath('../slug')[0].text
            
            print slug
            
            for attachment in attachments:
                basename = os.path.basename(attachment.attrib['href']).split('?')[0] 
                ext = os.path.splitext(basename)[1][1:].lower()
                
                # skip specific files
                if ext == "torrent" or basename == "missing.png":
                    continue

                
                title = attachment.text
                file_url = LOGIN_HOST + attachment.attrib['href'].split('?')[0] 
                

                
                print "   " +  ", ".join([ext, title, basename]) #  ''', file_url'''
                #ul.retrieve(LOGIN_HOST + attachment.attrib['href'], "download/" + attachment.xpath('../../slug')[0].text + ".pdf")


