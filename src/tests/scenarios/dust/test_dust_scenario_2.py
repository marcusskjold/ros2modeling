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

def test_dust_scenario_2_individual_EXV1_max_latency() -> None:
    """
    Uses version 1 of the Executor. 
    First assumes all callbacks with release-time 0 is released
    before executor starts polling (assumption A1), then checks for assumption
    that polling and callback releases at time 0 happens simultaneously (assumption A2). 
    Uses individual approach.
    """
    ros_system = yparse.parse_yaml("src/tests/input/dust_scenario_2_EXV1_individual.yaml")
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
            # Assumption A1)
            # check that no buffer-overflows
            overflows = dust_system.buffer_overflow(stop_time=90)
            assert False not in overflows.values()
            #check max-latencies
            latency_results = dust_system.max_latency(stop_time=90, checks=['T0', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert latency_results == {
                    'T0' : 10,
                    'H' : 27,
                    'M' : 23,
                    'L' : 33,
                    'SH' : 30,
                    'SM' : 35,
                    'SL' : 40
            }
            # Assumption A2)
            # check that no buffer-overflows
            overflows = dust_system.buffer_overflow(stop_time=90, prioritized=False)
            assert False not in overflows.values()
            #check max-latencies
            latency_results = dust_system.max_latency(stop_time=90, prioritized=False, checks=['T0', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert latency_results == {
                'T0' : 10,
                'H' : 40,
                'M' : 50,
                'L' : 55,
                'SH' : 65,
                'SM' : 65,
                'SL' : 65
            }

def test_dust_scenario_2_holistic_EXV1_max_latency() -> None: 
    """
    Uses version 1 of the Executor. 
    First assumes all callbacks with release-time 0 is released
    before executor starts polling (assumption A1), then checks for assumption
    that polling and callback releases at time 0 happens simultaneously (assumption A2). 
    Uses holistic approach.
    """
    ros_system = yparse.parse_yaml("src/tests/input/dust_scenario_2_EXV1_holistic.yaml")
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
            # Assumption A1)
            # check that no buffer-overflows
            # overflows = dust_system.buffer_overflow(stop_time=90)
            # assert False not in overflows.values()
            #check max-latencies
            latency_results = dust_system.max_latency(stop_time=90, checks=['T0', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert latency_results == {
                'T0' : 10,
                'H' : 27,
                'M' : 23,
                'L' : 33,
                'SH' : 35,
                'SM' : 45,
                'SL' : 40
            }
            # Assumption A2)
            # check that no buffer-overflows
            # overflows = dust_system.buffer_overflow(stop_time=90, prioritized=False)
            # assert False not in overflows.values()
            # #check max-latencies
            # latency_results = dust_system.max_latency(stop_time=90, prioritized=False, checks=['T0', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            # expected_results = {
            #     'T0' : 10,
            #     'SH' : 65,
            #     'SM' : 65,
            #     'SL' : 65,
            #     'H' : 40,
            #     'M' : 50,
            #     'L' : 55
            # }
            # assert expected_results.items() <= latency_results.items()



def test_dust_scenario_2_individual_EXV2_max_latency() -> None:
    """
    Uses version 2 of the Executor. 
    First assumes all callbacks with release-time 0 is released
    before executor starts polling (assumption A1), then checks for assumption
    that polling and callback releases at time 0 happens simultaneously (assumption A2). 
    Uses individual approach.
    """
    ros_system = yparse.parse_yaml("src/tests/input/dust_scenario_2_EXV2_individual.yaml")
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
            # Assumption A1)
            # check that buffer-overflow happens
            overflows = dust_system.buffer_overflow(stop_time=90)
            assert False in overflows.values()
            #check max-latencies
            latency_results = dust_system.max_latency(stop_time=90, checks=['T0', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert latency_results == {
                'T0' : 22,
                'H' : 12,
                'M' : 13,
                'L' : 18,
                'SH' : 20,
                'SM' : 25,
                'SL' : 30
            }
            # Assumption A2)
            # check that buffer-overflow happens
            overflows = dust_system.buffer_overflow(stop_time=90, prioritized=False)
            assert False in overflows.values()
            #check max-latencies
            latency_results = dust_system.max_latency(stop_time=90, prioritized=False, checks=['T0', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert latency_results == {
                'T0' : 22,
                'SH' : 35,
                'SM' : 35,
                'SL' : 35,
                'H' : 35,
                'M' : 35,
                'L' : 35
            }
        
def test_dust_scenario_2_holistic_EXV2_max_latency() -> None: 
    """
    Uses version 1 of the Executor. 
    First assumes all callbacks with release-time 0 is released
    before executor starts polling (assumption A1), then checks for assumption
    that polling and callback releases at time 0 happens simultaneously (assumption A2). 
    Uses holistic approach.
    """
    ros_system = yparse.parse_yaml("src/tests/input/dust_scenario_2_EXV2_holistic.yaml")
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
            # Assumption A1)
            latency_results = dust_system.max_latency(stop_time=90, checks=['T0', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            assert latency_results == {
                'T0' : 22,
                'SH' : 20,
                'SM' : 25,
                'SL' : 30,
                'H' : 12,
                'M' : 13,
                'L' : 18
            }
            # Assumption A2)
            # latency_results = dust_system.max_latency(stop_time=90, prioritized=False, checks=['T0', 'H', 'M', 'L', 'SH', 'SM', 'SL'])
            # expected_results = {
            #     'T0' : 22,
            #     'SH' : 35,
            #     'SM' : 35,
            #     'SL' : 35,
            #     'H' : 35,
            #     'M' : 35,
            #     'L' : 35
            # }
            # assert expected_results.items() <= latency_results.items()