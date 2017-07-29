#!/bin/bash
# Record a live feed from RTMP streaming point to disk for use with CRS

if [ $# -lt 1 ]; then
  echo "Usage: $0 rtmp://... [mono|stereo]"
  exit
fi

FFMPEG_BIN=`command -v ffmpeg`
RTMP_URL=$1
if [ "$2"  == 'mono' ]; then
  AUDIO="-b:a 128k -ac:a 1 -ar:a 48000 -filter:a:0 pan=mono:c0=FL -map 0:a -filter:a:1 pan=mono:c0=FR"
else
  AUDIO="-b:a 192k -ac:a 2 -ar:a 48000"
fi

mkdir -p $PWD/segments

$FFMPEG_BIN -re -i $RTMP_URL \
  -aspect 16:9 \
  -map 0:v -c:v:0 mpeg2video -pix_fmt:v:0 yuv422p -qscale:v:0 2 -qmin:v:0 2 \
  -qmax:v:0 7 -keyint_min 0 -bf:0 0 -g:0 0 -intra:0 -maxrate:0 90M -c:a mp2 \
  $AUDIO -flags +global_header -flags +ilme+ildct \
  -f segment -segment_time 180 -segment_format mpegts \
  ${PWD}/segments/room-%t-%05d.ts
