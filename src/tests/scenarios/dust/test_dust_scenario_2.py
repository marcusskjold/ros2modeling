from pprint import pprint
import roserer.ros2system as ros
#import roserer.yamlPrinter as yprint
import roserer.yamlParser as yparse
import roserer.systemvalidator as sv
import roserer.dust.dust_system as ds
import roserer.dust.dust_uppaal as du
import roserer.adapters.dust_adapter as da

from dotenv import load_dotenv
load_dotenv()
def test_dust_scenario_2_individual_A2_max_latency() -> None:
    ros_system = yparse.parse_yaml("src/tests/input/dust_scenario_2_individual.yaml")
    test_result: sv.ValidationResult = sv.validate_system(ros_system)
    if test_result.errors != []:
        for ln in test_result.errors:
            print(ln)
            raise Exception("Something went wrong when validating the system!")
    else:
        errors, warnings, dust_system = da.transform_system(system=ros_system, validationresult=test_result)
        for ln in errors:
            print(ln)
            raise Exception("Something went wrong transforming the system!")
        for ln in warnings:
            print(ln)
        if dust_system is not None:
            #print(dust_system.gen_declaration())
            #print(dust_system)
            #print(dust_system.gen_system())
            # uses state-space saving strategy.
            #print(dust_system.max_latency(stop_time=90))
            latency_results = dust_system.max_latency(stop_time=90)
            assert latency_results == {
                'TIMER0' : 22,
                'SERVICE0' : 20,
                'SERVICE1' : 25,
                'SERVICE2' : 30,
                'SUBSCRIBER0' : 12,
                'SUBSCRIBER1' : 13,
                'SUBSCRIBER2' : 18
            }