#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import argparse
import subprocess
import json

def get_stream(args):
    try:
        streaminfo = subprocess.check_output(['ffprobe', '-print_format', 'json', '-show_streams', '-loglevel', 'quiet', '-probesize', args.probesize, args.url])
    except:
        print('CRITICAL - Can not receive stream')
        sys.exit(2)

    streams = json.loads(streaminfo)['streams']
    if args.streamindex >= len(streams):
        print('CRITICAL - No stream with index %s ' % args.streamindex)
        sys.exit(2)

    stream = streams[args.streamindex]
    if args.verbose:
        print('Using stream %d/%d' % (args.streamindex, len(streams) - 1))
        for k,v in stream.items():
            print(k,v)

    return stream

def print_parameters(args, stream):
    if args.height:
        if 'height' in stream:
            sys.stdout.write(', height (%s:%s)' % (stream['height'], args.height))
        else:
            sys.stdout.write(', height (None:%s)' % args.height)

    if args.width:
        if 'width' in stream:
            sys.stdout.write(', width (%s:%s)' % (stream['width'], args.width))
        else:
            sys.stdout.write(', width (None:%s)' % args.width)

def check_stream(args):
    stream = get_stream(args)
    streamOkay = True
    
    if args.height and ('height' not in stream or args.height != int(stream['height'])):
        streamOkay = False
    
    if args.width and ('width' not in stream or args.width != int(stream['width'])):
        streamOkay = False

    if streamOkay:
        sys.stdout.write('OK - All stream parameters are correct')
        print_parameters(args, stream)
        sys.stdout.write('\n')
        sys.exit(0)
    else:
        sys.stdout.write('WARNING - Some stream parameters are not correct')
        print_parameters(args, stream)
        sys.stdout.write('\n')
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='check RTMP stream with Nagios output')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='Verbose output (Not Nagios compatible)')
    parser.add_argument('-r', '--url',
        type=str,
        required=True,
        help='URL')
    parser.add_argument('-vw', '--width',
        type=int,
        help='Expected Width')
    parser.add_argument('-vh', '--height',
        type=int,
        help='Expected Height')
    parser.add_argument('-i', '--streamindex',
        type=int,
        default=0,
        help='ffmpeg stream index')
    parser.add_argument('-s', '--probesize',
        type=str,
        default='6M',
        help='Size of video snippet')
    
    args = parser.parse_args(sys.argv[1:])

    if args.verbose:
            print('Application arguments:\n%s' % str(vars(args)))

    check_stream(args)

sys.exit(0)

# vim: set ts=4 sw=4 expandtab

