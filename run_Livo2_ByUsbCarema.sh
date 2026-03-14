#!/usr/bin/env bash
set -eo pipefail

# ---------- args ----------
VIDEO_DEV="${1:-/dev/video0}"
FPS="${2:-30.0}"
WIDTH="${3:-640}"
HEIGHT="${4:-480}"
OFFSET_MS="${5:-12.0}"
USE_RVIZ="${6:-true}"   # true / false

# ---------- paths ----------
ROS_SETUP="/opt/ros/humble/setup.bash"
LIVOX_WS="/home/gr/Livo2/ws_livox"
LIVO2_WS="/home/gr/Livo2/Livo2-Ros2"

FAST_CFG="${LIVO2_WS}/install/fast_livo/share/fast_livo/config/avia.yaml"
CAM_CFG="${LIVO2_WS}/install/fast_livo/share/fast_livo/config/camera_pinhole.yaml"
RVIZ_CFG="${LIVO2_WS}/install/fast_livo/share/fast_livo/rviz_cfg/fast_livo2.rviz"
MID360_LAUNCH="${LIVOX_WS}/install/livox_ros_driver2/share/livox_ros_driver2/launch_ROS2/msg_MID360_launch.py"
TIMESYNC_NODE="${LIVO2_WS}/tools/usb_cam_timestamp_compensator.py"

LOG_DIR="${LIVO2_WS}/log/run_usb_mid360_$(date +%Y%m%d_%H%M%S)"
mkdir -p "${LOG_DIR}"

# ---------- env ----------
source "${ROS_SETUP}"
source "${LIVOX_WS}/install/setup.bash"
source "${LIVO2_WS}/install/setup.bash"

pids=()

cleanup() {
  for p in "${pids[@]:-}"; do
    kill "$p" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

wait_topic_type() {
  local topic="$1"
  local type="$2"
  local timeout_s="${3:-20}"
  local t=0
  until ros2 topic list -t | grep -Fq "${topic} [${type}]"; do
    sleep 1
    t=$((t + 1))
    if [[ $t -ge $timeout_s ]]; then
      echo "ERROR: wait topic timeout: ${topic} [${type}]"
      return 1
    fi
  done
}

echo "[1/4] 清理旧进程..."
pkill -f livox_ros_driver2_node || true
pkill -f usb_cam_node_exe || true
pkill -f usb_cam_timestamp_compensator.py || true
pkill -f fastlivo_mapping || true
pkill -f "image_transport.*republish" || true

echo "[2/4] 启动 MID360 驱动..."
ros2 launch "${MID360_LAUNCH}" > "${LOG_DIR}/livox.log" 2>&1 &
pids+=($!)
wait_topic_type "/livox/lidar" "livox_ros_driver2/msg/CustomMsg" 25
wait_topic_type "/livox/imu" "sensor_msgs/msg/Imu" 25

echo "[3/4] 启动 USB 相机 + 时间补偿..."
ros2 run usb_cam usb_cam_node_exe --ros-args \
  -p video_device:="${VIDEO_DEV}" \
  -p framerate:="${FPS}" \
  -p image_width:="${WIDTH}" \
  -p image_height:="${HEIGHT}" \
  --remap image_raw:=/image_raw_usb > "${LOG_DIR}/usb_cam.log" 2>&1 &
pids+=($!)

python3 "${TIMESYNC_NODE}" --ros-args \
  -p input_topic:=/image_raw_usb \
  -p output_topic:=/image_raw \
  -p fixed_offset_ms:="${OFFSET_MS}" \
  -p use_arrival_time:=false \
  -p target_frame_id:=camera > "${LOG_DIR}/timesync.log" 2>&1 &
pids+=($!)

wait_topic_type "/image_raw_usb" "sensor_msgs/msg/Image" 20
wait_topic_type "/image_raw" "sensor_msgs/msg/Image" 20

echo "[4/4] 启动 FAST-LIVO..."
ros2 run fast_livo fastlivo_mapping --ros-args \
  --params-file "${FAST_CFG}" \
  --params-file "${CAM_CFG}" > "${LOG_DIR}/fastlivo.log" 2>&1 &
FAST_PID=$!
pids+=($FAST_PID)

if [[ "${USE_RVIZ}" == "true" ]]; then
  rviz2 -d "${RVIZ_CFG}" > "${LOG_DIR}/rviz.log" 2>&1 &
  pids+=($!)
fi

echo "启动完成。日志目录: ${LOG_DIR}"
echo "可检查："
echo "  ros2 topic hz /livox/imu"
echo "  ros2 topic hz /livox/lidar"
echo "  ros2 topic hz /image_raw"
echo "  ros2 topic hz /cloud_registered"
echo "  ros2 topic hz /aft_mapped_to_init"

wait "${FAST_PID}"
