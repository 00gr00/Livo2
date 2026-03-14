ARG BASE_IMAGE=docker.m.daocloud.io/library/ros:humble-ros-base-jammy

FROM ${BASE_IMAGE} AS base

ARG DEBIAN_FRONTEND=noninteractive
ARG ROS_DISTRO=humble
ARG LIVO2_REPO_URL=https://github.com/00gr00/Livo2.git
ARG LIVO2_REF=main
ARG LIVO2_SOURCE_MODE=context
ARG BUILDPLATFORM
ARG TARGETPLATFORM
ARG TARGETARCH
ARG TARGETOS
ARG WS_LIVOX_SKIP_PACKAGES=mvs_ros2_pkg
ARG LIVO2_COLCON_ARGS=

SHELL ["/bin/bash", "-lc"]

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TZ=Etc/UTC
ENV ROS_DISTRO=${ROS_DISTRO}
ENV LIVO2_ROOT=/workspace/Livo2
ENV BUILDPLATFORM=${BUILDPLATFORM}
ENV TARGETPLATFORM=${TARGETPLATFORM}
ENV TARGETARCH=${TARGETARCH}
ENV TARGETOS=${TARGETOS}

LABEL org.opencontainers.image.source="https://github.com/00gr00/Livo2.git"
LABEL org.opencontainers.image.description="Core multi-arch build image for Livo2 (ROS2 Humble, Livox, FAST-LIVO2)."

RUN echo "Build platform: ${BUILDPLATFORM}" \
 && echo "Target platform: ${TARGETPLATFORM}" \
 && echo "Target arch: ${TARGETARCH}" \
 && case "${TARGETARCH}" in \
      amd64|arm64) echo "Supported target architecture: ${TARGETARCH}" ;; \
      *) echo "Unsupported target architecture: ${TARGETARCH}" && exit 1 ;; \
    esac

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    gnupg2 \
    locales \
    lsb-release \
    software-properties-common \
    tzdata \
 && locale-gen en_US en_US.UTF-8 \
 && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY . /tmp/livo2-context

RUN case "${LIVO2_SOURCE_MODE}" in \
      context) \
        mv /tmp/livo2-context "${LIVO2_ROOT}" ;; \
      git) \
        rm -rf /tmp/livo2-context && \
        git clone --branch "${LIVO2_REF}" --depth 1 "${LIVO2_REPO_URL}" "${LIVO2_ROOT}" ;; \
      *) \
        echo "Unsupported LIVO2_SOURCE_MODE: ${LIVO2_SOURCE_MODE}" && exit 1 ;; \
    esac


FROM base AS system-deps

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    python3-colcon-common-extensions \
    python3-numpy \
    libapr1-dev \
    libboost-chrono-dev \
    libboost-filesystem-dev \
    libboost-system-dev \
    libboost-thread-dev \
    libeigen3-dev \
    libfmt-dev \
    libopencv-dev \
    libpcl-dev \
    ros-${ROS_DISTRO}-ament-cmake \
    ros-${ROS_DISTRO}-cv-bridge \
    ros-${ROS_DISTRO}-geometry-msgs \
    ros-${ROS_DISTRO}-image-transport \
    ros-${ROS_DISTRO}-nav-msgs \
    ros-${ROS_DISTRO}-pcl-conversions \
    ros-${ROS_DISTRO}-pcl-ros \
    ros-${ROS_DISTRO}-rclcpp \
    ros-${ROS_DISTRO}-rclpy \
    ros-${ROS_DISTRO}-rviz2 \
    ros-${ROS_DISTRO}-sensor-msgs \
    ros-${ROS_DISTRO}-std-msgs \
    ros-${ROS_DISTRO}-tf2 \
    ros-${ROS_DISTRO}-tf2-geometry-msgs \
    ros-${ROS_DISTRO}-tf2-ros \
    ros-${ROS_DISTRO}-visualization-msgs \
 && rm -rf /var/lib/apt/lists/*


FROM system-deps AS third-party

WORKDIR ${LIVO2_ROOT}/Sophus
RUN mkdir -p build \
 && cd build \
 && cmake .. \
 && make -j"$(nproc)" \
 && make install

WORKDIR ${LIVO2_ROOT}/Livox-SDK2
RUN mkdir -p build \
 && cd build \
 && cmake .. \
 && make -j"$(nproc)" \
 && make install


FROM third-party AS ws-livox

ARG ROS_DISTRO=humble
ARG WS_LIVOX_SKIP_PACKAGES=mvs_ros2_pkg
ARG LIVO2_COLCON_ARGS=

WORKDIR ${LIVO2_ROOT}/ws_livox
RUN source /opt/ros/${ROS_DISTRO}/setup.bash \
 && colcon build \
    --symlink-install \
    --packages-skip ${WS_LIVOX_SKIP_PACKAGES} \
    ${LIVO2_COLCON_ARGS}


FROM ws-livox AS livo2-ros

ARG ROS_DISTRO=humble
ARG LIVO2_COLCON_ARGS=

WORKDIR ${LIVO2_ROOT}/Livo2-Ros2
RUN source /opt/ros/${ROS_DISTRO}/setup.bash \
 && source ${LIVO2_ROOT}/ws_livox/install/setup.bash \
 && colcon build \
    --symlink-install \
    ${LIVO2_COLCON_ARGS}


FROM livo2-ros AS runtime

WORKDIR ${LIVO2_ROOT}

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
