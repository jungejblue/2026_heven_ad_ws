import json
from pathlib import Path

from heven_carla_bringup.config_validator import validate_all


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_configs_are_valid():
    validate_all(PACKAGE_ROOT / "config")


def test_requested_topic_ids_are_present():
    with (PACKAGE_ROOT / "config" / "heven_sensors.json").open(
        "r", encoding="utf-8"
    ) as stream:
        document = json.load(stream)

    vehicle = next(
        item for item in document["objects"] if item.get("id") == "ego_vehicle"
    )
    sensor_ids = {sensor["id"] for sensor in vehicle["sensors"]}
    assert {"left_cam", "right_cam", "front_cam", "lidar"}.issubset(sensor_ids)

