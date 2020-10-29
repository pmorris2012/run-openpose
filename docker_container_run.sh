#!/bin/bash

docker run \
    -v $(pwd):/data \
    -it --rm --gpus all --ipc="host" \
    pmorris2012/run-openpose \
    --input_folder="/data/images" --output_folder="/data/images_pose" \
    --face --hand --draw_pose --draw_black_pose
