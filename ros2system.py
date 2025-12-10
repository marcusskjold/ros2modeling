from dataclasses import dataclass
from enum import Enum
# from typing import string

TimeUnit = int
Value = int
QualityOfService = dict
Buffer = int
Topic = str

DEFAULT_EXECUTOR = "SingleThreadedExecutor"
DEFAULT_QOS: QualityOfService = {"buffersize": 10}


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
class ExternalOutput:
    pass


@dataclass
class Trigger:
    value: int
    callback_name: str



@dataclass
class Timer(Trigger):
    period: TimeUnit
    offset: TimeUnit


@dataclass
class ExternalInput(Trigger):
    description: str



@dataclass
class Publisher():
    name: str
    qos_offered: QualityOfService
    topic: Topic
    buffer: Buffer


@dataclass
class Callback(NamedElement):
    wcet: TimeUnit
    read_variables: list[Variable]
    write_variables: list[Variable]
    calls: list[NamedElement]
    publisher: str

    def __init__(self, name: str, wcet=0, read_variables=[],
                 write_variables=[], calls=[], outputs=[],
                 publisher: str = None):
        self.read_variables = read_variables
        self.name = name
        self.wcet = wcet
        self.read_variables = read_variables
        self.write_variables = write_variables
        self.calls = calls
        self.publisher = publisher


@dataclass
class Subscription():
    topic: Topic
    buffer: Buffer
    qos_requested: QualityOfService
    callback: str

    def __init__(self, topic: Topic,
                 callback: Callback,
                 qos_requested: QualityOfService = DEFAULT_QOS):
        self.topic = topic
        self.qos_requested = qos_requested
        self.buffer = qos_requested["buffersize"]
        self.callback = callback.name


@dataclass
class Service():
    pass


@dataclass
class Action():
    pass


@dataclass
class Node(NamedElement):
    name: str
    publishers: list[Publisher]
    callbacks: list[Callback]
    subscriptions: list[Subscription]
    variables: list[Variable]
    timers: list[Timer]
    services: list[Service]
    actions: list[Action]
    external_inputs: list[ExternalInput]

    def add_subscription(self,
                         topic: Topic,
                         callback: Callback,
                         qos_requested: QualityOfService = DEFAULT_QOS) -> Subscription:
        self.subscriptions.append(
            Subscription(topic=topic, callback=callback, qos_requested=qos_requested))

    def add_callback(self, name: str = None, wcet=0, read_variables=[],
                     write_variables=[], calls=[],
                     publisher: Publisher = None) -> Callback:
        if name is None:
            name = self.name + "callback" + str(len(self.callbacks))
        if publisher is None:
            pname = None
        else:
            pname = publisher.name
        callback = Callback(name=name, wcet=wcet,
                            read_variables=read_variables,
                            write_variables=write_variables,
                            calls=calls, publisher=pname)
        self.callbacks.append(callback)
        return callback

    def add_publisher(self,
                      name: str = None,
                      qos_offered: QualityOfService = DEFAULT_QOS,
                      topic: Topic = None) -> Publisher:
        if name is None:
            name = self.name + "publisher" + str(len(self.publishers))
        publisher = Publisher(name=name,
                              qos_offered=qos_offered,
                              topic=topic,
                              buffer=qos_offered["buffersize"],
                              )
        self.publishers.append(publisher)
        return publisher

    def add_timer(self,
                  name: str = None,
                  period: TimeUnit = 0,
                  offset: TimeUnit = 0,
                  callback: Callback = None) -> Timer:
        if callback is None:
            callback = self.add_callback()
        if name is None:
            name = self.name + "timer" + str(len(self.timers))
        timer = Timer(
            value=0, callback_name=callback.name, period=period, offset=offset)
        self.timers.append(timer)
        return timer


@dataclass
class Executor(NamedElement):
    name: str
    implementation: str
    nodes: list[Node]

    def add_node(self, name: str = None) -> Node:

        if name is None:
            name = self.name + "node" + str(len(self.nodes))

        node = Node(name=name, subscriptions=[],
                    variables=[], timers=[], services=[],
                    actions=[], external_inputs=[],
                    callbacks=[], publishers=[])
        node.name = name
        self.nodes.append(node)
        return node

    def add_nodes(self, nodenames: list[str]) -> list[Node]:
        return [self.add_node(name=name) for name in nodenames]


@dataclass
class DDS:
    implementation: str
    topics: list[Topic]

    def add_topic(self, name: str = None) -> Topic:
        topic = name
        if topic is None:
            topic = "topic" + str(len(self.topics))

        self.topics.append(topic)
        return topic

    def add_topics(self, names: list[str] = None) -> list[Topic]:
        return [self.add_topic(name) for name in names]


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
        self.dds = DDS(implementation=dds_implementation, topics=[])
