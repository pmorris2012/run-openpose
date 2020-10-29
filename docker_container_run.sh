#!/bin/bash

docker run \
    -it \
    --rm \
    -p 7777:8888 \
    -v /home:/home \
    --gpus all \
    --ipc="host" \
    --name container_name \
    ubuntu:18.04 \
    /bin/bash
