import sys
import cv2
import os
import pyopenpose as op
import numpy as np
import argparse
from tqdm import tqdm

from drawing import draw_keypoints
from file_utils import move_path, replace_ext, create_dirs
from cv_utils import check_image, check_video, get_video_properties

parser = argparse.ArgumentParser(description="scans an folder for images/videos, processes them with OpenPose, and saves the output in a separate folder. For more info on OpenPose parameters, see https://github.com/CMU-Perceptual-Computing-Lab/openpose/blob/master/doc/demo_overview.md#main-flags")

# Options
parser.add_argument('--input_folder', default="/Input", help="the folder to search for images/videos to process")
parser.add_argument('--output_folder', default="/Output", help="the folder output where Coords/Videos/Images will be saved")
parser.add_argument('--face', dest='face', action='store_true', help="face points will be saved (and drawn, if drawing flags are set)")
parser.add_argument('--hand', dest='hand', action='store_true', help="hand points will be saved (and drawn, if drawing flags are set)")
parser.add_argument('--draw_pose', dest='draw_pose', action='store_true', help="pose will be drawn on the original video and saved")
parser.add_argument('--draw_black_pose', dest='draw_black_pose', action='store_true', help="pose will be drawn on a black background and saved")

# Openpose parameters
parser.add_argument('--net_resolution', default="-1x368", help="OpenPose parameter")
parser.add_argument('--scale_number', type=int, default=1, help="OpenPose parameter")
parser.add_argument('--scale_gap', type=float, default=0.25, help="OpenPose parameter")
parser.add_argument('--hand_scale_number', type=int, default=1, help="OpenPose parameter")
parser.add_argument('--hand_scale_range', type=float, default=0.4, help="OpenPose parameter")

# Miscellaneous Options
parser.add_argument('--image_ext', default=".png", help="the file extension output images will be written with.")
parser.add_argument('--video_ext', default=".avi", help="the file extension output videos will be written with. this may need to match the video codec.")
parser.add_argument('--fourcc_code', default="XVID", help="the codec output videos will be written with (see https://www.fourcc.org/codecs.php for possible codes)")
parser.add_argument('--include_coord_confidence', dest='include_coord_confidence', action='store_true', help="include confidence score with the x and y keypoint coordinates in the output arrays")
parser.add_argument('--compress_coords', dest='compress_coords', action='store_true', help="will save the coordinate files in compressed format to save space.")

# Help/Other
parser.add_argument('--verbose', dest='verbose', action='store_true', help="show video progress and log each image")

args = parser.parse_args()

FOURCC_CODE = cv2.VideoWriter_fourcc(*args.fourcc_code)

pose_dir = os.path.join(args.output_folder, "Pose")
black_pose_dir = os.path.join(args.output_folder, "Black_Pose")
coords_dir = os.path.join(args.output_folder, "Coords")

# Custom Params (refer to include/openpose/flags.hpp for more parameters)
params = dict()
params["model_folder"] = "/openpose/models/"
params["face"] = args.face
params["hand"] = args.hand
params["hand_scale_number"] = args.hand_scale_number
params["hand_scale_range"] = args.hand_scale_range
params["net_resolution"] = args.net_resolution
params["scale_number"] = args.scale_number
params["scale_gap"] = args.scale_gap
params["display"] = 0
params["render_pose"] = 0 #we will manually draw pose, so we turn this off

# Starting OpenPose
opWrapper = op.WrapperPython()
opWrapper.configure(params)
opWrapper.start()

modes = ['body']
if args.face: 
    modes.append('face')
if args.hand: 
    modes.extend(['handl', 'handr'])

array_dict = {
    "body": lambda result: result.poseKeypoints,
    "face": lambda result: result.faceKeypoints,
    "handl": lambda result: result.handKeypoints[0],
    "handr": lambda result: result.handKeypoints[1]
}

def get_keypoints(image):
    datum = op.Datum()
    datum.cvInputData = image
    opWrapper.emplaceAndPop([datum])
    return datum

def draw_pose(image, result, modes):
    for mode in modes:
        array = array_dict[mode](result)
        image = draw_keypoints(image, array, mode=mode)
    return image

def rescale_coord_array(array, frame_size):
    rescale_dim = np.argmin(frame_size)
    pixel_offset = (max(frame_size) - min(frame_size)) / 2

    found_idxs = array.sum(axis=-1) > 0 #only scale keypoints found by openpose
    array[found_idxs,rescale_dim] += pixel_offset

    if not args.include_coord_confidence:
        array = array[:,:,:2]
    array[:,:,:2] /= max(frame_size) #scale xy coords between [0, 1]
    array[~found_idxs,:2] = np.nan #replace keypoints not found with NaN
    return array

def rescale_coords(result, modes, frame_size):
    arrays = {}
    for mode in modes:
        array = array_dict[mode](result)
        if (len(array.shape) > 0) and (array.shape[0] > 0):
            arrays[mode] = rescale_coord_array(array, frame_size)
            
    return arrays

def create_write_dir(path, from_dir, to_dir, ext):
    write_path = move_path(path, from_dir, to_dir)
    write_path = replace_ext(write_path, ext)
    create_dirs(write_path)
    return write_path

def save_coord_arrays(path, array_dict, compressed=False):
    save_function = np.savez_compressed if compressed else np.savez
    save_function(path, **array_dict)

def process_image(image_path):
    frame = cv2.imread(image_path)
    frame_size = (frame.shape[1], frame.shape[0])
    
    result = get_keypoints(frame)

    if args.draw_pose:
        image_pose = draw_pose(frame, result, modes)
        pose_path = create_write_dir(image_path, args.input_folder, pose_dir, ext=args.image_ext)
        cv2.imwrite(pose_path, image_pose)
    if args.draw_black_pose:
        black = np.zeros_like(frame) #get black image
        black_pose = draw_pose(black, result, modes)
        black_pose_path = create_write_dir(image_path, args.input_folder, black_pose_dir, ext=args.image_ext)
        cv2.imwrite(black_pose_path, black_pose)

    coords_path = create_write_dir(image_path, args.input_folder, coords_dir, ext='.npz')
    coord_arrays = rescale_coords(result, modes, frame_size)
    if len(coord_arrays) > 0:
        save_coord_arrays(coords_path, coord_arrays, compressed=args.compress_coords)

def process_video(video_path, total_progress_bar=None):
    video = cv2.VideoCapture(video_path)
    props = get_video_properties(video)
    frame_size = (props['width'], props['height'])

    if args.draw_pose:
        pose_path = create_write_dir(video_path, args.input_folder, pose_dir, ext=args.video_ext)
        video_pose = cv2.VideoWriter(pose_path, FOURCC_CODE, props['fps'], frame_size)
    if args.draw_black_pose:
        black_pose_path = create_write_dir(video_path, args.input_folder, black_pose_dir, ext=args.video_ext)
        video_black_pose = cv2.VideoWriter(black_pose_path, FOURCC_CODE, props['fps'], frame_size)
        
    coords_path = create_write_dir(video_path, args.input_folder, coords_dir, ext='/')
    
    progress_bar = tqdm(initial=1, total=props['frames'], desc=os.path.basename(video_path), unit='frame', dynamic_ncols=True, disable=(not args.verbose))
    frames_remaining, frame = video.read()
    frame_idx = 0
    while frames_remaining:
        result = get_keypoints(frame)

        if args.draw_pose:
            image_pose = draw_pose(frame, result, modes)
            video_pose.write(image_pose)
        if args.draw_black_pose:
            black = np.zeros_like(frame) #get black image
            black_pose = draw_pose(black, result, modes)
            video_black_pose.write(black_pose)

        coords_frame_path = os.path.join(coords_path, str(frame_idx) + ".npz")
        coord_arrays = rescale_coords(result, modes, frame_size)
        if len(coord_arrays) > 0:
            save_coord_arrays(coords_frame_path, coord_arrays, compressed=args.compress_coords)

        frames_remaining, frame = video.read()
        frame_idx += 1
        progress_bar.update(1)
        if total_progress_bar is not None:
            total_progress_bar.update(1)
        
    progress_bar.close()
    video.release()
    if args.draw_pose:
        video_pose.release()
    if args.draw_black_pose:
        video_black_pose.release()

def find_images_videos(directory, files):
    images, videos, video_lengths = [], [], []
    for file in files:
        file_path = os.path.join(directory, file)
        if check_image(file_path):
            images.append(file_path)
        elif check_video(file_path):
            videos.append(file_path)

            props = get_video_properties(file_path)
            video_lengths.append(props['frames'])

    return images, videos, video_lengths

#os.walk recursively goes through all the files in args.input_folder
image_paths, video_paths, video_lengths = [], [], []
for directory, folders, files in os.walk(args.input_folder):
    images, videos, lengths = find_images_videos(directory, files)
    image_paths.extend(images)
    video_paths.extend(videos)
    video_lengths.extend(lengths)

    print(F"found {len(images):8} images and {len(videos):8} videos ({sum(lengths):9} video frames) in {directory}")
    
print(F"TOTAL: found {len(image_paths)} images and {len(video_paths)} videos ({sum(video_lengths)} video frames)")
    
for image_path in tqdm(image_paths, desc=F'all images', unit='image', dynamic_ncols=True, disable=(len(image_paths)==0)):
    process_image(image_path)
    if args.verbose:
        tqdm.write(F"processed {image_path}")

progress_bar = tqdm(total=sum(video_lengths), desc=F'all videos', unit='frame', dynamic_ncols=True)
for video_path in video_paths:
    process_video(video_path, progress_bar)

progress_bar.close()
print("Done.")
