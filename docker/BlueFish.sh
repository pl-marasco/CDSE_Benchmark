#! /bin/bash

docker build . --no-cache -t testbed:latest
docker run --privileged --name guybrush_threepwood -dit testbed:latest
docker exec -t guybrush_threepwood python /root/testbed/BlueFish.py
