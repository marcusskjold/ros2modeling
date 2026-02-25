import pytest
import roserer.qos as qos
from roserer.qos import Duration, QOSDurabilityPolicy, QOSHistoryPolicy, QOSLivelinessPolicy, QOSReliabilityPolicy


# Function, expected output, input
parse_funcs_valid = [
        (qos.parse_bool,     True,                     True),
        (qos.parse_bool,     True,                     "true"),
        (qos.parse_bool,     True,                     "True"),
        (qos.parse_bool,     False,                    False), 
        (qos.parse_bool,     False,                    "false"),
        (qos.parse_bool,     False,                    "False"),
        (qos.parse_int,      1,                        1),
        (qos.parse_int,      -1,                       -1),
        (qos.parse_int,      0,                        0),
        (qos.parse_int,      1.0,                      1),
        (qos.parse_int,      1,                        "1"),
        (qos.parse_int,      0,                        "0"),
        (qos.parse_int,      1,                        "1   "),
        (qos.parse_int,      1,                        "   1   "),
        (qos.parse_int,      458699,                   "458699"),
        (qos.parse_duration, Duration(1,2),            Duration(1,2)),
        (qos.parse_duration, Duration(),               Duration()),
        (qos.parse_duration, Duration(1,0),            Duration(0,1_000_000_000)),
        (qos.parse_duration, Duration(1,0),            "(1,0)"),
        (qos.parse_duration, Duration(898989,757575),  "(898989,757575)"),
        (qos.parse_duration, Duration(),               "(0,0)"),
        (qos.parse_duration, Duration(-1,0),           "(-1,0)"),
        (qos.parse_duration, Duration(1,-0),           "(1,0)"),
        (qos.parse_duration, Duration(0,-4),           "(0,-4)"),
        (qos.parse_duration, Duration(1,1),            "( 1,1)"),
        (qos.parse_duration, Duration(1,1),            "(1 ,1)"),
        (qos.parse_duration, Duration(1,1),            "(1, 1)"),
        (qos.parse_duration, Duration(1,1),            "(1,1 )"),
        (qos.parse_duration, Duration(1,1),            "( 1 , 1 )"),
        (qos.parse_duration, Duration(1,1),            "( 1   , 1 )"),
        (qos.parse_duration, Duration(1,0),            "(00000,1000000000)"),
        ]

# Function, Error type, Input
parse_funcs_invalid = [
        (qos.parse_bool,     ValueError,     "test"),
        (qos.parse_bool,     ValueError,     ""),
        (qos.parse_bool,     ValueError,     "not true"),
        (qos.parse_bool,     ValueError,     "(True)"),
        (qos.parse_int,      TypeError,      1.0),
        (qos.parse_int,      TypeError,      0.0),
        (qos.parse_int,      ValueError,     "1.0"),
        (qos.parse_int,      ValueError,     "True"),
        (qos.parse_int,      ValueError,     "(1)"),
        (qos.parse_duration, ValueError, "not true"), # TODO improve error type
        (qos.parse_duration, ValueError, ""),
        (qos.parse_duration, ValueError, "test"),
        (qos.parse_duration, ValueError, "1,1"),
        (qos.parse_duration, ValueError, "(1,1"),
        (qos.parse_duration, ValueError, "()"),
        (qos.parse_duration, ValueError, "(,)"),
        (qos.parse_duration, ValueError, "(1,)"),
        (qos.parse_duration, ValueError, "(,1)"),
        (qos.parse_duration, ValueError, "(1,1,1)"),
        (qos.parse_duration, ValueError, "(1,1)1"),
        (qos.parse_duration, ValueError, "dd(1,1)"),
        (qos.parse_duration, ValueError, "(1,1)\n"),
        (qos.parse_duration, ValueError, "\n(1,1)"),
        (qos.parse_duration, ValueError, "(1\n,1)"),
        (qos.parse_duration, ValueError, "(1,,1)"),
        (qos.parse_duration, ValueError, "(1.0,1)"),
        (qos.parse_duration, ValueError, "(1.0,1)"),
        (qos.parse_duration, ValueError, "[1,,1]"),
        (qos.parse_duration, ValueError, "Duration(1,1)"),
        ]


@pytest.mark.parametrize("func,exp_out,inp", parse_funcs_valid)
def test_parse_funcs__positive(func, exp_out: bool, inp: bool | str):
    assert func(inp) == exp_out


@pytest.mark.parametrize("func,err,inp",parse_funcs_invalid)
def test_parse_funcs_negative(func, err, inp):
    with pytest.raises(err):
        func(inp)


Dur = QOSDurabilityPolicy
His = QOSHistoryPolicy
Liv = QOSLivelinessPolicy
Rel = QOSReliabilityPolicy

parse_enum__valid = [
        (Dur, Dur.SYSTEM_DEFAULT, Dur.SYSTEM_DEFAULT),
        (His, His.SYSTEM_DEFAULT, His.SYSTEM_DEFAULT),
        (Liv, Liv.SYSTEM_DEFAULT, Liv.SYSTEM_DEFAULT),
        (Rel, Rel.SYSTEM_DEFAULT, Rel.SYSTEM_DEFAULT),
        # (Rel, Rel.SYSTEM_DEFAULT, "system_default"),
        (Rel, Rel.SYSTEM_DEFAULT, 0),
        (His, His.UNKNOWN, 3),
        ]

parse_enum__invalid = [
        (Dur, ValueError, 5),
        (Dur, ValueError, -1),
        (Dur, TypeError, .0),
        (Dur, TypeError, None),
        (Liv, ValueError, ""),
        (Liv, ValueError, "test"),
        (Liv, ValueError, "system default"),

        ]


@pytest.mark.parametrize("enumtype,exp_out,input", parse_enum__valid)
def test_parse_enum__positive(enumtype, exp_out, input):
    assert qos.parse_enum(enumtype, input) == exp_out


@pytest.mark.parametrize("func,err,inp",parse_enum__invalid)
def test_parse_enum__negative(func, err, inp):
    with pytest.raises(err):
        qos.parse_enum(func, inp)
