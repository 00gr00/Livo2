#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-livo2-core:dev}"

docker run --rm -it \
  --network host \
  --privileged \
  -e DISPLAY="${DISPLAY:-:0}" \
  -e QT_X11_NO_MITSHM=1 \
  -e ROS_DISTRO=humble \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v /dev:/dev \
  -w /workspace/Livo2 \
  "${IMAGE}" \
  bash

