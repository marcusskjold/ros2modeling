from dataclasses import dataclass

#TODO: Make enums (in validator) available to the user of this class

TimeUnit = int
Topic = str

DEFAULT_EXECUTOR = "SingleThreadedExecutor"
DEFAULT_DISTRIBUTION = "Rolling" #TODO: Make this overridable inside system?
UNSPECIFIED = "Generic" #When not specified in model


#Default-arguments based on ROS2's own default topic/service QoS (see: https://github.com/ros2/rmw/blob/rolling/rmw/include/rmw/qos_profiles.h )#
#For extendability, we could store it as a map of dict, 
# mapping each kind of QoS-setting to a dict (e.g. service, parameter, sensor)
@dataclass
class QualityOfService:
    history: str
    depth: int
    reliability: str
    durability: str
    deadline: int
    lifespan: int
    liveliness: str
    liveliness_lease_duration: int

    def __init__(self,
                 history: str = "keep_last",
                 depth: int = 10,
                 reliability: str = "reliable",
                 durability: str = "volatile",
                 deadline: int | str = "default",
                 lifespan: int | str = "default",
                 liveliness: str = "system_default",
                 liveliness_lease_duration = "default"
                 ):
        #TODO: convert default to -1 here
        self.history=history
        self.depth=depth
        self.reliability=reliability
        self.durability=durability
        self.deadline= 0 if deadline == "default" else deadline
        self.lifespan= 0 if lifespan == "default" else lifespan
        self.liveliness=liveliness
        self.liveliness_lease_duration= 0 if liveliness_lease_duration == "default" else liveliness_lease_duration

#alias
QoS = QualityOfService

#default object
DEFAULT_QOS = QoS()

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
    qos: QualityOfService
    topic: Topic

    def __init__(self,
                 name: str,
                 topic: Topic,
                 qos: QualityOfService = DEFAULT_QOS):
        self.name = name
        self.topic = topic
        self.qos = qos


@dataclass
class Client():
    name: str
    service: str
    qos: QualityOfService


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
    calls: list[str] #TODO: what is this, or is it maintained fine as list of string?
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
    qos: QualityOfService
    callback: str

    def __init__(self, topic: Topic,
                 callback: str,
                 qos: QualityOfService = DEFAULT_QOS):
        self.topic = topic
        self.qos = qos
        self.callback = callback


@dataclass
class Service():
    name: str
    callback: Callback
    qos: QualityOfService


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

    def add_external_input(self, callback: Callback=None, name: str = None) -> ExternalInput:

        if name is None:
            name = self.name + "_input" + str(len(self.external_inputs))

        if callback is None:
            raise ValueError("Please provide valid callback for external input")
        
        input = ExternalInput(name=name, callback=callback)
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
                         callback: Callback = None,
                         qos:
                         QualityOfService = None) -> Subscription:
        if callback is None:
            raise ValueError("Please provide valid callback for subscription")
        if qos is None:
            qos = self.default_qos
        else: 
            qos = QoS(**qos)
        self.subscriptions.append(
            Subscription(topic=topic,
                         callback=callback.name,
                         qos=qos))

    def add_service(self,
                    callback: Callback = None, #Can be alternative type, arguably, as it has specific interface
                    name: str = None,
                    qos: QualityOfService = None) -> Service: 
        if callback is None:
            raise ValueError("Please provide valid callback for service")
        if qos is None:
            qos = self.default_qos
        else: 
            qos = QoS(**qos)
        if name is None:
            name = self.name + "_service" + str(len(self.services))
        service = Service(name=name,
                          callback=callback,
                          qos=qos)
        self.services.append(service)
        return service

    def add_client(self,
                   service: str,
                   name: str = None,
                   qos: QualityOfService = None) -> Client:
        if name is None:
            name = self.name + "_client" + str(len(self.clients))
        if qos is None:
            qos = self.default_qos
        else: 
            qos = QoS(**qos)
        client = Client(name=name, service=service, qos=qos)
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
                     requests: list[Request] = None) -> Callback: ###TODO: requests could be made from tuples instead???
        if read_variables is None:
            read_variables = []
        if write_variables is None:
            write_variables = []
        if calls is None:
            calls = []
        if requests is None:
            requests = []
        if name is None:
            name = self.name + "_cb" + str(len(self.callbacks))
        if publishers is None:
            pnames = []
        else:
            pnames = [publisher.name for publisher in publishers]
        callback = Callback(name=name, wcet=wcet,
                            read_variables=read_variables,
                            write_variables=write_variables,
                            calls=calls, publishers=pnames,
                            external_outputs=outputs,
                            requests=requests)
        self.callbacks.append(callback)
        return callback

    def add_publisher(self,
                      name: str = None,
                      qos: QualityOfService = None,
                      topic: Topic = None) -> Publisher:
        if name is None:
            name = self.name + "_publisher" + str(len(self.publishers))
        if qos is None:
            qos = self.default_qos
        else: 
            qos = QoS(**qos)
        if topic is None:
            raise ValueError("Please provide topic for publisher")
        publisher = Publisher(name=name,
                              qos=qos,
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
            raise ValueError("Please provide valid callback for timer")
        if name is None:
            name = self.name + "_timer" + str(len(self.timers))
        timer = Timer(
            callback=callback.name,
            period=period,
            offset=offset,
            name=name)
        self.timers.append(timer)
        return timer

    def add_variable(self, name: str = None):
        if name is None:
            name = self.name + "_var" + str(len(self.variables))
        var = Variable(name=name)
        self.variables.append(var)
        return var

    def get_topic(self, publisher_name: str, default_value=None) -> str:
        for pub in self.publishers:
            if publisher_name == pub.name:
                return pub.topic
        return default_value


@dataclass
class Executor():
    name: str
    ros_distribution: str
    implementation: str
    default_qos: QualityOfService
    nodes: list[Node]


    def add_node(self, name: str = None, subscriptions=None,
                 variables=None, timers=None, services=None,
                 actions=None, external_inputs=None,
                 callbacks=None, publishers=None,
                 clients=None,
                 external_outputs=None,
                 default_qos=None
                 ) -> Node:

        if name is None:
            name = self.name + "_node" + str(len(self.nodes))
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
        if default_qos is None:
            default_qos = self.default_qos
        else: 
            default_qos = QoS(**default_qos)

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
    default_qos: QualityOfService
    executors: list[Executor]

    def add_executor(self, name: str = None,
                     implementation: str = DEFAULT_EXECUTOR,
                     ros_distribution: str = DEFAULT_DISTRIBUTION,
                     default_qos: QualityOfService = None) -> Executor:

        if name is None:
            name = self.name + "_executor" + str(len(self.executors))
        if (ros_distribution is None):
            raise ValueError("Please provide distribution")
        if default_qos is None:
            default_qos = self.default_qos
        else: 
            default_qos = QoS(**default_qos)

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
    default_qos: QualityOfService
    hosts: list[Host]

    def add_host(self,
                 name: str = None,
                 operating_system: str = UNSPECIFIED,
                 architecture=UNSPECIFIED,
                 default_qos=None) -> Host:
        if name is None:
            name = self.name + "_host" + str(len(self.hosts))
        if default_qos is None:
            default_qos = self.default_qos
        else: 
            default_qos = QoS(**default_qos)
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

    def __init__(self, name: str, dds_implementation: str = UNSPECIFIED, default_qos=None):

        self.name = name
        self.hosts = []
        self.dds_implementation = dds_implementation
        self.default_qos = DEFAULT_QOS if default_qos is None else QoS(**default_qos)