#! /usr/bin/env bash

xhost +localhost
docker compose build
docker compose run jviewer $@
