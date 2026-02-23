from enum import Enum
from pprint import pprint
from typing import Any
import copy
from ruamel.yaml import YAML
from roserer.qos import QoS


YamlObject = dict[str, 'YamlObject'] | list['YamlObject'] | str | int

def visit(obj: Any, parent_qos: QoS | None = None) -> YamlObject:
    if isinstance(obj, (str, int)):
        return obj
    elif isinstance(obj, list):
        out = []
        for k in obj:
            out.append(visit(k, parent_qos))
        return out
    elif isinstance(obj, dict):
        out: dict = {}
        for k, v in obj.items():
            out[k] = visit(obj[v], parent_qos)
            if out[k] is None:
                del out[k]
            if out[k] == []:
                del out[k]
        return out
    elif isinstance(obj, Enum):
        return 1

    else:
        d = obj.__dict__
        print()
        print(obj.__class__)
        print()
        pprint(d)
        qos = d.get('qos')
        if qos is not None and isinstance(qos, QoS):
            parent_qos = qos
        qos = d.get('default_qos')
        if qos is not None and isinstance(qos, QoS):
            parent_qos = qos
        out = {}
        for k, v in d.items():
            if k == 'qos' or k == 'default_qos':
                pass
            if k == 'name':
                k = obj.__class__.__name__.lower()
            out[k] = visit(v, parent_qos)
            if out[k] is None:
                del out[k]
            if out[k] == []:
                del out[k]
        return out


def to_yaml(obj: Any) -> YamlObject:
    return visit(copy.deepcopy(obj))


def save_to_yaml(obj: Any, filename: str) -> None:
    yaml = YAML()
    yaml.default_flow_style = False
    with open(f"{filename}.yaml", 'wb') as out:
        res = to_yaml(obj)
        yaml.dump(res, out)
