#!/bin/python3
import urllib.request, urllib.parse, urllib.error
import hashlib 
import time
import subprocess
import datetime

interval = 30
version_url = "http://events.ccc.de/congress/2014/Fahrplan/version"

version = None
while True:
   try:
      res = urllib.request.urlopen(version_url,timeout=2)   
   except urllib.error.URLError as err:
      print("could not get Fahrplan from " + str(version_url))
      print("reason " + str(err.reason))
      time.sleep(interval)
      continue
   text = res.read().decode('UTF-8')
   tmp = str(text).replace('\n',' ')
   inpos= tmp.rfind('URL: ')
   outpos = len(tmp)
   url = tmp[inpos+5:outpos]
   tmphash = hashlib.md5()
   tmphash.update(url.encode('UTF-8'))
   if (tmphash.hexdigest() != version):
      print(str(datetime.datetime.now()) + " new schedule")
      version = tmphash.hexdigest()
      tgz = urllib.request.urlopen(url)
      target = open('schedule.tar.gz','wb')
      target.write(tgz.read())
      try:
         res = subprocess.check_call(['tar', '-xzf', 'schedule.tar.gz'])
      except subprocess.CalledProcessError as err:
         print("error unpacking tar")
   else:
      print(str(datetime.datetime.now()) + " no schedule update")
   time.sleep(interval) 
