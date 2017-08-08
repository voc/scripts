#!/bin/bash

for dirready in `find -maxdepth 2 -mindepth 1 -name muxed.mp4`; do
  echo rm -f "`dirname "$dirready" `"/*.ts
  rm -f "`dirname "$dirready" `"/*.ts
done

