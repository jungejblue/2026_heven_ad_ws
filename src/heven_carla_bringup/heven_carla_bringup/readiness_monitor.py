"""Periodically report HEVEN sensor receive rates and readiness."""

from __future__ import annotations

from collections import Counter
from functools import partial

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from sensor_msgs.msg import Image, Imu, NavSatFix, PointCloud2
from std_msgs.msg import Bool

from .topic_contract import READY_TOPIC, SENSOR_TOPICS


class ReadinessMonitor(Node):
    def __init__(self) -> None:
        super().__init__("heven_readiness_monitor")
        self.declare_parameter("report_period_seconds", 5.0)
        self.report_period = float(
            self.get_parameter("report_period_seconds").value
        )
        if self.report_period <= 0.0:
            raise ValueError("report_period_seconds must be positive")

        ready_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.create_subscription(Bool, READY_TOPIC, self._on_ready, ready_qos)

        subscriptions = {
            "left_cam": (Image, SENSOR_TOPICS["left_cam"]),
            "right_cam": (Image, SENSOR_TOPICS["right_cam"]),
            "front_cam": (Image, SENSOR_TOPICS["front_cam"]),
            "lidar": (PointCloud2, SENSOR_TOPICS["lidar"]),
            "imu": (Imu, SENSOR_TOPICS["imu"]),
            "gnss": (NavSatFix, SENSOR_TOPICS["gnss"]),
        }
        self._subscriptions = []
        for name, (message_type, topic) in subscriptions.items():
            self._subscriptions.append(
                self.create_subscription(
                    message_type,
                    topic,
                    partial(self._on_message, name),
                    qos_profile_sensor_data,
                )
            )

        self.counts: Counter = Counter()
        self.ready = False
        self.create_timer(self.report_period, self._report)

    def _on_ready(self, message: Bool) -> None:
        if message.data and not self.ready:
            self.get_logger().info("/heven/sensors_ready became True.")
        self.ready = bool(message.data)

    def _on_message(self, name: str, _message) -> None:
        self.counts[name] += 1

    def _report(self) -> None:
        rates = {
            name: self.counts[name] / self.report_period
            for name in SENSOR_TOPICS
        }
        self.counts.clear()
        formatted = ", ".join(f"{name}={rate:.1f}Hz" for name, rate in rates.items())
        state = "READY" if self.ready else "WARMING_UP"
        self.get_logger().info(f"state={state}; {formatted}")


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ReadinessMonitor()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == "__main__":
    main()
