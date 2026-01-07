import sys
import copy
from ruamel.yaml import YAML

s = sys.stdout
yaml = YAML()
yaml.default_flow_style = False


def to_yaml(obj):
    # qos_stack = []
    def visit(obj):
        if obj is None:
            pass
        elif isinstance(obj, dict):
            out = {}
            for k in obj:
                out[k] = visit(obj[k])
                if out[k] is None:
                    del out[k]
                if out[k] == []:
                    del out[k]
        elif isinstance(obj, list):
            out = []
            for k in obj:
                out.append(visit(k))
        elif isinstance(obj, str):
            out = obj
        elif isinstance(obj, int):
            out = obj
        # elif isinstance(obj, ros.QualityOfService)
        else:
            d = obj.__dict__
            out = {}
            for field in d:
                key = field
                if field == 'name':
                    key = obj.__class__.__name__.lower()
                out[key] = visit(d[field])
                if out[key] is None:
                    del out[key]
                if out[key] == []:
                    del out[key]
        return out
    return visit(copy.deepcopy(obj))


def save_to_yaml(obj, filename):
    with open(f"{filename}.yaml", 'wb') as out:
        res = to_yaml(obj)
        yaml.dump(res, out)
