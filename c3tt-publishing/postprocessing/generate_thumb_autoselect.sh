#!/bin/bash

CANDIDATES=10

BASEDIR=$(dirname $0)

INPUT="$1"
LENGTH=$(ffprobe -loglevel quiet -print_format default -show_format "$INPUT" | grep duration= | sed -e 's/duration=\([[:digit:]]*\).*/\1/g')

# extract candidates and convert to non-anamorphic images
for i in $(seq 1 $CANDIDATES)
do
	POS=$[ $RANDOM % $LENGTH ]
	ffmpeg -loglevel error -ss $POS -i "$INPUT"  -an -r 1 -filter:v 'scale=sar*iw:ih' -vframes 1 -f image2 -vcodec mjpeg -y $POS.jpg
done

WINNER=$(python2 $BASEDIR/select.py *.jpg)

mv "$WINNER" winner.jpg

ffmpeg -loglevel error -i winner.jpg -filter:v 'crop=ih*4/3:ih' -s 192x144 thumb.jpg
