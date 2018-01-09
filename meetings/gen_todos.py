#!/usr/bin/env python3
import sys
import subprocess
import re
import argparse
import requests

parser = argparse.ArgumentParser(prefix_chars='-+')
parser.add_argument('pad_name', action="store", help="name of pad to harvest todo items from, e.g. 33c3-mumble2")
parser.add_argument('+content', action="store_true", help="")
args = parser.parse_args()

wget = "/usr/local/bin/wget"
#wget = "/usr/bin/wget"

pad_name = ""
pad_url = "https://video.pads.ccc.de/ep/pad/export/" + args.pad_name + "/latest?format=txt"
out = subprocess.check_output(wget + " -O - '" + pad_url
        + "' | grep TODO | grep -v DONE | sed -e 's/^[ \t\*]*//' | cut -d' ' -f 2-", shell=True)

out = out.decode('utf-8')

todos = out.splitlines()


print("== TODOs")

for item in todos:
    match = re.match('^@?([A-Za-z]+): (.+?)$', item)
    if match:
        #print(match)
        print("* <todo @" + match.group(1) + ">" + match.group(2) + "</todo>")
    else:
        print("* <todo>" + item + "</todo>")

if args.content:
    print()
    print("== Pad")
    #print(out)
    print(requests.get(pad_url).text)
