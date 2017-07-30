#!/bin/bash

# read the tutorial about git bisect!
#
# then use
#   git bisect start
#   git bisect good <spec>
#   git bisect bad <spec>
#   git bisect run <this script>

# this was used for FFmpeg but should be general purpose
# just adjust configureopts, makeopts and the test command to your needs

_configure_opts="--enable-gpl --disable-decklink --enable-static --disable-asm --disable-ffserver --disable-ffplay --disable-doc --disable-stripping  --disable-encoders --disable-muxers"
_make_opts=-j8


git clean -dxf >/dev/null 2>/dev/null

./configure $_configure_opts 1>/tmp/config.log 2>&1 && make $make_opts 1>/tmp/make.log 2>&1

if [ $? -ne 0 ]; then
  echo Broken build
  sleep 3
  exit 125
fi

# your testcommand here!
./ffprobe foo.mp3 2>&1|grep Chapter

if [ $? -ne 0 ]; then
  echo Bad build
  exit 124
else
  echo Good build
  exit 0
fi

