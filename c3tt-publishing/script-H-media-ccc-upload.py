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
import inspect
import logging

from c3t_rpc_client import * 
from media_ccc_de_api_client import *
from auphonic_client import *
from youtube_client import *
from twitter_client import *

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logging.addLevelName( logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName( logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.addLevelName( logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
logging.addLevelName( logging.DEBUG, "\033[1;85m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logging.info("C3TT publishing")
logging.debug("reading config")

### handle config
#make sure we have a config file
if not os.path.exists('client.conf'):
    logging.error("Error: config file not found")
    sys.exit(1)
    
config = configparser.ConfigParser()
config.read('client.conf')
source = config['general']['source']
dest = config['general']['dest']

source = "c3tt" #TODO quickfix for strange parser behavior

if source == "c3tt":
    ################### C3 Tracker ###################
    #project = "projectslug"
    group = config['C3Tracker']['group']
    secret =  config['C3Tracker']['secret']

    if config['C3Tracker']['host'] == "None":
            host = socket.getfqdn()
    else:
        host = config['C3Tracker']['host']

    url = config['C3Tracker']['url']
    from_state = config['C3Tracker']['from_state']
    to_state = config['C3Tracker']['to_state']
    token = config['twitter']['token'] 
    token_secret = config['twitter']['token_secret']
    consumer_key = config['twitter']['consumer_key']
    consumer_secret = config['twitter']['consumer_secret']

if True:
    ################### media.ccc.de #################
    #API informations
    api_url =  config['media.ccc.de']['api_url']
    api_key =  config['media.ccc.de']['api_key']
    #download_thumb_base_url = config['media.ccc.de']['download_thumb_base_url']
    #download_base_url = config['media.ccc.de']['download_base_url']

    #release host information
    # upload_host = config['media.ccc.de']['uplod_host']
    # upload_user = config['media.ccc.de']['upload_user']
    # upload_pw = config['media.ccc.de']['upload_pw'] #it is recommended to use key login. PW musts be set but can be random
    # upload_path = config['media.ccc.de']['upload_path']

#if we dont use the tracker we need to get the informations from the config
if source != 'c3tt':
    #################### conference information ######################
    rec_path = config['conference']['rec_path']
    image_path = config['conference']['image_path']
    webgen_loc = config['conference']['webgen_loc']

    ################### script environment ########################
    # base dir for video input files (local)
    video_base = config['env']['video_base']
    # base dir for video output files (local)
    output = config['env']['output']

#path to the thumb export.
#this is also used as postfix for the publishing dir
thumb_path = config['env']['thumb_path']

# #codec / container related paths
# #this paths should be the same on media and local !!
# #if you want to add new codecs make sure media.ccc.de knows the mimetype BEFORE you push something
# codecs = {
# "h264" : {"path" : "mp4/",
#           "ext" : ".mp4",
#           "mimetype" : "video/mp4"},
# "webm" : {"path" : "webm/",
#           "ext": ".webm",
#           "mimetype" : "video/webm"},
# "ogv" : {"path" : "ogv/",
#          "ext" : ".ogv",
#          "mimetype" : "video/ogg"},
# "mp3" : {"path" : "mp3/", 
#          "ext" : ".mp3",
#          "mimetype" : "audio/mpeg"},
# "opus" : {"path" : "opus/",
#           "ext" : ".opus", 
#           "mimetype" : "audio/opus"},
# "ogg"  : {"path" : "ogg/",
#           "ext"  :  ".ogg"}
# }

#internal vars
ticket = None
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
title = None
subtitle = None 
description = None
profile_slug = None
folder = None
mime_type = None
target_youtube = None
target_media = None

def choose_target_from_properties():
    global target_youtube
    global target_media

    logging.debug("encoding profile youtube flag: " + ticket['Publishing.YouTube.EnableProfile'] + " project youtube flag: " + ticket['Publishing.YouTube.Enable'])
    if ticket['Publishing.YouTube.EnableProfile'] == "yes" and ticket['Publishing.YouTube.Enable'] == "yes" and not has_youtube_url:
        logging.debug("publishing on youtube")
        target_youtube = True
        youtubeFromTracker()

    logging.debug("encoding profile media flag: " + ticket['Publishing.Media.EnableProfile'] + " project media flag: " + ticket['Publishing.Media.Enable'])
    if ticket['Publishing.Media.EnableProfile'] == "yes" and ticket['Publishing.Media.Enable'] == "yes":
        logging.debug("publishing on media")
        target_media = True
        mediaFromTracker()

################################# Here be dragons #################################
def iCanHazTicket():
    logging.info("getting ticket from " + url)
    logging.info("=========================================")
    
    #check if we got a new ticket
    global ticket_id
    ticket_id = assignNextUnassignedForState(from_state, to_state, url, group, host, secret)
    if ticket_id != False:
        #copy ticket details to local variables
        logging.info("Ticket ID:" + str(ticket_id))
        global ticket
        ticket = getTicketProperties(str(ticket_id), url, group, host, secret)
        logging.debug("Ticket: " + str(ticket))
        global acronym
        global local_filename
        global local_filename_base
        global profile_extension
        global profile_slug
        global video_base
        global output
        global filename
        global guid
        global slug
        global title
        global subtitle 
        global description
        global download_base_url
        global folder
        global has_youtube_url
        global people
        global tags
        global language #language field in ticket
        global lang #lang for single audio release
        
        #TODO add here some try magic to catch missing properties

        if 'Fahrplan.Slug' in ticket:
                slug = ticket['Fahrplan.Slug']	
        else:
                slug = str(ticket['Encoding.Basename'])

        slug_c = slug.replace(":","_")    
        guid = ticket['Fahrplan.GUID']
        acronym = ticket['Project.Slug']
        filename = str(ticket['EncodingProfile.Basename']) + "." + str(ticket['EncodingProfile.Extension'])
        title = ticket['Fahrplan.Title']
        if 'Fahrplan.Person_list' in ticket:
                people = ticket['Fahrplan.Person_list'].split(', ') 
        else:
                people = [ ]
        if 'Media.Tags' in ticket:
                tags = ticket['Media.Tags'].replace(' ', ''). \
                                            split(',')
        else:
                tags = [ ticket['Project.Slug'] ]
        local_filename = str(ticket['Fahrplan.ID']) + "-" +ticket['EncodingProfile.Slug'] + "." + ticket['EncodingProfile.Extension']
        local_filename_base =  str(ticket['Fahrplan.ID']) + "-" + ticket['EncodingProfile.Slug']
        video_base = str(ticket['Publishing.Path'])
        output = str(ticket['Publishing.Path']) + "/"+ str(thumb_path)
        download_base_url =  str(ticket['Publishing.Base.Url'])
        profile_extension = ticket['EncodingProfile.Extension']
        profile_slug = ticket['EncodingProfile.Slug']
        if 'Record.Language' in ticket:
            language = str(ticket['Record.Language'])
        else:
            logging.error("No Record.Language propertie in ticket")
            setTicketFailed(ticket_id, "No Record.Language propertie in ticket", url, group, host, secret)
            sys.exit(-1)
            
        if 'YouTube.Url0' in ticket and ticket['YouTube.Url0'] != "":
                has_youtube_url = True
        else:
                has_youtube_url = False
        title = ticket['Fahrplan.Title']
        folder = ticket['EncodingProfile.MirrorFolder']
        
        if 'Fahrplan.Subtitle' in ticket:
                subtitle = ticket['Fahrplan.Subtitle']
        if 'Fahrplan.Abstract' in ticket:
                description = ticket['Fahrplan.Abstract']
        #debug
        logging.debug("Data for media: guid: " + guid + " slug: " + slug_c + " acronym: " + acronym  + " filename: "+ filename + " title: " + title + " local_filename: " + local_filename + ' video_base: ' + video_base + ' output: ' + output + ' people: ' + ", ".join(people) + ' tags: ' + ", ".join(tags) + ' language: ' + language)
        
        if not os.path.isfile(video_base + local_filename):
            logging.error("Source file does not exist (%s)" % (video_base + local_filename))
            setTicketFailed(ticket_id, "Source file does not exist (%s)" % (video_base + local_filename), url, group, host, secret)
            sys.exit(-1)
        if not os.path.exists(output):
            logging.error("Output path does not exist (%s)" % (output))
            setTicketFailed(ticket_id, "Output path does not exist (%s)" % (output), url, group, host, secret)
            sys.exit(-1)
        else: 
            if not os.access(output, os.W_OK):
                logging.error("Output path is not writable (%s)" % (output))
                setTicketFailed(ticket_id, "Output path is not writable (%s)" % (output), url, group, host, secret)
                sys.exit(-1)
    else:
        logging.warn("No ticket for this task, exiting")
        sys.exit(0);

def mediaFromTracker():
    logging.info("creating event on " + api_url)
    logging.info("=========================================")

    #create a event on media
    if profile_slug != "mp3" and profile_slug != "opus":          
        try:
            make_event(api_url, download_base_url, local_filename, local_filename_base, api_key, acronym, guid, video_base, output, slug, title, subtitle, description, people, tags, language)
        except RuntimeError as err:
            logging.error("Creating event failed")
            setTicketFailed(ticket_id, "Creating event failed, in case of audio releases make sure event exists: \n" + str(err), url, group, host, secret)
            sys.exit(-1)
    else:
        lang_id = ticket['Encoding.LanguageIndex']
        langs = language.rsplit('-')
        language = str(langs[lang_id])
        filename = str(ticket['Encoding.LanguageTemplate']) % (language)
        filename = filename + str(ticket['EncodingProfile.Extension']
        #filename = str(slug + '-' + str(ticket['Fahrplan.ID']) + '-' + language + '-' + str(ticket['Encoding.LanguageTemplate']) + '.' + str(ticket['EncodingProfile.Extension'] )
        logging.debug('Choosing ' + language +' with LanguageIndex ' + lang_id + ' and filename ' + filename)
         
    #publish the media file on media
    if not 'Publishing.Media.MimeType' in ticket:
        setTicketFailed(ticket_id, "Publishing failed: No mime type, please use property Publishing.Media.MimeType in encoding profile! \n" + str(err), url, group, host, secret)
    mime_type = ticket['Publishing.Media.MimeType']

    try:
        publish(local_filename, filename, api_url, download_base_url, api_key, guid, filesize, length, mime_type, folder, video_base, language)
    except RuntimeError as err:
        setTicketFailed(ticket_id, "Publishing failed: \n" + str(err), url, group, host, secret)
        logging.error("Publishing failed: \n" + str(err))
        sys.exit(-1) 
                 
    # set ticket done
    logging.info("set ticket done")
    setTicketDone(ticket_id, url, group, host, secret)
                     
def auphonicFromTracker():
    logging.info("Pushing file to Auphonic")

def youtubeFromTracker():
    try:
        youtubeUrls = publish_youtube(ticket, config['youtube']['client_id'], config['youtube']['secret'])
        props = {}
        for i, youtubeUrl in enumerate(youtubeUrls):
            props['YouTube.Url'+str(i)] = youtubeUrl

        setTicketProperties(ticket_id, props, url, group, host, secret)

    except RuntimeError as err:
        setTicketFailed(ticket_id, "Publishing failed: \n" + str(err), url, group, host, secret)
        logging.error("Publishing failed: \n" + str(err))
        sys.exit(-1)

iCanHazTicket()
choose_target_from_properties()
#send_tweet(ticket, token, token_secret, consumer_key, consumer_secret)
logging.info("set ticket done")
#setTicketDone(ticket_id, url, group, host, secret)
