from types import NotImplementedType
from roserer.types import Duration
import pytest

def test_duration_overflow() -> None:
    with pytest.raises(OverflowError):
        Duration(9_223_372_036_854_775_809)
    with pytest.raises(OverflowError):
        Duration(-9_223_372_036_854_775_809)

def test_duration_str() -> None:
    assert str(Duration(1,2)) == "1000000002 nanoseconds"
    assert str(Duration(9223372036, 854775807)) == "Infinite"

def test_duration_add() -> None:
    assert Duration(1,2) + Duration(2,1) == Duration(3,3)

def test_duration_subtract() -> None:
    assert Duration(1,2) - Duration(2,1) == Duration(-1,1)

def test_duration_multiplication() -> None:
    assert Duration(0,2) * 3 == Duration(0,6)
    assert Duration(10,0) * 0.1 == Duration(1,0)

def test_duration_eq() -> None:
    assert Duration(0,0) != Duration(0,1)
    assert Duration(0,0) <= Duration(0,1)
    assert Duration(0,2) >= Duration(0,1)
    assert Duration(4,2) > Duration(0,10000)
