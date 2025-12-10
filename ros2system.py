from dataclasses import dataclass
from enum import Enum
# from typing import string

type TimeUnit = int
type Value = int
type QualityOfService = dict
type Buffer = int

DEFAULT_EXECUTOR = "SingleThreadedExecutor"


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
class Trigger:
    value: int
    callback: Callback

    def release(self):
        return self.callback


@dataclass
class Timer(Trigger):
    period: TimeUnit
    offset: TimeUnit


@dataclass
class ExternalInput(Trigger):
    description: str


@dataclass
class Input(Trigger):
    pass


@dataclass
class Output():
    qos_offered: QualityOfService

@dataclass
class Interface(NamedElement):
    inputs: list[Input]
    outputs: list[Output]


@dataclass
class Topic(Interface):
    pass

@dataclass
class Publisher(Output):
    topic: Topic

@dataclass
class Callback:
    @dataclass
    class Result:
        wcet: TimeUnit
        write_variable: list[Variable]
        calls: list['Callback']
        outputs: list[Output]
    read_variables: list[Variable]
    results: dict[Value, Result]

    def __init__(self, wcet: int, publish: Topic,
                 read_variables: list[Variable] = [],
                 results: dict[Value, Result] = {}):
        default_result = 'Result'(
            wcet=wcet,
            write_variable=[],
            calls=[],
            outputs=[publish])
        self.read_variables = read_variables
        self.results = {0: default_result}


@dataclass
class Subscription(Input):
    topic: Topic
    buffer: Buffer
    qos_requested: QualityOfService

    def __init__(self, topic: Topic = None,
                 qos_requested: QualityOfService = None):
        self.topic = topic
        self.qos_requested = qos_requested
        self.buffer = qos_requested["buffersize"]


@dataclass
class Service(Interface):
    pass


@dataclass
class Action(Interface):
    pass


@dataclass
class Node(NamedElement):
    name: str
    subscriptions: list[Subscription]
    variables: list[Variable]
    timers: list[Timer]
    services: list[Service]
    actions: list[Action]
    external_inputs: list[ExternalInput]

    def subscribe_to(self,
                     topic: Topic,
                     callback: Callback,
                     qos_requested: QualityOfService,
                     value: Value = 0) -> Subscription:
        self.subscriptions.append(
            Subscription(topic, callback, qos_requested, value=value))



@dataclass
class Executor(NamedElement):
    name: str
    implementation: str
    nodes: list[Node]

    def add_node(self, name: str = None) -> Node:

        if (name is None):
            raise ValueError("Please provide name")

        node = Node(name=name, subscriptions=[],
                    variables=[], timers=[], services=[],
                    actions=[], external_inputs=[])
        node.name = name
        self.nodes.append(node)
        return node

    def add_nodes(self, nodenames: list[str]) -> list[Node]:
        return [self.add_node(name=name) for name in nodenames]


InterfaceType = Enum('InterfaceType', ['Topic', 'Service', 'Action'])


@dataclass
class DDS:
    implementation: str
    interfaces: dict[InterfaceType, list[Interface]]

    def add_topic(self, name: str = None) -> Topic:
        if name is None:
            name = "topic" + str(len(self.interfaces[InterfaceType.Topic]))

        topic = Topic(inputs=None, outputs=None, name=name)
        self.interfaces[InterfaceType.Topic].append(topic)

    def add_topics(self, names: list[str] = None) -> list[Topic]:
        return [self.add_topic(name) for name in names]

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
                     implementation: str = DEFAULT_EXECUTOR) -> Executor:

        if name is None:
            name = self.name + "_executor" + str(len(self.executors))

        executor = Executor(name=name, implementation=implementation, nodes=[])
        self.executors.append(executor)
        return executor

    def add_node(self, name: str = None) -> Node:
        executor = self.add_executor()
        return executor.add_node(name)


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

    def add_topic(self, name: str = None) -> Topic:
        self.dds.add_topic(name=name)

    def add_topics(self, names: list[str] = None) -> list[Topic]:
        self.dds.add_topics(names=names)

    def __init__(self, dds_implementation: str = None):

        if (dds_implementation is None):
            raise ValueError("Please provide dds_implementation")

        self.hosts = []
        self.dds = DDS(interfaces=None, implementation=dds_implementation)
