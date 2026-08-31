# HEVEN 센서 Config 수정 가이드

## 1. 파일별 역할

| 파일 | 수정 대상 |
|---|---|
| `config/heven_sensors.json` | 센서 타입, ID, 수량, 장착 위치, 해상도, FOV, 주기, 노이즈 |
| `config/vehicle_only.json` | 차량 타입·ID와 최초 스폰 위치 |
| `config/bridge.yaml` | CARLA 주소, 맵, synchronous mode, world 시간 간격 |
| `config/heven_sensors.rviz` | RViz 표시 토픽과 시각화 옵션 |
| `heven_carla_bringup/topic_contract.py` | 코드가 기대하는 고정 ROS 토픽 |
| `heven_carla_bringup/sensor_gate.py` | readiness 판정에 포함되는 센서와 메시지 타입 |
| `heven_carla_bringup/readiness_monitor.py` | 센서별 수신 주파수 모니터링 |
| `heven_carla_bringup/config_validator.py` | 허용 센서 ID·타입·주기 검증 |

기존 센서의 파라미터만 바꿀 때는 대부분 `heven_sensors.json`만 수정한다. 센서 ID,
타입, 수량 또는 주기 구조를 바꿀 때는 코드 계약 파일까지 함께 수정한다.

## 2. 좌표와 단위

`carla_spawn_objects` JSON은 차량 Actor 원점 기준 ROS 오른손 좌표를 사용한다.

| 값 | 의미 | 단위 |
|---|---|---|
| `x` | 차량 전방 | m |
| `y` | 차량 좌측 | m |
| `z` | 위쪽 | m |
| `roll` | x축 회전 | degree |
| `pitch` | y축 회전 | degree |
| `yaw` | z축 회전 | degree |

현재 Bridge 변환 관계는 다음과 같다.

```text
x_ros     =  x_carla
y_ros     = -y_carla
z_ros     =  z_carla
roll_ros  =  roll_carla
pitch_ros = -pitch_carla
yaw_ros   = -yaw_carla
```

따라서 현재 JSON에서 `y>0`은 좌측, `yaw>0`은 좌측을 향하도록 사용한다. 카메라를
아래로 숙이는 CARLA pitch가 음수라면 JSON pitch는 양수가 된다. 부호는 수치만으로
확정하지 말고 첫 실행 영상과 TF를 함께 확인한다.

## 3. 카메라 수정

예시:

```json
{
  "type": "sensor.camera.rgb",
  "id": "left_cam",
  "spawn_point": {
    "x": 0.80,
    "y": 0.23,
    "z": 0.52,
    "roll": 0.0,
    "pitch": 12.0,
    "yaw": 25.0
  },
  "image_size_x": 1280,
  "image_size_y": 720,
  "fov": 70.42,
  "sensor_tick": 0.0,
  "gamma": 2.2,
  "enable_postprocess_effects": true
}
```

| 키 | 수정 기준 |
|---|---|
| `spawn_point` | 차량 모델에서 측정한 카메라 optical center와 장착 각도 |
| `image_size_x/y` | 실제 인지 노드 입력 또는 실제 카메라 운용 해상도 |
| `fov` | CARLA의 수평 FOV. 실제 사양이 대각 FOV라면 수평 FOV로 변환 |
| `sensor_tick` | `0.0`이면 현재 world tick마다 발행 |
| `gamma` | 영상 밝기 응답 검증 후 설정 |
| `enable_postprocess_effects` | 재현성 우선이면 `false`, 시각적 효과가 필요하면 `true` |

초점거리 `fx`와 영상 폭 `W`를 알면 수평 FOV는 다음과 같다.

```text
HFOV = 2 * atan(W / (2 * fx))
```

카메라 `id`를 바꾸면 `/carla/ego_vehicle/<id>/image`와
`/carla/ego_vehicle/<id>/camera_info`도 같이 바뀐다.

## 4. LiDAR 수정

현재 설정은 OS1-64, 1024 columns, 20 Hz를 근사한다.

```json
"channels": 64,
"range": 120.0,
"points_per_second": 1310720,
"rotation_frequency": 20.0,
"upper_fov": 22.5,
"lower_fov": -22.5,
"horizontal_fov": 360.0,
"sensor_tick": 0.0
```

`points_per_second`의 초기 계산은 다음 관계를 사용한다.

```text
points_per_second = channels * columns_per_rotation * rotation_frequency
64 * 1024 * 20 = 1,310,720 points/s
```

실제 장비가 OS1-32/64/128 중 무엇인지와 512/1024/2048 mode, 10/20 Hz 중 어떤
운용 모드를 쓰는지 확정한 뒤 세 값을 함께 변경한다. `rotation_frequency`만 바꾸고
`points_per_second`를 그대로 두면 회전당 수평 포인트 수가 달라진다.

CARLA의 채널은 수직 FOV 안에 균일 분포되므로 실제 Ouster beam calibration과
동일하다고 간주하지 않는다.

## 5. IMU 수정

장착 위치와 자세는 실제 IMU 측정 원점 및 축 방향을 기준으로 한다. 현재는 차체
중심 하단의 초기값이며 모든 noise와 bias가 0이다.

주요 키:

```text
sensor_tick
noise_seed
noise_accel_stddev_x/y/z
noise_gyro_stddev_x/y/z
noise_gyro_bias_x/y/z
```

실제 센서 datasheet의 noise density를 그대로 표준편차 필드에 넣으면 안 된다.
sampling rate와 bandwidth에 따른 단위 변환이 필요하다. CARLA 기본 IMU에는 bias
random walk, scale factor, 온도 및 진동 모델이 충분히 포함되지 않는다.

## 6. GNSS 수정

GNSS `spawn_point`는 실제 안테나 phase center를 기준으로 입력한다. 현재 설정은
LiDAR 상부 안테나 위치의 초기 근사다.

주요 키:

```text
sensor_tick
noise_seed
noise_alt_bias / noise_alt_stddev
noise_lat_bias / noise_lat_stddev
noise_lon_bias / noise_lon_stddev
```

NTRIP과 RTK FIX/FLOAT 상태는 이 패키지에서 구현하지 않는다. CARLA GNSS 출력은
실제 수신기, 보정 데이터 지연 및 위성 가시성 모델의 대체물이 아니다.

## 7. 센서 주기 변경

현재 `bridge.yaml`은 다음과 같다.

```yaml
synchronous_mode: true
fixed_delta_seconds: 0.05
```

따라서 world는 20 Hz이다.

| `sensor_tick` | 실제 의미 | 현재 readiness에 미치는 영향 |
|---:|---:|---|
| `0.0` | world tick마다 발행, 20 Hz | 현재 baseline과 일치 |
| `0.05` | 20 Hz 요청 | 주기는 같지만 현재 validator는 baseline 값 `0.0`만 허용 |
| `0.10` | 10 Hz 요청 | 20 Hz 센서와 timestamp가 겹치는 시점에만 완전 세트 생성 |
| `0.01` | 100 Hz 요청 | world가 20 Hz이므로 실제로 100 Hz를 만들 수 없음 |

현재 validator는 초기 검증 조건을 고정하기 위해 모든 실제 센서의
`sensor_tick=0.0`을 요구한다. 동일 20 Hz라도 `0.05`로 명시하려면
`config_validator.py`의 규칙과 관련 테스트를 함께 수정해야 한다.

IMU 100 Hz, 카메라 20 Hz, LiDAR 10 Hz로 바꾸려면 먼저
`fixed_delta_seconds=0.01`로 world를 100 Hz로 변경하고 각 센서 tick을 각각
`0.01`, `0.05`, `0.10`으로 설정한다. 이때 현재 `sensor_gate`의 여섯 센서
same-stamp 판정은 공통 timestamp가 존재할 때만 완전 세트를 만든다. 정수 배 관계로
정렬된 센서는 느린 센서 시점에 완전 세트가 생길 수 있지만, 이것이 모든 메시지를
동기화해 준다는 뜻은 아니다. 주기와 위상이 어긋나면 readiness가 True가 되지 않을
수도 있다. 멀티레이트 소비자는 센서별 timestamp buffer와 기준 센서 중심의 근접
timestamp 결합으로 재설계해야 한다.

## 8. 센서 추가·삭제·이름 변경

JSON만 수정하면 Bridge 토픽은 생성될 수 있지만 HEVEN readiness 계약은 자동으로
바뀌지 않는다. 다음 파일을 모두 점검한다.

1. `config/heven_sensors.json`
2. `heven_carla_bringup/topic_contract.py`
3. `heven_carla_bringup/sensor_gate.py`
4. `heven_carla_bringup/readiness_monitor.py`
5. `heven_carla_bringup/config_validator.py`
6. `config/heven_sensors.rviz`
7. `test/test_topic_contract.py`, `test/test_config_files.py`

`sensor.pseudo.actor_list`는 `spawn_sensors_only=True`가 기존 차량을 찾는 데 필요하므로
삭제하지 않는다. `sensor.pseudo.tf`와 `sensor.pseudo.odom`도 RViz TF와 odometry를
사용한다면 유지한다.

## 9. 수정 후 적용 및 검증

실행 중인 bring-up을 먼저 종료한 뒤 다음 순서로 검증한다.

```bash
cd ~/2026_heven_ad_ws
source /opt/ros/humble/setup.bash

python3 -m json.tool \
  src/heven_carla_bringup/config/heven_sensors.json >/dev/null

colcon build \
  --symlink-install \
  --packages-select heven_carla_bringup

source install/setup.bash
ros2 run heven_carla_bringup heven_validate_config
```

CARLA Editor에서 K-City를 Play한 다음 실행한다.

```bash
ros2 launch heven_carla_bringup heven_bringup.launch.py
```

토픽과 readiness를 확인한다.

```bash
ros2 topic list | sort
ros2 topic echo /heven/sensors_ready --once

ros2 topic hz /carla/ego_vehicle/left_cam/image
ros2 topic hz /carla/ego_vehicle/right_cam/image
ros2 topic hz /carla/ego_vehicle/front_cam/image
ros2 topic hz /carla/ego_vehicle/lidar
ros2 topic hz /carla/ego_vehicle/imu
ros2 topic hz /carla/ego_vehicle/gnss
```

마지막으로 RViz와 실제 카메라 영상에서 장착 방향, 차체 가림, LiDAR 원점의 차체
간섭, TF frame, 메시지 timestamp 및 주파수를 함께 확인한다.

## 10. 공식 참고 문서

- CARLA 0.9.15 sensor attributes:
  <https://carla.readthedocs.io/en/0.9.15/ref_sensors/>
- CARLA ROS Bridge spawn objects 및 sensors-only 방식:
  <https://carla.readthedocs.io/projects/ros-bridge/en/latest/carla_spawn_objects/>
