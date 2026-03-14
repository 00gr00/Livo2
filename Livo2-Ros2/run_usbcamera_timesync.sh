#!/usr/bin/env bash
set -euo pipefail

OFFSET_MS="${1:-0.0}"
USE_ARRIVAL_TIME="${2:-false}"
TARGET_FRAME_ID="${3:-}"

python3 /home/gr/Livo2/Livo2-Ros2/tools/usb_cam_timestamp_compensator.py --ros-args \
  -p input_topic:=/image_raw_usb \
  -p output_topic:=/image_raw \
  -p fixed_offset_ms:=${OFFSET_MS} \
  -p use_arrival_time:=${USE_ARRIVAL_TIME} \
  -p target_frame_id:=${TARGET_FRAME_ID}
