# Livo2

Livo2 是一个围绕 Livox LiDAR、相机和 ROS2 Humble 组织的多模块工程仓库，目标是跑通 LiDAR-IMU-Visual 融合建图链路。当前仓库推荐的主线是：

`MID360 -> livox_ros_driver2 -> livox_retimestamp -> MVS 相机 -> FAST-LIVO2 -> RViz`

仓库里同时保留了海康 MVS 相机驱动、Livox SDK2、Sophus 以及 STM32 时间同步工程，方便在同一目录下完成驱动、算法和同步链路联调。

## 1. 当前仓库结构

```text
Livo2/
├── run_Livo2_ByUsbCarema.sh   # 一键启动脚本，当前默认入口（usb版）
├── get_Livo2_source.sh        # source ROS2 与两个工作空间环境
├── tools/
│   ├── start_livo2.launch.py  # 顶层一键启动入口(海康版)
│   └── livox_retimestamp.py   # Livox 话题重打时间戳并输出 *_sync
├── ws_livox/                  # LiDAR / 相机驱动 ROS2 工作空间
│   └── src/
│       ├── livox_ros_driver2/ # Livox MID360 ROS2 驱动
│       └── mvs_ros2_pkg/      # 海康 MVS 相机 ROS2 驱动
├── Livo2-Ros2/                # FAST-LIVO2 ROS2 工作空间
│   ├── src/FAST-LIVO2/        # FAST-LIVO2 主包
│   └── tools/
│       └── usb_cam_timestamp_compensator.py  # USB 相机备用时间补偿方案
├── Livox-SDK2/                # Livox 官方 SDK2
├── Sophus/                    # Sophus 依赖源码
└── stm32_timersync-open/      # STM32 时间同步工程
```

说明：

- `ws_livox` 和 `Livo2-Ros2` 都已经包含 `build/`、`install/`、`log/`，说明这个仓库已经被本地构建过。
- 顶层 [`start_livo2.launch.py`](/home/gr/Livo2/tools/start_livo2.launch.py) 是当前推荐入口。
- [`run_Livo2_ByUsbCarema.sh`](/home/gr/Livo2/run_Livo2_ByUsbCarema.sh) 仍可作为 USB 相机备用方案。

## 2. 项目主链路

当前推荐入口 [`start_livo2.launch.py`](/home/gr/Livo2/tools/start_livo2.launch.py) 组织了如下流程：

1. `source /opt/ros/humble/setup.bash`
2. `source ws_livox/install/setup.bash`
3. `source Livo2-Ros2/install/setup.bash`
4. 启动 `livox_ros_driver2` 的 `msg_MID360_launch.py`
5. 启动 `mvs_ros2_pkg` 相机节点，发布 `/left_camera/image`
6. 启动 [`livox_retimestamp.py`](/home/gr/Livo2/tools/livox_retimestamp.py)，输出 `/livox/lidar_sync` 与 `/livox/imu_sync`
7. 延迟启动 `fast_livo/fastlivo_mapping`
8. 可选启动 RViz
9. 启动后自动执行一轮话题自检

运行期间关键话题包括：

- `/livox/lidar`
- `/livox/imu`
- `/livox/lidar_sync`
- `/livox/imu_sync`
- `/left_camera/image`
- `/left_camera/image/camera_info`
- `/cloud_registered`
- `/aft_mapped_to_init`

## 3. 关键目录说明

### `Livo2-Ros2/src/FAST-LIVO2`

FAST-LIVO2 是这个仓库里的核心算法包，包名为 `fast_livo`。从源码和配置来看，它依赖以下输入：

- LiDAR 点云话题
- IMU 话题
- 图像话题
- 相机内参配置
- LiDAR/相机外参配置

默认配置文件位于：

- [`avia.yaml`](/home/gr/Livo2/Livo2-Ros2/src/FAST-LIVO2/config/avia.yaml)
- [`camera_pinhole.yaml`](/home/gr/Livo2/Livo2-Ros2/src/FAST-LIVO2/config/camera_pinhole.yaml)

需要注意的是，`avia.yaml` 中当前启用的是：

- `lid_topic: /livox/lidar_sync`
- `imu_topic: /livox/imu_sync`
- `img_topic: "/left_camera/image"`

而当前推荐的顶层 launch 已经显式补上了 `livox_retimestamp.py`，因此它会把原始话题：

- `/livox/lidar`
- `/livox/imu`

转换成 FAST-LIVO2 默认使用的：

- `/livox/lidar_sync`
- `/livox/imu_sync`

后续排障时，优先核对安装目录下实际生效的参数文件：

- `/home/gr/Livo2/Livo2-Ros2/install/fast_livo/share/fast_livo/config/avia.yaml`
- `/home/gr/Livo2/Livo2-Ros2/install/fast_livo/share/fast_livo/config/camera_pinhole.yaml`

### `tools`

顶层工具目录保存当前推荐运行链路所需的辅助脚本：

- [`start_livo2.launch.py`](/home/gr/Livo2/tools/start_livo2.launch.py)
- [`livox_retimestamp.py`](/home/gr/Livo2/tools/livox_retimestamp.py)

其中 `livox_retimestamp.py` 用于：

- 订阅 `/livox/lidar` 与 `/livox/imu`
- 重写消息头时间戳
- 发布到 `/livox/lidar_sync` 与 `/livox/imu_sync`

这样可以和当前 [`avia.yaml`](/home/gr/Livo2/Livo2-Ros2/src/FAST-LIVO2/config/avia.yaml) 中的默认输入话题保持一致。

### `Livo2-Ros2/tools`

[`usb_cam_timestamp_compensator.py`](/home/gr/Livo2/Livo2-Ros2/tools/usb_cam_timestamp_compensator.py) 是一个简单直接的 ROS2 Python 节点，用于：

- 订阅 `/image_raw_usb`
- 根据固定时间偏移修正图像时间戳
- 发布到 `/image_raw`
- 可选发布调试话题 `/usb_cam_time_offset_ms`

当前启动脚本默认 `fixed_offset_ms=12.0`。

### `ws_livox/src/livox_ros_driver2`

这是 Livox MID360 的 ROS2 驱动，当前脚本使用：

- [`launch_ROS2/msg_MID360_launch.py`](/home/gr/Livo2/ws_livox/src/livox_ros_driver2/launch_ROS2/msg_MID360_launch.py)
- [`config/MID360_config.json`](/home/gr/Livo2/ws_livox/src/livox_ros_driver2/config/MID360_config.json)

当前配置里的主机 IP 为 `192.168.1.50`，LiDAR IP 为 `192.168.1.3`。如果换电脑或网卡，必须同步修改 `MID360_config.json`。

### `ws_livox/src/mvs_ros2_pkg`

这是海康 MVS 相机 ROS2 驱动。它依赖系统安装 MVS SDK，并在 CMake 中硬编码了：

- `/opt/MVS/include`
- `/opt/MVS/lib/64/` 或 `/opt/MVS/lib/aarch64/`

如果你打算使用海康相机，需要先在系统中安装 MVS SDK，再构建 `ws_livox`。

### `stm32_timersync-open`

这里保存的是 STM32 时间同步工程，适合后续做外部同步链路调试或二次开发，不是当前 ROS2 主链路启动的必需目录。

## 4. 依赖关系

根据源码和构建脚本，当前仓库的主要依赖如下：

- Ubuntu 22.04
- ROS2 Humble
- `colcon`
- PCL
- Eigen3
- OpenCV
- Boost
- Sophus
- Livox-SDK2
- `usb_cam`
- `image_transport`
- `cv_bridge`
- 可选：MVS SDK
- 可选：STM32 同步链路开发环境

另外，`FAST-LIVO2` 的 CMake 还显式依赖：

- `vikit_common`
- `vikit_ros`

并且链接路径写成了工作空间安装目录下的 `.so`：

```cmake
${CMAKE_SOURCE_DIR}/../../install/vikit_common/lib/libvikit_common.so
${CMAKE_SOURCE_DIR}/../../install/vikit_ros/lib/libvikit_ros.so
```

这意味着：

- `Livo2-Ros2` 工作空间里需要先存在并成功安装 `vikit_common` 和 `vikit_ros`
- 清理安装目录或迁移目录时，要特别留意这两个包是否仍能被找到

## 5. 推荐启动方式

### 方式 A：使用顶层一键启动 launch

```bash
cd /home/gr/Livo2
source /opt/ros/humble/setup.bash
source /home/gr/Livo2/ws_livox/install/setup.bash
source /home/gr/Livo2/Livo2-Ros2/install/setup.bash
ros2 launch /home/gr/Livo2/tools/start_livo2.launch.py
```

这个入口会一起启动：

- `livox_ros_driver2`
- `mvs_ros2_pkg`
- `livox_retimestamp.py`
- `fast_livo`
- `rviz2`
- 启动后自检

常用可选参数：

```bash
ros2 launch /home/gr/Livo2/tools/start_livo2.launch.py use_rviz:=false
ros2 launch /home/gr/Livo2/tools/start_livo2.launch.py self_check_delay_sec:=15.0
ros2 launch /home/gr/Livo2/tools/start_livo2.launch.py enable_self_check:=false
ros2 launch /home/gr/Livo2/tools/start_livo2.launch.py \
  mvs_camera_config:=/home/gr/Livo2/ws_livox/install/mvs_ros2_pkg/share/mvs_ros2_pkg/config/right_camera_trigger.yaml
```

启动后默认会输出一轮自检，检查以下话题是否正常：

- `/livox/lidar`
- `/livox/imu`
- `/livox/lidar_sync`
- `/livox/imu_sync`
- `/left_camera/image`
- `/left_camera/image/camera_info`
- `/cloud_registered`
- `/aft_mapped_to_init`

如果看到下面这种输出，说明对应链路已经通了：

```text
[SELF-CHECK][OK] Livox raw lidar: /livox/lidar
[SELF-CHECK][OK] Camera image: /left_camera/image
[SELF-CHECK][OK] FAST-LIVO registered cloud: /cloud_registered
```

### 方式 B：使用 USB 相机备用脚本

```bash
cd /home/gr/Livo2
./run_Livo2_ByUsbCarema.sh
```

可选参数：

```bash
./run_Livo2_ByUsbCarema.sh [VIDEO_DEV] [FPS] [WIDTH] [HEIGHT] [OFFSET_MS] [USE_RVIZ]
```

例如：

```bash
./run_Livo2_ByUsbCarema.sh /dev/video0 30 640 480 12.0 true
```

### 方式 C：手动 source 环境并分别启动

```bash
cd /home/gr/Livo2
source ./get_Livo2_source.sh
```

然后分别启动：

```bash
ros2 launch livox_ros_driver2 msg_MID360_launch.py
python3 /home/gr/Livo2/tools/livox_retimestamp.py --ros-args \
  -p lidar_in:=/livox/lidar \
  -p lidar_out:=/livox/lidar_sync \
  -p imu_in:=/livox/imu \
  -p imu_out:=/livox/imu_sync
ros2 run mvs_ros2_pkg mvs_camera_node \
  /home/gr/Livo2/ws_livox/install/mvs_ros2_pkg/share/mvs_ros2_pkg/config/left_camera_trigger.yaml
ros2 run fast_livo fastlivo_mapping --ros-args \
  --params-file /home/gr/Livo2/Livo2-Ros2/install/fast_livo/share/fast_livo/config/avia.yaml \
  --params-file /home/gr/Livo2/Livo2-Ros2/install/fast_livo/share/fast_livo/config/camera_pinhole.yaml
rviz2 -d /home/gr/Livo2/Livo2-Ros2/install/fast_livo/share/fast_livo/rviz_cfg/fast_livo2.rviz
```

如果使用 USB 相机链路，还需要额外启动 `usb_cam` 和 `usb_cam_timestamp_compensator.py`。

## 6. 推荐构建顺序

当前仓库更像“集成环境”，建议按下面顺序构建：

### 1) 构建 Livox 驱动工作空间

```bash
cd /home/gr/Livo2/ws_livox
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

### 2) 构建 FAST-LIVO2 工作空间

```bash
cd /home/gr/Livo2/Livo2-Ros2
source /opt/ros/humble/setup.bash
source /home/gr/Livo2/ws_livox/install/setup.bash
colcon build --symlink-install --continue-on-error
```

如果 `vikit_*`、`Sophus`、`usb_cam` 或 OpenCV/PCL 缺失，构建会失败，需要先补依赖。

## 7. 调试建议

常用检查命令：

```bash
ros2 topic list -t
ros2 topic hz /livox/imu
ros2 topic hz /livox/lidar
ros2 topic hz /livox/lidar_sync
ros2 topic hz /left_camera/image
ros2 topic hz /cloud_registered
ros2 topic echo /left_camera/image/camera_info --once
```

一键脚本会把日志输出到：

```text
/home/gr/Livo2/Livo2-Ros2/log/run_usb_mid360_时间戳/
```

其中常见日志文件包括：

- `livox.log`
- `usb_cam.log`
- `timesync.log`
- `fastlivo.log`
- `rviz.log`

## 8. 当前仓库状态总结

从现有文件可以看出，这个仓库已经具备以下能力：

- 基于 ROS2 Humble 的 LiDAR-IMU-Visual 建图环境
- MID360 驱动集成
- 顶层一键启动与启动后自检
- Livox 原始话题到 `*_sync` 话题的重打时间戳桥接
- 海康 MVS 相机驱动接入
- USB 相机链路与时间补偿
- STM32 时间同步工程留档

同时也有几个维护上需要注意的点：

- 顶层还没有统一 README，初次接手成本偏高
- 源码配置与启动脚本中的默认话题存在不一致
- `FAST-LIVO2` 的部分依赖链接到安装目录，路径耦合较强
- 仓库内包含大量构建产物，迁移和清理时要谨慎
