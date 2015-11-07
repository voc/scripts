#!/bin/sh
#
# Cam recordings to segments 
#
# This script can be used to convert files captured to a sd card into a format
# that can be used by the c3tt [1] and fuse-ts [2].
#
# [1] https://repository.fem.tu-ilmenau.de/trac/c3tt/wiki
# [2] http://subversion.fem.tu-ilmenau.de/repository/cccongress/trunk/tools/fuse-ts/
#
# Copyright (c) 2015, c3voc
# All rights reserved.

FFMPEG_BIN=`command -v ffmpeg`
FFPROBE_BIN=`command -v ffprobe`

# Do argument and dependency checks.
if [ "0" -eq "$#" ]; then
  echo "Usage: ${0} /video/source/directory"
  echo
  echo "Recommended workflow:"
  echo "  1. cp sd_card/ /my/convert_destination/"
  echo "  2. sh cm2seg.sh /my/convert_destination/"
  echo "  3. wait"
  echo "  4. vidir /my/convert_destination/segments"
  echo "     to fix room, date and time"
  echo "  5. mv /my/convert_destination/segments/*ts /video/capture/"
  echo "  6. prepare tracker and scripts"
  echo "  7. cut"
  exit 1
fi

if [ -z "${FFMPEG_BIN}" ]; then
  echo "ffmpeg is not installed!"
  exit 1
fi

if ! [ "$TERM" = "screen" ] && ! [ -n "$TMUX" ]; then
  echo "You should run this script inside a tmux or screen session!"
  exit 1
fi

# Create destination_path/segments directory.
if ! [ -d "${1}/segments" ]; then
  mkdir ${1}/segments
  if ! [ "0" -eq $? ]; then
    echo "${1}/segments directory could not be created!"
    exit 1
  fi
fi

# Convert source material into mpeg-ts files.
for file in `ls -1 ${1}/*\.* | grep -v *\.ts`; do
  $FFMPEG_BIN -i $file \
    -aspect 16:9 \
    -map 0:v -c:v:0 mpeg2video -pix_fmt:v:0 yuv422p -qscale:v:0 2 -qmin:v:0 2 \
    -qmax:v:0 7 -keyint_min 0 -bf:0 0 -g:0 0 -intra:0 -maxrate:0 90M -c:a mp2 \
    -b:a 192k -ac:a 1 -ar:a 48000 -map 0:a -filter:a:0 pan=mono:c0=FL -map 0:a \
    -filter:a:1 pan=mono:c0=FR -flags +global_header -flags +ilme+ildct -f mpegts \
    ${file%.*}.ts;
done
printf "\n\nConverted source material into ts files.\n\n"

# Concatenate all converted ts files to one file.
#
# We need a list of files seperated with a pipe.
ts_files=`ls ${1}/*\.ts | grep -v complete\.ts | xargs | tr -s ' ' '|'`
$FFMPEG_BIN -i "concat:${ts_files}" -c copy -f mpegts ${1}/complete.ts

if ! [ "0" -eq $? ]; then
  echo "Concatenating ts files failed!"
  exit 1
fi
printf "\n\nConcatenated ts files into ${1}/complete.ts\n\n"

# Let's create segments for the tracker.
#
# First calculate duration…
duration=`$FFPROBE_BIN ${1}/complete.ts 2>&1 | grep -i 'duration' | cut -d ' ' -f 4 | tr -s ',' 'h'`
printf "\n\nStart with creating 180s segments. It will take ${duration}!\n\n"
# …try do create segments.
$FFMPEG_BIN -re -i ${1}/complete.ts -c copy -flags +global_header -flags \
  +ilme+ildct -f segment -segment_time 180 -segment_format mpegts \
  ${1}/segments/room-%t-%05d.ts

if ! [ "0" -eq $? ]; then
  printf "\n\nCreating segments failed!"
  exit 1
else
  printf "\n\nFind your segnemts in ${1}/segments/."
  echo "You have to fix the room name, recording date and time with vidir or something else."
fi

exit 0
