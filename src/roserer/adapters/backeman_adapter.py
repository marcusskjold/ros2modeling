import logging
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
    return len(callback.publishers) == 1 or len(callback.write_variables) == 0

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
            errors += [f"[E101]: System has {n} {nodetype.name.lower()}s, but target"
                       f" metamodel supports at most {limit}"]
    return errors

def error_graph_multiple_topic_publishers(graph: RosGraphView) -> list[str]:
    return [f"[E102]: Topic '{topic.name}' has more than one publishing node:\n"
            f"    Publishers: {[pub.name for pub in topic.incoming]}"
            for topic in graph[NodeType.TOPIC].values() if len(topic.incoming) != 1]

def error_graph_multiple_variable_writers(graph: RosGraphView) -> list[str]:
    return [f"[E103]: Variable '{variable.name}' has more than one writer:\n"
            f"    Writers: {[cb.name for cb in variable.incoming]}"
            for variable in graph[NodeType.VARIABLE].values() if len(variable.incoming) != 1]

def error_graph_multiple_callback_triggers(graph: RosGraphView) -> list[str]:
    return [f"[E104]: Callback '{cb.name}' has more than one trigger"
            for cb in graph[NodeType.CALLBACK].values() 
            if 1 != sum(trigger.nodetype in [NodeType.SUBSCRIBER, NodeType.TIMER] 
                        for trigger in cb.incoming)]

def warning_topic_case_insensitive(graph: RosGraphView) -> list[str]:
    #TODO: Remember to document why this check is important
    return [f"[W101]: Topic '{topic.name}' is not upper case, model assumes upper"
            "case names. Name is forced to upper case during transformation"
            for topic in graph[NodeType.TOPIC].values() if topic.name != topic.name.upper()]

def validate_chain(chain: list[GraphNode], graph: RosGraphView) -> list[str]:
    errors = []
    startt = chain[0].nodetype
    if not (startt == NodeType.CALLBACK or startt == NodeType.TIMER):
        errors += ["[E105] Invalid chain: Monitored chain starts with a non-timer"
                   " object"]
    endt = chain[-1].nodetype
    if not (endt == NodeType.CALLBACK or endt == NodeType.TOPIC):
        errors += [f"[E106] Invalid chain: Monitored chain ends with a {endt.name}"]
    for node, next_node in zip(chain, chain[1:]):
        if next_node not in node.outgoing:
            errors += [f"[E107] Invalid chain: {node.name} is not linked to"
                       f" {next_node.name}"]
    try:
        chain = graph.find_equivalent_chain(chain)
    except ValueError as ve:
        errors += [f"[E108] Invalid chain: {ve}"]
    return errors

def error_system_incorrect_bcet(system: ros.System) -> list[str]:
    callbacks = system.get_callbacks()
    if all(cb.bcet == cb.wcet for cb in callbacks):
        return []
    if all(cb.bcet == cb.wcet // 2 for cb in callbacks):
        return []
    else:
        return ["[E123]: This model can only model systems that are deterministic "
                "(meaning for each callback, the bcet == wcet) or if "
                "non-deterministic, the bcew of every callback must be wcet / 2"]


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
            feedback += [f"[W102]: '{parent}' has buffersize {str(qos.depth)}"]
    if feedback != []:
        feedback += ["    Note that the Backeman model assumes buffers are large" 
                     "enough to avoid overflow.", 
                     "    In the concrete Uppaal model, a buffersize of 20 is used."]
    return feedback

def validate_timer(timer: ros.Timer) -> Feedback:
    feedback = Feedback()
    if timer.end:
        feedback.warnings += [f"[W103]: Timer {timer.name} has end time, this model"
                              " assumes that timers continue indefinitely"]
    return feedback

def validate_subscription(sub: ros.Subscription) -> Feedback:
    feedback = Feedback()
    if sub.wall_times is not None:
        feedback.errors += [f"[E109]: Subscription {sub.name} has wall times set."
                            " This model does not support wall times"]
    return feedback

def validate_variable(var: ros.Variable) -> Feedback:
    feedback = Feedback()
    errors, warnings = feedback.errors, feedback.warnings
    if var.condition:
        errors += [
                f"[E110] Variable {var.name}: This model does not support conditions"]
    if var.reset_after_read:
        warnings += [f"[W104] Variable {var.name}: This model does not support"
                     " reset after read, but this should not affect results"]
    return feedback

def validate_callback(cb: ros.Callback) -> Feedback:
    feedback = Feedback()
    errors = feedback.errors
    reads = len(cb.read_variables)
    writes = len(cb.write_variables)

    if is_main_task(cb):
        if writes != 0:
            errors += [f"[E111]: Main task '{cb.name}' writes to internal variables"]
    else:
        if reads != 0:
            errors += [f"[E112]: Subtask '{cb.name}' reads variables"]
        if writes > 1:
            errors += [f"[E113]: Subtask '{cb.name}' writes to more than one variable"]

    if cb.calls is not None:
        errors += [f"[E114]: cb '{cb.name}' calls other callbacks"]

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
        warnings += [f"[E115]: Name of node '{node.name}' is not upper case, model"
                     " assumes upper case names. Name is forced to upper case"]
    if len(node.publishers) > 1:
        errors += [f"[E116]: Node '{node.name}' publishes to more than one topic"]
    if len(node.publishers) < 1:
        errors += [f"[E117]: Node '{node.name}' does not have a publisher"]

    main_tasks = sum(is_main_task(cb) for cb in node.callbacks)
    if main_tasks > 1:
        errors += [f"[E118]: Node '{node.name}' has more than one main task"]
    elif main_tasks == 0:
        errors += [f"[E119]: Node '{node.name}' does not have a main task"]

    if not (is_valid_data_generator(node) 
            or is_valid_timer(node)
            or is_valid_subscriber(node)):
        errors += [f"[E120] Node '{node.name}': is neither a data generator, "
                   "timer or subscriber"]
        errors += ["    Full contents of node:",
                   f"    Timers:        {len(node.timers)}",
                   f"    Subscriptions: {len(node.subscriptions)}",
                   f"    Callbacks:     {len(node.callbacks)}",
                   f"    Variables:     {len(node.variables)}"]
    if (not is_valid_data_generator(node)
        and any(timer.probability != 100 for timer in node.timers)):
        errors += [f"[E124]: Node '{node.name}' has non-deterministic timers, yet "
                   "it is not a valid data generator. This model only supports non-"
                   "deterministic release of timer callbacks for nodes that are "
                   "sources of data."]

    return feedback

def validate_executor(executor: ros.Executor) -> Feedback:
    VALID_ROS_DISTRIBUTIONS: set[DISTRIBUTION] = set([
        DISTRIBUTION.Iron,
        DISTRIBUTION.Humble,
        DISTRIBUTION.Galactic,
        DISTRIBUTION.Foxy,
        DISTRIBUTION.Eloquent,
        ])
    VALID_EXECUTORS: set[EXECUTOR] = set([EXECUTOR.SingleThreadedExecutor])
    impl = executor.implementation
    feedback = Feedback()
    errors = feedback.errors
    if impl not in VALID_EXECUTORS:
        errors += [f"[E121]: Host uses an unsupported executor {impl.name}"]
    ros = executor.ros_distribution
    if ros not in VALID_ROS_DISTRIBUTIONS:
        errors += [f"[E122]: Host uses an unsupported ros distribution {ros}"]
    return feedback

def validate_system(system: ros.System, chain: list[GraphNode]) -> Feedback:

    feedback = Feedback()
    errors, warnings = feedback.errors, feedback.warnings
    executor = system.hosts[0].executors[0]

    graph = RosGraphView(system)
    errors += error_graph_limited_node_types(graph)
    errors += error_graph_multiple_topic_publishers(graph)
    errors += error_graph_multiple_variable_writers(graph)
    if chain != []:
        errors += validate_chain(chain, graph)
    errors += error_system_incorrect_bcet(system)
    warnings += warning_buffer_size(system)
    feedback += validate_executor(executor)

    feedback += run_validation(executor.nodes, validate_node)
    feedback += run_validation(system.get_callbacks(), validate_callback)
    feedback += run_validation(system.get_timers(), validate_timer)

    return feedback

# ========================== MONITORING ================================

def monitor(system: bk.System, generator: str, actuator: str, external_event: bool):
    system.actuator = actuator.upper()
    period = -1
    for node in system.nodes:
        node: bk.Node
        if node.name == generator.upper():
            node: bk.DataGenerator
            node.monitored = True
            period = node.period
    if external_event:
        system.period = period
    else:
        system.period = 0

# ============================== MAPPING ===============================

def is_system_deterministic(system: ros.System) -> bool:
    return all(cb.bcet == cb.wcet for cb in system.get_callbacks())

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
    timer = node.timers[0]
    period = timer.period
    delay = timer.offset
    probability = timer.probability
    wcet = node.callbacks[0].wcet
    name = node.name.upper()
    if probability == 100:
        bksystem.add_datagenerator(
                name=name, period=period, wcet=wcet, delay=delay, prio=priority)
    else:
        bksystem.add_probalisticdatagenerator(
                name=name, period=period, wcet=wcet, delay=delay, prob=probability, 
                prio=priority)

# TODO: Move and improve this note
# For examples of how to construct different systems according to which node
# is monitored, see Backeman & Seceleanu (2025), section 4.2
# See also backeman/demo:validation_ss(), prio_inversion() & case_study()

def get_data_source_for_cb_in_chain(chain: list[GraphNode], cb: GraphNode) -> str:
    prev = chain[chain.index(cb)-1]
    if prev.nodetype == NodeType.VARIABLE:
        writecb = prev.incoming[0]
        assert writecb.nodetype == NodeType.CALLBACK
        writesub = writecb.incoming[0]
        assert writesub.nodetype == NodeType.SUBSCRIBER
        writetopic = writesub.incoming[0]
        assert writetopic.nodetype == NodeType.TOPIC
        assert cb.parent is not None
        nn = cb.parent.name.upper()
        wn = writetopic.name.upper()
        assert (isinstance(wn, str))
        return nn + "x" + wn + "_data"
    elif prev.nodetype == NodeType.SUBSCRIBER:
        return "pd"
    else:
        raise Exception(
                f"The graph node previous in the chain to callback {cb.name} was"
                " neither a variable or subscriber. Validation must be incorrect.")

def add_timer(bksystem: bk.System, node: ros.Node, priority: int, chain: list[GraphNode]
              ) -> None:
    main_task, sub_tasks = get_main_and_sub_tasks(node)
    name: str = node.name.upper()
    wcet: int = main_task.wcet
    subscribers: list[str] = [s.topic for s in node.subscriptions]
    wcets: list[int] = [node.get_callback(s.callback).wcet for s in node.subscriptions]
    period = node.timers[0].period
    delay = node.timers[0].offset

    main_task_in_chain = rosgraph.find_in_list(chain, NodeType.CALLBACK, main_task.name)
    if main_task_in_chain is None:
        # NOTE: This is an arbitrary assignment.
        #       Supposing the timer is not part of the monitored chain:
        #       Then any timer or subscriber downstream of the timer that are part of the
        #       monitored chain will not read from a variable that contains data
        #       originating from this timer.
        data_source = name + "x" + subscribers[0] + "_data"
    else:
        data_source = get_data_source_for_cb_in_chain(chain, main_task_in_chain)
        assert data_source != "pd"

    bksystem.add_timer(name=name, period=period, wcet=wcet, delay=delay, 
                       subscribers=subscribers, wcets=wcets, data_source=data_source,
                       prio=priority)

def add_subscriber(bksystem: bk.System, node: ros.Node, chain: list[GraphNode]) -> None:
    
    main_task, sub_tasks = get_main_and_sub_tasks(node)

    name: str = node.name.upper()
    wcet: int = main_task.wcet
    data_source: str = "pd"
    topic: str
    subscribers: list[str] = []
    wcets: list[int] = []

    for sub in node.subscriptions:
        if sub.callback == main_task.name:
            topic = sub.topic.upper()
        else:
            for cb in sub_tasks:
                if sub.callback == cb.name:
                    subscribers.append(sub.topic)
                    wcets.append(cb.wcet)
    assert topic

    main_task_in_chain = rosgraph.find_in_list(chain, NodeType.CALLBACK, main_task.name)
    if sub_tasks == [] or main_task_in_chain is None:
        data_source = "pd"
    else:
        data_source = get_data_source_for_cb_in_chain(chain, main_task_in_chain)
    
    # log.debug("Data source: " + data_source )
    bksystem.add_subscriber(name=name,
                       topic=topic,
                       wcet=wcet,
                       subscribers=subscribers,
                       wcets=wcets,
                       data_source=data_source)

def map_system(system: ros.System, chain: list[GraphNode], external_event: bool) -> bk.System:
    out = bk.System(system.name.upper())
    out.deterministic_hosts(is_system_deterministic(system))
    graph = RosGraphView(system)
    chain = graph.find_equivalent_chain(chain)
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

    generator = chain[0].parent
    actuator = chain[-1].parent
    assert generator is not None
    assert actuator is not None
    monitor(out, generator.name, actuator.name, external_event)

    return out

# ===================== TRANSFORMATION ===========================

def transform_system(system: ros.System, chain: list[GraphNode] | tuple[str,str],
                     external_event: bool = False,
                     ) -> tuple[Feedback, bk.System | None]:

    feedback = validator.validate_system(system)

    if feedback.errors != []:
        return feedback + Feedback(["System is not well formed, cannot start"
                                    " transformation. Validation feedback:"]), None
    if not isinstance(chain, list):
        mon, act = chain
        chain = get_valid_chains(system, mon, act)[0]
    
    feedback += validate_system(system, chain)

    if feedback.errors != []:
        return feedback, None
    return feedback, map_system(system, chain, external_event)

def get_valid_chains(system: ros.System, monitor_node: str, actuator_node: str
               ) -> list[list[GraphNode]]:
    graph = RosGraphView(system)
    for n in system.get_nodes():
        if n.name == monitor_node and is_valid_data_generator(n):
            for cb in n.callbacks:
                if is_main_task(cb):
                    monitor_cb = cb.name
            if monitor_cb == "":
                raise ValueError("Monitor node name is not valid")
        if n.name == actuator_node:
            for cb in n.callbacks:
                if is_main_task(cb):
                    actuator_cb = cb.name
            if actuator_cb == "":
                raise ValueError("Actuator node name is not valid")
    chains = graph[NodeType.CALLBACK][monitor_cb].get_paths_to(
            graph[NodeType.CALLBACK][actuator_cb])
    if len(chains) < 1:
        raise ValueError("There is no data connection between monitor and actuator")
    return chains
