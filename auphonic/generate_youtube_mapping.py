# -*- coding: UTF-8 -*-
# Created in 2014 by Andi <andi@muc.ccc.de> and Mazdermind?

import os
import re
import json
import argparse
import requests

parser = argparse.ArgumentParser(description='Fetch finished Auphonic-Productions visible for the specified login from Auphonic and parse all Youtube-Urls out, order them by talk-id and resturn a mapping-json')
parser.add_argument('--auphonic-login', dest='auphonic',default = os.path.expandvars("./.auphonic-login"),
    help="path of a file containing username:password of your auphonic account")

args = parser.parse_args()

# read the auphonic login-data file
with open(args.auphonic) as fp:
    auphonic_login = fp.read().strip().split(':', 1)

# fetch the list of all visible productions from auphonic
r = requests.get(
    'https://auphonic.com/api/productions.json?limit=10000',
    auth=(auphonic_login[0], auphonic_login[1])
)

# test for success
if r.status_code != 200:
    print("fetching productions failed with response: ", r, r.text)
    sys.exit(1)

# parse the result as json
productions = r.json()

# dict to collect talkid-youtube-pairs
urls = {}

# pattern to extract talk-.ids form filenames
pattern = re.compile("[0-9]+")

# if auphonic returned production
if productions['data']:
    # iterate them
    for production in productions['data']:
        # iterate all outgoing services
        for service in production['outgoing_services']:
            # if this service posted the video successfully on youtube
            if service['type'] == 'youtube' and service['result_page']:
                # test if the filename starts with a number and retrieve it
                filename = production['input_file']
                match = pattern.match(filename)

                if not match:
                    print(u'"{0}" does not start with a number, skipping'.format(filename))

                else:
                    # extract the number
                    talkid = int(match.group(0))

                    #don't overwrite newer entries
                    if not urls.has_key(talkid):
                        # store the youtube-url under that id
                        urls[talkid] = service['result_page']
                    #else:
                    #   print 'duplicate: %i %s ' % (talkid, service['result_page'])

# dump the resulting urls as pretty json
print json.dumps(urls, indent=4)
