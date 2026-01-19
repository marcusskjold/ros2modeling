from roserer.systemvalidator import is_valid_value


def test_is_valid_value_dds_positive() -> None:
    """
    The list of valid dds implementations are taken from
    https://docs.ros.org/en/rolling/Installation/RMW-Implementations/DDS-Implementations.html
    Accessed 2026-01-19
    """
    assert is_valid_value("dds", "Generic") == []
    assert is_valid_value("dds", "Cyclone") == []
    assert is_valid_value("dds", "Fast") == []
    assert is_valid_value("dds", "RTI Connext") == []
    assert is_valid_value("dds", "Gurum") == []


def test_is_valid_value_dds_negative() -> None:
    assert is_valid_value("dds", "") != []
    assert is_valid_value("dds", "Cyclon") != []


def test_is_valid_value_executor_positive() -> None:
    """
    The most common executors are SingleThreadedExecutor and MultiThreadedExecutor:
    https://docs.ros.org/en/rolling/Concepts/Intermediate/About-Executors.html
    Accessed 2026-01-19

    The EventsExecutor was first introduced with Iron Irwini:
    https://docs.ros.org/en/rolling/Releases/Release-Iron-Irwini.html#introduction-of-a-new-executor-type-the-events-executor
    Accessed 2026-01-19
    """
    assert is_valid_value("executor", "SingleThreadedExecutor") == []
    assert is_valid_value("executor", "MultiThreadedExecutor") == []
    assert is_valid_value("executor", "EventsExecutor") == []
