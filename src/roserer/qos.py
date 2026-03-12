from enum import Enum
from roserer.types import (
        Duration, DURATION_UNSPECIFIED, DURATION_BEST_AVAILABLE,
        parse_enum, parse_int, parse_duration, parse_bool, 
        )
from dataclasses import dataclass

DEADLINE_DEFAULT = DURATION_UNSPECIFIED
LIVELINESS_LEASE_DURATION_DEFAULT = DURATION_UNSPECIFIED
LIFESPAN_DEFAULT = DURATION_UNSPECIFIED
DEADLINE_BEST_AVAILABLE = DURATION_BEST_AVAILABLE
LIVELINESS_LEASE_DURATION_BEST_AVAILABLE = DURATION_BEST_AVAILABLE
# rmw/types.h:728
DEPTH_SYSTEM_DEFAULT = 0

# rmw/types.h:370 | rclpy/qos.py:334
class QOSReliabilityPolicy(Enum):
    SYSTEM_DEFAULT = 0
    RELIABLE = 1
    BEST_EFFORT = 2
    UNKNOWN = 3
    BEST_AVAILABLE = 4

# rmw/types.h:404 | rclpy/qos.py:317
class QOSHistoryPolicy(Enum):
    SYSTEM_DEFAULT = 0
    KEEP_LAST = 1
    KEEP_ALL = 2
    UNKNOWN = 3

# rmw/types.h:421 | rclpy/qos.py:352
class QOSDurabilityPolicy(Enum):
    SYSTEM_DEFAULT = 0
    TRANSIENT_LOCAL = 1
    VOLATILE = 2
    UNKNOWN = 3
    BEST_AVAILABLE = 4

# rmw/types.h:472 | rclpy/qos.py:370
class QOSLivelinessPolicy(Enum):
    SYSTEM_DEFAULT = 0
    AUTOMATIC = 1
    MANUAL_BY_TOPIC = 3
    UNKNOWN = 4
    BEST_AVAILABLE = 5

# rmw/types.h:569 | rclpy/qos.py:56
@dataclass
class QualityOfService():
    history: QOSHistoryPolicy
    depth: int
    reliability: QOSReliabilityPolicy
    durability: QOSDurabilityPolicy
    deadline: Duration
    lifespan: Duration
    liveliness: QOSLivelinessPolicy
    liveliness_lease_duration: Duration
    avoid_ros_namespace_conventions: bool

    def __init__(
        self,
        history: QOSHistoryPolicy | str = QOSHistoryPolicy.KEEP_LAST,
        depth: int | str = 10,
        reliability: QOSReliabilityPolicy | str = QOSReliabilityPolicy.RELIABLE,
        durability: QOSDurabilityPolicy | str = QOSDurabilityPolicy.VOLATILE,
        deadline: Duration | str = DEADLINE_DEFAULT,
        lifespan: Duration | str = LIFESPAN_DEFAULT,
        liveliness: QOSLivelinessPolicy | str = QOSLivelinessPolicy.SYSTEM_DEFAULT,
        liveliness_lease_duration: Duration | str = DURATION_UNSPECIFIED,
        avoid_ros_namespace_conventions: bool | str = False
    ):
        self.history = parse_enum(QOSHistoryPolicy, history)
        self.depth = parse_int(depth)
        self.reliability = parse_enum(QOSReliabilityPolicy, reliability)
        self.durability = parse_enum(QOSDurabilityPolicy, durability)
        self.deadline = parse_duration(deadline)
        self.lifespan = parse_duration(lifespan)
        self.liveliness = parse_enum(QOSLivelinessPolicy, liveliness)
        self.liveliness_lease_duration = parse_duration(liveliness_lease_duration)
        self.avoid_ros_namespace_conventions = parse_bool(avoid_ros_namespace_conventions)

QoS = QualityOfService

# This section is referenced from
# https://github.com/ros2/rmw/blob/kilted/rmw/include/rmw/qos_profiles.h
def qos_profile_sensor_data() -> QualityOfService:
    return QualityOfService(
        history=QOSHistoryPolicy.KEEP_LAST,
        depth = 5,
        reliability=QOSReliabilityPolicy.BEST_EFFORT,
        durability = QOSDurabilityPolicy.VOLATILE,
        deadline=DEADLINE_DEFAULT,
        lifespan=LIFESPAN_DEFAULT,
        liveliness=QOSLivelinessPolicy.SYSTEM_DEFAULT,
        liveliness_lease_duration=LIVELINESS_LEASE_DURATION_DEFAULT,
        avoid_ros_namespace_conventions=False
    )

def qos_profile_parameters() -> QualityOfService:
    return QualityOfService(
        history=QOSHistoryPolicy.KEEP_LAST,
        depth=1000,
        reliability=QOSReliabilityPolicy.RELIABLE,
        durability=QOSDurabilityPolicy.VOLATILE,
        deadline=DEADLINE_DEFAULT,
        lifespan=LIFESPAN_DEFAULT,
        liveliness=QOSLivelinessPolicy.SYSTEM_DEFAULT,
        liveliness_lease_duration=LIVELINESS_LEASE_DURATION_DEFAULT,
        avoid_ros_namespace_conventions=False
    )

def qos_profile_default() -> QualityOfService:
    return QualityOfService(
        history=QOSHistoryPolicy.KEEP_LAST,
        depth=10,
        reliability=QOSReliabilityPolicy.RELIABLE,
        durability=QOSDurabilityPolicy.VOLATILE,
        deadline=DEADLINE_DEFAULT,
        lifespan=LIFESPAN_DEFAULT,
        liveliness=QOSLivelinessPolicy.SYSTEM_DEFAULT,
        liveliness_lease_duration=LIVELINESS_LEASE_DURATION_DEFAULT,
        avoid_ros_namespace_conventions=False
    )

def qos_profile_services_default() -> QualityOfService:
    return QualityOfService(
        history=QOSHistoryPolicy.KEEP_LAST,
        depth=10,
        reliability=QOSReliabilityPolicy.RELIABLE,
        durability=QOSDurabilityPolicy.VOLATILE,
        deadline=DEADLINE_DEFAULT,
        lifespan=LIFESPAN_DEFAULT,
        liveliness=QOSLivelinessPolicy.SYSTEM_DEFAULT,
        liveliness_lease_duration=LIVELINESS_LEASE_DURATION_DEFAULT,
        avoid_ros_namespace_conventions=False
    )

def qos_profile_parameter_events() -> QualityOfService:
    return QualityOfService(
        history=QOSHistoryPolicy.KEEP_LAST,
        depth=1000,
        reliability=QOSReliabilityPolicy.RELIABLE,
        durability=QOSDurabilityPolicy.VOLATILE,
        deadline=DEADLINE_DEFAULT,
        lifespan=LIFESPAN_DEFAULT,
        liveliness=QOSLivelinessPolicy.SYSTEM_DEFAULT,
        liveliness_lease_duration=LIVELINESS_LEASE_DURATION_DEFAULT,
        avoid_ros_namespace_conventions=False
    )

def qos_profile_rosout_default() -> QualityOfService:
    return QualityOfService(
        history=QOSHistoryPolicy.KEEP_LAST,
        depth=1000,
        reliability=QOSReliabilityPolicy.RELIABLE,
        durability=QOSDurabilityPolicy.TRANSIENT_LOCAL,
        deadline=DEADLINE_DEFAULT,
        lifespan=Duration(10,0),
        liveliness=QOSLivelinessPolicy.SYSTEM_DEFAULT,
        liveliness_lease_duration=LIVELINESS_LEASE_DURATION_DEFAULT,
        avoid_ros_namespace_conventions=False
    )

def qos_profile_system_default() -> QualityOfService:
    return QualityOfService(
        history=QOSHistoryPolicy.SYSTEM_DEFAULT,
        depth=DEPTH_SYSTEM_DEFAULT,
        reliability=QOSReliabilityPolicy.SYSTEM_DEFAULT,
        durability=QOSDurabilityPolicy.SYSTEM_DEFAULT,
        deadline=DEADLINE_DEFAULT,
        lifespan=LIFESPAN_DEFAULT,
        liveliness=QOSLivelinessPolicy.SYSTEM_DEFAULT,
        liveliness_lease_duration=LIVELINESS_LEASE_DURATION_DEFAULT,
        avoid_ros_namespace_conventions=False
    )

def qos_profile_best_available() -> QualityOfService:
    return QualityOfService(
        history=QOSHistoryPolicy.KEEP_LAST,
        depth=10,
        reliability=QOSReliabilityPolicy.BEST_AVAILABLE,
        durability=QOSDurabilityPolicy.BEST_AVAILABLE,
        deadline=DEADLINE_BEST_AVAILABLE,
        lifespan=LIFESPAN_DEFAULT,
        liveliness=QOSLivelinessPolicy.BEST_AVAILABLE,
        liveliness_lease_duration=LIVELINESS_LEASE_DURATION_BEST_AVAILABLE,
        avoid_ros_namespace_conventions=False
    )

def qos_profile_unknown() -> QualityOfService:
    return QualityOfService(
        history=QOSHistoryPolicy.UNKNOWN,
        depth=DEPTH_SYSTEM_DEFAULT,
        reliability=QOSReliabilityPolicy.UNKNOWN,
        durability=QOSDurabilityPolicy.UNKNOWN,
        deadline=DEADLINE_DEFAULT,
        lifespan=LIFESPAN_DEFAULT,
        liveliness=QOSLivelinessPolicy.UNKNOWN,
        liveliness_lease_duration=LIVELINESS_LEASE_DURATION_DEFAULT,
        avoid_ros_namespace_conventions=False
    )

class QoSPresetProfiles(Enum):
    UNKNOWN = qos_profile_unknown
    DEFAULT = qos_profile_default
    SYSTEM_DEFAULT = qos_profile_system_default
    SENSOR_DATA = qos_profile_sensor_data
    SERVICES_DEFAULT = qos_profile_services_default
    PARAMETERS = qos_profile_parameters
    PARAMETER_EVENTS = qos_profile_parameter_events
    # This is a preset profile present in rclpy, but not present in rmw.
    # ACTION_STATUS_DEFAULT = qos_profile_action_status_default
    BEST_AVAILABLE = qos_profile_best_available
    ROSOUT_DEFAULT = qos_profile_rosout_default
