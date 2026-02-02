# This documents relevant values and types used by rmw
# https://github.com/ros2/rmw/blob/kilted/rmw/include/rmw/types.h
# This is relevant to ensure correctness, and the values are used by tests
# Types and values are introduced in the same order as in the rmw header file.
# All line numbers reference the kilted file versions.
# Refer also to https://design.ros2.org/articles/qos.html


# The rmw_unique_network_flow_endpoints_requirement enum is not relevant here.
import re
from typing import TypeVar
from argparse import ArgumentError, ArgumentTypeError
from dataclasses import dataclass
from enum import Enum
import math
from typing import Union

### This class is taken and modified from the kilted version of rclpy/duration.py
# Unnecessary dependencies have been removed, such that this is usable outside a full 
# ROS installation.
# Also the duration is stored as a simple duration in the class
class Duration:
    """A period between two time points, with nanosecond precision."""

    def __init__(
            self,
            seconds: Union[int, float] = 0,
            nanoseconds: Union[int, float] = 0
            ) -> None:
        """
        Create an instance of :class:`Duration`, combined from given seconds and nanoseconds.

        :param seconds: Time span seconds, if any, fractional part will be included.
        :param nanoseconds: Time span nanoseconds, if any, fractional part will be discarded.
        """
        total_nanoseconds = int(seconds * S_TO_NS)
        total_nanoseconds += int(nanoseconds)
        if total_nanoseconds >= 2**63 or total_nanoseconds < -2**63:
            # pybind11 would raise TypeError, but we want OverflowError
            raise OverflowError(
                'Total nanoseconds value is too large to store in C duration.')
        self.nanoseconds = int(total_nanoseconds)

    # @property
    # def nanoseconds(self) -> int:
    #     return self._duration_handle.nanoseconds

    def __repr__(self) -> str:
        return 'Duration(nanoseconds={0})'.format(self.nanoseconds)

    def __str__(self) -> str:
        if self == DURATION_INFINITE:
            return 'Infinite'
        return f'{self.nanoseconds} nanoseconds'

    def __add__(self, other: 'Duration') -> 'Duration':
        if isinstance(other, Duration):
            return Duration(nanoseconds=other.nanoseconds + self.nanoseconds)
        return NotImplemented

    def __sub__(self, other: 'Duration') -> 'Duration':
        if isinstance(other, Duration):
            return Duration(nanoseconds=self.nanoseconds - other.nanoseconds)
        return NotImplemented

    def __mul__(self, other: Union[int, float]) -> 'Duration':
        if isinstance(other, int):
            return Duration(nanoseconds=self.nanoseconds * other)
        if isinstance(other, float):
            if not math.isfinite(other):
                if other == float('inf'):
                    return DURATION_INFINITE
                else:
                    raise ValueError("Can't multiply duration with nan")
            return Duration(nanoseconds=int(self.nanoseconds * other))
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Duration):
            return self.nanoseconds == other.nanoseconds
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Duration):
            return not self.__eq__(other)
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Duration):
            return self.nanoseconds < other.nanoseconds
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if isinstance(other, Duration):
            return self.nanoseconds <= other.nanoseconds
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, Duration):
            return self.nanoseconds > other.nanoseconds
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if isinstance(other, Duration):
            return self.nanoseconds >= other.nanoseconds
        return NotImplemented


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


# Duration = tuple[int, int]

S_TO_NS = 1_000_000_000

# Time in rmw is encoded as a second part + nanosecond part (rmw/time.h)
# rmw/time.h:54
# Deadline default (rmw/types.h:517)
DURATION_INFINITE: Duration = Duration(9223372036, 854775807) 
# Lease duration default (rmw/types.h:542)
# Lifespan default (rwm/type.h:537)
DURATION_UNSPECIFIED: Duration = Duration(0, 0) # rmw/time.h:55
DEADLINE_DEFAULT = DURATION_UNSPECIFIED
LIVELINESS_LEASE_DURATION_DEFAULT = DURATION_UNSPECIFIED
LIFESPAN_DEFAULT = DURATION_UNSPECIFIED
# for both deadline (rmw/types.h:539) and for lease duration (rmw/types.h:567)
DURATION_BEST_AVAILABLE: Duration = Duration(9223372036, 854775806)  # rmw/types.h:520
DEADLINE_BEST_AVAILABLE = DURATION_BEST_AVAILABLE
LIVELINESS_LEASE_DURATION_BEST_AVAILABLE = DURATION_BEST_AVAILABLE

# rmw/types.h:728
DEPTH_SYSTEM_DEFAULT = 0


def parse_bool(arg: bool | str) -> bool:
    if isinstance(arg, bool):
        return arg
    elif arg in ["True", "true"]:
        return True
    elif arg in ["False", "false"]:
        return False
    else:
        raise ValueError(f"{arg} is not convertible to bool")


def parse_duration(arg: Duration | str) -> Duration:
    if isinstance(arg, Duration):
        return arg
    elif isinstance(arg, str):
        p = re.compile(r'^\( *(-?\d+) *, *(-?\d+) *\)\Z')
        m = p.match(arg)
        return Duration(int(m.group(1)),int(m.group(2)))
    else:
        raise TypeError(f"{arg} is neither a string nor a Duration")


def parse_int(arg: int | str) -> int:
    if isinstance(arg, int):
        return arg
    elif isinstance(arg, str):
        return int(arg)
    else:
        raise TypeError(f"{arg} is not convertible to int")


E = TypeVar('E', bound=Enum)
def parse_enum(enumtype: type[E], arg: E | str | int) -> E:
    if not isinstance(arg, str) and isinstance(arg, enumtype):
        return arg
    elif isinstance(arg, (str, int)):
        return enumtype(arg)
    elif isinstance(arg, int):
        return enumtype(arg)
    else:
        raise TypeError("")

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
        liveliness_lease_duration: Duration | str = LIVELINESS_LEASE_DURATION_DEFAULT,
        avoid_ros_namespace_conventions: bool | str = False
    ):
        self.history = history
        self.depth = depth
        self.reliability = reliability
        self.durability = durability
        self.deadline = deadline
        self.lifespan = lifespan
        self.liveliness = liveliness
        self.liveliness_lease_duration = liveliness_lease_duration
        self.avoid_ros_namespace_conventions = avoid_ros_namespace_conventions


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
