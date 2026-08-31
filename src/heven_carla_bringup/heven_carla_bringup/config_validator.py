"""Validate the installed HEVEN bridge and object configuration files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .topic_contract import SENSOR_TOPICS


EXPECTED_REAL_SENSORS = {
    "left_cam": "sensor.camera.rgb",
    "right_cam": "sensor.camera.rgb",
    "front_cam": "sensor.camera.rgb",
    "lidar": "sensor.lidar.ray_cast",
    "imu": "sensor.other.imu",
    "gnss": "sensor.other.gnss",
}


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def find_vehicle(document: Dict) -> Dict:
    vehicles = [
        item
        for item in document.get("objects", [])
        if item.get("type") == "vehicle.heven.ev"
        and item.get("id") == "ego_vehicle"
    ]
    if len(vehicles) != 1:
        raise ValueError(
            "Configuration must contain exactly one vehicle.heven.ev with "
            "id='ego_vehicle'."
        )
    return vehicles[0]


def validate_vehicle_config(path: Path) -> None:
    vehicle = find_vehicle(load_json(path))
    point = vehicle.get("spawn_point", {})
    required = {"x", "y", "z", "roll", "pitch", "yaw"}
    missing = required.difference(point)
    if missing:
        raise ValueError(f"vehicle_only.json missing spawn keys: {sorted(missing)}")


def validate_sensor_config(path: Path) -> None:
    document = load_json(path)
    vehicle = find_vehicle(document)
    sensors = vehicle.get("sensors", [])
    by_id = {sensor.get("id"): sensor for sensor in sensors}

    if len(by_id) != len(sensors):
        raise ValueError("Sensor IDs must be unique and non-empty.")

    for sensor_id, expected_type in EXPECTED_REAL_SENSORS.items():
        sensor = by_id.get(sensor_id)
        if sensor is None:
            raise ValueError(f"Missing sensor id '{sensor_id}'.")
        if sensor.get("type") != expected_type:
            raise ValueError(
                f"Sensor '{sensor_id}' type must be '{expected_type}', "
                f"not '{sensor.get('type')}'."
            )
        point = sensor.get("spawn_point", {})
        required = {"x", "y", "z", "roll", "pitch", "yaw"}
        missing = required.difference(point)
        if missing:
            raise ValueError(
                f"Sensor '{sensor_id}' missing spawn keys: {sorted(missing)}"
            )
        if float(sensor.get("sensor_tick", -1.0)) != 0.0:
            raise ValueError(
                f"Initial 20 Hz validation requires {sensor_id}.sensor_tick=0.0."
            )

    for pseudo_id in ("tf", "odometry"):
        if pseudo_id not in by_id:
            raise ValueError(f"Missing pseudo sensor '{pseudo_id}'.")

    actor_lists = [
        item
        for item in document.get("objects", [])
        if item.get("type") == "sensor.pseudo.actor_list"
    ]
    if len(actor_lists) != 1:
        raise ValueError(
            "spawn_sensors_only requires exactly one sensor.pseudo.actor_list."
        )


def validate_all(config_directory: Path) -> None:
    validate_vehicle_config(config_directory / "vehicle_only.json")
    validate_sensor_config(config_directory / "heven_sensors.json")


def main() -> None:
    from ament_index_python.packages import get_package_share_directory

    share = Path(get_package_share_directory("heven_carla_bringup"))
    validate_all(share / "config")
    print("PASS: HEVEN CARLA ROS 2 configuration is valid.")
    print("Expected sensor topics:")
    for name, topic in SENSOR_TOPICS.items():
        print(f"  {name:>10}: {topic}")


if __name__ == "__main__":
    main()
