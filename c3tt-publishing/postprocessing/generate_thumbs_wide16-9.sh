#!/bin/sh
# generate thumbnails
# and video preview in 16:9
# gif and thumb in 4:3 cropped

# 256x144 widescreen thumb size?
# 640x360 preview / video clip

set -e
file="$1"
outdir="$2"

# source exists?
[ -r "$file" ] || exit 1

genthum () {
    SRC="$1"
    n="$2"
    offs="$3"
    # -f singlejpeg
    echo "[+] Generating thumbnail for $SRC at $offs"
    ffmpeg -ss "$offs" -i "$SRC" -an -r 1 -vframes 1 -f image2 -vcodec mjpeg "$DIR/gif$n.jpg" > /dev/null 2>&1 < /dev/null
}

DIR=`mktemp -d`
trap "rm -fr $DIR; exit 0" EXIT

if [ -z "$outdir" ]; then 
  outjpg=${file%.*}.jpg
  outjpg_preview=${file%.*}_preview.jpg
else
  outjpg=${outdir}/$(basename ${file%.*}.jpg)
  outjpg_preview=${outdir}/$(basename ${file%.*}_preview.jpg)
fi

# preview image in 16:9 like video
echo "[ ] creating static first poster image from intro"
genthum "$file" 0 00:03:42
convert -resize 640x360\! $DIR/gif0.jpg "${outjpg_preview}"
rm -f $DIR/gif0.jpg

echo "[ ] creating thumb $outjpg"
genthum "$file" 0 00:00:23

# ani gif is 4:3
mogrify -resize 256x144\!   $DIR/gif*.jpg 
mogrify -crop 192x144+32+0   $DIR/gif*.jpg 

# create thumbnail and static first image
cp $DIR/gif0.jpg "${outjpg}"
rm -f $DIR/gif0.jpg
echo ===============================
