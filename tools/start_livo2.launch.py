#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    root_dir = os.path.dirname(os.path.abspath(__file__))

    fast_livo_share = get_package_share_directory("fast_livo")
    livox_share = get_package_share_directory("livox_ros_driver2")
    mvs_share = get_package_share_directory("mvs_ros2_pkg")

    default_avia_config = os.path.join(fast_livo_share, "config", "avia.yaml")
    default_camera_params = os.path.join(fast_livo_share, "config", "camera_pinhole.yaml")
    default_rviz_config = os.path.join(fast_livo_share, "rviz_cfg", "fast_livo2.rviz")
    default_mvs_config = os.path.join(mvs_share, "config", "left_camera_trigger.yaml")
    default_livox_launch = os.path.join(livox_share, "launch_ROS2", "msg_MID360_launch.py")
    livox_retimestamp_script = os.path.join(root_dir, "livox_retimestamp.py")

    use_rviz_arg = DeclareLaunchArgument(
        "use_rviz",
        default_value="true",
        description="Whether to launch RViz2.",
    )
    avia_params_arg = DeclareLaunchArgument(
        "avia_params_file",
        default_value=default_avia_config,
        description="Full path to the FAST-LIVO LiDAR/IMU config file.",
    )
    camera_params_arg = DeclareLaunchArgument(
        "camera_params_file",
        default_value=default_camera_params,
        description="Full path to the FAST-LIVO camera config file.",
    )
    mvs_camera_config_arg = DeclareLaunchArgument(
        "mvs_camera_config",
        default_value=default_mvs_config,
        description="Full path to the MVS camera driver YAML.",
    )
    rviz_config_arg = DeclareLaunchArgument(
        "rviz_config_file",
        default_value=default_rviz_config,
        description="Full path to the RViz config file.",
    )
    fast_livo_delay_arg = DeclareLaunchArgument(
        "fast_livo_delay_sec",
        default_value="3.0",
        description="Delay in seconds before starting FAST-LIVO.",
    )
    enable_self_check_arg = DeclareLaunchArgument(
        "enable_self_check",
        default_value="true",
        description="Whether to run post-startup topic self checks.",
    )
    self_check_delay_arg = DeclareLaunchArgument(
        "self_check_delay_sec",
        default_value="8.0",
        description="Delay in seconds before running self checks.",
    )

    livox_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(LaunchConfiguration("livox_launch_file")),
    )

    mvs_camera = Node(
        package="mvs_ros2_pkg",
        executable="mvs_camera_node",
        name="mvs_camera_trigger",
        arguments=[
            LaunchConfiguration("mvs_camera_config"),
            "--ros-args",
            "--log-level",
            "info",
        ],
        output="screen",
        respawn=True,
    )

    livox_retimestamp = ExecuteProcess(
        cmd=[
            "python3",
            livox_retimestamp_script,
            "--ros-args",
            "-p",
            "lidar_in:=/livox/lidar",
            "-p",
            "lidar_out:=/livox/lidar_sync",
            "-p",
            "imu_in:=/livox/imu",
            "-p",
            "imu_out:=/livox/imu_sync",
            "-p",
            "frame_id:=livox_frame",
        ],
        output="screen",
    )

    fast_livo = Node(
        package="fast_livo",
        executable="fastlivo_mapping",
        name="fastlivo_mapping",
        output="screen",
        parameters=[
            LaunchConfiguration("avia_params_file"),
            LaunchConfiguration("camera_params_file"),
        ],
    )

    delayed_fast_livo = TimerAction(
        period=LaunchConfiguration("fast_livo_delay_sec"),
        actions=[fast_livo],
    )

    rviz = Node(
        condition=IfCondition(LaunchConfiguration("use_rviz")),
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", LaunchConfiguration("rviz_config_file")],
        output="screen",
    )

    livox_launch_arg = DeclareLaunchArgument(
        "livox_launch_file",
        default_value=default_livox_launch,
        description="Full path to the livox_ros_driver2 launch file.",
    )

    self_check = ExecuteProcess(
        condition=IfCondition(LaunchConfiguration("enable_self_check")),
        cmd=[
            "bash",
            "-lc",
            r"""
set +e

check_topic() {
  local topic="$1"
  local label="$2"
  local timeout_s="${3:-8}"
  if timeout "${timeout_s}s" ros2 topic echo "${topic}" --once > /dev/null 2>&1; then
    echo "[SELF-CHECK][OK] ${label}: ${topic}"
  else
    echo "[SELF-CHECK][FAIL] ${label}: ${topic}"
  fi
}

echo "[SELF-CHECK] Starting topic checks..."
check_topic "/livox/lidar" "Livox raw lidar" 10
check_topic "/livox/imu" "Livox raw imu" 10
check_topic "/livox/lidar_sync" "Livox synced lidar" 10
check_topic "/livox/imu_sync" "Livox synced imu" 10
check_topic "/left_camera/image" "Camera image" 10
check_topic "/left_camera/image/camera_info" "Camera info" 10
check_topic "/cloud_registered" "FAST-LIVO registered cloud" 12
check_topic "/aft_mapped_to_init" "FAST-LIVO odometry" 12
echo "[SELF-CHECK] Done."
""",
        ],
        output="screen",
    )

    delayed_self_check = TimerAction(
        period=LaunchConfiguration("self_check_delay_sec"),
        actions=[self_check],
    )

    return LaunchDescription(
        [
            use_rviz_arg,
            avia_params_arg,
            camera_params_arg,
            mvs_camera_config_arg,
            rviz_config_arg,
            fast_livo_delay_arg,
            enable_self_check_arg,
            self_check_delay_arg,
            livox_launch_arg,
            livox_driver,
            mvs_camera,
            livox_retimestamp,
            delayed_fast_livo,
            delayed_self_check,
            rviz,
        ]
    )
