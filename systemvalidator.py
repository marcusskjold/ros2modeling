import ros2system as ros

DDS_IMPLEMENTATIONS = [
    "Cyclone",
    "Fast",
    "RTI connext",
    "Gurum"
]

external_inputs: list[ros.ExternalInput]
external_outputs: list[ros.ExternalOutput]
global_executors: list[str]
global_nodes: list[str]
global_


def validate_dds(dds) -> list[str]:
    if dds not in DDS_IMPLEMENTATIONS:
        return [f"dds '{dds}' not among {DDS_IMPLEMENTATIONS}"]
    else:
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


def validate_node(node: ros.Node) -> str:
    """
    A bk node is a ros node with one primary trigger, publisher and callback,
    along with a list of secondary triggers, and callbacks.
    bk nodes are of three different fundamental types:
    Subscriber, Timer, and DataGenerator.
    TODO: DataGenerator can be probabilistic

    """
    if node.name is None:
        raise ValueError("All nodes must have names")
    pass


def validate_host(host: ros.Host) -> list[str]:
    feedback = []
    if host.name is None:
        feedback.append("Host must have a name")
    if host.name == "":
        feedback.append("Host must have a name")
    if len(host.executors) < 1:
        feedback.append("Host must have at least one host")
        feedback.extend(validate_executor(executor))
        if executor in global_executors:
            feedback.append(
                f"executor {executor.name} is owned by multiple hosts")
    host.operating_system


def validate_system(system: ros.System) -> list[str]:
    feedback = []
    if system.name is None:
        feedback.append("System must have a name")
    if system.name == "":
        feedback.append("System must have a name")
    if len(system.hosts) < 1:
        feedback.append("System must have at least one host")
    external_inputs = system.external_inputs
    external_outputs = system.external_outputs
    feedback.extend(validate_dds(system.dds_implementation))
    for host in system.hosts:
        feedback.extend(validate_host(host))
    if feedback == []:
        return ["System is well formed"]
    else:
        return feedback
