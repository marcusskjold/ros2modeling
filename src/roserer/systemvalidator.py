import roserer.rosgraph as rosgraph
from roserer.types import Feedback, run_validation, NodeType
from roserer.rosgraph import RosGraphView
import roserer.ros2system as ros
import roserer.qos as qos
from roserer.qos import Duration

"""
TODO: Make dicts to map executors to distributions (check for age)
      and operating systems to architectures
TODO: Check if QOS policies are compatible between offer and request
TODO: Add operating system versions
TODO: Consider adding uniqueness checks to all lists
      (that they are essentially sets)
"""


"""
Validation has four stages:
1. Type check with a static type checker such as ty
   This provides guarantees that all objects have valid fields, and that all functions
   are called with correct parameters.
2. The validator starts by constructing a graph representation of the system.
   This provides guarantees described in roserer.rosgraph:RosGraphView.get_graph_view_from()
   Notable:
   - Each node has a single parent
   - Each string reference is valid
3. The validator runs. This gives errors and warnings for graph constraints and
   ros system object constraints.
   Graph:
   - Warning if a topic or service is a source of data, or if a topic is a data sink
     This can catch spelling mistakes in topic names, or well-formedness mistakes in
     the system design.
   - Error if any object that is not either a data generator or could represent input
     external to the system represents a source of data in the graph representation of
     the system.
   - Error if any object type except Node, Executor, Host or System contains another
     system object.
   - Error if any edges in the graph except those to interfaces (topics, services,
     actions) crosses containment boundary (e.g. a callback publishing through a
     publisher in a different node)
4. Each model transformer is responsible for providing validation of model-specific 
   constraints.

"""

# =================== HELPER ==============================

# ===================== GRAPH / RELATIONSHIPS ===================================

# ==================== WARNINGS ===================================

def warning_graph_unbalanced_interfaces(graph: RosGraphView) -> list[str]:
    """
    Report each unbalanced interface in the ros graph.

    Checks if the ros graph has any topics that are only either published to or
    subscribed to, or if any services are offered, but not requested.
    A service cannot be requested without being offered, as this would case an
    error during graph generation (see roserer.rosgraph:string_resolve).

    This is categorized as a warning, because a model could use unbalanced 
    topics or services to serve as input or output channels for their models.
    Note that this means that error_graph_invalid_source does not flag topics
    or services as invalid sources.

    # TODO: Can we convert "wall times" into external input? Currently interfaces
            triggered only by wall times are considered unbalanced.
    """
    sinks = graph.get_sinks()
    sources = graph.get_sources()
    out = []
    out += [f"[W001]: topic {node.name} is published to, but not subscribed to"
            for node in rosgraph.filter_list_by_type(sinks, [NodeType.TOPIC])]
    out += [f"[W002]: topic {node.name} is subscribed to, but not published to"
            for node in rosgraph.filter_list_by_type(sources, [NodeType.TOPIC])]
    out += [f"[W003]: service {node.name} is offered, but not requested"
            for node in rosgraph.filter_list_by_type(sources, [NodeType.SERVICE])]
    # A service cannot be a sink, as it must point to a callback
    # TODO: Check for actions, when they are included.
    # TODO: Handle wall_times by creating external input nodes 
    return out

def warning_graph_empty_container(graph: RosGraphView) -> list[str]:
    """
    Report each empty container in the ros graph.

    SYSTEM, HOST, EXECUTOR and NODE are considered container types. A node of one of
    these types that has no children may indicate a modeling error (e.g. it does not
    make sense to include a host with no executors in your model.) or redundant
    information.
    """
    valid_containers: set[NodeType] = set([NodeType.SYSTEM,
                                           NodeType.HOST,
                                           NodeType.EXECUTOR,
                                           NodeType.NODE])
    nodes = graph.get_all_nodes()
    return [f"[W004]: Container {node.nodetype.name} {node.name} does not contain"
            " other objects."
            for node in nodes
            if node.nodetype in valid_containers
            and node.children == []]

def warning_graph_disconnected_at_host_level(graph: RosGraphView) -> list[str]:
    """
    Report if ros graph is connected at the host level.

    If a ROS2 system is distributed over multiple hosts, but there is no communication
    between elements in those different hosts, the part of the system on one host 
    should have no bearing on the part on another.
    A system that is disconnected at the host level may indicate a modeling mistake,
    but should not cause problems for model checking.
    """
    hosts = graph.get_contracted_view([NodeType.HOST]).get_all_nodes()
    if len(hosts) > 1:
        origin = hosts[0]
        connected = origin.weakly_connected_with()
        for host in hosts:
            if host not in connected:
                return ["[W005]: Not all hosts are connected, for example no object"
                        f" in {host.name} communicates with any object in {origin.name}"]
    return []

# ==================== ERRORS ===================================

def error_graph_invalid_source(graph: RosGraphView) -> list[str]:
    """
    Report each invalid source of data in the ros graph.

    In a ROS2 system, data is either generated from an external input, a message
    or request posted from outside the modelled system, or by a timer.
    
    When representing the data flow as a graph, if some element not of these four
    types is a source node - meaning it has no incoming edges - it must be either
    an unused and therefor redundant part of the system, or it represents a mistake
    in design or modelling of the actual system.
    """
    # TODO: Revisit after wall times discussion
    valid_sources: list[NodeType] = [NodeType.TIMER,
                                     NodeType.TOPIC,
                                     NodeType.EXTERNAL_INPUT,
                                     NodeType.SERVICE]
    invalid_sources = {t for t in NodeType} - set(valid_sources)
    sources = graph.get_sources()
    return [f"[E001]: {node.nodetype.name} {node.name} is a source of data, only"
            f" {[source.name for source in valid_sources]} are valid"
            for node in rosgraph.filter_list_by_type(sources, invalid_sources)]

def error_graph_invalid_container_type(graph: RosGraphView) -> list[str]:
    """
    Report each invalid parent in the ros graph.

    In a ROS2 system, a node is administrated by an executor, which lives on a host.
    Topics are not contained by any other object. All other objects are contained by a
    node. 

    If a graph node of any type except SYSTEM, HOST, EXECUTOR or NODE contains
    another graph node, it represents an error in modeling.

    This validation should never catch an error when run on a non-contracted graph, as 
    containment hierarchies are specified through the typed fields of ros2system 
    classes. Further the graph generation function never assigns an invalid parent.
    For this reason, similar validations are not made to ensure the correct type of
    parents and children relations.
    """
    valid_containers: set[NodeType] = set([NodeType.SYSTEM,
                                           NodeType.HOST,
                                           NodeType.EXECUTOR,
                                           NodeType.NODE])
    nodes = graph.get_all_nodes()
    return [f"[E002]: {node.nodetype.name} {node.name} contains other objects, only"
            f" {[source.name for source in valid_containers]} are valid containers.\n"
            f"    Children of {node.name}: {node.children}"
            for node in nodes
            if node.nodetype not in valid_containers
            and node.children != []]

def error_graph_inter_node_shared_memory(graph: RosGraphView) -> list[str]:
    """
    Report each edge in the ros graph that incorrectly crosses containment boundaries.

    Each ros2system object that handles data is contained in a node.
    Data may only be exchanged between nodes through topics, services or actions.
    In a ros graph representation, this means that the pair of nodes for any incoming 
    or outgoing edge must share the same parent, except those edges that either 
    originates or ends at a TOPIC, SERVICE or ACTION type node.

    A violation of this constraint is either an error in modeling, or means that the
    modelled system has shared inter-node memory.
    """
    # TODO: Properly support topics
    interfaces = set([NodeType.SERVICE, NodeType.ACTION, NodeType.TOPIC])
    return [f"[E003]: {child.nodetype} '{child.name}' shares data with"
            f" {target.nodetype} '{target.name}', even though they belong to different"
            " nodes."
            for node in graph[NodeType.NODE].values()
            for child in node.children
            for target in child.outgoing
            if child.nodetype not in interfaces
            and target.nodetype not in interfaces 
            and target.parent != child.parent]

def error_graph_contains_cycles(graph:RosGraphView) -> list[str]:
    """
    Reports if graph contains cycles.

    The data flow of ros2systems is assumed to be acyclic for the kinds of response-
    time analysis this library is written for.

    A violation of this constraint signifies either a modeling error or a system that
    is not suited for analysis by this package.
    """
    if graph.check_for_cycles():
        return ["[E004]: Graph of system contains cycles. Only acyclic systems may "
                "be analyzed"]
    else:
        return []

# checks that each subscription to same topic uses the same wall_times
# TODO: Consider this would become redundant if wall times were moved to the external output object
def error_system_different_subscription_times(system : ros.System) -> list[str]:
    feedback = []
    topic_subs = {}
    for subscription in system.get_subscriptions():
        topic_subs.setdefault(subscription.topic,[]).append(subscription.wall_times)
    for topic in topic_subs:
        if not all(wt == topic_subs[topic][0] for wt in topic_subs[topic]):
            feedback += [f"[E005]: Different wall-times are being used for"
                         f" subscriptions to {topic}. Make sure that you are using the"
                         " same times for consistency"]
    return feedback

# ==================== OBJECT VALIDATORS ===================================

def warning_system_timer_period_too_small(system: ros.System) -> list[str]:
    warnings: list[str] = []
    if RosGraphView(system).check_for_cycles():
        return []
    for node in system.get_nodes():
        for timer in node.timers:
            wcet = node.full_wcet(timer.callback)
        if timer.period < wcet:
            warnings += [f"[W006]: The timer {timer.name} has a period of"
                         f" {timer.period}. However, the combined wcets of the callback"
                         f" released by this timer is {wcet} (including nested calls)."
                         f" If a model assumes fixed execution-time (equal to wcet),"
                         " then a buffer overflow will trivially occur."]
    return warnings

def validate_qos(qos: qos.QoS, parent: str) -> Feedback:
    """
    Notice that deadline and lifespan are not used in any models currently
    """
    errors = []
    if qos.depth < 0:
        errors += [f"[E006]: {parent} has invalid qos depth policy"]
    # TODO create proper comparison functions for durations
    # Not a current priority, because they are unused
    if qos.deadline < Duration(0, 0):
        errors += [f"[E007]: {parent} has invalid qos deadline policy"]
    if qos.lifespan < Duration(0, 0):
        errors += [f"[E008]: {parent} has invalid qos lifespan policy"]
    if qos.liveliness_lease_duration < Duration(0, 0):
        errors += [ f"[E009]: {parent} has invalid qos liveliness_lease_duration"
                   " policy"]
    return Feedback(errors, [])

def validate_wall_times(owner : str, wall_times : list[int]) -> Feedback:
    """
    Walltimes are well formed if:
    - It is a weakly increasing sequence of timepoints
      (e.g. two messages could arrive simultaneously)
    """
    errors = []
    if not all(wall_times[i] <= wall_times[i+1] for i in range(len(wall_times) - 1)):
        errors += [f"[E010]: Wall-times of {owner} are not weakly increasing."]
    if not all(time >= 0 for time in wall_times):
        errors += [f"[E011]: Wall-times of {owner} include negative time"]
    return Feedback(errors, [])

def validate_client(client: ros.Client) -> Feedback:
    return Feedback()

def validate_publisher(publisher: ros.Publisher) -> Feedback:
    return Feedback()

def validate_variable(var: ros.Variable) -> Feedback:
    return Feedback()

def validate_callback(callback: ros.Callback,) -> Feedback:
    if callback.wcet < 0:
        return Feedback([f"[E012]: Callback '{callback.name}' has a negative wcet"], 
                        [])
    if callback.bcet < 0:
        return Feedback([f"[E017]: Callback '{callback.name}' has a negative bcet"], 
                        [])
    if callback.bcet > callback.wcet:
        return Feedback([f"[E018]: Callback '{callback.name}' has a bcet larger than its wcet"], 
                        [])
    # Remember to validate requests if necessary
    # Not currently necessary
    return Feedback()

def validate_external_input(input: ros.ExternalInput) -> Feedback:
    # TODO: External input should be external to the node object.
    return Feedback()

def validate_external_output(output: ros.ExternalOutput) -> Feedback:
    return Feedback()

def validate_subscription(subscription: ros.Subscription) -> Feedback:
    """
    A subscription is well formed if:
    - It has well-formed wall-times (if any)
    - It has the same wall_times (in terms of length and values) as other subscriptions
      with the same topic
    """
    if subscription.wall_times:
        return validate_wall_times(subscription.name, subscription.wall_times)
    return Feedback()

def validate_timer(timer: ros.Timer) -> Feedback:
    """
    A timer is well formed if:
    - It has a valid period
    - It calls a callback that is owned by the same node
    - It's end-time is None or positive 
    - It's end-time is None or doesn't precede the first callback-release of the timer
    """
    feedback = Feedback()
    errors = feedback.errors
    if timer.period < 0:
        errors += [f"Timer '{timer.name}' must not have a negative period"]
    if timer.end: # TODO: probably add modulo/residue here -> maybe split up
        if timer.end < 0:
            errors += [f"Timer '{timer.name}' must end at a positive point in time."]
        first_release = (timer.offset % timer.period) if timer.offset < 0 else timer.period + timer.offset
        if timer.end < first_release:
            errors += [f"Timer '{timer.name}' ends before it releases anything."]
    return feedback

def validate_service(service: ros.Service) -> Feedback:
    """
    A service is well formed if:
    - It has well-formed wall-times (if any)
    """
    feedback = Feedback()
    if service.wall_times:
        feedback += validate_wall_times(service.name, service.wall_times)
    return feedback

def validate_action(action: ros.Action) -> Feedback:
    #TODO: Implement actions
    return Feedback()

def validate_node(node: ros.Node) -> Feedback:
    """
    A node is well formed if:
    - It has at least one trigger 
      [timer, subscription, service, external input, action]
    - It has at least one callback
    """
    feedback = Feedback()
    errors = feedback.errors
    # internal
    if len(node.callbacks) < 1:
        errors += [f"[E013]: Node '{node.name}' must have at least one callback"]
    total_triggers = (0
            + len(node.external_inputs)
            + len(node.subscriptions)
            + len(node.timers)
            + len(node.services)
            + len(node.actions)
            )
    if total_triggers < 1:
        errors += [f"[E014]: Node '{node.name}' must have at least one trigger"]
    return feedback

def validate_executor(executor: ros.Executor) -> Feedback:
    return Feedback()

def validate_host(host: ros.Host) -> Feedback:
    return Feedback()

def validate_system(system: ros.System) -> Feedback:
    feedback = Feedback()
    logger = logging.getLogger(__name__)
    logger.info("Start validation")
    try:
        logger.info("Build graph")
        graph = RosGraphView(system)
        logger.info("Graph built")
    except ValueError as ve:
        return Feedback([f"[E015]: System is not a valid data graph.\n{ve}"], [])
    if len(graph[NodeType.NODE]) < 1:
        return Feedback(["[E016]: System has no nodes"], [])

    # Validate objects
    feedback += run_validation(system.hosts, validate_host)
    feedback += run_validation(system.get_executors(), validate_executor)
    feedback += run_validation(system.get_nodes(), validate_node)
    feedback += run_validation(system.get_callbacks(), validate_callback)
    feedback += run_validation(system.get_subscriptions(), validate_subscription)
    feedback += run_validation(system.get_publishers(), validate_publisher)
    feedback += run_validation(system.get_clients(), validate_client)
    feedback += run_validation(system.get_services(), validate_service)
    feedback += run_validation(system.get_external_inputs(), validate_external_input)
    feedback += run_validation(system.get_external_outputs(), validate_external_output)
    feedback += run_validation(system.get_timers(), validate_timer)
    feedback += run_validation(system.get_variables(), validate_variable)
    feedback += run_validation(system.get_executors(), validate_executor)
    for profile, parent in system.get_qos_profiles():
            feedback += validate_qos(profile, parent)

    # Validate relationships
    feedback.errors += error_system_different_subscription_times(system)
    feedback.errors += error_graph_contains_cycles(graph)
    feedback.errors += error_graph_inter_node_shared_memory(graph)
    feedback.errors += error_graph_invalid_container_type(graph)
    feedback.errors += error_graph_invalid_source(graph)

    feedback.warnings += warning_graph_disconnected_at_host_level(graph)
    feedback.warnings += warning_graph_empty_container(graph)
    feedback.warnings += warning_graph_unbalanced_interfaces(graph)
    feedback.warnings += warning_system_timer_period_too_small(system)

    return feedback
