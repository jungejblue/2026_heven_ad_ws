"""Stable ROS topic names used by the HEVEN CARLA sensor suite."""

SENSOR_TOPICS = {
    "left_cam": "/carla/ego_vehicle/left_cam/image",
    "right_cam": "/carla/ego_vehicle/right_cam/image",
    "front_cam": "/carla/ego_vehicle/front_cam/image",
    "lidar": "/carla/ego_vehicle/lidar",
    "imu": "/carla/ego_vehicle/imu",
    "gnss": "/carla/ego_vehicle/gnss",
}

CAMERA_INFO_TOPICS = {
    "left_cam": "/carla/ego_vehicle/left_cam/camera_info",
    "right_cam": "/carla/ego_vehicle/right_cam/camera_info",
    "front_cam": "/carla/ego_vehicle/front_cam/camera_info",
}

ODOMETRY_TOPIC = "/carla/ego_vehicle/odometry"
READY_TOPIC = "/heven/sensors_ready"
VEHICLE_CONTROL_TOPIC = "/carla/ego_vehicle/vehicle_control_cmd"
VEHICLE_STATUS_TOPIC = "/carla/ego_vehicle/vehicle_status"

