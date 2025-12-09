from dataclasses import dataclass
from enum import Enum
# from typing import string

type TimeUnit = int
type Value = int
type QualityOfService = dict


@dataclass
class NamedElement:
    name: str


@dataclass
class ContainedElement:
    container: NamedElement


@dataclass
class Variable:
    value: int
    pass


@dataclass
class Output:
    qos_offered: QualityOfService
    pass


@dataclass
class ExternalOutput:
    pass


@dataclass
class Callback:
    @dataclass
    class Result:
        write_variable: list[Variable]
        wcet: TimeUnit
        calls: list['Callback']
        outputs: list[Output]
    read_variable: list[Variable]
    results: dict[Value, Result]


@dataclass
class Trigger:
    value: int
    pass


@dataclass
class Timer(Trigger):
    period: TimeUnit
    offset: TimeUnit


@dataclass
class ExternalInput(Trigger):
    description: str


@dataclass
class Input(Trigger):
    qos_requested: QualityOfService
    pass


@dataclass
class Output:
    qos_offered: QualityOfService
    pass


@dataclass
class Interface(NamedElement):
    inputs: list[Input]
    outputs: list[Output]


@dataclass
class Topic(Interface):
    pass


@dataclass
class Service(Interface):
    pass


@dataclass
class Action(Interface):
    pass


@dataclass
class Node(NamedElement):
    name: str
    releases: dict[Trigger, list[Callback]]
    variables: list[Variable]


@dataclass
class Executor(NamedElement):
    name: str
    implementation: str
    nodes: list[Node]

    def add_node(self, name: str = None) -> Node:

        if name is None:
            name = self.name + "_node" + str(len(self.nodes))

        node = Node(releases=[], variables=[], name=name)
        self.nodes.append(node)
        return node

    def add_nodes(self, nodenames: list[str]) -> list[Node]:
        return [self.add_node(name=name) for name in nodenames]


InterfaceType = Enum('InterfaceType', ['Topic', 'Service', 'Action'])


@dataclass
class DDS:
    implementation: str
    interfaces: dict[InterfaceType, list[Interface]]

    def add_topic(self, name: str = None):
        if name is None:
            name = "topic" + str(len(self.interfaces[InterfaceType.Topic]))

        topic = Topic(inputs=None, outputs=None)
        self.interfaces[InterfaceType.Topic].append(topic)

    def __init__(self, implementation=None, interfaces=None):
        self.implementation = implementation
        self.interfaces = {InterfaceType.Topic: [],
                           InterfaceType.Service: [],
                           InterfaceType.Action: []}


@dataclass
class Host(NamedElement):
    name: str
    operating_system: str
    executors: list[Executor]

    def add_executor(self, name: str = None,
                     implementation: str = None) -> Executor:

        if (implementation is None):
            raise ValueError("Please provide implementation")
        if name is None:
            name = self.name + "_executor" + str(len(self.executors))

        executor = Executor(name=name, implementation=implementation, nodes=[])
        self.executors.append(executor)
        return executor


@dataclass
class System:
    dds: DDS
    hosts: list[Host]

    def add_host(self, name: str = None, operating_system: str = None) -> Host:

        if (operating_system is None):
            raise ValueError("Please provide operating_system")

        if name is None:
            name = "host" + str(len(self.hosts))

        host = Host(executors=[], operating_system=operating_system, name=name)
        self.hosts.append(host)
        return host

    def __init__(self, dds_implementation: str = None):

        if (dds_implementation is None):
            raise ValueError("Please provide dds_implementation")

        self.hosts = []
        self.dds = DDS(interfaces=None, implementation=dds_implementation)
