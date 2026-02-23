import roserer.ros2system as ros
from roserer.systemvalidator import validate_system, ValidationResult
import roserer.yamlParser as parse
from roserer.yamlParser import parse_yaml
from roserer.adapters.backeman_adapter import transform_system

def errprint(errors):
    for err in errors:
        print(err)

sys = parse_yaml("src/tests/input/example.yaml")
valid = validate_system(sys)
valid: ValidationResult

errprint(valid.errors)



