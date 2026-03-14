#!/usr/bin/env python3
import copy

import rclpy
from rclpy.node import Node

from livox_ros_driver2.msg import CustomMsg
from sensor_msgs.msg import Imu


class LivoxRetimestampNode(Node):
    def __init__(self):
        super().__init__('livox_retimestamp')

        self.declare_parameter('lidar_in', '/livox/lidar')
        self.declare_parameter('lidar_out', '/livox/lidar_sync')
        self.declare_parameter('imu_in', '/livox/imu')
        self.declare_parameter('imu_out', '/livox/imu_sync')
        self.declare_parameter('frame_id', 'livox_frame')

        lidar_in = self.get_parameter('lidar_in').value
        lidar_out = self.get_parameter('lidar_out').value
        imu_in = self.get_parameter('imu_in').value
        imu_out = self.get_parameter('imu_out').value
        self.frame_id = self.get_parameter('frame_id').value

        self.lidar_pub = self.create_publisher(CustomMsg, lidar_out, 10)
        self.imu_pub = self.create_publisher(Imu, imu_out, 200)

        self.lidar_sub = self.create_subscription(
            CustomMsg, lidar_in, self.lidar_cb, 10
        )
        self.imu_sub = self.create_subscription(
            Imu, imu_in, self.imu_cb, 200
        )

        self.get_logger().info(f'lidar: {lidar_in} -> {lidar_out}')
        self.get_logger().info(f'imu:   {imu_in} -> {imu_out}')

    def lidar_cb(self, msg: CustomMsg):
        out = copy.deepcopy(msg)
        now_msg = self.get_clock().now().to_msg()

        out.header.stamp = now_msg
        if self.frame_id:
            out.header.frame_id = self.frame_id

        # Livox CustomMsg 关键字段：必须一起改
        out.timebase = int(now_msg.sec) * 1000000000 + int(now_msg.nanosec)

        self.lidar_pub.publish(out)

    def imu_cb(self, msg: Imu):
        out = copy.deepcopy(msg)
        now_msg = self.get_clock().now().to_msg()

        out.header.stamp = now_msg
        if self.frame_id:
            out.header.frame_id = self.frame_id

        self.imu_pub.publish(out)


def main():
    rclpy.init()
    node = LivoxRetimestampNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()