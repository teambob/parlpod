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

PACKAGES=$(echo dist/lib64/python3*/site-packages)
if [ ! -d "$PACKAGES" ]
then
	echo "Error: directory $PACKAGES does not exist"
	exit 1
fi

cp -r parlpod "$PACKAGES"
cd "$PACKAGES"
zip "$filename" -r .
