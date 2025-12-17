import ros2system as ros

"""
A ros2 system model consists of
Hosts
Variables
ExternalOutputs

TODO: Make dicts to map executors to distributions (check for age)
      and operating systems to architectures
TODO: Check if QOS policies are compatible between offer and request
TODO: Add operating system versions

"""

DDS_IMPLEMENTATIONS = [
    "Generic",
    "Cyclone",
    "Fast",
    "RTI connext",
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


def is_valid_value(typ: str, val: str) -> list[str]:

    if val not in VALID_VALUES[typ]:
        return [f"{typ} '{val}' not among {VALID_VALUES[typ]}"]
    else:
        return []


def register(object_name, object_type: str,
             parent_name: str, objects) -> list[str]:
    if (object_name is None) or (object_name == ""):
        return [f"{object_type} owned by {parent_name} is missing name. "
                "Skipping validation of branch."]
    elif object_name in objects[object_type]:
        return [f"{object_type} '{object_name}' has multiple owners, "
                f"or name is not unique among {object_type}s. "
                "Skipping validation of branch."]
    else:
        objects[object_type][object_name] = parent_name
        return []


def verify_registration(object_name: str, object_type: str,
                        parent_name: str, expector: str, objects) -> list[str]:
    if object_name not in objects[object_type]:
        return [f"Even though {expector} expected so, {object_type} "
                f"'{object_name}' is not registered to any parent."]
    elif parent_name != objects[object_type][object_name]:
        return [f"Even though {expector} expected so, {object_type} "
                f"'{object_name}' is not contained within the parent "
                f"'{parent_name}'"]
    else:
        return []


def subset_check(key1: str, key2: str, sets) -> list[str]:
    keyset1 = sets[key1].keys()
    keyset2 = sets[key2].keys()
    if keyset1 <= keyset2:
        return []
    else:
        return [f"Mismatched: Some {key1} are not among {key2}"]


def validate_qos(qos: ros.QualityOfService, parent: str) -> list[str]:
    feedback = []
    if qos["history"] not in QOS["history"]:
        feedback += [f"{parent} has invalid qos history policy"]
    if qos["depth"] < 0:
        feedback += [f"{parent} has invalid qos depth policy"]
    if qos["reliability"] not in QOS["reliability"]:
        feedback += [f"{parent} has invalid qos reliability policy"]
    if qos["durability"] not in QOS["durability"]:
        feedback += [f"{parent} has invalid qos durability policy"]
    if qos["deadline"] < 0:
        feedback += [f"{parent} has invalid qos deadline policy"]
    if qos["lifespan"] < 0:
        feedback += [f"{parent} has invalid qos lifespan policy"]
    if qos["liveliness"] not in QOS["liveliness"]:
        feedback += [f"{parent} has invalid qos liveliness policy"]
    if qos["liveliness_lease_duration"] < 0:
        feedback += [
            f"{parent} has invalid qos liveliness_lease_duration policy"]
    return feedback


def add_interface(name: str, container_name: str,
                  typ: str, interface_type: str, interfaces):
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


def validate_client(client: ros.Client, parent: ros.Node,
                    objects, interfaces) -> list[str]:
    """
    A client is well formed if:
    - It has a name
    - It is only owned by one node
    - It has a valid quality of service profile
    - It names the service it requests
    """
    feedback = register(client.name, "client", parent.name, objects)
    if feedback != []:
        print(feedback)
        return feedback

    feedback += validate_qos(client.qos_profile, client.name)
    feedback += add_interface(client.service, client.name,
                              "Service", "services requested", interfaces)

    return feedback


def validate_publisher(publisher: ros.Publisher, parent: ros.Node,
                       objects, interfaces) -> list[str]:
    """
    A publisher is well formed if:
    - It has a name
    - It is only owned by one node
    - It has a valid quality of service profile
    - It names the topic it publishes to
    """

    feedback = register(publisher.name, "publisher", parent.name, objects)
    if feedback != []:
        return feedback

    feedback += validate_qos(publisher.qos_offered, publisher.name)
    feedback += add_interface(publisher.topic, publisher.name,
                              "topic", "topics published to", interfaces)

    return feedback


def validate_callback(callback: ros.Callback, parent: ros.Node,
                      objects, interfaces) -> list[str]:
    """
    A callback is well formed if:
    - It has a name
    - It is only owned by one node
    - It only uses publishers owned by the parent node
    - It only reads and writes to variables owned by the parent node
    - It only outputs to external outputs owned by the parent node
    - All requests have a valid timeout
    - All requests refer to a client owned by the parent node
    - It has a valid wcet
    """
    feedback = register(callback.name, "callback", parent.name, objects)
    if feedback != []:
        return feedback
    name = callback.name
    pname = parent.name
    for publisher in callback.publishers:
        feedback += verify_registration(
            publisher, "publisher", pname, name, objects)
    for read in callback.read_variables:
        feedback += verify_registration(
            read.name, "variable", pname, name, objects)
    for write in callback.write_variables:
        feedback += verify_registration(
            write.name, "variable", pname, name, objects)
    for output in callback.external_outputs:
        feedback += verify_registration(
            output.name, "external_output", pname, name, objects)
    for request in callback.requests:
        feedback += verify_registration(
            request.client.name, "client", pname, name, objects)
        if request.timeout < 0:
            feedback += [
                f"A request of callback '{name}' has a negative timeout."]
    if callback.wcet < 0:
        feedback += [f"Callback '{name}' has a negative wcet"]

    return feedback


def validate_input(input: ros.ExternalInput, parent: ros.Node,
                   objects, interfaces) -> list[str]:
    """
    An external input is well formed if:
    - It has a name
    - It is only owned by one node
    - It calls a callback that is owned by the same node
    """
    feedback = register(input.name, "external_input", parent.name, objects)
    if feedback != []:
        return feedback

    feedback += verify_registration(input.callback, "callback", parent.name, input.name, objects)

    return feedback

def validate_subscription(subscription: ros.Subscription, parent: ros.Node, objects, interfaces) -> list[str]:
    """
    A subscription is well formed if:
    - It has a valid quality of service profile
    - It names the topic it subscribes to
    - It calls a callback that is owned by the same node
    """
    pname = parent.name
    feedback = []
    feedback += validate_qos(subscription.qos_requested, pname)
    feedback += add_interface(subscription.topic, pname, "Topic", "topics subscribed to", interfaces)
    feedback += verify_registration(subscription.callback, "callback", pname, pname, objects)

    return feedback

def validate_timer(timer: ros.Timer, parent: ros.Node, objects, interfaces) -> list[str]:
    """
    A subscription is well formed if:
    - It has a name
    - It is only owned by one node
    - It has a valid period
    - It calls a callback that is owned by the same node
    """
    feedback = register(timer.name, "timer", parent.name, objects)
    if feedback != []:
        return feedback

    if timer.period < 0:
        feedback += [f"Timer '{timer.name}' must not have a negative period"]

    feedback += verify_registration(timer.callback, "callback", parent.name, timer.name, objects)

    return feedback

def validate_service(service: ros.Service, parent: ros.node, objects, interfaces) -> list[str]:
    """
    A service is well formed if:
    - It has a name
    - It is only owned by one node
    - It has a valid quality of service profile
    - It calls a callback that is owned by the same node
    """

    feedback = register(service.name, "service", parent.name, objects)
    if feedback != []:
        return feedback

    feedback += validate_qos(service.qos_requested, service.name)
    feedback += add_interface(service.name, node.name, "service", "services offered", interfaces)

    feedback += verify_registration(service.callback, "callback", parent.name, service.name, objects)
    return feedback


def validate_action(action: ros.Action, parent: ros.Node) -> list[str]:
    """
    TODO
    """
    return []


def validate_node(node: ros.Node, parent: ros.Executor, objects, interfaces) -> list[str]:
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
    """
    feedback = register(node.name, "node", parent.name, objects)
    if feedback != []:
        return feedback

    # outputs
    for client in node.clients:
        feedback += validate_client(client, node, objects, interfaces)
    for publisher in node.publishers:
        feedback += validate_publisher(publisher, node, objects, interfaces)

    # internal
    for variable in node.variables:
        feedback += register(variable.name, "variable", node.name, objects)
    for output in node.external_outputs:
        feedback += register(output.name, "external_output", node.name, objects)
    if len(node.callbacks) < 1:
        feedback += f"Node '{node.name}' must have at least one callback"
    for callback in node.callbacks:
        feedback += validate_callback(callback, node, objects, interfaces)

    total_triggers = 0
    for input in node.external_inputs:
        feedback += validate_input(input, node, objects, interfaces)
        total_triggers += 1
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
    if total_triggers < 1:
        feedback += f"Node '{node.name}' must have at least one trigger"

    for callback in node.callbacks:
        for called_name in callback.calls:
            feedback += verify_registration(called_name, "callback", node.name, callback.name, objects)
    return feedback


def validate_executor(executor: ros.Executor, parent: ros.Host, objects, interfaces) -> list[str]:
    """
    An executor is well formed if:
    - It has a name
    - It is only owned by one host
    - It has a valid ros distribution
    - It has a valid executor implementation
    - It has at least one node
    - All nodes are well formed
    """
    feedback = register(executor.name, "executor", parent.name, objects)
    if feedback != []:
        return feedback

    feedback += is_valid_value("distribution", executor.ros_distribution)
    feedback += is_valid_value("executor", executor.implementation)

    if len(executor.nodes) < 1:
        feedback += [f"Executor '{executor.name}' must have at least one node"]

    for node in executor.nodes:
        feedback += validate_node(node, executor, objects, interfaces)
    return feedback


def validate_host(host: ros.Host, parent: ros.System, objects, interfaces) -> list[str]:
    """
    A host is well formed if:
    - It has a name
    - It has a valid operating system
    - It has a valid architecture
    - It has at least one executor
    - All executors are well formed
    """
    feedback = register(host.name, "host", parent.name, objects)
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


def validate_system(system: ros.System) -> tuple[list[str], dict[str, dict[str, str], dict[str, dict[str, list[str]]]]]:
    """
    A system is well formed if:
    - It has a name
    - It has a valid dds
    - It has at least one host
    - All hosts are well formed
    - There is a server offering each service that a client requests
    - There is a publisher to each topic that a subscriber subscribes to
    """
    feedback = []

    interfaces: dict[str, dict[str, list[str]]] = {
        "services requested": {},
        "services offered": {},
        "topics subscribed to": {},
        "topics published to": {},
    }

    objects: dict[str, dict[str, str]] = {
        "callback": {},
        "external_input": {},
        "external_output": {},
        "executor": {},
        "node": {},
        "host": {},
        "timer": {},
        "service": {},
        "client": {},
        "variable": {},
        "publisher": {},
    }

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

    if feedback == []:
        return (["System is well formed"], objects, interfaces)
    else:
        return (feedback, objects, interfaces)
