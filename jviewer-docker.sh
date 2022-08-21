#! /usr/bin/env bash

xhost +localhost
docker compose build
docker compose run --entrypoint="" jviewer /usr/local/bin/jviewer-starter.py "$@"
