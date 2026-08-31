from heven_carla_bringup.topic_contract import SENSOR_TOPICS


def test_requested_topic_contract():
    assert SENSOR_TOPICS["left_cam"] == "/carla/ego_vehicle/left_cam/image"
    assert SENSOR_TOPICS["right_cam"] == "/carla/ego_vehicle/right_cam/image"
    assert SENSOR_TOPICS["front_cam"] == "/carla/ego_vehicle/front_cam/image"
    assert SENSOR_TOPICS["lidar"] == "/carla/ego_vehicle/lidar"

