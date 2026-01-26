from roserer.ros2system import QualityOfService


# This is a test of the defined default values.
# https://github.com/ros2/rmw/blob/79ee1d7915098815df2c1abc8c0062c1ffe7dc9a/rmw/include/rmw/qos_profiles.h
# https://github.com/ros2/rmw/blob/rolling/rmw/include/rmw/types.h#L540 
# Avoid ros namespace collisions is described in rmw/types.h around line 600
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

# https://github.com/ros2/rmw/blob/rolling/rmw/include/rmw/types.h
# https://github.com/ros2/rmw/blob/kilted/rmw/include/rmw/types.h
# We see that For integer values, there are enums for each of the fields
#     [history, durability, reliability, liveliness]
# The fields that define durations have a default duration = 0
# It is called RMW_DURATION_UNSPECIFIED
# https://github.com/ros2/rmw/blob/5cc9dda460cb5002fc69797a9f4e5fb070d9d011/rmw/include/rmw/time.h#L55
# 
# Deadline RMW_QOS_DEADLINE_BEST_AVAILABLE
# https://github.com/ros2/rmw/blob/rolling/rmw/include/rmw/types.h#L534C9-L534C40 n
