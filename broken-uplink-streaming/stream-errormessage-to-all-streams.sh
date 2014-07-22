#!/bin/sh
ffmpeg -y -ar 48000 -ac 2 -f s16le -i /dev/zero -f image2 -loop 1 -re -r 25 -i down.png  -threads 2 -pix_fmt yuv420p -acodec libfaac -vcodec libx264 -f flv - | \
	tee >(ffmpeg -y -loglevel warning -i - -c:v copy -c:a copy -f flv rtmp://127.0.0.1/stream/saal1_native_hq) | \
	tee >(ffmpeg -y -loglevel warning -i - -c:v copy -c:a copy -f flv rtmp://127.0.0.1/stream/saal2_native_hq) | \
	tee >(ffmpeg -y -loglevel warning -i - -c:v copy -c:a copy -f flv rtmp://127.0.0.1/stream/saal3_native_hq) | \
	tee >(ffmpeg -y -loglevel warning -i - -c:v copy -c:a copy -f flv rtmp://127.0.0.1/stream/saal4_native_hq) | \
	tee >(ffmpeg -y -loglevel warning -i - -c:v copy -c:a copy -f flv rtmp://127.0.0.1/stream/saal5_native_hq) | \
	tee >(ffmpeg -y -loglevel warning -i - -c:v copy -c:a copy -f flv rtmp://127.0.0.1/stream/saal1_native_lq) | \
	tee >(ffmpeg -y -loglevel warning -i - -c:v copy -c:a copy -f flv rtmp://127.0.0.1/stream/saal2_native_lq) | \
	tee >(ffmpeg -y -loglevel warning -i - -c:v copy -c:a copy -f flv rtmp://127.0.0.1/stream/saal3_native_lq) | \
	tee >(ffmpeg -y -loglevel warning -i - -c:v copy -c:a copy -f flv rtmp://127.0.0.1/stream/saal4_native_lq) | \
	tee >(ffmpeg -y -loglevel warning -i - -c:v copy -c:a copy -f flv rtmp://127.0.0.1/stream/saal5_native_lq) > /dev/null

