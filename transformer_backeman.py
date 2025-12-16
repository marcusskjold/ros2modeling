import backeman.system as bk
import ros2system as ros
"""
For the notes ros will refer to the models from the ros2system module
while bk will refer to models as specified by backeman.system
'pd' is the default data variable, meant for synchronous communication
through uppaal broadcast channels
"""


class TranslationError(Exception):
    """Error caused because the ros model has complexities that cannot
    be translated into the desired model-checking framework
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class WellformednessError(Exception):
    """Error caused because the ros model is not well formed.
    Some error has been made when defining the system
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


# It is assumed that each node publishes to unique topics
topicpublishers: dict[str, str] = {}
topicsubscribers: dict[str, list[str]] = {}


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
    if sub.buffer < 1:
        raise TranslationError(f"""
        Buffers are assumed to be large enough to avoid overflow,
        subscriber of {node.name} has a too small buffer
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


def validate_timer(node: ros.Node) -> bool:
    """
    Timer - self, nid, name, period, delay, wcet, data_source, prio
    """
    pass


def validate_datagenerator(node: ros.Node) -> bool:
    """
    Timer - self, nid, name, period, delay, wcet, data_source, prio
    """
    pass


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
    if is_simple_subscriber(node):
        return "simple subscriber"
    if is_simple_timer(node):
        return "simple timer"
    if is_simple_datagenerator(node):
        return "simple datagenerator"
    else:
        return "complex or invalid"

    pass


def validate_system(system: ros.System) -> bool:
    """
    ros systems can specify dds_implementation, whereas
    bk systems do not care about this information, and so it is ignored
    ros systems have external inputs and output, which bk also ignores
    ros systems have hosts, which have executors, whereas
    bk systems assume that a system consists of one host with an executor.
    therefor a ros system with a different amount of either is invalid.

    TODO: Double check this assumption
    bk assumes that executors are the default SingleThreadedExecutor

    TODO: bk systems allow for nondeterministic hosts.
    This include both nondeterminism in the sense that
    a task's execution time can vary between a best case
    (BCET, which is taken by bk to mean half of WCET) and a worst case (WCET).
    Also, nodes can be nondeterministic, which is relevant further down.
    For now, we only consider nondeterministic hosts.

    TODO: bk systems have a designated monitored node and monitored actuator,
    and specifies the period og the monitored data generator.

    bk uses the SingleThreadedExecutor that was the default before Jazzy,
    it has a deterministic ordering of what task is executed in the wait set.
    Timers are before topics which are before services, also the order that
    tasks of the same type are registered determines the ordering of execution.
    This behavior is recreated by giving higher priority to timers, and by ordering
    otherwise according to their place in the list of nodes.

    """
    if system.name is None:
        raise ValueError("System must have a name")
    if len(system.hosts) != 1:
        raise ValueError("System must have exactly one host")
    host = system.hosts[0]
    if len(host.executors) != 1:
        raise ValueError("System must have exactly one executor")
    executor = host.exexutors[0]
    if executor.nodes is None:
        raise ValueError("System must have a list of nodes")
    if executor.implementation != "SingleThreadedExecutorPreJazzy":
        raise ValueError("Executor must be SingleThreadedExecutorPreJazzy")
    return True


def map_node(node: ros.Node) -> bk.Node:
    """
    bk has different node classes, ros has a single very expressive node class
    """
    pass


def map_system(system: ros.System) -> bk.System:
    if not validate_system(system):
        raise ValueError("Invalid input system")
    name = system.name
    deterministic = True  # TODO: Support this
    monitored_actuator = None  # TODO
    monitor_period = 0  # TODO
    nodes = system.hosts[0].executors[0].nodes
    out = bk.System(name)
    out.deterministic_hosts(deterministic)
    out.nodes = [map_node(node) for node in nodes]
    out.monitor(actuator=monitored_actuator, period=monitor_period)  # TODO
