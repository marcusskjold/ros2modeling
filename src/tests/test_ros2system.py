from roserer.ros2system import *


def test_qualityofservice_defaultinit_matches_rosdefaults() -> None:
    qos = QualityOfService()
    assert qos.history == "keep_last"
    assert qos.depth == 10
    assert qos.reliability == "reliable"
    assert qos.durability == "volatile"
    assert qos.deadline == 0
    assert qos.lifespan == 0
    assert qos.liveliness == "system_default"
    assert qos.liveliness_lease_duration == 0
