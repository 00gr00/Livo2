#!/usr/bin/env bash
set -euo pipefail

DEVICE="${1:-/dev/video0}"
FPS="${2:-30.0}"
WIDTH="${3:-640}"
HEIGHT="${4:-480}"

# Publish raw USB camera frames to /image_raw_usb.
ros2 run usb_cam usb_cam_node_exe --ros-args \
  -p video_device:=${DEVICE} \
  -p framerate:=${FPS} \
  -p image_width:=${WIDTH} \
  -p image_height:=${HEIGHT} \
  --remap image_raw:=/image_raw_usb
