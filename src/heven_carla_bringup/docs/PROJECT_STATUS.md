# HEVEN CARLA ROS 2 구현 현황

기준일: 2026-08-31

## 완료 상태

- Ubuntu 22.04, ROS 2 Humble, CARLA 0.9.15 기반 환경을 사용한다.
- CARLA 서버는 사용자 빌드이므로 버전 문자열이 `0.9.15-dirty`이며, ROS Bridge의
  0.9.15 Python API와 실제 연결 및 동기 실행이 확인됐다.
- workspace는 `2026_heven_ad_ws`이다.
- ROS Bridge는 `ttgamage/carla-ros-bridge` 포크를 사용한다.
- K-City 맵은 `heven_kcity/Maps/kcity/kcity`이다.
- 차량 Blueprint는 `vehicle.heven.ev`, ROS/CARLA role 및 id는
  `ego_vehicle`이다.
- ROS Bridge가 유일한 synchronous tick 관리자이며 20 Hz로 실행한다.
- 차량을 먼저 스폰하고 브레이크를 유지한 상태에서 시뮬레이션 시간 2초를 기다린
  다음 센서를 부착한다.
- 센서 부착 뒤 여섯 센서의 동일 timestamp 완전 세트 5개를 논리적으로 폐기한 뒤
  `/heven/sensors_ready=True`를 발행한다.
- RViz 사용 여부는 `launch_rviz` launch argument로 분리돼 있다.
- 차량 스폰, 2초 안정화, 센서 스폰, ROS 토픽 발행의 전체 bring-up 정상 동작을
  사용자 환경에서 확인했다.

## 현재 센서 계약

| 용도 | ID | CARLA 타입 | ROS 토픽 |
|---|---|---|---|
| 좌측 차선 카메라 | `left_cam` | `sensor.camera.rgb` | `/carla/ego_vehicle/left_cam/image` |
| 우측 차선 카메라 | `right_cam` | `sensor.camera.rgb` | `/carla/ego_vehicle/right_cam/image` |
| 전방 객체 카메라 | `front_cam` | `sensor.camera.rgb` | `/carla/ego_vehicle/front_cam/image` |
| LiDAR | `lidar` | `sensor.lidar.ray_cast` | `/carla/ego_vehicle/lidar` |
| IMU | `imu` | `sensor.other.imu` | `/carla/ego_vehicle/imu` |
| GNSS | `gnss` | `sensor.other.gnss` | `/carla/ego_vehicle/gnss` |

NTRIP은 구현하지 않는다. 카메라는 Logitech HD Pro Webcam의 초기 근사, LiDAR는
OS1-64 1024×20 mode의 초기 근사이며 실제 보유 센서 사양 확정 후 보정한다.

## 해결한 주요 문제

1. 차량 스폰 직후 센서 기록을 시작하던 문제를 차량 우선 스폰 및 시뮬레이션 시간
   2초 안정화 방식으로 변경했다.
2. 센서 원본 토픽과 readiness를 분리해 초기 5개 동기 세트를 인지·기록 노드가
   사용하지 않도록 했다.
3. ROS 2 Humble에 없는 `launch.actions.LogError` 사용을 제거하고 `Shutdown`
   event를 Humble API에 맞게 수정했다.
4. `ttgamage` 포크가 launch 파일을 비표준 위치에 설치하는 문제를 피하기 위해
   `carla_spawn_objects` 실행 파일을 직접 Node action으로 실행한다.
5. launch 급종료 시 HEVEN 보조 노드가 이미 종료된 rclpy context를 다시 정리하며
   traceback을 출력하던 경로를 보완했다.

## 남아 있는 모델링 한계

- `0.9.15-dirty`는 사용자 빌드 표시이므로 실험 재현 시 CARLA commit과 변경 상태를
  별도로 기록해야 한다.
- CARLA ray-cast LiDAR는 실제 Ouster의 비균일 수직 beam angle, multi-return 및
  실제 회전 스캔 motion distortion을 완전히 재현하지 않는다.
- 현재 readiness의 검증 기준은 모든 센서가 동일한 20 Hz인 baseline이다. 멀티레이트
  구성에서는 readiness의 의미와 소비자 동기화 로직을 다시 정의해야 한다.
- 카메라·LiDAR·IMU·GNSS의 실제 장착 위치와 실제 장비 사양 확정 후 config를 다시
  보정해야 한다.
