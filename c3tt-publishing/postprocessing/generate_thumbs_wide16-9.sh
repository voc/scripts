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
  outgif=${file%.*}.gif
  outjpg=${file%.*}.jpg
  outjpg_preview=${file%.*}_preview.jpg
else
  outgif=${outdir}/$(basename ${file%.*}.gif)
  outjpg=${outdir}/$(basename ${file%.*}.jpg)
  outjpg_preview=${outdir}/$(basename ${file%.*}_preview.jpg)
fi

# don't overwrite
if [ -r "$outgif" ]; then
  echo "[!] won't overwrite $outgif"
  exit
fi

# preview image in 16:9 like video
echo "[ ] creating static first poster image from intro"
genthum "$file" 0 00:00:09
convert -resize 640x360\! $DIR/gif0.jpg "${outjpg_preview}"
rm -f $DIR/gif0.jpg

echo "[ ] creating animated $outgif"
genthum "$file" 0 00:00:23
genthum "$file" 1 00:00:42
genthum "$file" 2 00:01:23
genthum "$file" 3 00:03:23
genthum "$file" 4 00:05:23
genthum "$file" 5 00:09:23
genthum "$file" 6 00:15:42
genthum "$file" 7 00:25:42

# ani gif is 4:3
mogrify -resize 256x144\!   $DIR/gif*.jpg 
mogrify -crop 192x144+32+0   $DIR/gif*.jpg 

# create thumbnail and static first image
cp $DIR/gif0.jpg "${outjpg}"
rm -f $DIR/gif0.jpg
convert -delay 200 $DIR/gif*.jpg -loop 0 "${outgif}"
echo ===============================
