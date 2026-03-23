# This documents relevant values and types used by rmw
# https://github.com/ros2/rmw/blob/kilted/rmw/include/rmw/types.h
# This is relevant to ensure correctness, and the values are used by tests
# Types and values are introduced in the same order as in the rmw header file.
# All line numbers reference the kilted file versions.
# Refer also to https://design.ros2.org/articles/qos.html


# The rmw_unique_network_flow_endpoints_requirement enum is not relevant here.
from dataclasses import dataclass
import re
from typing import TypeVar, Callable, Iterable
from enum import Enum, auto
import math
from typing import Union
T = TypeVar('T')
E = TypeVar('E', bound=Enum)

@dataclass
class Feedback():
    errors: list[str]
    warnings: list[str]

    def __init__(
            self,
            errors: list[str] | None = None,
            warnings: list[str] | None = None
            ) -> None:
        if errors is None:
            errors = []
        if warnings is None:
            warnings = []
        self.errors = errors
        self.warnings = warnings

    def __add__(self, other: 'Feedback') -> 'Feedback':
        return Feedback(self.errors + other.errors, self.warnings + other.warnings)

    def __iadd__(self, other: 'Feedback') -> 'Feedback':
        self.errors += other.errors
        self.warnings += other.warnings
        return self

    def contains(self, string) -> bool:
        return any(string in f for f in self.errors + self.warnings)

def run_validation(
        objects: Iterable[T],
        func: Callable[[T], Feedback],
        ) -> Feedback:
    f = Feedback()
    for o in objects:
        f += func(o)
    return f

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
        Create an instance of :class:`Duration`, combined from given seconds and
        nanosecondsk
        :param seconds: Time span seconds, if any, fractional part will be included.
        :param nanoseconds: Time span nanoseconds, if any, fractional part will be
                            discarded.
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

# Duration = tuple[int, int]

S_TO_NS = 1_000_000_000

# Time in rmw is encoded as a second part + nanosecond part (rmw/time.h)
# rmw/time.h:54
# Deadline default (rmw/types.h:517)
DURATION_INFINITE: Duration = Duration(9223372036, 854775807)
# Lease duration default (rmw/types.h:542)
# Lifespan default (rwm/type.h:537)
DURATION_UNSPECIFIED: Duration = Duration(0, 0) # rmw/time.h:55
# for both deadline (rmw/types.h:539) and for lease duration (rmw/types.h:567)
DURATION_BEST_AVAILABLE: Duration = Duration(9223372036, 854775806)  # rmw/types.h:520

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
        if m is None:
            raise ValueError(
                    "Invalid format of argument string. Expected '(int, int)', "
                    f"got '{arg}'")
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

def parse_enum(enumtype: type[E], arg: E | str | int) -> E:
    if not isinstance(arg, str) and isinstance(arg, enumtype):
        return arg
    elif isinstance(arg, str):
        return enumtype[arg.upper()]
    elif isinstance(arg, int):
        return enumtype(arg)
    else:
        raise TypeError("")

# ====================== System, host, executor enums =================================

class TimeUnit(Enum):
    NANOSECONDS = 0
    MICROSECONDS = 1
    MILLISECONDS = 2
    SECONDS = 3
    MINUTES = 4
    UNSPECIFIED = 5

class DDS_IMPLEMENTATION(Enum):
    Generic = auto()
    Cyclone = auto()
    Fast = auto()
    Connext = auto()
    Gurum = auto()

class EXECUTOR(Enum):
    SingleThreadedExecutor = auto()
    MultiThreadedExecutor = auto()
    StaticSingleThreadedExecutor = auto()
    EventsExecutor = auto()

class OPERATING_SYSTEM(Enum):
    Generic = auto()
    Windows = auto()
    Debian = auto()
    MacOS = auto()
    Ubuntu = auto()
    OpenEmbedded = auto()
    RTLinuxKernel = auto()

class ARCHITECTURE(Enum):
    Generic = auto()
    amd64 = auto()
    arm64 = auto()
    arm32 = auto()

class DISTRIBUTION(Enum):
    Rolling = auto()
    Kilted = auto()
    Jazzy = auto()
    Iron = auto()
    Humble = auto()
    Galactic = auto()
    Foxy = auto()
    Eloquent = auto()
    Dashing = auto()
    Crystal = auto()
    Bouncy = auto()
    Ardent = auto()

class NodeType(Enum):
    SYSTEM = auto()
    HOST = auto()
    EXECUTOR = auto()
    NODE = auto()
    CALLBACK = auto()
    EXTERNAL_INPUT = auto()
    EXTERNAL_OUTPUT = auto()
    TIMER = auto()
    SERVICE = auto()
    CLIENT = auto()
    VARIABLE = auto()
    PUBLISHER = auto()
    SUBSCRIBER = auto()
    ACTION = auto()
    TOPIC = auto()
