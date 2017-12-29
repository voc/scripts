ffmpeg \
        -y -nostdin -analyzeduration 10000 \
        -i tcp://127.0.0.1:20000 \
        -threads:0 0 \
        -aspect 16:9 \
        -map '0:v' \
        -c:v libx264 \
        -maxrate:v:0 6000k -crf:0 29 \
        -bufsize:v:0 15360k -pix_fmt:0 yuv420p \
        -profile:v:0 main -g:v:0 25 \
        -preset:v:0 veryfast \
        \
        -map '0:a' \
        -ac 2 -c:a aac -b:a 96k -ar 44100 \
        \
        -y -f matroska \
        -password $YOURICECASTSTREAMINGPASSWORD \
        -content_type video/webm \
        icecast://live.ber.c3voc.de:8000/4k_experiment
