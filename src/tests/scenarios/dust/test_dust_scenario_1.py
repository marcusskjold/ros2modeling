import pytest
from pprint import pprint
import roserer.ros2system as ros
#import roserer.yamlPrinter as yprint
import roserer.yamlParser as yparse
import roserer.systemvalidator as sv
import roserer.dust.dust_system as ds
import roserer.dust.dust_uppaal as du
# import roserer.adapters.dust_adapter as da

from dotenv import load_dotenv
load_dotenv()

def test_dust_scenario_1_individual_EXV1_A1_max_latency() -> None:
    """
    Uses version 1 of the Executor. 
    Assumes all callbacks with release-time 0 is released
    before executor starts polling (assumption A1). 
    Uses individual approach.
    """
    ros_system = yparse.parse_yaml("src/tests/input/dust_scenario_1_EXV1_individual.yaml")
    test_result: sv.ValidationResult = sv.validate_system(ros_system)
    if test_result.errors != []:
        for ln in test_result.errors:
            print(ln)
            raise Exception("Something went wrong when validating the system!")
    else:
        errors, warnings, dust_system = da.transform_system(system=ros_system, validationresult=test_result)
        if errors != []:
            print(errors)
            raise Exception("Something went wrong transforming the system!")
        for ln in warnings:
            print(ln)
        if dust_system is not None:
            # TODO: check if stop_time could be used?
            # check that buffer-overflow happens
            overflows = dust_system.buffer_overflow(checks=['T0', 'T1', 'T2', 'T3', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert False not in overflows.values()
            #check max-latencies
            latency_results = dust_system.max_latency(checks=['T0', 'T1', 'T2', 'T3', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert latency_results == {
                'T0' : 8,
                'T1' : 13,
                'T2' : 7,
                'T3' : 12,
                'H' : 65,
                'M' : 55,
                'L' : 60,
                'SH' : 65,
                'SM' : 70,
                'SL' : 75
            }

def test_dust_scenario_1_holistic_EXV1_A1_max_latency() -> None:
    """
    Uses version 1 of the Executor. 
    Assumes all callbacks with release-time 0 is released
    before executor starts polling (assumption A1). 
    Uses holistic approach.
    """
    ros_system = yparse.parse_yaml("src/tests/input/dust_scenario_1_EXV1_holistic.yaml")
    test_result: sv.ValidationResult = sv.validate_system(ros_system)
    if test_result.errors != []:
        for ln in test_result.errors:
            print(ln)
            raise Exception("Something went wrong when validating the system!")
    else:
        errors, warnings, dust_system = da.transform_system(system=ros_system, validationresult=test_result)
        if errors != []:
            print(errors)
            raise Exception("Something went wrong transforming the system!")
        for ln in warnings:
            print(ln)
        if dust_system is not None:
            # TODO: check if stop_time could be used?
            # check that buffer-overflow happens
            overflows = dust_system.buffer_overflow(checks=['T0', 'T1', 'T2', 'T3', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert False not in overflows.values()
            # check max-latencies
            expected_result = {
                'T0': 8,
                'T1': 13,
                'T2': 7,
                'T3': 12,
                'H' : 65,
                'M' : 55,
                'L' : 60,
                'SH': 65,
                'SM': 70,
                'SL': 75
            }
            latency_results = dust_system.max_latency(checks=['T0', 'T1', 'T2', 'T3', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert expected_result.items() <= latency_results.items()

def test_dust_scenario_1_individual_EXV2_A1_max_latency() -> None:
    """
    Uses version 2 of the Executor. 
    Assumes all callbacks with release-time 0 is released
    before executor starts polling (assumption A1). 
    Uses individual approach.
    """
    ros_system = yparse.parse_yaml("src/tests/input/dust_scenario_1_EXV2_individual.yaml")
    test_result: sv.ValidationResult = sv.validate_system(ros_system)
    if test_result.errors != []:
        for ln in test_result.errors:
            print(ln)
            raise Exception("Something went wrong when validating the system!")
    else:
        errors, warnings, dust_system = da.transform_system(system=ros_system, validationresult=test_result)
        if errors != []:
            print(errors)
            raise Exception("Something went wrong transforming the system!")
        for ln in warnings:
            print(ln)
        if dust_system is not None:
            # TODO: check if stop_time could be used?
            # check that buffer-overflow happens
            overflows = dust_system.buffer_overflow(checks=['T0', 'T1', 'T2', 'T3', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert False not in overflows.values()
            # check max-latencies
            #print(dust_system.gen_declaration())
            #print(dust_system)
            #print(dust_system.gen_system())
            latency_results = dust_system.max_latency(checks=['T0', 'T1', 'T2', 'T3', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert latency_results == {
                'T0' : 28,
                'T1' : 33,
                'T2' : 17,
                'T3' : 22,
                'SH' : 65,
                'SM' : 70,
                'SL' : 75,
                'H' : 65,
                'M' : 55,
                'L' : 60
            }

def test_dust_scenario_1_holistic_EXV2_A1_max_latency() -> None:
    """
    Uses version 2 of the Executor. 
    Assumes all callbacks with release-time 0 is released
    before executor starts polling (assumption A1). 
    Uses holistic approach.
    """
    ros_system = yparse.parse_yaml("src/tests/input/dust_scenario_1_EXV2_holistic.yaml")
    test_result: sv.ValidationResult = sv.validate_system(ros_system)
    if test_result.errors != []:
        for ln in test_result.errors:
            print(ln)
            raise Exception("Something went wrong when validating the system!")
    else:
        errors, warnings, dust_system = da.transform_system(system=ros_system, validationresult=test_result)
        if errors != []:
            print(errors)
            raise Exception("Something went wrong transforming the system!")
        for ln in warnings:
            print(ln)
        if dust_system is not None:
            # TODO: check if stop_time could be used?
            # check that buffer-overflow happens
            overflows = dust_system.buffer_overflow(checks=['T0', 'T1', 'T2', 'T3', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert False not in overflows.values()
            # check max-latencies
            expected_result = {
                'T0' : 28,
                'T1' : 33,
                'T2' : 17,
                'T3' : 22,
                'H' : 65,
                'M' : 55,
                'L' : 60,
                'SH' : 65,
                'SM' : 70,
                'SL' : 75
            }
            latency_results = dust_system.max_latency(checks=['T0', 'T1', 'T2', 'T3', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert expected_result.items() <= latency_results.items()