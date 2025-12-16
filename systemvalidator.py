import ros2system as ros

"""
A ros2 system model consists of
Hosts
Variables
ExternalOutputs

TODO: Make dicts to map executors to distributions (check for age)
and operating systems to architectures
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
    "Ardent Apalone",
    "Bouncy Bolson",
    "Kilted Kaiju",
    "Jazzy Jalisco",
    "Iron Irwini",
    "Humble Hawksbill",
    "Galactic Geochelone",
    "Foxy Fitzroy",
    "Dashing Diademata",
    "Crystal Clemmys"
]

objects: dict[str, dict[str, str]] = {
    "external_input": {},
    "external_output": {},
    "executor": {},
    "node": {},
    "host": {}
}


def is_valid_value(typ: str, val: str):
    valid_values = {
        "dds": DDS_IMPLEMENTATIONS,
        "distribution": DISTRIBUTIONS,
        "os": OPERATING_SYSTEMS,
        "architecture": ARCHITECTURES,
        "executor": EXECUTORS,
    }

    if val not in valid_values[typ]:
        return f"{typ} '{val}' not among {valid_values[typ]}"


def register(obj, typ: str, parent) -> list[str]:
    name = obj.name
    if (name is None) or (name == ""):
        return [f"{typ} is missing name. Skipping validation of branch. Full {typ}: {print(obj)}"]
    if obj in objects[typ]:
        return [f"{typ} '{name}' has multiple owners. Skipping validation of branch."]
    objects[typ][name] = parent.name
    return []


def is_simple_subscriber(node: ros.Node) -> bool:
    """
    A simple subscriber has a single subscription which posts to a unique topic
    """
    if len(node.actions) != 0:
        return False
    if len(node.clients) != 0:
        return False
    if len(node.external_inputs) != 0:
        return False
    if len(node.timers) != 0:
        return False
    if len(node.variables) != 0:
        return False
    if len(node.services) != 0:
        return False
    if len(node.publishers) != 1:
        return False
    if len(node.subscriptions) != 1:
        return False
    if len(node.callbacks) != 1:
        return False

    pub: ros.Publisher = node.publishers[0]
    sub: ros.Subscription = node.subscriptions[0]
    cb: ros.Callback = node.callbacks[0]

    # Check subscriber
    # TODO: Make this a more meaningful check
    # TODO: Make a wellformedness error type and a modeltranslation error type
    sub.na
    if sub.buffer < 1:
        raise WellformednessError(f"""
        Subscriber of {node.name} has a too small buffer
        """)
    if sub.callback != cb.name:
        raise WellformednessError(f"""
        Node '{node.name}' is not well-formed.
        Subscription does not call callback '{cb.name}'
        """)

    # Check publisher
    if pub.topic in topicpublishers:
        raise TranslationError(f"""
        All nodes are assumed to publish to unique topics,
        however both {node.name} and {topicpublishers[pub.topic]} publish to
        topic {pub.topic}
        """)
    if pub.buffer < 1:
        raise TranslationError(f"""
        Buffers are assumed to be large enough to avoid overflow,
        publisher of {node.name} has a too small buffer
        """)

    # Check callback
    if cb.name is None: raise WellformednessError(f"Callback of node '{node.name}' has no name")
    if len(cb.calls) != 0:
        return False
    if len(cb.write_variables) != 0:
        raise WellformednessError( f"Callback '{cb.name}' writes to variables outside of parent node")
    if len(cb.requests) != 0:
        raise WellformednessError( f"Callback '{cb.name}' has requests, yet parent node has no clients")
    if len(cb.external_outputs) != 0:
        return False
    if len(cb.read_variables) != 0:
        raise WellformednessError( f"Callback '{cb.name}' reads from variables outside of parent node")
    if cb.wcet is None:
        raise WellformednessError(f"Callback '{cb.name}' has now wcet")
    if len(cb.publishers) != 1:
        return False
    if cb.publishers[0] != pub.name:
        raise WellformednessError(f"""
        Node '{node.name}' is not well-formed.
        Callback '{cb.name}' does not publish to '{pub.name}'
        """)

    if sub.topic not in topicsubscribers:
        topicsubscribers[sub.topic] = []
    topicsubscribers[sub.topic].append(node.name)
    topicpublishers[pub.topic] = node.name

    return True


"""
Callbacks own requests
"""


def validate_node(node: ros.Node, parent: ros.Executor) -> list[str]:
    """
    A node is well formed if:
    - It has a name
    - It is only owned by one executor

    - TODO: actions are valid
    - All external inputs are well formed
    - All variables are well formed
    """
    feedback = register(node, "node", parent)
    if feedback is not []:
        return feedback

    for input in system.external_inputs:
        feedback.extend(register(input, "external_input"))

    for output in system.external_outputs:
        feedback.extend(register(input, "external_outputs"))


    # Unvalidated

    # triggers
    node.external_inputs
    node.services
    node.subscriptions
    node.timers

    # outputs
    node.clients
    node.publishers

    # internal
    node.callbacks
    for variable in node.variables:
        validate_variable(variable)

    # TODO: Add support for actions
    actions = node.actions

    return feedback



def validate_executor(executor: ros.Executor, parent: ros.Host) -> list[str]:
    """
    An executor is well formed if:
    - It has a name
    - It is only owned by one host
    - It has a valid ros distribution
    - It has a valid executor implementation
    - It has at least one node
    - All nodes are well formed
    """
    feedback = register(executor, "executor", parent)
    if feedback is not []:
        return feedback

    feedback.append(is_valid_value("distribution", executor.distribution))
    feedback.append(is_valid_value("executor", executor.implementation))

    nodes = executor.nodes
    if len(nodes) < 1:
        feedback.append(f"Executor '{executor.name}' must have at least one node")

    for node in nodes:
        feedback.extend(validate_node(node, executor))
    return feedback


def validate_host(host: ros.Host, parent: ros.System) -> list[str]:
    """
    A host is well formed if:
    - It has a name
    - It has a valid operating system
    - It has a valid architecture
    - It has at least one executor
    - All executors are well formed
    """
    feedback = register(host, "host", parent)
    if feedback is not []:
        return feedback

    feedback.append(is_valid_value("os", host.operating_system))
    feedback.append(is_valid_value("architecture", host.architecture))

    executors = host.executors
    if len(executors) < 1:
        feedback.append(f"Host '{host.name}' must have at least one executor")

    for executor in executors:
        feedback.extend(validate_executor(executor, host))
    return feedback


def validate_system(system: ros.System) -> list[str]:
    """
    A system is well formed if:
    - It has a name
    - It has a valid dds
    - It has at least one host
    - All hosts are well formed
    """
    feedback = []

    if (system.name is None) or (system.name == ""):
        feedback.append("System must have a name")

    feedback.append(is_valid_value("dds", system.dds_implementation))

    hosts = system.hosts
    if len(hosts) < 1:
        feedback.append("System must have at least one host")

    for host in hosts:
        feedback.extend(validate_host(host), system)

    if feedback == []:
        return ["System is well formed"]
    else:
        return feedback
