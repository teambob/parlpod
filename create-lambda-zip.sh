#!/bin/bash
set -ex

filename=$(readlink -f lambda-dev.zip)

if [ -f "$filename" ]
then
  rm -- "$filename"
fi

python3 -m venv dist
source dist/bin/activate
pip3 install -r requirements.txt
deactivate

zip "$filename" -r parlpod

cd dist/lib/python3*/site-packages/
zip "$filename" -r .
