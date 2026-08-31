from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_spawners_do_not_depend_on_fork_launch_install_path():
    source = (PACKAGE_ROOT / "launch" / "heven_bringup.launch.py").read_text(
        encoding="utf-8"
    )

    assert "IncludeLaunchDescription" not in source
    assert "PythonLaunchDescriptionSource" not in source
    assert source.count('executable="carla_spawn_objects"') == 2
    assert '{"spawn_sensors_only": False}' in source
    assert '{"spawn_sensors_only": True}' in source


def test_humble_launch_api_contract():
    source = (PACKAGE_ROOT / "launch" / "heven_bringup.launch.py").read_text(
        encoding="utf-8"
    )

    assert "LogError," not in source
    assert "LogError(" not in source
    assert "from launch.events import Shutdown" in source
