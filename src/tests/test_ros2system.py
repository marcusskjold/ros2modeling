import ros2model.ros2system as ros
import pytest


def func(x):
    return x + 1


def test_answer():
    assert func(3) == 5
