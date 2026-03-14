#!/usr/bin/env bash
set -e

if [[ -n "${ROS_DISTRO:-}" && -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
fi

if [[ -f "/workspace/Livo2/ws_livox/install/setup.bash" ]]; then
  source "/workspace/Livo2/ws_livox/install/setup.bash"
fi

if [[ -f "/workspace/Livo2/Livo2-Ros2/install/setup.bash" ]]; then
  source "/workspace/Livo2/Livo2-Ros2/install/setup.bash"
fi

exec "$@"

