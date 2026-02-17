import roserer.ros2system as ros
import roserer.qos as qos

"""
A ros2 system model consists of
Hosts
Variables
ExternalOutputs

TODO: Make dicts to map executors to distributions (check for age)
      and operating systems to architectures
TODO: Check if QOS policies are compatible between offer and request
TODO: Add operating system versions
TODO: Consider adding uniqueness checks to all lists
      (that they are essentially sets)
    # consider checking for infinite recursion in main validator
    # callbacks calling each other in cycles
TODO: Make constant dicts into enums in separate package

"""

# ==================== CONSTANTS ===================================

DDS_IMPLEMENTATIONS = [
    "Generic",
    "Cyclone",
    "Fast",
    "RTI Connext",
    "Gurum"
]

EXECUTORS = [
    "SingleThreadedExecutor",
    "MultiThreadedExecutor",
    "StaticSingleThreadedExecutor",
    "EventsExecutor"
]

OPERATING_SYSTEMS = [
    "Generic",
    "Windows",
    "Debian",
    "MacOS",
    "Ubuntu",
    "OpenEmbedded"
]

ARCHITECTURES = [
    "Generic",
    "amd64",
    "arm64",
    "arm32"
]

DISTRIBUTIONS = [
    "Rolling",
    "Kilted",
    "Jazzy",
    "Iron",
    "Humble",
    "Galactic",
    "Foxy",
    "Eloquent",
    "Dashing",
    "Crystal",
    "Bouncy",
    "Ardent",
    "Rolling Ridley",
    "Kilted Kaiju",
    "Jazzy Jalisco",
    "Iron Irwini",
    "Humble Hawksbill",
    "Galactic Geochelone",
    "Foxy Fitzroy",
    "Eloquent Elusor",
    "Dashing Diademata",
    "Crystal Clemmys",
    "Bouncy Bolson",
    "Ardent Apalone"
]

# See rmw/rmw/src/qos_string_conversions.c
# TODO: Delete this, it is unnescessary
QOS = {
    "history": ["system_default", "keep_last", "keep_all"],
    "depth": int,
    "reliability": ["system_default", "best_available",
                    "reliable", "best_effort"],
    "durability": ["system_default", "best_available",
                   "volatile", "transient_local"],
    "deadline": int,
    "lifespan": int,
    "liveliness": ["automatic", "manual_by_topic",
                   "system_default", "best_available"],
    "liveliness_lease_duration": int
}

VALID_VALUES = {
    "dds": DDS_IMPLEMENTATIONS,
    "distribution": DISTRIBUTIONS,
    "os": OPERATING_SYSTEMS,
    "architecture": ARCHITECTURES,
    "executor": EXECUTORS,
}


"""
Each attribute corresponds to an object-type and contains a dict that maps the name of an object of that type
to the name of it's containing object / parent.
Example:
    Containments(
    node: {
        'node1': Executor(name='executor1', ...),
        ...
        },
    ...
    callback: {
        'callback1': Node(name='node1'),
        ...
        },
    ...
    )
"""

class Containments:
    host            : dict[str,ros.System]
    executor        : dict[str,ros.Host]
    node            : dict[str,ros.Executor]
    callback        : dict[str,ros.Node]
    external_input  : dict[str,ros.Node]
    external_output : dict[str,ros.Node]
    timer           : dict[str,ros.Node]
    service         : dict[str,ros.Node]
    client          : dict[str,ros.Node]
    variable        : dict[str,ros.Node]
    publisher       : dict[str,ros.Node]
    subscription    : dict[str,ros.Node]
    action          : dict[str,ros.Node]

    def __init__(self):
        self.host = {}
        self.executor = {}
        self.node = {}
        self.callback = {}
        self.external_input = {}
        self.external_output = {}
        self.timer = {}
        self.service = {}
        self.client = {}
        self.variable = {}
        self.publisher = {}
        self.subscription = {}
        self.action = {}

"""
Type for named ROS2-objects. To be used for annotations
"""
NamedROSObject = ros.System | ros.Host | ros.Executor | ros.Node | ros.Callback | ros.ExternalInput \
 | ros.ExternalOutput | ros.Timer | ros.Service | ros.Client | ros.Variable | ros.Publisher | ros.Action

"""
Each entry maps an type of interface to a dict that maps the name of an interface to a
list of names of object that engage in that interface.
The interface types are directional.
Example:
    {
    'topic published to': {
        'topic1': [
            'callback1',
            ...
            ],
        ...
        }
    ...
    'topic subscribed to': {
        'topic1': [
            'callback2',
            ...
            ],
        ...
        }
    }
"""
Interfaces = dict[str, dict[str, list[str]]]

Graph = dict[str, list[str]]

# ==================== FUNCTIONS ===================================

def is_valid_value(typ: str, val: str) -> list[str]:

    if val not in VALID_VALUES[typ]:
        return [f"{typ} '{val}' not among {VALID_VALUES[typ]}"]
    else:
        return []


def register(
        object_name: str,
        object_type: str,
        parent: NamedROSObject, 
        objects: Containments
        ) -> list[str]:
    if (object_name is None) or (object_name == ""):
        return [f"{object_type} owned by {parent.name} is missing name. "
                "Skipping validation of branch."]
    elif object_name in getattr(objects, object_type):
        return [f"{object_type} '{object_name}' has multiple owners, "
                f"or name is not unique among {object_type}s. "
                "Skipping validation of branch."]
    else:
        getattr(objects, object_type)[object_name] = parent
        return []


def verify_registration(
        object_name: str,
        object_type: str,
        parent: NamedROSObject,
        expector: str,
        objects: Containments
        ) -> list[str]:
    if object_name not in getattr(objects, object_type):
        return [f"Even though {expector} expected so, {object_type} "
                f"'{object_name}' is not registered to any parent."]
    elif parent != getattr(objects, object_type)[object_name]:
        return [f"Even though {expector} expected so, {object_type} "
                f"'{object_name}' is not contained within the parent "
                f"'{parent.name}'"]
    else:
        return []


def subset_check(key1: str, key2: str, sets: dict[str, dict]) -> list[str]:
    keyset1 = sets[key1].keys()
    keyset2 = sets[key2].keys()
    if keyset1 <= keyset2:
        return []
    else:
        return [f"Mismatched: Some {key1} are not among {key2}"]

def add_interface(
        name: str,
        container_name: str,
        typ: str,
        interface_type: str,
        interfaces: Interfaces
        ) -> list[str]:
    """
    Checks if the name is not empty.
    Registers the name inside the interfaces dict.
    This is done to create a global, nonhierarchical overview of which topics,
    services, etc. are read from and written to, such that it can be checked
    at the end if any nodes read from a communication interface that no node
    writes to.
    """
    if (name is None) or (name == ""):
        return [f"{typ} inside '{container_name}' is missing name."]
    else:
        interfaces[interface_type].setdefault(name, [])
        interfaces[interface_type][name].append(container_name)
        return []


# ==================== RESULT ======================================


def check_for_cycles(
        graph: Graph,
        sources: list[str]
        ) -> bool:
    
    to_visit = set(graph.keys())
    visited: list[str] = []

    def visit(cb):
        if cb not in to_visit:
            return False
        if cb in visited:
            return True
        visited.append(cb)
        dependents = graph[cb] + graph[cb]
        for dep in dependents:
            if visit(dep):
                return True
        to_visit.remove(cb)

    for s in sources:
        if visit(s):
            return True

    return False


def make_callback_graph(
        objects: Containments,
        interfaces: Interfaces
        ) -> tuple[Graph, set[str], set[str]]:
    callbacks = set(objects.callback.keys())
    sources = callbacks.copy()
    sinks = callbacks.copy()
    graph: Graph = {}
    publishers = interfaces["topics published to"]
    subscribers = interfaces["topics subscribed to"]
    readers = interfaces["variables read from"]
    writers = interfaces["variables written to"]
    # for services
    request_senders = interfaces["services requested"]
    servers = interfaces["services offered"]
    request_receivers = interfaces["services received from"]


    def visit(match, outputs, inputs):
        for channel in outputs:
            for outputter in outputs[channel]:
                if outputter == match:
                    receivers = inputs.get(channel)
                    if receivers is not None:
                        sinks.discard(match)
                        sources.difference_update(receivers)
                        graph[cb] += receivers

    for cb in callbacks:
        if cb in graph:
            continue
        graph[cb] = []
        visit(cb, publishers, subscribers)
        visit(cb, writers, readers)
        visit(cb, request_senders, servers)
        visit(cb, servers, request_receivers)

    return graph, sources, sinks


def get_paths_from(
        graph: Graph,
        source: str,
        target: str
        ) -> list[list[str]]:
    next = [(source, [source])]
    paths = []

    if check_for_cycles(graph, [source]):
        raise Exception(f"There is a cycle in the graph from {source} callback, "
                        "cannot find chains")

    while len(next) > 0:
        current, path = next.pop()
        if current == target:
            paths.append(path)
            continue
        nexts = graph[current]
        for n in nexts:
            next.append((n, path + [n]))

    return paths


class ValidationResult():
    errors: list[str]
    interfaces: Interfaces
    objects: Containments
    graph: Graph | None
    sources: set[str] | None
    sinks: set[str] | None

    def __init__(
            self,
            errors: list[str],
            interfaces: Interfaces,
            objects: Containments
            ) -> None:
        self.errors = errors
        self.interfaces = interfaces
        self.objects = objects
        if errors != []:
            self.graph = None
            self.sources = None
            self.sinks = None
        else:
            graph, sources, sinks = make_callback_graph(objects, interfaces)
            self.graph = graph
            self.sources = sources
            self.sinks = sinks

    def get_paths_from(self, source: str, target: str) -> list[list[str]]:
        if self.graph is None:
            raise ValueError("ValidationResult does not have graph")
        return get_paths_from(self.graph, source, target)

    def get_all_cb_chains(self) -> list[list[str]]:
        chains = []
        if self.sources is None or self.sinks is None:
            return chains
        for source in self.sources:
            for sink in self.sinks:
                chains += self.get_paths_from(source, sink)
        return chains


# ==================== VALIDATORS ===================================


def validate_qos(qos: qos.QoS, parent: str) -> list[str]:
    """
    Notice that deadline and lifespan are not used in any models currently
    """
    feedback = []
    if qos.depth < 0:
        feedback += [f"{parent} has invalid qos depth policy"]
    # TODO create proper comparison functions for durations
    # Not a current priority, because they are unused
    if qos.deadline < (0, 0):
        feedback += [f"{parent} has invalid qos deadline policy"]
    if qos.lifespan < (0, 0):
        feedback += [f"{parent} has invalid qos lifespan policy"]
    if qos.liveliness_lease_duration < (0, 0):
        feedback += [
            f"{parent} has invalid qos liveliness_lease_duration policy"]
    return feedback


def validate_client(
        client: ros.Client,
        parent: ros.Node,
        objects: Containments, 
        interfaces: Interfaces
        ) -> list[str]:
    """
    A client is well formed if:
    - It has a name
    - It is only owned by one node
    - It has a valid quality of service profile
    - It names the service it requests
    """
    feedback = register(client.name, "client", parent, objects)
    if feedback != []:
        return feedback

    feedback += validate_qos(client.qos, client.name)


    return feedback


def validate_publisher(
        publisher: ros.Publisher, 
        parent: ros.Node,
        objects: Containments, 
        interfaces: Interfaces
        ) -> list[str]:
    """
    A publisher is well formed if:
    - It has a name
    - It is only owned by one node
    - It has a valid quality of service profile
    - It names the topic it publishes to
    """

    feedback = register(publisher.name, "publisher", parent, objects)
    if feedback != []:
        return feedback

    feedback += validate_qos(publisher.qos, publisher.name)

    return feedback


def validate_callback(
        callback: ros.Callback,
        parent: ros.Node,
        objects: Containments, 
        interfaces: Interfaces
        ) -> list[str]:
    """
    A callback is well formed if:
    - It has a name
    - It is only owned by one node
    - It only uses publishers owned by the parent node
    - It only reads and writes to variables owned by the parent node
    - It only outputs to external outputs owned by the parent node
    - It has a valid wcet
    - It satisfies the invariants listed in validate_callback_references
    """
    feedback = register(callback.name, "callback", parent, objects)
    if feedback != []:
        return feedback
    name = callback.name
    for publisher in callback.publishers:
        feedback += verify_registration(
            publisher, "publisher", parent, name, objects)
        feedback += add_interface(parent.get_publisher(publisher).topic, name,
                                  "topic", "topics published to", interfaces)
    for read in callback.read_variables:
        read: ros.Variable
        feedback += verify_registration(
            read.name, "variable", parent, name, objects)
        feedback += add_interface(read.name, name, "variable",
                                  "variables read from", interfaces)
    for write in callback.write_variables:
        write: ros.Variable
        feedback += verify_registration(
            write.name, "variable", parent, name, objects)
        feedback += add_interface(write.name, name, "variable",
                                  "variables written to", interfaces)
    for output in callback.external_outputs:
        feedback += verify_registration(
            output.name, "external_output", parent, name, objects)
    if callback.wcet < 0:
        feedback += [f"Callback '{name}' has a negative wcet"]

    return feedback

def validate_callback_references(
        callback: ros.Callback,
        parent: ros.Node,
        objects: Containments, 
        interfaces: Interfaces
        ) -> list[str]:
    """
    A callback is well formed, with respect to its references to other callbacks, if:
    - it's calls only refers to vaild callbacks owned by the parent node
    - Any request refer to a client owned by the parent node
    - Any response to a request refers to a defined, valid callback
    """
    feedback = []
    name = callback.name
    for called_name in callback.calls:
           feedback += verify_registration(
                   called_name, "callback", parent, name, objects)
    if callback.request is not None:
            request = callback.request
            feedback += verify_registration(
                request.client, "client", parent, name, objects)
            feedback += verify_registration(
            request.response, "callback", parent, name, objects)
            feedback += add_interface(
                parent.get_client(request.client).service,
                name, "Requesting client", "services requested", interfaces)
            # add's the response-callback to the interfaces-dict also
            feedback += add_interface(
                parent.get_client(request.client).service,
                request.response, "Responding client", "services received from", interfaces)
    return feedback

# TODO : adapt to how external_input is structured now
def validate_input(
        input: ros.ExternalInput,
        parent: ros.Node,
        objects: Containments,
        interfaces: Interfaces
        ) -> list[str]:
    """
    An external input is well formed if:
    - It has a name
    - It is only owned by one node
    - It calls a callback that is owned by the same node
    """
    feedback = register(input.name, "external_input", parent, objects)
    if feedback != []:
        return feedback
    if isinstance(input.source, ros.Subscription):
        verify_registration(input.source.name, "subscription",
                            parent, input.name, objects)
    elif isinstance(input.source, ros.Service):
        verify_registration(input.source.name, "service",
                            parent, input.name, objects)
    else:
        feedback += [f"source is not an acceptable type. Make sure it is \
                     either a Subscription or a Service"]
    # TODO: check that values in wall_times are appropriate!!!
    return feedback


def validate_subscription(
        subscription: ros.Subscription,
        parent: ros.Node,
        objects: Containments,
        interfaces: Interfaces
        ) -> list[str]:
    """
    A subscription is well formed if:
    - It has a name
    - It has a valid quality of service profile
    - It names the topic it subscribes to
    - It calls a callback that is owned by the same node
    """
    pname = parent.name
    feedback = []
    feedback = register(subscription.name, "subscription", parent, objects)
    if feedback != []:
        return feedback
    feedback += validate_qos(subscription.qos, pname)
    feedback += add_interface(subscription.topic, subscription.callback,
                              "Topic", "topics subscribed to", interfaces)
    feedback += verify_registration(subscription.callback,
                                    "callback", parent, pname, objects)

    return feedback


def validate_timer(
        timer: ros.Timer,
        parent: ros.Node,
        objects: Containments, 
        interfaces: Interfaces
        ) -> list[str]:
    """
    A timer is well formed if:
    - It has a name
    - It is only owned by one node
    - It has a valid period
    - It calls a callback that is owned by the same node
    """
    feedback = register(timer.name, "timer", parent, objects)
    if feedback != []:
        return feedback

    if timer.period < 0:
        feedback += [f"Timer '{timer.name}' must not have a negative period"]

    feedback += verify_registration(timer.callback, "callback",
                                    parent, timer.name, objects)

    return feedback


def validate_service(
        service: ros.Service,
        parent: ros.Node,
        objects: Containments,
        interfaces: Interfaces
        ) -> list[str]:
    """
    A service is well formed if:
    - It has a name
    - It is only owned by one node
    - It has a valid quality of service profile
    - It calls a callback that is owned by the same node
    """

    feedback = register(service.name, "service", parent, objects)
    if feedback != []:
        return feedback

    feedback += validate_qos(service.qos, service.name)
    feedback += add_interface(service.name, service.callback, "service",
                              "services offered", interfaces)
    feedback += verify_registration(service.callback, "callback",
                                    parent, service.name, objects)

    return feedback


def validate_action(action: ros.Action, parent: ros.Node) -> list[str]:
    """
    TODO
    """
    return []


def validate_node(
        node: ros.Node,
        parent: ros.Executor,
        objects: Containments,
        interfaces: Interfaces
        ) -> list[str]:
    """
    A node is well formed if:
    - It has a name
    - It is only owned by one executor
    - It has at least one trigger
    - It has at least one callback
    - All variables have names
    - All variables are only owned by this node
    - All external outputs have names
    - All external outputs are only owned by this callback

    - All contained items are well formed:
        - External inputs
        - Services
        - Subscriptions
        - Actions
        - Timers
        - Actions (TODO)
        - Clients
        - Publishers
        - Callbacks

    - All callbacks only call callbacks that are also owned by this node
    - All publishers are used by at least one callback
    """
    feedback = register(node.name, "node", parent, objects)
    if feedback != []:
        return feedback

    # outputs
    for client in node.clients:
        feedback += validate_client(client, node, objects, interfaces)
    for publisher in node.publishers:
        feedback += validate_publisher(publisher, node, objects, interfaces)

    # internal
    for variable in node.variables:
        feedback += register(variable.name, "variable", node, objects)
    for output in node.external_outputs:
        feedback += register(output.name, "external_output", node, objects)
    if len(node.callbacks) < 1:
        feedback += f"Node '{node.name}' must have at least one callback"
    for callback in node.callbacks:
        feedback += validate_callback(callback, node, objects, interfaces)

    total_triggers = 0
    for subscription in node.subscriptions:
        feedback += validate_subscription(subscription, node, objects, interfaces)
        total_triggers += 1
    for timer in node.timers:
        feedback += validate_timer(timer, node, objects, interfaces)
        total_triggers += 1
    for service in node.services:
        feedback += validate_service(service, node, objects, interfaces)
        total_triggers += 1
    for action in node.actions:
        validate_action(action, node)  # TODO: Add support for actions
        total_triggers += 1
    for input in node.external_inputs:
        feedback += validate_input(input, node, objects, interfaces)
        total_triggers += 1
    if total_triggers < 1:
        feedback += f"Node '{node.name}' must have at least one trigger"

    # one more iteration for validating (potential) references to other callbacks
    for callback in node.callbacks:
        validate_callback_references(callback, node, objects, interfaces)

    used_publishers = [publisher for publisher in
                       callback.publishers for callback in node.callbacks]
    for publisher in node.publishers:
        if publisher.name not in used_publishers:
            feedback += [f"Publisher '{publisher.name}' inside node '{node.name}' "
                         "is unused"]
    return feedback


def validate_executor(
        executor: ros.Executor,
        parent: ros.Host,
        objects: Containments,
        interfaces: Interfaces
        ) -> list[str]:
    """
    An executor is well formed if:
    - It has a name
    - It is only owned by one host
    - It has a valid ros distribution
    - It has a valid executor implementation
    - It has at least one node
    - All nodes are well formed
    """
    feedback = register(executor.name, "executor", parent, objects)
    if feedback != []:
        return feedback

    feedback += is_valid_value("distribution", executor.ros_distribution)
    feedback += is_valid_value("executor", executor.implementation)

    if len(executor.nodes) < 1:
        feedback += [f"Executor '{executor.name}' must have at least one node"]

    for node in executor.nodes:
        feedback += validate_node(node, executor, objects, interfaces)
    return feedback


def validate_host(
        host: ros.Host,
        parent: ros.System,
        objects: Containments, 
        interfaces: Interfaces
        ) -> list[str]:
    """
    A host is well formed if:
    - It has a name
    - It has a valid operating system
    - It has a valid architecture
    - It has at least one executor
    - All executors are well formed
    """
    feedback = register(host.name, "host", parent, objects)
    if feedback != []:
        return feedback

    feedback += is_valid_value("os", host.operating_system)
    feedback += is_valid_value("architecture", host.architecture)

    executors = host.executors
    if len(executors) < 1:
        feedback += [f"Host '{host.name}' must have at least one executor"]

    for executor in executors:
        feedback += validate_executor(executor, host, objects, interfaces)
    return feedback


def validate_system(system: ros.System) -> ValidationResult:
    """
    A system is well formed if:
    - It has a name
    - It has a valid dds
    - It has at least one host
    - All hosts are well formed
    - There is a server offering each service that a client requests
    - There is a publisher to each topic that a subscriber subscribes to
    """
    feedback: list[str] = []

    interfaces: Interfaces = {
        "services requested": {},
        "services offered": {},
        "services received from": {},
        "topics subscribed to": {},
        "topics published to": {},
        "variables written to": {},
        "variables read from": {},
    }

    objects: Containments = Containments()

    if (system.name is None) or (system.name == ""):
        feedback += ["System must have a name"]

    feedback += is_valid_value("dds", system.dds_implementation)

    hosts = system.hosts
    if len(hosts) < 1:
        feedback += ["System must have at least one host"]
    for host in hosts:
        feedback += validate_host(host, system, objects, interfaces)
    feedback += subset_check("services requested", "services offered", interfaces)
    feedback += subset_check("topics subscribed to", "topics published to", interfaces)

    return ValidationResult(errors=feedback, objects=objects, interfaces=interfaces)
