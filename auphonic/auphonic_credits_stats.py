#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# Created in 2016 by Andi <andi@muc.ccc.de>
#
# Queries auphonic for the current productions archive and sums up used credits to create invoce for conference organzier
#

import os, sys
import re
import json
import argparse
import requests

parser = argparse.ArgumentParser(description='Fetch finished Auphonic-Productions visible for the specified login from Auphonic and sum up used credits by confernce acronym')
parser.add_argument('--auphonic-login', dest='auphonic', default = os.path.expandvars("./.auphonic-login"),
    help="path of a file containing username:password of your auphonic account")

args = parser.parse_args()

# TODO: Use Keepass Python API

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

credits = {}

# if auphonic returned production
if productions['data']:
    # iterate them
    for production in productions['data']:
        if not production['error_status']:
            sys.stdout.write('.')
            try:
                conference = production['metadata']['title'].split('-', 2)[0]
                used_credits = production['used_credits']['combined']
                if conference in credits:
                    credits[conference] += used_credits
                else:
                    credits[conference] = used_credits
            except Exception as e:
                print(e)
                print(production)
                print("")

# dump the resulting urls as pretty json
print("")
print json.dumps(credits, indent=4)
