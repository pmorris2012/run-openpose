#!/bin/bash

docker run \
    -v ~/Documents/dataset/Videos:/Input \
    -v ~/Documents/dataset/Videos_Pose:/Output \
    -it --rm --gpus all --ipc="host" \
    pmorris2012/run-openpose \
    --face --hands --draw_pose --draw_black_pose
