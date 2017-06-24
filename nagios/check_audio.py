#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import argparse
import subprocess
import re

def get_stream(args):
    try:
        streaminfo = subprocess.check_output(["ffmpeg", "-t", str(args.duration), "-i", args.url, "-af", "volumedetect", "-f", "null", "/dev/null"], stderr=subprocess.STDOUT)
    except:
        print("CRITICAL - Can not receive stream")
        sys.exit(2)

    return streaminfo

def check_stream(args):
    streaminfo = get_stream(args)
    msg = "CRITICAL - Can not parse filter output"
    streamOkay = False

    if args.verbose:
        print(streaminfo)

    match = re.search(r"max_volume: ([-\d].*) dB", streaminfo)
    
    if match:
        maxVolume = match.group(1)
        if float(maxVolume) >= args.level:
            msg = "OK - Max Audio Level %s dB | audio_level=%s" % (maxVolume, maxVolume)
            streamOkay = True
        else:
            msg = "CRITICAL - Max Audio Level %s dB | audio_level=%s" % (maxVolume, maxVolume)

    print(msg)
    if streamOkay:
        sys.exit(0)
    else:
        sys.exit(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check embedded audiostream maximum level with Nagios output")
    parser.add_argument('-v', '--verbose',
        action='store_true',
        help='Verbose output (Not Nagios compatible)')
    parser.add_argument('-r', '--url',
        type=str,
        required=True,
        help='URL')
    parser.add_argument('-l', '--level',
        type=float,
        required=True,
        help='Critical maximum audiolevel (e.g. -70)')
    parser.add_argument('-d', '--duration',
        type=float,
        default=2.0,
        help='Listening Duration')
    
    args = parser.parse_args(sys.argv[1:])

    if args.verbose:
            print("Application arguments:\n%s" % str(vars(args)))

    check_stream(args)

sys.exit(0)

# vim: set ts=4 sw=4

