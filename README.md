# run-openpose

Tool to process data with [OpenPose](https://github.com/CMU-Perceptual-Computing-Lab/openpose)

Uses the Openpose python API to recursively process all images and videos in a folder with openpose, writing coordinates and drawn images/video to an output folder. 

# 

# setup / installation

* Option 1 (Highly Recommended):
The tool can be run in [its own docker container](https://hub.docker.com/r/pmorris2012/run-openpose) by running a docker command in the terminal like the usage examples below, or running inside another container, like [this one](https://hub.docker.com/r/pmorris2012/openpose).

  * 1. If your computer has an Nvidia GPU, make sure you have an Nvidia graphics driver installed. If you can run `nvidia-smi` in the terminal and see the output, it's installed. Installation instructions can be found [here](https://askubuntu.com/a/61433) or by googling.
  * 2. Install docker, using [these ubuntu-specific instructions](https://docs.docker.com/engine/install/ubuntu/) or a different online tutorial.

* Option 2:
Compile OpenPose from source with Python API support. Documentation for doing this can be found on the [OpenPose](https://github.com/CMU-Perceptual-Computing-Lab/openpose) github. Ensure `pyopenpose` is accessible as a library in your chosen Python 3 installation so it can be called by the `process_folder.py` script. You will still need a working nvidia driver.

# how to use with Docker

In a terminal, use the `docker run` command to create a container from the `pmorris2012/run-openpose:latest` image. 
- The image will be downloaded from [DockerHub](https://hub.docker.com/r/pmorris2012/run-openpose) automatically if it isn't already. 
- Flags should be provided to set the input and output folders, container settings, and configuration arguments to give when calling `process_folder.py`.

Here are some template commands that use different settings to run OpenPose and/or draw keypoints. Copy and paste these into the terminal, making sure to change the folder paths to the `/Input` and `/Output` `-v` volume mounts, and adjust settings using the configuration flags below:

With face and hands, drawing new images/videos with both pose and black background versions
```
docker run \
    -v ~/Documents/dataset/Videos:/Input \
    -v ~/Documents/dataset/Videos_Pose:/Output \
    -it --rm --gpus all --ipc="host" \
    pmorris2012/run-openpose \
    --face --hands --draw_pose --draw_black_pose
```

same as above, but more accurate (slower)
```
docker run \
    -v ~/Documents/dataset/Videos:/Input \
    -v ~/Documents/dataset/Videos_Pose:/Output \
    -it --rm --gpus all --ipc="host" \
    pmorris2012/run-openpose \
    --face --hands --draw_pose --draw_black_pose --scale_number 4
```

maximum settings (need 16+Gb of GPU memory for this)
```
docker run \
    -v ~/Documents/dataset/Videos:/Input \
    -v ~/Documents/dataset/Videos_Pose:/Output \
    -it --rm --gpus all --ipc="host" \
    pmorris2012/run-openpose \
    --face --hands --draw_pose --draw_black_pose --net_resolution="1312x736" --scale_number 4 --hand_scale_number 6
```


Just get body coordinates (fastest)
```
docker run \
    -v ~/Documents/dataset/Videos:/Input \
    -v ~/Documents/dataset/Videos_Pose:/Output \
    -it --rm --gpus all --ipc="host" \
    pmorris2012/run-openpose
```

Print each image/video as it's processed
```
docker run \
    -v ~/Documents/dataset/Videos:/Input \
    -v ~/Documents/dataset/Videos_Pose:/Output \
    -it --rm --gpus all --ipc="host" \
    pmorris2012/run-openpose \
    --verbose
```

# `process_folder.py` configuration flags

```
usage: process_folder.py [-h] [--input_folder INPUT_FOLDER]
                         [--output_folder OUTPUT_FOLDER] [--face] [--hand]
                         [--draw_pose] [--draw_black_pose]
                         [--net_resolution NET_RESOLUTION]
                         [--scale_number SCALE_NUMBER] [--scale_gap SCALE_GAP]
                         [--hand_scale_number HAND_SCALE_NUMBER]
                         [--hand_scale_range HAND_SCALE_RANGE]
                         [--image_ext IMAGE_EXT] [--video_ext VIDEO_EXT]
                         [--fourcc_code FOURCC_CODE]
                         [--include_coord_confidence] [--verbose]

scans an folder for images/videos, processes them with OpenPose, and saves the
output in a separate folder. For more info on OpenPose parameters, see
https://github.com/CMU-Perceptual-Computing-
Lab/openpose/blob/master/doc/demo_overview.md#main-flags

optional arguments:
  -h, --help            show this help message and exit
  --input_folder INPUT_FOLDER
                        the folder to search for images/videos to process
  --output_folder OUTPUT_FOLDER
                        the folder output where Coords/Videos/Images will be
                        saved
  --face                face points will be saved (and drawn, if drawing flags
                        are set)
  --hand                hand points will be saved (and drawn, if drawing flags
                        are set)
  --draw_pose           pose will be drawn on the original video and saved
  --draw_black_pose     pose will be drawn on a black background and saved
  --net_resolution NET_RESOLUTION
                        OpenPose parameter
  --scale_number SCALE_NUMBER
                        OpenPose parameter
  --scale_gap SCALE_GAP
                        OpenPose parameter
  --hand_scale_number HAND_SCALE_NUMBER
                        OpenPose parameter
  --hand_scale_range HAND_SCALE_RANGE
                        OpenPose parameter
  --image_ext IMAGE_EXT
                        the file extension output images will be written with.
  --video_ext VIDEO_EXT
                        the file extension output videos will be written with.
                        this may need to match the video codec.
  --fourcc_code FOURCC_CODE
                        the codec output videos will be written with (see
                        https://www.fourcc.org/codecs.php for possible codes)
  --include_coord_confidence
                        include confidence score with the x and y keypoint
                        coordinates in the output arrays
  --verbose             show video progress and log each image
```
