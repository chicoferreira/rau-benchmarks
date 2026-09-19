#!/usr/bin/env bash

cd "$(dirname "$0")"

python configure-shadered.py 1920 1080

SHADERed.exe "$PWD/project/ssao.sprj"
