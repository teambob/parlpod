#!/bin/bash
set -ex

filename=$(readlink -f lambda-dev.zip)

if [ -f "$filename" ]
then
  rm -- "$filename"
fi

if [ ! -d "dist" ]
then
  mkdir "dist"
fi

pip3 install --system --target $PWD/dist/ -r requirements.txt

zip "$filename" -r parlpod

cd dist
zip "$filename" -r .
