#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-livo2-mvs:dev}"
MVS_SDK_PATH="${MVS_SDK_PATH:-/opt/MVS}"

docker run --rm -it \
  --network host \
  --privileged \
  -e DISPLAY="${DISPLAY:-:0}" \
  -e QT_X11_NO_MITSHM=1 \
  -e ROS_DISTRO=humble \
  -e LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/lib:/usr/lib:/lib:/opt/MVS/lib/64:/opt/MVS/lib/aarch64 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v /dev:/dev \
  -v "${MVS_SDK_PATH}:/opt/MVS:ro" \
  -w /workspace/Livo2 \
  "${IMAGE}" \
  bash

