from typing import Any, TypeVar
from dataclasses import dataclass
import roserer.qos
from roserer.qos import QoS

#TODO: Make enums (in validator) available to the user of this class


DEFAULT_EXECUTOR = "SingleThreadedExecutor"
DEFAULT_DISTRIBUTION = "Rolling"
UNSPECIFIED = "Generic"
DEFAULT_QOS = roserer.qos.qos_profile_default()


def _qos_init(q: QoS | dict[str, Any] | None, default: QoS) -> QoS:
    if q is None:
        return default
    elif not isinstance(q, QoS):
        return QoS(**q)
    else:
        return q


T = TypeVar ('T')
def _empty_list_init(x: list[T] | None) -> list[T]:
    if x is None:
        return []
    else:
        return x

def _name_init(name: str | None, parent: str, type: str, position: int) -> str:
    if name is None:
        return parent + "_" + type + str(position)
    else:
        return name


TimeUnit = int
Topic = str

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
    topic: Topic
    qos: QoS


@dataclass
class Client():
    name: str
    service: str
    qos: QoS


@dataclass
class Request():
    client: str
    # callback upon receiving response, e.g. handle_response(*args)
    response: str


@dataclass
class Callback():
    name: str
    wcet: TimeUnit
    read_variables: list[Variable]
    write_variables: list[Variable]
    calls: list[str]
    publishers: list[str]
    external_outputs: list[ExternalOutput]
    request: Request

    def __init__(
            self,
            name: str,
            wcet: int,
            read_variables: list[Variable] | None = None,
            write_variables: list[Variable] | None = None,
            calls: list[str] | None = None,
            external_outputs: list[ExternalOutput] | None = None,
            publishers: list[str] | None = None,
            request: Request | None = None
            ) -> None:
        self.name = name
        self.wcet = wcet
        self.read_variables = _empty_list_init(read_variables)
        self.write_variables = _empty_list_init(write_variables)
        self.calls = _empty_list_init(calls)
        self.publishers = _empty_list_init(publishers)
        self.external_outputs = _empty_list_init(external_outputs)
        self.request = request


@dataclass
class Subscription():
    topic: Topic
    callback: str
    qos: QoS


@dataclass
class Service():
    name: str
    callback: str
    qos: QoS


@dataclass
class Action():
    name: str


@dataclass
class ExternalInput():
    name: str
    callback: str


@dataclass
class Node():
    name: str
    default_qos: QoS
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

    def add_external_input(
            self,
            callback: Callback,
            name: str | None = None
            ) -> ExternalInput:

        input = ExternalInput(
                name=_name_init(name, self.name, "input", len(self.external_inputs)),
                callback=callback.name
                )
        self.external_inputs.append(input)
        return input

    def add_external_output(self, name: str | None = None) -> ExternalOutput:
        output = ExternalOutput(
                _name_init(name, self.name, "output", len(self.external_outputs)))
        self.external_outputs.append(output)
        return output

    def add_subscription(
            self,
            topic: Topic,
            callback: Callback,
            qos: QoS | dict[str, Any] | None = None
            ) -> Subscription:
        subscription = Subscription(
                topic=topic,
                callback=callback.name,
                qos=_qos_init(qos, self.default_qos)
                )
        self.subscriptions.append(subscription)
        return subscription

    def add_service(
            self,
            callback: Callback,
            name: str | None = None,
            qos: QoS | dict[str, Any] | None = None
            ) -> Service:
        service = Service(
                name=_name_init(name, self.name, "service", len(self.services)),
                callback=callback.name,
                qos=_qos_init(qos, self.default_qos)
                )
        self.services.append(service)
        return service

    def add_client(
            self,
            service: str,
            name: str | None = None,
            qos: QoS | dict[str, Any] | None = None
            ) -> Client:
        client = Client(
                name=_name_init(name, self.name, "client", len(self.clients)),
                service=service,
                qos=_qos_init(qos, self.default_qos)
                )
        self.clients.append(client)
        return client

    def add_callback(
            self,
            wcet: TimeUnit,
            name: str | None = None,
            read_variables: list[Variable] | None = None,
            write_variables: list[Variable] | None = None,
            calls: list[str] | None = None,
            outputs: list[ExternalOutput] | None = None,
            publishers: list[Publisher] | None = None,
            request: Request | None = None
            ) -> Callback:
        callback = Callback(
            name=_name_init(name, self.name, "cb", len(self.callbacks)),
            wcet=wcet,
            read_variables=read_variables,
            write_variables=write_variables,
            calls=calls,
            publishers=[publisher.name for publisher in _empty_list_init(publishers)],
            external_outputs=outputs,
            request=request
            )
        self.callbacks.append(callback)
        return callback

    def add_publisher(
            self,
            topic: Topic,
            name: str | None = None,
            qos: QoS | dict[str, Any] | None = None,
            ) -> Publisher:
        publisher = Publisher(
                name=_name_init(name, self.name, "publisher", len(self.publishers)),
                qos=_qos_init(qos, self.default_qos),
                topic=topic,
                )
        self.publishers.append(publisher)
        return publisher

    def add_timer(
            self,
            period: TimeUnit,
            callback: Callback,
            name: str | None = None,
            offset: TimeUnit = 0,
            ) -> Timer:
        timer = Timer(
                callback=callback.name,
                period=period,
                offset=offset,
                name=_name_init(name, self.name, "timer", len(self.timers))
                )
        self.timers.append(timer)
        return timer

    def add_variable(self, name: str | None = None):
        var = Variable(name=_name_init(name, self.name, "var", len(self.variables)))
        self.variables.append(var)
        return var

    def get_publisher(
            self,
            publisher_name: str
            ) -> Publisher:
        for pub in self.publishers:
            if publisher_name == pub.name:
                return pub
        raise ValueError("Publisher requested is not contained in this node")

    def get_client(
            self,
            client_name: str
            ) -> Client:
        for cli in self.clients:
            if client_name == cli.name:
                return cli
        raise ValueError("Client requested is not contained in this node")
    
    # finds callback-object from the timer-name
    def get_callback(
            self,
            cb_name: str
            ) -> Callback:
        for callback in self.callbacks:
            if callback.name == cb_name:
                return callback
        raise ValueError("Callback requested is not contained in this node")
    
    def get_service(
            self,
            service_name: str
            ) -> Service:
        for serv in self.services:
            if serv.name == service_name:
                return serv
        raise ValueError("Service requested is not contained in this node")
        


@dataclass
class Executor():
    name: str
    ros_distribution: str
    implementation: str
    default_qos: QoS
    nodes: list[Node]

    def add_node(
            self,
            name: str | None = None,
            default_qos: QoS | dict[str, Any] | None = None,
            subscriptions: list[Subscription] | None = None,
            variables: list[Variable] | None = None,
            timers: list[Timer] | None = None,
            services: list[Service] | None = None,
            actions: list[Action] | None = None,
            external_inputs: list[ExternalInput] | None = None,
            callbacks: list[Callback] | None = None,
            publishers: list[Publisher] | None = None,
            clients: list[Client] | None = None,
            external_outputs: list[ExternalOutput] | None = None,
            ) -> Node:

        node = Node(
                name=_name_init(name, self.name, "node", len(self.nodes)),
                subscriptions=_empty_list_init(subscriptions),
                variables=_empty_list_init(variables),
                timers=_empty_list_init(timers),
                services=_empty_list_init(services),
                actions=_empty_list_init(actions),
                external_inputs=_empty_list_init(external_inputs),
                callbacks=_empty_list_init(callbacks),
                publishers=_empty_list_init(publishers),
                clients=_empty_list_init(clients),
                external_outputs=_empty_list_init(external_outputs),
                default_qos=_qos_init(default_qos, self.default_qos)
                )

        self.nodes.append(node)
        return node

    def add_nodes(self, nodenames: list[str]) -> list[Node]:
        return [self.add_node(name=name) for name in nodenames]


@dataclass
class Host():
    name: str
    operating_system: str
    architecture: str
    default_qos: QoS
    default_distribution: str
    executors: list[Executor]

    def add_executor(
            self,
            name: str | None = None,
            implementation: str = DEFAULT_EXECUTOR,
            ros_distribution: str | None = None,
            default_qos: QoS | dict[str, Any] | None = None
            ) -> Executor:

        executor = Executor(
                name=_name_init(name, self.name, "executor", len(self.executors)),
                implementation=implementation,
                nodes=[],
                ros_distribution=
                    self.default_distribution if ros_distribution is None
                    else ros_distribution,
                default_qos=_qos_init(default_qos, self.default_qos))
        self.executors.append(executor)
        return executor

    def add_node(self, name: str | None = None) -> Node:
        executor = self.add_executor()
        return executor.add_node(name)


@dataclass
class System():
    name: str
    dds_implementation: str
    default_qos: QoS
    default_distribution: str
    hosts: list[Host]

    def add_host(
            self,
            name: str | None = None,
            operating_system: str = UNSPECIFIED,
            architecture: str = UNSPECIFIED,
            default_qos: QoS | dict[str, Any]| None = None,
            default_distribution: str | None = None
            ) -> Host:
        host = Host(executors=[],
                    operating_system=operating_system,
                    name=_name_init(name, self.name, "host", len(self.hosts)),
                    architecture=architecture,
                    default_qos=_qos_init(default_qos, self.default_qos),
                    default_distribution=
                        self.default_distribution if default_distribution is None
                        else default_distribution
                    )
        self.hosts.append(host)
        return host

    def __init__(
            self,
            name: str,
            dds_implementation: str = UNSPECIFIED,
            default_qos: QoS | dict[str, Any] | None = None,
            default_distribution: str = DEFAULT_DISTRIBUTION
            ):

        self.name = name
        self.hosts = []
        self.dds_implementation = dds_implementation
        self.default_qos = _qos_init(default_qos, DEFAULT_QOS)
        self.default_distribution = default_distribution

