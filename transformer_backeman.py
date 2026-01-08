import backeman.system as bk
import ros2system as ros
import systemvalidator as validator
"""
TODO: Implement mapping
TODO: Write test cases
TODO: Add check that no variable is written to that is not also read from and vice versa
TODO: Add validity check that all names should be unique

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
# TODO: Change to valid, such that future editions of ros do not have to be manually included
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
            buffer = publisher.qos.depth
            if buffer != 20:
                feedback += [
                    f"'{publisher.name}' has buffersize {str(buffer)}"]
        for subscriber in node.subscriptions:
            buffer = subscriber.qos.depth
            if buffer != 20:
                feedback += [f"A subscription of '{node.name}' "
                             f"has buffersize {str(buffer)}"]
    if feedback != []:
        feedback += ["Note that the Backeman model assumes buffers are large "
                     "enough to avoid overflow. In the concrete Uppaal model, "
                     "a buffersize of 20 is used."]
    return feedback


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
        len(node.variables) == 1 and
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
        len(node.subscriptions) > 0 and
        len(node.variables) <= 1
    ):
        return True
    else:
        return False


def validate_node(node: ros.Node):
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

    if node.name != node.name.upper():
        warnings += [f"Name of node '{node.name}' is not upper case, model "
                     f"assumes upper case names. Name is forced to upper case"]
    if len(node.publishers) > 1:
        errors += [f"Node '{node.name}' publishes to more than one topic"]
    if len(node.publishers) < 1:
        errors += [f"Node '{node.name}' does not have a publisher"]

    nodespec = {
        "sub_tasks": [],
        "main_task": None,
        "read_variable": None,
        "type": None,
    }

    main_tasks = 0
    for callback in node.callbacks:
        publishers = len(callback.publishers)
        reads = len(callback.read_variables)
        writes = len(callback.write_variables)
        calls = len(callback.calls)

        if publishers == 1:
            main_tasks += 1
            nodespec["main_task"] = callback
            if len(callback.write_variables) != 0:
                errors += [f"Main task '{callback.name}' writes to "
                           "internal variables"]
        else:
            nodespec["sub_tasks"].append(callback)
            if len(callback.read_variables) != 0:
                errors += [f"Subtask '{callback.name}' reads variables"]

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
    elif main_tasks == 0:
        errors += [f"Node '{node.name}' does not have a main task"]

    elif len(nodespec["sub_tasks"]) > 0:
        main_task = nodespec["main_task"]
        if len(main_task.read_variables) != 1:
            errors += [f"Main task '{main_task.name}' has subtasks, "
                       "but does not read from any of them"]
        else:
            nodespec["read variable"] = main_task.read_variables[0]

    if is_valid_data_generator(node):
        nodespec["type"] = "data generator"
    elif is_valid_timer(node):
        nodespec["type"] = "timer"
    elif is_valid_subscriber(node):
        nodespec["type"] = "subscriber"
    else:
        errors += [f"Node '{node.name}' is neither a data generator, "
                   "timer or subscriber"]
        errors += ["Full contents of node:",
                   f"    Timers:        {len(node.timers)}",
                   f"    Subscriptions: {len(node.subscriptions)}",
                   f"    Callbacks:     {len(node.callbacks)}",
                   f"    Variables:     {len(node.variables)}"]
    return errors, warnings, nodespec


def validate_system(system: ros.System,
                    objects,
                    interfaces) -> tuple[list[str], list[str]]:
    errors = ["Errors:"]
    warnings = ["Warnings:"]
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

    nodemap = {}

    for node in executor.nodes:
        errs, warns, nodespec = validate_node(node)
        errors += errs
        warnings += warns
        nodemap[node.name] = nodespec

    warnings += check_buffers(executor)

    return errors, warnings, nodemap


# ============================== MAPPING ===============================


def resolve_subscription_topic(subscriptions: list[ros.Subscription],
                               callback: str) -> str:
    for subscription in subscriptions:
        subscription: ros.Subscription
        if subscription.callback == callback:
            return subscription.topic

def map_subtask(sub: ros.Callback,
                read_variable: str,
                subscriptions: list[ros.Subscription]) -> tuple[list[str], list[int], str]:
    subtopic = resolve_subscription_topic(subscriptions, sub.name).upper()
    wcet = sub.wcet
    is_writer = False
    if sub.write_variables[0] == read_variable:
        is_writer = True

    return subtopic, wcet, is_writer


def map_subtasks(sub_tasks: list[ros.Callback],
                 read_variable: str,
                 subscriptions: list[ros.Subscription]) -> tuple[list[str], list[int], str]:
    subscribers = []
    wcets = []
    writer = None

    for sub in sub_tasks:
        subtopic, wcet, is_writer = map_subtask(sub, read_variable, subscriptions)
        subscribers.append(subtopic)
        wcets.append(wcet)
        if is_writer:
            writer = subtopic

    assert writer is not None

    return subscribers, wcets, writer


def map_system(system: ros.System,
               nodemap: dict[str, list[ros.Node]],
               objects,
               chain: list[str]) -> bk.System:
    name = system.name
    deterministic = True  # TODO: Support this

    out = bk.System(name.upper())
    out.deterministic_hosts(deterministic)
    nodes = system.hosts[0].executors[0].nodes

    max_priority = len(nodes) # TODO: Does this need to be length of all callbacks rather than nodes?

    for node in nodes:
        node: ros.Node
        spec = nodemap[node.name]
        main_task = spec["main_task"]
        main_task: ros.Callback
        sub_tasks = spec["sub_tasks"]
        sub_tasks: list[ros.Callback]
        node_type = spec["type"]

        name = node.name
        wcet = main_task.wcet

        if node_type == "data generator":
            period = node.timers[0].period
            delay = node.timers[0].offset
            out.add_datagenerator(name=name.upper(), period=period,
                                  wcet=wcet, delay=delay,
                                  prio=max_priority
                                  )
            max_priority -= 1
        elif node_type == "timer":
            period = node.timers[0].period
            delay = node.timers[0].offset
            read_variable = spec["read variable"]
            subscribers, wcets, data_source = map_subtasks(
                sub_tasks, read_variable, node.subscriptions)
            data_source = name.upper() + "x" + data_source.upper() + "_data"

            out.add_timer(name=name.upper(), period=period,
                          wcet=wcet, delay=delay,
                          subscribers=subscribers,
                          wcets=wcets,
                          data_source=data_source,
                          prio=max_priority
                          )
            max_priority -= 1
        elif node_type == "subscriber":
            topic = resolve_subscription_topic(node.subscriptions, main_task.name)
            data_source = "pd"

            read_variable = spec.get("read variable")
            if read_variable is not None:
                subscribers, wcets, writer = map_subtasks(
                    sub_tasks, read_variable, node.subscriptions)
                if main_task.name in chain:
                    prev = chain[chain.index(main_task.name)-1]
                    prevnode = objects["callback"][prev]
                    if prevnode == name:
                        data_source = name.upper() + "x" + writer.upper() + "_data"
            else:
                subscribers = []
                wcets = []

            out.add_subscriber(name=name.upper(),
                               topic=topic.upper(),
                               wcet=wcet,
                               subscribers=subscribers,
                               wcets=wcets,
                               data_source=data_source)

    monitor(out, chain[0], chain[-1])

    return out

# ===================== TRANSFORMATION ===========================


def transform_system(
        system: ros.System,
        chain: list[ros.Callback],
        validationresult: validator.ValidationResult = None) -> tuple[list[str], list[str], bk.System]:

    if validationresult is None:
        validationresult = validator.validate_system(system)
        validationresult: validator.ValidationResult
        if validationresult.errors != []:
            return (
                [["System is not well formed, cannot start transformation. "
                    "Validation feedback:"] + validationresult.errors],
                [],
                None)

    errors, warnings, nodemap = validate_system(
        system, validationresult.objects, validationresult.interfaces)

    if errors != ["Errors:"]:
        return errors, warnings, None
    if warnings == ["Warnings:"]:
        warnings = []

    return [], warnings, map_system(system, nodemap, validationresult.objects, chain)

# ========================== MONITORING ==========================


def monitor(system: bk.System, generator: str, actuator: str):
    system.actuator = actuator.upper()
    period = -1
    for node in system.nodes:
        node: bk.Node
        if node.name == generator.upper():
            node: bk.DataGenerator
            node.monitored = True
            period = node.period
    system.period = period

