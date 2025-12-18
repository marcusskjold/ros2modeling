from dataclasses import dataclass

#TODO: Make enums (in validator) available to the user of this class

TimeUnit = int
QualityOfService = dict
Topic = str

DEFAULT_EXECUTOR = "SingleThreadedExecutor"
DEFAULT_QOS: QualityOfService = {
    "history": "system_default",
    "depth": 10,
    "reliability": "system_default",
    "durability": "system_default",
    "deadline": 0,
    "lifespan": 0,
    "liveliness": "system_default",
    "liveliness_lease_duration": 0
}
DEFAULT_DISTRIBUTION = "Rolling" #TODO: Make this overridable inside system?
UNSPECIFIED = "Generic" #When not specified in model



@dataclass
class Variable:
    name: str


@dataclass
class ExternalOutput:
    name: str


@dataclass
class Timer():
    name: str
    period: TimeUnit
    offset: TimeUnit
    callback: str


@dataclass
class Publisher():
    name: str
    qos_offered: QualityOfService
    topic: Topic

    def __init__(self,
                 name: str,
                 topic: Topic,
                 qos_offered: QualityOfService = DEFAULT_QOS):
        self.name = name
        self.topic = topic
        self.qos_offered = qos_offered


@dataclass
class Client():
    name: str
    service: str
    qos_profile: QualityOfService


@dataclass
class Request():
    client: str
    timeout: TimeUnit


@dataclass
class Callback():
    name: str
    wcet: TimeUnit
    read_variables: list[Variable]
    write_variables: list[Variable]
    calls: list[str]
    publishers: list[str]
    external_outputs: list[ExternalOutput]
    requests: list[Request]

    def __init__(self,
                 name: str,
                 wcet=0,
                 read_variables=None,
                 write_variables=None,
                 calls=None,
                 external_outputs=None,
                 publishers: list[str] = None,
                 requests: list[Request] = None):
        if write_variables is None:
            write_variables = []
        if calls is None:
            calls = []
        if external_outputs is None:
            external_outputs = []
        if read_variables is None:
            read_variables = []
        if requests is None:
            requests = []
        if publishers is None:
            publishers = []
        self.read_variables = read_variables
        self.name = name
        self.wcet = wcet
        self.read_variables = read_variables
        self.write_variables = write_variables
        self.calls = calls
        self.publishers = publishers
        self.external_outputs = external_outputs
        self.requests = requests


@dataclass
class Subscription():
    topic: Topic
    qos_requested: QualityOfService
    callback: str

    def __init__(self, topic: Topic,
                 callback: Callback,
                 qos_requested: QualityOfService = DEFAULT_QOS):
        self.topic = topic
        self.qos_requested = qos_requested
        self.callback = callback.name


@dataclass
class Service():
    name: str
    callback: Callback
    qos_requested: QualityOfService


@dataclass
class Action():
    name: str


@dataclass
class ExternalInput():
    name: str
    callback: Callback


@dataclass
class Node():
    name: str
    publishers: list[Publisher]
    callbacks: list[Callback]
    subscriptions: list[Subscription]
    variables: list[Variable]
    timers: list[Timer]
    services: list[Service]
    actions: list[Action]
    external_inputs: list[ExternalInput]
    external_outputs: list[ExternalOutput]
    clients: list[Client]
    default_qos: QualityOfService

    def add_external_input(self, name: str = None) -> ExternalInput:

        if name is None:
            name = self.name + "_input" + str(len(self.external_inputs))

        input = ExternalInput(name)
        self.external_inputs.append(input)
        return input

    def add_external_output(self, name: str = None) -> ExternalOutput:

        if name is None:
            name = self.name + "_output" + str(len(self.external_outputs))

        output = ExternalOutput(name)
        self.external_outputs.append(output)
        return output

    def add_subscription(self,
                         topic: Topic,
                         callback: Callback,
                         qos_requested:
                         QualityOfService = None) -> Subscription:
        if qos_requested is None:
            qos_requested = self.default_qos
        self.subscriptions.append(
            Subscription(topic=topic,
                         callback=callback,
                         qos_requested=qos_requested))

    def add_service(self,
                    wcet: TimeUnit,
                    name: str = None,
                    qos_profile: QualityOfService = None,
                    calls: list[Callback] = None) -> Service:
        if qos_profile is None:
            qos_profile = self.default_qos
        if calls is None:
            calls = []
        if name is None:
            name = self.name + "service" + str(len(self.services))
        callback = self.add_callback(
            name=name + "_cb",
            wcet=wcet,
            publishers=[self.add_publisher(
                name=name + "_publisher",
                qos_offered=qos_profile,
                topic=name
            )]
        )
        service = Service(name=name,
                          callback=callback,
                          qos_requested=qos_profile)
        self.services.append(service)
        return service

    def add_client(self,
                   service: str,
                   qos_profile: QualityOfService = None) -> Client:
        if qos_profile is None:
            qos_profile = self.default_qos
        client = Client(service=service, qos_profile=qos_profile)
        self.clients.append(client)
        return client

    def add_callback(self,
                     wcet: TimeUnit,
                     name: str = None,
                     read_variables=None,
                     write_variables=None,
                     calls: list = None,
                     outputs: list[ExternalOutput] = None,
                     publishers: list[Publisher] = None,
                     requests: list[Request] = None) -> Callback:
        if read_variables is None:
            read_variables = []
        if write_variables is None:
            write_variables = []
        if calls is None:
            calls = []
        if requests is None:
            requests = []
        if name is None:
            name = self.name + "callback" + str(len(self.callbacks))
        if publishers is None:
            pnames = []
        else:
            pnames = [publisher.name for publisher in publishers]
        callback = Callback(name=name, wcet=wcet,
                            read_variables=read_variables,
                            write_variables=write_variables,
                            calls=calls, publishers=pnames,
                            external_outputs=outputs)
        self.callbacks.append(callback)
        return callback

    def add_publisher(self,
                      name: str = None,
                      qos_offered: QualityOfService = None,
                      topic: Topic = None) -> Publisher:
        if qos_offered is None:
            qos_offered = self.default_qos
        if name is None:
            name = self.name + "publisher" + str(len(self.publishers))
        if topic is None:
            raise ValueError("Please provide topic to publisher")
        publisher = Publisher(name=name,
                              qos_offered=qos_offered,
                              topic=topic,
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
            callback=callback.name,
            period=period,
            offset=offset,
            name=name)
        self.timers.append(timer)
        return timer

    def add_variable(self, name: str = None):
        if name is None:
            name = self.name + "var" + str(len(self.variables))
        var = Variable(name=name)
        self.variables.append(var)
        return var


@dataclass
class Executor():
    name: str
    ros_distribution: str
    implementation: str
    nodes: list[Node]
    default_qos: QualityOfService

    def add_node(self, name: str = None, subscriptions=None,
                 variables=None, timers=None, services=None,
                 actions=None, external_inputs=None,
                 callbacks=None, publishers=None,
                 clients=None,
                 external_outputs=None,
                 default_qos=DEFAULT_QOS
                 ) -> Node:

        if name is None:
            name = self.name + "node" + str(len(self.nodes))
        if subscriptions is None:
            subscriptions = []
        if variables is None:
            variables = []
        if timers is None:
            timers = []
        if services is None:
            services = []
        if actions is None:
            actions = []
        if external_inputs is None:
            external_inputs = []
        if callbacks is None:
            callbacks = []
        if publishers is None:
            publishers = []
        if clients is None:
            clients = []
        if external_outputs is None:
            external_outputs = []

        node = Node(name=name,
                    subscriptions=subscriptions,
                    variables=variables,
                    timers=timers,
                    services=services,
                    actions=actions,
                    external_inputs=external_inputs,
                    callbacks=callbacks,
                    publishers=publishers,
                    clients=clients,
                    external_outputs=external_outputs,
                    default_qos=default_qos
                    )
        node.name = name
        self.nodes.append(node)
        return node

    def add_nodes(self, nodenames: list[str]) -> list[Node]:
        return [self.add_node(name=name) for name in nodenames]


@dataclass
class Host():
    name: str
    operating_system: str
    architecture: str
    executors: list[Executor]
    default_qos: QualityOfService

    def add_executor(self, name: str = None,
                     implementation: str = DEFAULT_EXECUTOR,
                     ros_distribution: str = DEFAULT_DISTRIBUTION,
                     default_qos: dict = DEFAULT_QOS) -> Executor:

        if name is None:
            name = self.name + "_executor" + str(len(self.executors))
        if (ros_distribution is None):
            raise ValueError("Please provide distribution")

        executor = Executor(name=name, implementation=implementation, nodes=[],
                            ros_distribution=ros_distribution,
                            default_qos=default_qos)
        self.executors.append(executor)
        return executor

    def add_node(self, name: str = None) -> Node:
        executor = self.add_executor()
        return executor.add_node(name)


@dataclass
class System():
    name: str
    dds_implementation: str
    hosts: list[Host]
    default_qos: QualityOfService

    def add_host(self,
                 name: str = None,
                 operating_system: str = UNSPECIFIED,
                 architecture=UNSPECIFIED,
                 default_qos=None) -> Host:
        if default_qos is None:
            default_qos = self.default_qos
        if (operating_system is None):
            raise ValueError("Please provide operating_system")
        if (architecture is None):
            raise ValueError("Please provide architecture")
        if name is None:
            name = "host" + str(len(self.hosts))

        host = Host(executors=[],
                    operating_system=operating_system,
                    name=name,
                    architecture=architecture,
                    default_qos=default_qos)
        self.hosts.append(host)
        return host

    def add_topic(self, name: str = None) -> Topic:
        self.dds.add_topic(name=name)

    def add_topics(self, names: list[str] = None) -> list[Topic]:
        self.dds.add_topics(names=names)

    def __init__(self, name: str, dds_implementation: str = None):

        if (dds_implementation is None):
            raise ValueError("Please provide dds_implementation")

        self.name = name
        self.hosts = []
        self.dds_implementation = dds_implementation
        self.default_qos = DEFAULT_QOS
