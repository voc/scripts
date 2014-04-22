#!/usr/bin/python3
#    Copyright (C) 2014  derpeter
#    derpeter@berlin.ccc.de
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
import argparse
import sys
import os
import urllib.request, urllib.parse, urllib.error
import requests
import subprocess
import xmlrpc.client
import socket
import xml.etree.ElementTree as ET
import json
import configparser
import paramiko

from c3t_rpc_client import C3TClient 
from media_ccc_de_api_client import *
from auphonic_client import *

#make sure we have a config file
if not os.path.exists('client.conf'):
    print("Error: config file not found")
    sys.exit(1)
    
config = configparser.ConfigParser()
config.read('client.conf')

################### C3 Tracker ###################
#project = "projectslug"
group = config['C3Tracker']['group']
secret =  config['C3Tracker']['secret']
host = config['C3Tracker']['host']
url = config['C3Tracker']['url']
from_state = config['C3Tracker']['from_state']
to_state = config['C3Tracker']['to_state']

################### media.ccc.de #################
#API informations
api_url =  config['media.ccc.de']['api_url']
api_key =  config['media.ccc.de']['api_key']
download_thumb_base_url = config['media.ccc.de']['download_thumb_base_url']
download_base_url = config['media.ccc.de']['download_base_url']

#release host information
# upload_host = config['media.ccc.de']['uplod_host']
# upload_user = config['media.ccc.de']['upload_user']
# upload_pw = config['media.ccc.de']['upload_pw'] #it is recommended to use key login. PW musts be set but can be random
# upload_path = config['media.ccc.de']['upload_path']

#################### conference information ######################
rec_path = config['conference']['rec_path']
image_path = config['conference']['image_path']
webgen_loc = config['conference']['webgen_loc']
#currently 4:3 and 16:9 are supported by the media API
aspect = config['conference']['aspect']

################### script environment ########################
# base dir for video input files (local)
video_base = config['env']['video_base'] #in case of C3TT this will be overwritten!!
# base dir for video output files (local)
output = config['env']['output'] #in case of C3TT this will be overwritten!!!
#define paths to the scripts
post = config['env']['post']
#path to the thumb export.
#this is also used as postfix for the publishing dir
thumb_path = config['env']['thumb_path']

#codec / container related paths
#this paths should be the same on media and local !!
#if you want to add new codecs make sure media.ccc.de knows the mimetype BEFORE you push something
codecs = {
"h264" : {"path" : "mp4/",
          "ext" : ".mp4",
          "mimetype" : "video/mp4"},
"webm" : {"path" : "webm/",
          "ext": ".webm",
          "mimetype" : "video/webm"},
"ogv" : {"path" : "ogv/",
         "ext" : ".ogv",
         "mimetype" : "video/ogg"},
"mp3" : {"path" : "mp3/", 
         "ext" : ".mp3",
         "mimetype" : "audio/mpeg"},
"opus" : {"path" : "opus/",
          "ext" : ".opus", 
          "mimetype" : "audio/opus"},
"ogg"  : {"path" : "ogg/",
          "ext"  :  ".ogg"}
}

#internal vars
filesize = 0
length = 0
sftp = None
ssh = None
title = None
frab_data = None
acronyms = None
guid = None
filename = None
debug = 0
slug = None
slug_c = None #slug without :
rpc_client = None

################################## media.ccc.de related functions ##################################

def get_mime_type_from_slug():
  if profile_slug == "h264-iprod":
    return 'vnd.voc/h264-lq'
  if profile_slug == "h264-hq":
    return 'video/mp4'
  if profile_slug == "h264-hd":
    return 'vnd.voc/h264-hd'
  if profile_slug == 'webm':
    return "video/webm"
  if profile_slug == 'ogg':
    return "video/ogg"
  if profile_slug == 'mp3':
    return "audio/mpeg"
  if profile_slug == 'opus':
    return "audio/opus"

################################# SCP functions ##################################
# connect to the upload host 
def connect_ssh():
    print("## Establishing SSH connection ##")
    client = paramiko.SSHClient()
    #client.get_host_keys().add(upload_host,'ssh-rsa', key)
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(upload_host, username=upload_user, password=upload_pw)
    except paramiko.SSHException:
        print("ERROR: SSH negotiation failed")
        print(sys.exc_value)
        sys.exit(1)
    except paramiko.AuthenticationException:
        print ("ERROR: Authentication failed. Please check credentials")
        print (sys.exc_value)
        sys.exit(1)
    except paramiko.BadHostKeyException:
        print ("ERROR: Bad host key. Check your known_hosts file")
        print (sys.exc_value)
        sys.exit(1)
    except paramiko.PasswordRequiredException:
        print ("ERROR: Password required. No ssh key in the agent?")
        print (sys.exc_value)
        sys.exit(1)
    except:
        print ("ERROR: Could not open ssh connection")
        print (sys.exc_value)
        sys.exit(1)
        
    global ssh 
    ssh = client
    global sftp
    sftp = paramiko.SFTPClient.from_transport(client.get_transport())
    print ("SSH connection established")
    
# push the thumbs to the upload host
def upload_thumbs():
    print ("## uploading thumbs ##")
    
    # check if ssh connection is open
    if ssh == None or sftp == None:
        connect_ssh()
    thumbs_ext = {".gif",".jpg","_preview.jpg"}
    for ext in thumbs_ext:
        try:
            sftp.put(output + thumb_path + local_filename_base + ext, upload_path + thumb_path + guid + ext)
        except paramiko.SSHException:
            print ("ERROR: could not upload thumb becaus of SSH problem")
            print (sys.exc_value)
            sys.exit(1)
        except IOError:
            print ("ERROR: could not create file in upload dir")
            print (sys.exc_value)
            sys.exit(1)
            
    print ("uploading thumbs done")

#uploads a file from path relative to the output dir to the same path relative to the upload_dir
def upload_file(filename, path):
    print ("## uploading "+ path + filename + " ##")
    
    # check if ssh connection is open
    if (ssh == None or sftp == None):
        connect_ssh()
    
    try:
        sftp.put(output + path + filename, upload_path + path + filename)
    except paramiko.SSHException:
        print ("ERROR: could not upload thumb becaus of SSH problem")
        print (sys.exc_value)
        sys.exit(1)
    except IOError:
        print ("ERROR: could not create file in upload dir")
        print (sys.exc_value)
        sys.exit(1)
            
    print ("uploading " + filename + " done")
    
################################# Here be dragons #################################
def iCanHazTicket():
    #check if we got a new ticket
    ticket_id = assignNextUnassignedForState()
    if ticket_id != False:
        #copy ticket details to local variables
        #TODO make this nice
        print("Ticket ID:" + str(ticket_id))
        ticket = getTicketProperties(str(ticket_id))
        global acronym
        global local_filename
        global local_filename_base
        global profile_extension
        global profile_slug
        guid = ticket['Fahrplan.GUID']
        slug = ticket['Fahrplan.Slug']
        slug_c = slug.replace(":","_")    
        acronym = ticket['Meta.Acronym']
        filename = str(ticket['EncodingProfile.Basename']) + "." + str(ticket['EncodingProfile.Extension'])
        title = ticket['Fahrplan.Title']
        local_filename = ticket['Fahrplan.ID'] + "-" + ticket['EncodingProfile.Slug'] + "." + ticket['EncodingProfile.Extension']
        local_filename_base =  ticket['Fahrplan.ID'] + "-" + ticket['EncodingProfile.Slug']
        video_base = str(ticket['Processing.BaseDir']) + str(ticket['Processing.RelPath.Prerelease'])
        output = str(ticket['Processing.BaseDir']) + str(ticket['Processing.RelPath.Output'])
        profile_extension = ticket['EncodingProfile.Extension']
        profile_slug = ticket['EncodingProfile.Slug']
        #debug
        print("Data for media: guid: " + guid + " slug: " + slug_c + " acronym: " + acronym  + " filename: "+ filename + " title: " + title + " local_filename: " + local_filename + ' video_base: ' + video_base + ' output: ' + output)
    else:
        print("No ticket for this task, exiting")
        sys.exit(0);

def eventFromC3TT():
    #create the event on media
    if make_event():
        if(not publish()):
            #publishing has failed => set ticket failed
            setTicketFailed(ticket_id, "Error_during_publishing")
            #debug 
            print("Publishing failed")
            sys.exit()
          
        # set ticket done
        else:
            #debug
            print("set ticket done")
            setTicketDone(ticket_id)
    else:
        print("event creation on media.ccc.de failed")
        setTicketFailed(ticket_id, "Error_during_creation_of_event_on_media")
                     
def auphonicFromTracker():
    print("Pushing file to Auphonic")
    

