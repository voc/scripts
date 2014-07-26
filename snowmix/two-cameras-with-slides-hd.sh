#!/bin/sh

export SM=/home/peter/AAA-VOC/Snowmix-0.4.3

echo "starting snowmix"
$SM/src/snowmix two-cameras-with-slides-hd.ini &
MIXPID=$!
sleep 2

echo "av mirror"
$SM/scripts/av_output2screen &
MIRRORPID=$!

# Load the Snowmix and GStreamer settings
#./input2feed 1 '/home/peter/2014-06-21-Modellflugplatz2.mp4' &
#FEED1PID=$!

./input2feed 2 '/home/peter/2014-06-21-Modellflugplatz2.mp4' &
FEED2PID=$!

./input2feed 3 '/home/peter/UAV.mp4' &
FEED3PID=$!

echo "starting mixer-gui"
$SM/tcl/snowcub.tcl 127.0.0.1 9999 >/dev/null 2>&1

kill $MIRRORPID
#kill $FEED1PID
kill $FEED2PID
kill $FEED3PID
kill $MIXPID
