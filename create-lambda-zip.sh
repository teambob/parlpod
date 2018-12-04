#!/bin/bash
set -ex

filename=$(readlink -f lambda-dev.zip)

if [ -f "$filename" ]
then
  rm -- "$filename"
fi

zip "$filename" -r parlpod

cd dist/lib/python3.6/site-packages/
zip "$filename" -r .
