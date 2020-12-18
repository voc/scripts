#!/usr/bin/python3

import json
import os
import urllib.request
import sys
import base64
import re

status_url = "http://localhost:7999/status-json.xsl"
graphite_url = "https://monitoring.c3voc.de/graphite/render?target=summarize(minion*_lan_c3voc_de.systemd_units.gauge.*@*active,%221h%22,%22last%22)&format=json&from=-1h"

def parse_icecast():
    with urllib.request.urlopen(status_url) as conn:
        json_body = conn.read()
    return json.loads(json_body.decode("utf-8"))

def parse_graphite():
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, graphite_url, "winkekatze", "NXGary1q3Inejefuky476phdib6UMu")
    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    opener = urllib.request.build_opener(handler)
    opener.open(graphite_url)
    urllib.request.install_opener(opener)
    with urllib.request.urlopen(graphite_url) as conn:
        json_body = conn.read()
    return json.loads(json_body.decode("utf-8"))

def get_transcodes():
    transcoders = []
    for transcode in parse_graphite():
        transcode_name = transcode['target'].split("(")[-1].split(".")[0]
        transcode_service = transcode['target'].split("(")[-1].split(".")[3].split(",")[0]
        transcode_state = transcode['datapoints'][1][0]
        transcoders.append({"name": transcode_name, "service": transcode_service, "state": transcode_state})
    transcoders.sort(key=lambda item: item["name"])
    return transcoders

def get_sources():
    sources = []
    for source in parse_icecast()["icestats"]["source"]:
        source_name = source["listenurl"].split("/")[-1]
        if source_name.find("_") < 0:
            sources.append({"name": source_name, "start": source['stream_start_iso8601']})
    sources.sort(key=lambda item: item["name"])
    return sources


if __name__ == "__main__":
    for source in get_sources():
        #print(source)
        print("checking if transcoding for {0} is running anywhere".format(source["name"]))
        templist = []
        for k in get_transcodes():
            if k['service'].split("_")[1].split("@")[1] == source['name']:
                templist.append(k)
            #r = re.compile("s6")
            #templist = list(filter(r.match, k))
            #print(k)
            #print(templist)
        transcodings = []
        for transcode in templist:
            #print(transcode)
            if transcode['service'].split('_')[1].split('@')[0] == 'audio' and transcode["state"] == 1.0:
                #if str(source['name']) == str(transcode['service']).split("_")[1].split("@")[1]:
                transcodings.append("== audio running for {0} on {1}".format(source['name'], transcode['name'].split('_')[0]))
            #else:
            #    print("no audio transcoding running for {0}".format(source["name"]))
            if transcode['service'].split('_')[1].split('@')[0] == 'h264' and transcode["state"] == 1.0:
                #if str(source['name']) == str(transcode['service']).split("_")[1].split("@")[1]:
                transcodings.append("== h264 running for {0} on {1}".format(source['name'], transcode['name'].split('_')[0]))
            #else:
            #    print("no h264 transcoding running for {0}".format(source["name"]))
            if transcode['service'].split('_')[1].split('@')[0] == 'vpx' and transcode["state"] == 1.0:
                #if str(source['name']) == str(transcode['service']).split("_")[1].split("@")[1]:
                transcodings.append("== vpx running for {0} on {1}".format(source['name'], transcode['name'].split('_')[0]))
            #else:
            #    print("no vpx transcoding running for {0}".format(source["name"]))
        for t in transcodings:
            print(t)
            #if str(source['name']) == str(transcode['service']).split("_")[1].split("@")[1]:
            #    if transcode["state"] == 1.0:
            #        print("== service {1} running on host {0} with state {2}".format(transcode['name'], transcode['service'], transcode["state"]))
            #    else:
            #        print("== {0} transcoding for {1} not running, need to start".format(transcode['service'].split("_")[2], source['name']))
            #else:
            #    continue
            #    #print("== transcoding for {0} not running, need to start".format(source['name']))
    sys.exit(0)
