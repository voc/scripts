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


def make_thumbs(video_base, local_filename, aspect, output):
    debug = 1
    print(("## generating thumbs for "  + video_base + local_filename + " ##"))
    if (aspect == "16:9"):
        print("making 16:9 thumbs")
        if debug > 0:
            print(video_base)
            print("DEBUG: sh postprocessing/generate_thumbs_wide16-9.sh " + video_base + local_filename + " " + output)
        result = subprocess.check_output(["postprocessing/generate_thumbs_wide16-9.sh" , video_base + local_filename , output])
        print(result)
    if (aspect == "4:3"):
        if debug > 0:
            print("sh postprocessing/generate_thumbs.sh" + video_base + local_filename + " " + output)
        print("making 4:3 thumbs")
        result = subprocess.check_output(["postprocessing/generate_thumbs.sh" , video_base + local_filename , output])
    print("thumbs created")
    
# make a new event on media
def make_event(api_url, download_thumb_base_url, local_filename, local_filename_base, api_key, acronym, guid, video_base, aspect, output, slug):
    print(("## generating new event on " + api_url + " ##"))
    
    #generate the thumbnails (will not overwrite existing thumbs)
    make_thumbs(video_base, local_filename, aspect, output)
        
    # prepare variables for api call
    thumb_url = download_thumb_base_url + local_filename_base + ".jpg"
    poster_url = download_thumb_base_url + local_filename_base + "_preview.jpg"
    preview_url = download_thumb_base_url + local_filename_base +".gif"
    url = api_url + 'events'
    headers = {'CONTENT-TYPE' : 'application/json'}
    payload = {'api_key' : api_key,
               'acronym' : acronym,
               'guid' : guid,
               'slug' : slug,
               'poster_url' : poster_url,
               'thumb_url' : thumb_url,
               'gif_url' : preview_url }     

    #call media api (and ignore SSL this should be fixed on media site)
    try:
        print("api url: " + url)
        r = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
    except requests.packages.urllib3.exceptions.MaxRetryError as err:
        print("Error during creating of event: " + str(err))
        return False
#     except:
#         print ("Unhandelt ssl / retry problem")
#         return False
    
    if r.status_code == 200 or r.status_code == 201:
        print("new event created")
        return True
    else:
        if r.status_code == 422:
            print("event already exists. => publishing")
            return True
        else:
            print(("ERROR: Could not add event: " + str(r.status_code) + " " + r.text))
            return False

# get filesize and length of the media file
def get_file_details(local_filename, video_base):
    if local_filename == None:
        print("Error: No filename supplied.")
        sys.exit(1)
    
    if os.path.exists(video_base + local_filename):
        global filesize    
        filesize = os.stat(video_base + local_filename).st_size
        filesize = int(filesize / 1024 / 1024)
        
        try:
            global r
            r = subprocess.check_output('ffprobe ' + video_base + local_filename +" 2>&1 | grep Duration | cut -d ' ' -f 4 | sed s/,// ", shell=True)
        except:
            print("ERROR: could not get duration " + exc_value)
        #result = commands.getstatusoutput("ffprobe " + output + path + filename + " 2>&1 | grep Duration | cut -d ' ' -f 4 | sed s/,// ")
        global length
        length = r.decode().split(":")            
        length = (int(length[0]) * 60 + int(length[1])) * 60 + int(length[2])
        if length == 0:
            print("Error: file length is 0")
        else:
            print("filesize: " + str(filesize) + " length: " + str(length))
            return [filesize,length]
    else:
        print("Error: " + video_base + local_filename + " not found")
        sys.exit(1)

# publish a file on media
def publish(local_filename, filename, api_url, download_base_url, api_key, guid, filesize, length, mime_type, folder, video_base):
    print(("## publishing "+ filename + " to " + api_url + " ##"))
    
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
    print(payload)
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
    except requests.exceptions.SSLError:
        print("ssl cert error")
    except requests.packages.urllib3.exceptions.MaxRetryError as err:
        print("Error during creating of event: " + str(err))
        return False
    except:
        print ("Unhandelt ssl / retry problem")
        return False
    
    if r.status_code != 200 and r.status_code != 201:
            print(("ERROR: Could not publish talk: " + str(r.status_code) + " " + r.text))
            return False
    
    print(("publishing " + filename + " done"))
    return True