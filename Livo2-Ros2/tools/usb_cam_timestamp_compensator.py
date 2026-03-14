#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float64


class UsbCamTimestampCompensator(Node):
    def __init__(self) -> None:
        super().__init__('usb_cam_timestamp_compensator')

        self.declare_parameter('input_topic', '/image_raw_usb')
        self.declare_parameter('output_topic', '/image_raw')
        self.declare_parameter('fixed_offset_ms', 0.0)
        self.declare_parameter('use_arrival_time', False)
        self.declare_parameter('target_frame_id', '')
        self.declare_parameter('publish_debug', True)

        self.input_topic = self.get_parameter('input_topic').value
        self.output_topic = self.get_parameter('output_topic').value

        self.sub = self.create_subscription(Image, self.input_topic, self.image_cb, 50)
        self.pub = self.create_publisher(Image, self.output_topic, 50)

        self.debug_pub = None
        if bool(self.get_parameter('publish_debug').value):
            self.debug_pub = self.create_publisher(Float64, '/usb_cam_time_offset_ms', 10)

        self.frame_count = 0
        self.warned_zero_stamp = False

        self.get_logger().info(
            f'USB cam timestamp compensator started: {self.input_topic} -> {self.output_topic}'
        )

    def image_cb(self, msg: Image) -> None:
        offset_ms = float(self.get_parameter('fixed_offset_ms').value)
        use_arrival_time = bool(self.get_parameter('use_arrival_time').value)
        target_frame_id = str(self.get_parameter('target_frame_id').value)

        if use_arrival_time:
            now = self.get_clock().now().to_msg()
            base_sec = now.sec
            base_ns = now.nanosec
        else:
            base_sec = msg.header.stamp.sec
            base_ns = msg.header.stamp.nanosec

            if base_sec == 0 and base_ns == 0:
                now = self.get_clock().now().to_msg()
                base_sec = now.sec
                base_ns = now.nanosec
                if not self.warned_zero_stamp:
                    self.get_logger().warn(
                        'Input image stamp is zero. Falling back to arrival time for stamping.'
                    )
                    self.warned_zero_stamp = True

        total_ns = int(base_sec) * 1_000_000_000 + int(base_ns)
        corrected_ns = total_ns - int(offset_ms * 1_000_000.0)
        if corrected_ns < 0:
            corrected_ns = 0

        out = Image()
        out.header = msg.header
        out.height = msg.height
        out.width = msg.width
        out.encoding = msg.encoding
        out.is_bigendian = msg.is_bigendian
        out.step = msg.step
        out.data = msg.data

        out.header.stamp.sec = corrected_ns // 1_000_000_000
        out.header.stamp.nanosec = corrected_ns % 1_000_000_000

        if target_frame_id:
            out.header.frame_id = target_frame_id

        self.pub.publish(out)

        if self.debug_pub is not None:
            dbg = Float64()
            dbg.data = offset_ms
            self.debug_pub.publish(dbg)

        self.frame_count += 1
        if self.frame_count % 300 == 0:
            self.get_logger().info(
                f'published={self.frame_count}, offset_ms={offset_ms:.3f}, use_arrival_time={use_arrival_time}'
            )


def main() -> None:
    rclpy.init()
    node = UsbCamTimestampCompensator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
