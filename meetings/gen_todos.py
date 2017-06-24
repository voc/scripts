#!/usr/bin/env python3
import sys
import subprocess
import re
import optparse

parser = optparse.OptionParser()
parser.add_option('-p', '--pad', action="store", dest="pad_name", help="name of pad to harvest todo items from, e.g. 33c3-mumble2", default="33c3-mumble2")
options, args = parser.parse_args()

wget = "/usr/local/bin/wget"
#wget = "/usr/bin/wget"

pad_name = ""
out = subprocess.check_output(wget + " -O - https://video.pads.ccc.de/ep/pad/export/" + options.pad_name + "/latest\?format\=txt --no-check-certificate | grep TODO | grep -v DONE | sed -e 's/^[ \t\*]*//' | cut -d' ' -f 2-", shell=True)

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


