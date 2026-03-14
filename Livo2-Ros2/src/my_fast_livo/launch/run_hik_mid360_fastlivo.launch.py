from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    home = os.path.expanduser("~")

    livox_share = get_package_share_directory("livox_ros_driver2")
    mvs_share = get_package_share_directory("mvs_ros2_pkg")
    fast_livo_share = get_package_share_directory("fast_livo")

    livox_launch = os.path.join(livox_share, "launch_ROS2", "msg_MID360_launch.py")
    hik_launch = os.path.join(mvs_share, "launch", "mvs_camera_trigger.py")

    avia_yaml = os.path.join(fast_livo_share, "config", "avia.yaml")
    camera_yaml = os.path.join(fast_livo_share, "config", "camera_pinhole.yaml")
    rviz_cfg = os.path.join(fast_livo_share, "rviz_cfg", "fast_livo2.rviz")

    retimestamp_script = os.path.join(home, "Livo2", "tools", "livox_retimestamp.py")

    return LaunchDescription([
        SetEnvironmentVariable(
            name="LD_LIBRARY_PATH",
            value="/usr/lib/x86_64-linux-gnu:/opt/ros/humble/lib/x86_64-linux-gnu:/opt/ros/humble/lib:" +
                  os.environ.get("LD_LIBRARY_PATH", "")
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(livox_launch)
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(hik_launch)
        ),

        TimerAction(
            period=2.0,
            actions=[
                ExecuteProcess(
                    cmd=["python3", retimestamp_script],
                    output="screen"
                )
            ]
        ),

        TimerAction(
            period=4.0,
            actions=[
                Node(
                    package="fast_livo",
                    executable="fastlivo_mapping",
                    name="laserMapping",
                    output="screen",
                    parameters=[avia_yaml, camera_yaml]
                )
            ]
        ),

        TimerAction(
            period=6.0,
            actions=[
                Node(
                    package="rviz2",
                    executable="rviz2",
                    name="rviz2",
                    output="screen",
                    arguments=["-d", rviz_cfg]
                )
            ]
        ),
    ])
