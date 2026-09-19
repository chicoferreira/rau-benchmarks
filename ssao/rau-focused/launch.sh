#!/usr/bin/env bash

# usage: ./launch.sh [extra rau flags...]
#
# The same project and flags as ssao/rau, opened in the focus view, so the
# scene is drawn with none of the editor's panels around it.

cd "$(dirname "$0")"

exec bash ../rau/launch.sh --focused "$@"
