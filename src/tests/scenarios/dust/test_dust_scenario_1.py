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
            #print(dust_system.gen_declaration())
            #print(dust_system)
            #print(dust_system.gen_system())
            latency_results = dust_system.max_latency()
            assert latency_results == {
                'TIMER0_EX_0' : 28,
                'TIMER1_EX_0' : 33,
                'TIMER2_EX_0' : 17,
                'TIMER3_EX_0' : 22,
                'SERVICE0_EX_0' : 65,
                'SERVICE1_EX_0' : 70,
                'SERVICE2_EX_0' : 75,
                'SUBSCRIBER0_EX_0' : 65,
                'SUBSCRIBER1_EX_0' : 55,
                'SUBSCRIBER2_EX_0' : 60
            }

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
            latency_results = dust_system.max_latency()
            assert latency_results == {
                'TIMER0_EX_0' : 8,
                'TIMER1_EX_0' : 13,
                'TIMER2_EX_0' : 7,
                'TIMER3_EX_0' : 12,
                'SERVICE0_EX_0' : 65,
                'SERVICE1_EX_0' : 70,
                'SERVICE2_EX_0' : 75,
                'SUBSCRIBER0_EX_0' : 65,
                'SUBSCRIBER1_EX_0' : 55,
                'SUBSCRIBER2_EX_0' : 60
            }

#TODO: test
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
            expected_result = {
                'TIMER0_EX_1'      : 8,
                'TIMER1_EX_1'      : 13,
                'TIMER2_EX_1'      : 7,
                'TIMER3_EX_1'      : 12,
                'SUBSCRIBER0_EX_1' : 65,
                'SUBSCRIBER1_EX_1' : 55,
                'SUBSCRIBER2_EX_1' : 60,
                'SERVICE0_EX_1'    : 65,
                'SERVICE1_EX_1'    : 70,
                'SERVICE2_EX_1'    : 75
            }
            latency_results = dust_system.max_latency()
            assert expected_result.items() <= latency_results.items()

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
            expected_result = {
                'TIMER0_EX_1' : 28,
                'TIMER1_EX_1' : 33,
                'TIMER2_EX_1' : 17,
                'TIMER3_EX_1' : 22,
                'SERVICE0_EX_1' : 65,
                'SERVICE1_EX_1' : 70,
                'SERVICE2_EX_1' : 75,
                'SUBSCRIBER0_EX_1' : 65,
                'SUBSCRIBER1_EX_1' : 55,
                'SUBSCRIBER2_EX_1' : 60
            }
            latency_results = dust_system.max_latency()
            print(latency_results)
            assert expected_result.items() <= latency_results.items()