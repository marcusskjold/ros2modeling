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
# TODO: make into test
def test_dust_scenario_1_individual_A2_max_latency() -> None:
    ros_system = yparse.parse_yaml("src/tests/input/dust_scenario_1_individual.yaml")
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
            latency_results = dust_system.max_latency()
            assert latency_results == {
                'TIMER0' : 28,
                'TIMER1' : 33,
                'TIMER2' : 17,
                'TIMER3' : 22,
                'SERVICE0' : 65,
                'SERVICE1' : 70,
                'SERVICE2' : 75,
                'SUBSCRIBER0' : 65,
                'SUBSCRIBER1' : 55,
                'SUBSCRIBER2' : 60
            }
            #print(dust_system.max_latency())