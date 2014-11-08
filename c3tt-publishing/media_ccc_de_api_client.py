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
# generate thumbs

import subprocess
import urllib.request, urllib.parse, urllib.error
import requests
import json
import sys
import os
import logging
logger = logging.getLogger()

def make_thumbs(video_base, local_filename, output):
    debug = 1
    
    logger.info(("## generating thumbs for "  + video_base + local_filename + " ##"))

    try:
        subprocess.check_call(["postprocessing/generate_thumb_autoselect_compatible.sh", video_base + local_filename, output])
    except subprocess.CalledProcessError as err:
        logger.error("A fault occurred")
        logger.error("Fault code: %d" % err.returncode)
        logger.error("Fault string: %s" % err.output)
        logger.error("Command %s" % err.cmd)
        return False
         
    logger.info("thumbs created")
    return True
    
# make a new event on media
def make_event(api_url, download_base_url, local_filename, local_filename_base, api_key, acronym, guid, video_base, output, slug, title, subtitle, description):
    logger.info(("## generating new event on " + api_url + " ##"))
    
    #generate the thumbnails (will not overwrite existing thumbs)
    if not os.path.isfile(output + "/" + str(local_filename_base) + ".jpg"):
        if not make_thumbs(video_base, local_filename, output):
            return False
    else:
        logger.info("thumb exists skipping")
            
    # prepare variables for api call
    thumb_url = download_base_url + "thumbs/" + str(local_filename_base) + ".jpg"
    poster_url = download_base_url + "thumbs/" + str(local_filename_base) + "_preview.jpg"
    url = api_url + 'events'
    headers = {'CONTENT-TYPE' : 'application/json'}
    payload = {'api_key' : api_key,
               'acronym' : acronym,
               'guid' : guid,
               'poster_url' : poster_url,
               'thumb_url' : thumb_url,
	       'slug' : slug,
	       'title' : title,
	       'subtitle' : subtitle,
	       'description' : description
	      }     
    logger.debug(payload)

    #call media api (and ignore SSL this should be fixed on media site)
    try:
        logger.debug("api url: " + url)
        r = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
    except requests.packages.urllib3.exceptions.MaxRetryError as err:
        logger.error("Error during creating of event: " + str(err))
        return False
#     except:
#         logger.error("Unhandelt ssl / retry problem")
#         return False
    
    if r.status_code == 200 or r.status_code == 201:
        logger.debug(r.text)
        logger.info("new event created")
        return True
    else:
        if r.status_code == 422:
            logger.info("event already exists. => publishing")
            return True
        else:
            logger.error(("ERROR: Could not add event: " + str(r.status_code) + " " + r.text))
            return False

# get filesize and length of the media file
def get_file_details(local_filename, video_base):
    if local_filename == None:
        logger.error("Error: No filename supplied.")
    
    if os.path.exists(video_base + local_filename):
        global filesize    
        filesize = os.stat(video_base + local_filename).st_size
        filesize = int(filesize / 1024 / 1024)
        
        try:
            global r
            r = subprocess.check_output('ffprobe -print_format flat -show_format -loglevel quiet ' + video_base + local_filename +' 2>&1 | grep format.duration | cut -d= -f 2 | sed -e "s/\\"//g" -e "s/\..*//g" ', shell=True)
        except:
            logger.error("ERROR: could not get duration " + exc_value)
        #result = commands.getstatusoutput("ffprobe " + output + path + filename + " 2>&1 | grep Duration | cut -d ' ' -f 4 | sed s/,// ")
        global length
        length = int(r.decode())
        if length == 0:
            logger.error("Error: file length is 0")
        else:
            logger.debug("filesize: " + str(filesize) + " length: " + str(length))
            return [filesize,length]
    else:
        logger.error("Error: " + video_base + local_filename + " not found")
        sys.exit(1)

# publish a file on media
def publish(local_filename, filename, api_url, download_base_url, api_key, guid, filesize, length, mime_type, folder, video_base):
    logger.info(("## publishing "+ filename + " to " + api_url + " ##"))
    
    #orig_file_url = download_base_url + codecs[args.codecs]['path'] + filename
    orig_file_url = download_base_url + local_filename 
    
    # make sure we have the file size and length
    ret = get_file_details(local_filename, video_base)
    
    url = api_url + 'recordings'
    headers = {'CONTENT-TYPE' : 'application/json'}
    payload = {'api_key' : api_key,
               'guid' : guid,
               'recording' : {'original_url' : orig_file_url,
                              'filename' : filename,
                              'folder' : folder,
                              'mime_type' : mime_type,
                              'size' : str(ret[0]),
                              'length' : str(ret[1])
                              }
               }
    logger.debug(payload)
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
    except requests.exceptions.SSLError:
        logger.error("ssl cert error")
        return False
    except requests.packages.urllib3.exceptions.MaxRetryError as err:
        logger.error("Error during creating of event: " + str(err))
        return False
    except:
        logger.error ("Unhandelt ssl / retry problem")
        return False
    
    if r.status_code != 200 and r.status_code != 201:
        logger.error(("ERROR: Could not publish talk: " + str(r.status_code) + " " + r.text))
        return False
    
    logger.info(("publishing " + filename + " done"))
    return True
