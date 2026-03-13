from roserer.rosgraph import RosGraphView, GraphNode
import roserer.backeman.system as bk
import roserer.ros2system as ros
import roserer.systemvalidator as validator
import roserer.rosgraph as rosgraph
from roserer.types import DISTRIBUTION, EXECUTOR, NodeType, Feedback, run_validation
"""
TODO: Constraint: Reject offsets smaller than -period
TODO: Write test cases
TODO: Add check that no variable is written to that is not also read from and vice versa
      Sink check
TODO: Add validity check that all names should be unique
TODO: check for wall_times
---

- For the notes 'ros' will refer to the models from the ros2system module while 'bk'
  will refer to models as specified by backeman.system.
- 'pd' is the default data variable, meant for synchronous communication through uppaal
  broadcast channels
- Fields that bk systems ignore:
    - System.dds_implementation
    - Node.external_input
    - Node.external_output
- bk systems assume a single executor on a single host.
- bk systems must specify a data generator and a node ('actuator') to monitor.
- The monitored actuator is assumed to be a sink, when the graph is abstracted to a
  callback graph.

TODO: Find reference for this assumption:
      bk assumes that executors are the default SingleThreadedExecutor

TODO: bk systems allow for nondeterministic hosts.
      This include both nondeterminism in the sense that a task's execution time can
      vary between a best case (BCET, which is taken by bk to mean half of WCET) and a
      worst case (WCET).
      Also, nodes can be nondeterministic, which is relevant further down.
      For now, we only consider nondeterministic hosts.


- bk uses the SingleThreadedExecutor that was the default before Jazzy, it has a
  deterministic ordering of what task is executed in the wait set. Timers are before
  topics which are before services, also the order that tasks of the same type are
  registered determines the ordering of execution. This behavior is recreated by giving
  higher priority to timers, and by ordering otherwise according to their place in the
  list of nodes.
"""

# https://github.com/ros2/rclcpp/issues/2532
# The ROS2 SingleThreadedExecutor subtly changed behavior around Jazzy.
# Previously, execution of callbacks of the same type in the wait set would be
# ordered deterministically based on order of callback registration, but since,
# it is nondeterministic, and order is only imposed between different callback types
# TODO: Find the source for why distributions before eloquent are not valid

# ======================= HELPER ======================

def is_main_task(callback: ros.Callback) -> bool:
    return len(callback.publishers) == 1

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
    if (len(node.timers) == 1 
        and len(node.subscriptions) == 0 
        and len(node.callbacks) == 1 
        and len(node.variables) == 0):
        # Note that these variables are different from backeman write variables
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
    main, _ = get_main_and_sub_tasks(node)
    if (len(node.timers) == 1
        and len(node.subscriptions) > 0
        and len(node.callbacks) == len(node.subscriptions) + 1
        and len(main.read_variables) > 0):
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
    if (len(node.timers) == 0 
        and len(node.subscriptions) > 0 
        and len(node.callbacks) == len(node.subscriptions)):
        return True
    else:
        return False

# ====================== GRAPH / RELATIONSHIP VALIDATION =================

def error_graph_limited_node_types(graph: RosGraphView) -> list[str]:

    LIMITED_GRAPH_NODE_TYPES: dict[NodeType, int] = {
            NodeType.HOST: 1,
            NodeType.EXECUTOR: 1,
            NodeType.SERVICE: 0,
            NodeType.CLIENT: 0,
            NodeType.ACTION: 0,
            NodeType.EXTERNAL_INPUT: 0,
            NodeType.EXTERNAL_OUTPUT: 0
    }
    errors = []
    for nodetype in LIMITED_GRAPH_NODE_TYPES:
        n = len(graph[nodetype])
        limit = LIMITED_GRAPH_NODE_TYPES[nodetype]
        if not n <= limit:
            errors += [f"[Error]: System has {n} {nodetype.name.lower()}s, but target \
                    metamodel supports at most {limit}"]
    return errors

def error_graph_multiple_topic_publishers(graph: RosGraphView) -> list[str]:
    return [f"[Error]: Topic '{topic.name}' has more than one publishing node:\n    \
            Publishers: {topic.incoming}"
            for topic in graph[NodeType.TOPIC].values() if len(topic.incoming) != 1]

def error_graph_multiple_variable_writers(graph: RosGraphView) -> list[str]:
    return [f"[Error]: Topic '{variable.name}' has more than one writer:\n    \
            Writers: {variable.incoming}"
            for variable in graph[NodeType.VARIABLE].values() if len(variable.incoming) != 1]

def error_graph_multiple_callback_triggers(graph: RosGraphView) -> list[str]:
    return [f"[Error]: Topic '{cb.name}' has more than one trigger"
            for cb in graph[NodeType.CALLBACK].values() 
            if 1 != sum(trigger.nodetype in [NodeType.SUBSCRIBER, NodeType.TIMER] 
                        for trigger in cb.incoming)]

def warning_topic_case_insensitive(graph: RosGraphView) -> list[str]:
    return [f"[Warning]: Topic '{topic.name} is not upper case, model assumes upper \
            case names. Name is forced to upper case during transformation"
            for topic in graph[NodeType.TOPIC].values() if topic.name != topic.name.upper()]

def validate_chain(chain: list[GraphNode], graph: RosGraphView) -> list[str]:
    errors = []
    if chain[0].nodetype != NodeType.TIMER:
        errors += ["[Error] Invalid chain: Monitored chain starts with a non-timer \
                object"]
    endt = chain[-1].nodetype
    if not (endt == NodeType.CALLBACK or endt == NodeType.TOPIC):
        errors += [f"[Error] Invalid chain: Monitored chain ends with an {endt.name}"]
    for node, next_node in zip(chain, chain[1:]):
        if next_node not in node.outgoing:
            errors += [f"[Error] Invalid chain: {node.name} is not linked to \
                    {next_node.name}"]
    try:
        chain = rosgraph.find_equivalent_chain_in(graph, chain)
    except ValueError as ve:
        errors += [f"[Error] Invalid chain: {ve}"]
    return errors


# ======================= OBJECT VALIDATION ======================

def warning_buffer_size(system: ros.System) -> list[str]:
    """
    Report each object with a buffer where the buffer size is not 20.

    The buffer sizes of bk models are hard-coded to be 20.
    This is assumed to be sufficient to avoid overflow.

    Arguments:
    executor (ros.Executor):
    The executor containing the entire ros2system to validate.

    Returns:
    A list of warnings for each object contained by the executor that has a quality of
    service profile with a buffersize != 20.
    """
    feedback = []
    for qos, parent in system.get_qos_profiles():
        if qos.depth != 20:
            feedback += [f"[Warning]: '{parent}' has buffersize {str(qos.depth)}"]
    if feedback != []:
        feedback += ["    Note that the Backeman model assumes buffers are large \
                          enough to avoid overflow.", 
                     "    In the concrete Uppaal model, a buffersize of 20 is used."]
    return feedback

def validate_timer(timer: ros.Timer) -> Feedback:
    feedback = Feedback()
    if timer.end:
        feedback.errors += [f"[Warning]: Timer {timer.name} has end time, this model \
                assumes that timers continue indefinitely"]
    return feedback

def validate_subscription(sub: ros.Subscription) -> Feedback:
    feedback = Feedback()
    if sub.wall_times is not None:
        feedback.errors += [f"[Error]: Subscription {sub.name} has wall times set. \
                This model does not support wall times"]
    return feedback

def validate_variable(var: ros.Variable) -> Feedback:
    feedback = Feedback()
    errors, warnings = feedback.errors, feedback.warnings
    if var.condition:
        errors += [
                f"[Error] Variable {var.name}: This model does not support conditions"]
    if var.reset_after_read:
        warnings += [f"[Warning] Variable {var.name}: This model does not support \
                reset after read, but this should not affect results"]
    return feedback

def validate_callback(cb: ros.Callback) -> Feedback:
    feedback = Feedback()
    errors = feedback.errors
    reads = len(cb.read_variables)
    writes = len(cb.write_variables)

    if is_main_task(cb):
        if writes != 0:
            errors += [f"[Error]: Main task '{cb.name}' writes to internal variables"]
    else:
        if reads != 0:
            errors += [f"[Error]: Subtask '{cb.name}' reads variables"]
        if writes > 1:
            errors += [f"[Error]: Subtask '{cb.name}' writes to more than one variable"]

    if cb.calls is not None:
        errors += [f"[Error]: cb '{cb.name}' calls other callbacks"]

    return feedback

def validate_node(node: ros.Node) -> Feedback:
    """
    A bk node is a ros node with one primary trigger, publisher and callback,
    along with a list of secondary triggers, and callbacks.
    bk nodes are of three different fundamental types:
    Subscriber, Timer, and DataGenerator.
    See section 3 in Backeman & Seceleanu 2025
    """
    # TODO: DataGenerator can be probabilistic
    feedback = Feedback()
    errors, warnings = feedback.errors, feedback.warnings
    if node.name != node.name.upper():
        warnings += [f"[Error]: Name of node '{node.name}' is not upper case, model \
                assumes upper case names. Name is forced to upper case"]
    if len(node.publishers) > 1:
        errors += [f"[Error]: Node '{node.name}' publishes to more than one topic"]
    if len(node.publishers) < 1:
        errors += [f"[Error]: Node '{node.name}' does not have a publisher"]

    main_tasks = sum(is_main_task(cb) for cb in node.callbacks)
    if main_tasks > 1:
        errors += [f"[Error]: Node '{node.name}' has more than one main task"]
    elif main_tasks == 0:
        errors += [f"[Error]: Node '{node.name}' does not have a main task"]

    if not (is_valid_data_generator(node) 
            or is_valid_timer(node)
            or is_valid_subscriber(node)):
        errors += [f"[Error] Node '{node.name}': is neither a data generator, "
                   "timer or subscriber"]
        errors += ["    Full contents of node:",
                   f"    Timers:        {len(node.timers)}",
                   f"    Subscriptions: {len(node.subscriptions)}",
                   f"    Callbacks:     {len(node.callbacks)}",
                   f"    Variables:     {len(node.variables)}"]
    return feedback

def validate_executor(executor: ros.Executor) -> Feedback:
    VALID_ROS_DISTRIBUTIONS = set([
        DISTRIBUTION.Iron,
        DISTRIBUTION.Humble,
        DISTRIBUTION.Galactic,
        DISTRIBUTION.Foxy,
        DISTRIBUTION.Eloquent,
        ])
    VALID_EXECUTORS = set([EXECUTOR.SingleThreadedExecutor])
    impl = executor.implementation
    feedback = Feedback()
    errors = feedback.errors
    if impl not in VALID_EXECUTORS:
        errors += [f"[Error]: Host uses an unsupported executor {impl}"]
    ros = executor.ros_distribution
    if ros not in VALID_ROS_DISTRIBUTIONS:
        errors += [f"[Error]: Host uses an unsupported ros distribution {ros}"]
    return feedback

def validate_system(system: ros.System, chain: list[GraphNode]) -> Feedback:

    feedback = Feedback()
    errors, warnings = feedback.errors, feedback.warnings
    executor = system.hosts[0].executors[0]

    graph = rosgraph.get_graph_view_from(system)
    errors += error_graph_limited_node_types(graph)
    errors += error_graph_multiple_topic_publishers(graph)
    errors += error_graph_multiple_variable_writers(graph)
    errors += validate_chain(chain, graph)
    warnings += warning_buffer_size(system)
    feedback += validate_executor(executor)

    feedback += run_validation(executor.nodes, validate_node)
    feedback += run_validation(system.get_callbacks(), validate_callback)
    feedback += run_validation(system.get_timers(), validate_timer)

    return feedback

# ========================== MONITORING ================================

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

# ============================== MAPPING ===============================

def get_main_and_sub_tasks(node: ros.Node) -> tuple[ros.Callback, list[ros.Callback]]:
    main_task: ros.Callback
    sub_tasks: list[ros.Callback] = []
    # This needs to be the amount of callbacks
    # See backeman/system.py:System.add_dependencies() + System.next_id()
    for cb in node.callbacks:
        if is_main_task(cb):
            main_task=cb
        else:
            sub_tasks.append(cb)
    assert main_task
    return main_task, sub_tasks

def add_datagenerator(bksystem: bk.System, node: ros.Node, priority: int) -> None:
    period = node.timers[0].period
    delay = node.timers[0].offset
    wcet = node.callbacks[0].wcet
    name = node.name.upper()
    bksystem.add_datagenerator(
            name=name, period=period, wcet=wcet, delay=delay, prio=priority)

# TODO: Move and improve this note
# For examples of how to construct different systems according to which node
# is monitored, see Backeman & Seceleanu (2025), section 4.2
# See also backeman/demo:validation_ss(), prio_inversion() & case_study()

def data_source_for_cb_in_chain(cb: GraphNode, chain: list[GraphNode]) -> str:
    prev = chain[chain.index(cb)-1]
    if prev.nodetype == NodeType.VARIABLE:
        writer = prev.incoming[0]
        data_source = cb.name.upper() + "x" + writer.name.upper() + "_data"
    assert data_source
    return data_source

def add_timer(bksystem: bk.System, node: ros.Node, priority: int, chain: list[GraphNode]
              ) -> None:
    main_task, sub_tasks = get_main_and_sub_tasks(node)
    name: str = node.name.upper()
    wcet: int = main_task.wcet
    subscribers: list[str] = [t.name for t in sub_tasks]
    wcets: list[int] = [t.wcet for t in sub_tasks]
    period = node.timers[0].period
    delay = node.timers[0].offset
    # NOTE: This is an arbitrary assignment.
    #       Supposing the timer is not part of the monitored chain:
    #       Then any timer or subscriber downstream of the timer that are part of the
    #       monitored chain will not read from a variable that contains data
    #       originating from this timer.
    data_source = name + "x" + node.subscriptions[0].callback.upper() + "_data"

    main_task_in_chain: GraphNode
    for cb in chain:
        if cb.nodetype == NodeType.CALLBACK and cb.name == main_task.name:
            main_task_in_chain = cb

    if (main_task_in_chain):
        data_source = data_source_for_cb_in_chain(main_task_in_chain, chain)

    bksystem.add_timer(name=name, period=period, wcet=wcet, delay=delay, 
                       subscribers=subscribers, wcets=wcets, data_source=data_source,
                       prio=priority)

def add_subscriber(bksystem: bk.System, node: ros.Node, chain: list[GraphNode]) -> None:
    
    main_task, sub_tasks = get_main_and_sub_tasks(node)
    name: str = node.name.upper()
    wcet: int = main_task.wcet
    data_source: str = "pd"
    topic: str
    subscribers: list[str] = [t.name for t in sub_tasks]
    wcets: list[int] = [t.wcet for t in sub_tasks]

    for sub in node.subscriptions:
        if sub.callback == main_task.name:
            topic = sub.topic.upper()
    assert topic

    main_task_in_chain: GraphNode
    for cb in chain:
        if cb.nodetype == NodeType.CALLBACK and cb.name == main_task.name:
            main_task_in_chain = cb
    
    if (sub_tasks != [] and main_task_in_chain):
        data_source = data_source_for_cb_in_chain(main_task_in_chain, chain)

    bksystem.add_subscriber(name=name,
                       topic=topic,
                       wcet=wcet,
                       subscribers=subscribers,
                       wcets=wcets,
                       data_source=data_source)

def map_system(system: ros.System, chain: list[GraphNode]) -> bk.System:
    out = bk.System(system.name.upper())
    out.deterministic_hosts(True) # TODO: Support nondeterminism
    graph = rosgraph.get_graph_view_from(system)
    chain = rosgraph.find_equivalent_chain_in(graph, chain)
    nodes = system.get_nodes()
    max_priority = len(graph[NodeType.CALLBACK])
    for node in nodes:
        if is_valid_data_generator(node):
            add_datagenerator(out, node, max_priority)
            max_priority -= 1
        elif is_valid_timer(node):
            add_timer(out, node, max_priority, chain)
            max_priority -= 1
        elif is_valid_subscriber(node):
            add_subscriber(out, node, chain)
        else:
            raise Exception("Node failed to be added - validation must be incorrect")

    monitor(out, chain[0].name, chain[-1].name)

    return out

# ===================== TRANSFORMATION ===========================

def transform_system(system: ros.System, chain: list[GraphNode]
                     ) -> tuple[Feedback, bk.System | None]:

    feedback = validator.validate_system(system)
    if feedback.errors != []:
        return feedback + Feedback(["[Error]: System is not well formed, cannot start \
                transformation. Validation feedback:"]), None
    
    feedback += validate_system(system, chain)

    if feedback.errors != []:
        return feedback, None
    else:
        return feedback, map_system(system, chain)
