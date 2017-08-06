#!/bin/bash

if [ $# -lt 2 ]; then
  echo "A tool to fix naming / time stamps in a series of TS files for use with CRS."
  echo
  echo "Usage: $0 <room> <timestamp>"
  exit 1
fi

idx=0
ts=$2
room=$1

for i in *.ts; do
  mv $i ${room}-$(date +%Y-%m-%d_%H-%M-%S --date=@$ts)-$(printf %05d $idx).ts
  idx=$(($idx+1))
  ts=$(($ts+180))
done
