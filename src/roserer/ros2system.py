from typing import Any, TypeVar, Protocol
from dataclasses import dataclass
from roserer.qos import QoS, qos_profile_default
from roserer.types import (
        EXECUTOR, DISTRIBUTION, ARCHITECTURE, OPERATING_SYSTEM, DDS_IMPLEMENTATION,
        TimeUnit)

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

class HasName(Protocol):
    name: str

N = TypeVar("N", bound=HasName)

def _stringify_list(x: list[N] | list[str] | None) -> list[str]:
    out: list[str] = []
    if x is not None:
        for e in x:
            if isinstance(e, str):
                out.append(e)
            else:
                out.append(e.name)
    return out

def _name_init(name: str | None, parent: str, type: str, position: int) -> str:
    if name is None:
        return parent + "_" + type + str(position)
    else:
        return name

Topic = str

@dataclass
class Variable:
    name: str
    reset_after_read: bool
    condition: bool

@dataclass
class ExternalOutput:
    name: str

@dataclass
class Timer():
    name: str
    period: int
    offset: int
    end: int | None
    probability: int
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
    wcet: int
    bcet: int
    read_variables: list[str]
    write_variables: list[str]
    calls: str | None
    publishers: list[str]
    external_outputs: list[str]
    request: Request | None

    def __init__(
            self,
            name: str,
            wcet: int,
            bcet: int | None = None,
            read_variables: list[Variable] | list[str] | None = None,
            write_variables: list[Variable] | list[str] | None = None,
            calls: str | None = None,
            external_outputs: list[ExternalOutput] | list[str] | None = None,
            publishers: list[Publisher] | list[str] | None = None,
            request: Request | None = None
            ) -> None:
        self.name = name
        if bcet is None:
            bcet = wcet
        self.wcet = wcet
        self.bcet = bcet
        # TODO: Move to parser
        self.read_variables = _stringify_list(read_variables)
        self.write_variables = _stringify_list(write_variables)
        self.publishers = _stringify_list(publishers)
        self.external_outputs = _stringify_list(external_outputs)
        self.calls = calls
        self.request = request

@dataclass
class Subscription():
    name : str
    topic: Topic
    callback: str
    qos: QoS
    # TODO: Can we convert "wall times" into external input?
    wall_times: list[int] | None

@dataclass
class Service():
    name: str
    callback: str
    qos: QoS
    # TODO: Can we convert "wall times" into external input?
    wall_times: list[int] | None

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
            callback: Callback | str,
            name: str | None = None,
            qos: QoS | dict[str, Any] | None = None,
            wall_times: list[int] | None = None
            ) -> Subscription:
        if isinstance(callback, str):
            callback = self.get_callback(callback)
        subscription = Subscription(
                name=_name_init(name, 
                                self.name,
                                "subscription",
                                len(self.subscriptions)
                                ),
                topic=topic,
                callback=callback.name,
                qos=_qos_init(qos, self.default_qos),
                wall_times=wall_times
                )
        self.subscriptions.append(subscription)
        return subscription

    def add_service(
            self,
            callback: Callback,
            name: str | None = None,
            qos: QoS | dict[str, Any] | None = None,
            wall_times: list[int] | None = None
            ) -> Service:
        service = Service(
                name=_name_init(name, self.name, "service", len(self.services)),
                callback=callback.name,
                qos=_qos_init(qos, self.default_qos),
                wall_times=wall_times
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
            wcet: int,
            name: str | None = None,
            bcet: int | None = None,
            read_variables: list[str] | list[Variable] | None = None,
            write_variables: list[str] | list[Variable] | None = None,
            calls: str | None = None,
            outputs: list[str] | list[ExternalOutput] | None = None,
            publishers: list[str] | list[Publisher] | None = None,
            request: Request | None = None
            ) -> Callback:

        callback = Callback(
            name=_name_init(name, self.name, "cb", len(self.callbacks)),
            wcet=wcet,
            bcet=bcet,
            read_variables=read_variables,
            write_variables=write_variables,
            calls=calls,
            external_outputs=outputs,
            publishers=publishers,
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
            period: int,
            callback: Callback | str,
            name: str | None = None,
            offset: int = 0,
            end: int | None = None,
            probability: int = 100
            ) -> Timer:
        if probability < 0 or probability > 100:
            raise ValueError("Probability must be expressed as a number from 0 to 100")
        if isinstance(callback, str):
            callback = self.get_callback(callback)
        timer = Timer(
                callback=callback.name,
                period=period,
                offset=offset,
                name=_name_init(name, self.name, "timer", len(self.timers)),
                end=end,
                probability=probability
                )
        self.timers.append(timer)
        return timer

    def add_variable(
            self, 
            name: str | None = None,
            reset_after_read: bool = False,
            condition: bool = False
            ) -> Variable:
        var = Variable(
                name=_name_init(name, self.name, "var", len(self.variables)),
                reset_after_read=reset_after_read,
                condition=condition
                )
        self.variables.append(var)
        return var

    def get_publisher(self, name: str) -> Publisher:
        for pub in self.publishers:
            if name == pub.name:
                return pub
        raise ValueError(f"Publisher {name} requested is not contained in the node {self.name}")

    def get_client(self, client_name: str) -> Client:
        for cli in self.clients:
            if client_name == cli.name:
                return cli
        raise ValueError("Client requested is not contained in this node")
    
    # finds callback-object from the timer-name
    def get_callback(self, cb_name: str) -> Callback:
        for callback in self.callbacks:
            if callback.name == cb_name:
                return callback
        raise ValueError("Callback requested is not contained in this node")
    
    def get_service(self, service_name: str) -> Service:
        for serv in self.services:
            if serv.name == service_name:
                return serv
        raise ValueError("Service requested is not contained in this node")
    
    def get_subscription(self, sub_name: str) -> Subscription:
        for sub in self.subscriptions:
            if sub.name == sub_name:
                return sub
        raise ValueError("Subscription requested is not contained in this node")

    # gets sum of wcet of nested calls
    def full_wcet(self, cb: str | Callback) -> int:
        if isinstance(cb, str):
            cb = self.get_callback(cb)
        elif cb not in self.callbacks:
                raise ValueError("Callback is not contained in this node")
        cb: Callback
        wcet = cb.wcet
        while cb.calls is not None:
            nested_cb = self.get_callback(cb.calls)
            cb = nested_cb
            wcet += cb.wcet
        return wcet

@dataclass
class Executor():
    name: str
    ros_distribution: DISTRIBUTION
    implementation: EXECUTOR
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
    operating_system: OPERATING_SYSTEM
    architecture: ARCHITECTURE
    default_qos: QoS
    default_distribution: DISTRIBUTION
    executors: list[Executor]

    DEFAULT_EXECUTOR = EXECUTOR.SingleThreadedExecutor

    def add_executor(
            self,
            name: str | None = None,
            implementation: EXECUTOR = DEFAULT_EXECUTOR,
            ros_distribution: DISTRIBUTION | None = None,
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
    dds_implementation: DDS_IMPLEMENTATION
    default_qos: QoS
    default_distribution: DISTRIBUTION
    default_time_unit: TimeUnit
    hosts: list[Host]

    DEFAULT_DISTRIBUTION = DISTRIBUTION.Rolling
    GENERIC_ARCHITECTURE = ARCHITECTURE.Generic
    GENERIC_OPERATING_SYSTEM = OPERATING_SYSTEM.Generic
    GENERIC_DDS = DDS_IMPLEMENTATION.Generic
    DEFAULT_QOS = qos_profile_default()

    def add_host(
            self,
            name: str | None = None,
            operating_system: OPERATING_SYSTEM = GENERIC_OPERATING_SYSTEM,
            architecture: ARCHITECTURE = GENERIC_ARCHITECTURE,
            default_qos: QoS | dict[str, Any] | None = None,
            default_distribution: DISTRIBUTION | None = None
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

    def get_nodes(self)->list[Node]:
        """ returns list of all nodes in system """
        return [node 
                for host in self.hosts
                for executor in host.executors
                for node in executor.nodes]
    
    def get_node(self, node_name)-> Node:
        """ returns node with name 'node_name'. 
        Raises error if no node with given name present """
        n =  next((node for node in self.get_nodes() if node.name == node_name), None)
        if n is None:
            raise ValueError(f"Node with name, {node_name}, doesn't exist in this system.")
        return n


    def get_subscriptions(self)->list[Subscription]:
        """ returns list of all subscriptions in system """
        return [subscription
                for node in self.get_nodes()
                for subscription in node.subscriptions]
    
    def get_services(self)->list[Service]:
        """ returns list of all services in system """
        return [service
                for node in self.get_nodes()
                for service in node.services]
    
    def get_timers(self)->list[Timer]:
        """ returns list of all timers in system """
        return [timer
                for node in self.get_nodes()
                for timer in node.timers]

    def get_callbacks(self) -> list[Callback]:
        """Return all callbacks in the system"""
        return [cb for node in self.get_nodes() for cb in node.callbacks]

    def get_publishers(self) -> list[Publisher]:
        return [pub for node in self.get_nodes() for pub in node.publishers]

    def get_clients(self) -> list[Client]:
        return [client for node in self.get_nodes() for client in node.clients]

    def get_qos_profiles(self) -> list[tuple[QoS,str]]:
        """Get each qos profile and the name of the object to which it belongs"""
        return ([(pub.qos, pub.name) for pub in self.get_publishers()]
                + [(client.qos, client.name) for client in self.get_clients()]
                + [(sub.qos, sub.name) for sub in self.get_subscriptions()]
                + [(service.qos, service.name) for service in self.get_services()]
                # TODO: Add actions when implemented
                )
    def get_hosts(self) -> list[Host]:
        return self.hosts

    def get_executors(self) -> list[Executor]:
        return [executor for host in self.hosts for executor in host.executors]

    def get_external_inputs(self) -> list[ExternalInput]:
        return [inp for node in self.get_nodes() for inp in node.external_inputs]

    def get_external_outputs(self) -> list[ExternalOutput]:
        return [outp for node in self.get_nodes() for outp in node.external_outputs]

    def get_variables(self) -> list[Variable]:
        return [var for node in self.get_nodes() for var in node.variables]

    def get_actions(self) -> list[Action]:
        return [act for node in self.get_nodes() for act in node.actions]

    def __init__(
            self,
            name: str,
            dds_implementation: DDS_IMPLEMENTATION = GENERIC_DDS,
            default_qos: QoS | dict[str, Any] | None = None,
            default_distribution: DISTRIBUTION = DEFAULT_DISTRIBUTION,
            default_time_unit: TimeUnit = TimeUnit.UNSPECIFIED
            ):
        self.name = name
        self.hosts = []
        self.dds_implementation = dds_implementation
        self.default_qos = _qos_init(default_qos, self.DEFAULT_QOS)
        self.default_distribution = default_distribution
        self.default_time_unit = default_time_unit

