import backeman.system as bk
import ros2system as ros
import systemvalidator as validator
"""
TODO: Fix cycles

---

For the notes ros will refer to the models from the ros2system module
while bk will refer to models as specified by backeman.system
'pd' is the default data variable, meant for synchronous communication
through uppaal broadcast channels
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

# https://github.com/ros2/rclcpp/issues/2532
# The ROS2 SingleThreadedExecutor subtly changed behavior around Jazzy.
# Previously, execution of callbacks of the same type in the wait set would be
# ordered deterministically based on order of callback registration, but since,
# it is nondeterministic, and order is only imposed between different callback types
INVALID_ROS_DISTRIBUTIONS = [
    "Rolling",
    "Kilted",
    "Jazzy",
    "Dashing",
    "Crystal",
    "Bouncy",
    "Ardent",
    "Rolling Ridley",
    "Kilted Kaiju",
    "Jazzy Jalisco",
    "Dashing Diademata",
    "Crystal Clemmys",
    "Bouncy Bolson",
    "Ardent Apalone"
]


INVALID_EXECUTORS = [
    "MultiThreadedExecutor",
    "StaticSingleThreadedExecutor",
    "EventsExecutor"
]

INVALID_INTERFACES = [
    "services requested",
    "services offered",
]

LIMITED_ELEMENTS = {
    "host": 1,
    "executor": 1,
    "service": 0,
    "client": 0,
    "action": 0,
    "external_input": 0,
    "external_output": 0,
}

# ======================= VALIDATION ======================


def check_buffers(executor: ros.Executor) -> list[str]:
    feedback = []
    for node in executor.nodes:
        for publisher in node.publishers:
            buffer = publisher.qos_offered["depth"]
            if buffer != 20:
                feedback += [
                    f"'{publisher.name}' has buffersize {str(buffer)}"]
        for subscriber in node.subscriptions:
            buffer = subscriber.qos_requested["depth"]
            if buffer != 20:
                feedback += [f"A subscription of '{node.name}' "
                             f"has buffersize {str(buffer)}"]
    if feedback != []:
        feedback += ["Note that the Backeman model assumes buffers are large "
                     "enough to avoid overflow. In the concrete Uppaal model, "
                     "a buffersize of 20 is used."]
    return feedback


def check_for_cycles(system: ros.System,
                     objects: dict[str, dict[str, str]],
                     interfaces: dict[str, dict[str, list[str]]]) -> bool:
    """
    validate_system() establishes that there is exactly one publisher per topic
    validate_node() establishes that there is exactly one publisher per node
    using https://en.wikipedia.org/wiki/Topological_sorting
    """
    nodes = list(objects["node"].keys())
    subscribers = interfaces["topics subscribed to"].copy()
    publishers = interfaces["topics published to"].copy()
    visited = []
    # settled = []

    def visit(node: str):
        # print(f"Visiting node {node}")
        if node not in nodes:
            # print(f"Node {node} already settled")
            return False
        if node in visited:
            return True
        visited.append(node)
        # print(f"Node {node} worth visiting")
        dependents = []
        for topic in publishers:
            if node == objects["publisher"][publishers[topic][0]]:
                dependents = subscribers[topic]
        # print(f"{dependents} depend on {node}")
        for dep in dependents:
            if visit(dep):
                return True
        # print(f"settled {node}")
        nodes.remove(node)

    while len(nodes) > 0:
        if visit(nodes[0]):
            return True

    return False


def is_valid_data_generator(node: ros.Node) -> bool:
    """
    Definition 3:
    DGEN (p, d, wcet, t, wv), where:
    – p ∈ N, is the period,
    – d ∈ N is the delay,
    – wcet ∈ N is the WCET of the main task,
    – t ∈ T is the result-topic,
    – wv ∈ V is the write-variable.
    """
    if (
        len(node.timers) == 1 and
        len(node.subscriptions) == 0 and
        len(node.callbacks) == 1 and
        len(node.variables) == 0
        # Note that these variables are different from backeman write variables
    ):
        return True
    else:
        return False


def is_valid_timer(node: ros.Node) -> bool:
    """
    Definition 1:
    A timer node is defined as:
    tn = TMR(p, d, wcet, S, St, t, rv, wv),
    where:
    – p ∈ N+ is the period,
    – d ∈ N is the delay,
    wcet ∈ N is the WCET of the main task,
    S = {s1, . . . , sn}, si ∈ T , are the non-triggering subscribed topics,
    St = {st1, . . . , stn}, sti ∈ N, are the WCET of subscription tasks,
    t ∈ T is the result-topic,
    rv ∈ V, is the read-variable,
    wv ∈ V is the write-variable.
    """
    if (
        len(node.timers) == 1 and
        len(node.subscriptions) > 0 and
        len(node.variables) > 0 and
        len(node.callbacks > 1)
    ):
        return True
    else:
        return False


def is_valid_subscriber(node: ros.Node) -> bool:
    """
    Definition 2:
    A subscriber node is defined as:
    sn = SUB (s, wcet, S, St, t, rv, wv), where:
    – s ∈ T , s ∈ S, is the triggering topic,
    – wcet ∈ N is the WCET of the main task,
    – S = {s1, . . . , sn}, si ∈ T , are the non-triggering subscribed topics,
    – St = {st1, . . . , stn}, sti ∈ N, are the WCET of subscriptions tasks,
    – t ∈ T is the result-topic,
    – rv ∈ V, is the read-variable,
    – wv ∈ V is the write-variable.
    """
    if (
        len(node.timers) == 0 and
        len(node.subscriptions) > 0
    ):
        return True
    else:
        return False


def validate_node(node: ros.Node) -> tuple[list[str], list[str]]:
    """
    A bk node is a ros node with one primary trigger, publisher and callback,
    along with a list of secondary triggers, and callbacks.
    bk nodes are of three different fundamental types:
    Subscriber, Timer, and DataGenerator.
    TODO: DataGenerator can be probabilistic
    See section 3 in Backeman & Seceleanu 2025
    """
    errors = []
    warnings = []

    if len(node.publishers) > 1:
        errors += [f"Node '{node.name}' publishes to more than one topic"]
    if len(node.publishers) < 1:
        errors += [f"Node '{node.name}' does not have a publisher"]

    main_tasks = 0
    for callback in node.callbacks:
        publishers = len(callback.publishers)
        reads = len(callback.read_variables)
        writes = len(callback.write_variables)
        calls = len(callback.calls)

        if publishers == 0:
            main_tasks += 1
        if reads > 1:
            errors += [f"Callback '{callback.name}' reads from more than "
                       "one variable"]
        if writes > 1:
            errors += [f"Callback '{callback.name}' writes to more than "
                       "one variable"]
        if calls > 0:
            errors += [f"Callback '{callback.name}' calls more than "
                       "one callback"]
    if main_tasks > 1:
        errors += [f"Node '{node.name}' has more than one main task"]
    if main_tasks == 0:
        errors += [f"Node '{node.name}' does not have a main taks"]

    if not (
        is_valid_data_generator(node) or
        is_valid_timer(node) or
        is_valid_subscriber(node)
    ):
        errors += [f"Node '{node.name}' is neither a data generator, "
                   "timer or subscriber"]

    return errors, warnings


def validate_system(system: ros.System,
                    objects, interfaces) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    for elem in LIMITED_ELEMENTS:
        num = len(objects[elem])
        exp = LIMITED_ELEMENTS[elem]
        if num != exp:
            errors += [f"System has {num} {elem}s, but target metamodel "
                       f"supports at most {exp}"]

    for interface in INVALID_INTERFACES:
        if interfaces[interface] != {}:
            errors += [f"System has {interface}, which are not supported by "
                       "target metamodel"]
    for topic in interfaces["topics published to"]:
        publishers = interfaces["topics published to"][topic]
        if len(publishers) != 1:
            errors += [f"Topic '{topic}' has more than one publishing node: "
                       f"{publishers}"]

    executor = system.hosts[0].executors[0]
    impl = executor.implementation
    if impl in INVALID_EXECUTORS:
        errors += [f"Host uses an unsupported executor {impl}"]
    ros = executor.ros_distribution
    if ros in INVALID_ROS_DISTRIBUTIONS:
        errors += [f"Host uses an unsupported ros distribution {ros}"]

    for node in executor.nodes:
        errs, warns = validate_node(node)
        errors += errs
        warnings += warns

    if check_for_cycles(executor, objects, interfaces):
        errors += ["Cycles are not supported. There is a cycle among nodes"]
    warnings += check_buffers(executor)

    return (errors, warnings)





# There should be no clients, services or actions, external input or external output
# def validate_registry(objects):
#

# All publishers, subscribers,


def is_simple_subscriber(node: ros.Node) -> bool:
    """
    A simple subscriber has a single subscription which posts to a unique topic
    """
    if (not (len(node.actions) == 0)
            and (len(node.clients) == 0)
            and (len(node.external_inputs) == 0)
            and (len(node.timers) == 0)
            and (len(node.variables) == 0)
            and (len(node.services) == 0)
            and (len(node.publishers) == 1)
            and (len(node.subscriptions) == 1)
            and (len(node.callbacks) == 1)):
        return False

    pub: ros.Publisher = node.publishers[0]
    sub: ros.Subscription = node.subscriptions[0]
    cb: ros.Callback = node.callbacks[0]

    # Check publisher
    if pub.topic in topicpublishers:
        raise TranslationError(f"""
        All nodes are assumed to publish to unique topics,
        however both {node.name} and {topicpublishers[pub.topic]} publish to
        topic {pub.topic}
        """)
    if sub.buffer < 20:
        print("Note that the Backeman model assumes buffers are large enough to avoid overflow. "
              "In the concrete Uppaal model, a buffersize of 20 is used. "
              f"'{pub.name}' has buffersize = {str(pub.buffer)}")

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

# ============================== MAPPING ===============================

def map_node(node: ros.Node) -> bk.Node:
    """
    bk has different node classes, ros has a single very expressive node class
    """
    pass


def map_system(system: ros.System) -> bk.System:
    name = system.name
    deterministic = True  # TODO: Support this
    monitored_actuator = None  # TODO
    monitor_period = 0  # TODO
    nodes = system.hosts[0].executors[0].nodes
    out = bk.System(name)
    out.deterministic_hosts(deterministic)

# ===================== TRANSFORMATION ===========================

def transform_system(
        system: ros.System) -> tuple[list[str], bk.System]:

    feedback, objects, interfaces = validator.validate_system(system)
    if feedback != ["System is well formed"]:
        return ([["System is not well formed, cannot start transformation. "
                  "Validation feedback:"] + feedback],
                None)

    errors, warnings = validate_system(system, objects, interfaces)

    if errors != []:
        return feedback, None

    return (warnings, map_system(system))


