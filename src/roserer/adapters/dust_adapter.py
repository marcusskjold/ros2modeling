from roserer.rosgraph import RosGraphView
import roserer.types as types
from roserer.types import Feedback, DISTRIBUTION, DDS_IMPLEMENTATION, NodeType, run_validation
import roserer.dust.dust_system as ds
import roserer.ros2system as ros
import roserer.systemvalidator as validator
import roserer.qos as quality
from roserer.rosgraph import RosGraphView, GraphNode

############################----HELPER----############################

def unspecified_warning(component : str) -> list[str]:
    # TODO: Reword
    return [f"[W201]: This model does not consider the effect of {component}. "
            "This should not have an effect on the results of the model."]

############################----RELATIONAL VALIDATION----############################

def warning_graph_unconsidered_node_types(graph: RosGraphView) -> list[str]:

    LIMITED_GRAPH_NODE_TYPES: set[NodeType] = {
            NodeType.VARIABLE,
            NodeType.EXTERNAL_OUTPUT,
            NodeType.EXTERNAL_INPUT,
    }
    warnings = []
    for nodetype in LIMITED_GRAPH_NODE_TYPES:
        n = len(graph[nodetype])
        if n > 0:
            warnings += unspecified_warning(nodetype.name.lower())
    return warnings

def warning_system_disconnected_at_executor_level(graph: RosGraphView) -> list[str]:
    executors = graph.get_contracted_view([NodeType.EXECUTOR]).get_all_nodes()
    if len(executors) > 1:
        origin = executors[0]
        connected = origin.weakly_connected_with()
        for executor in executors:
            if executor not in connected:
                return [f"[W202]: Not all executors are connected, for example no object "
                        "in {executor.name} communicates with any object in {origin.name}"]
    return []

def error_graph_service_with_multiple_clients(graph: RosGraphView) -> list[str]:
    """
    Report each service that is requested by more than one client.

    The Dust-model models service/client relations by instantiating a pair of one-to-one
    topics.
    If a service is requested by multiple clients, it must be modeled using multiple
    topics. In this case, the topics will have separate buffers.

    A violation of this constraint would result in buffer overflow checks becoming
    invalid.
    """
    return [f"[E201]: Service {service.name} is requested by more than one client."
            for service in graph[NodeType.SERVICE].values()
            if len(service.incoming) > 1 ]

def error_node_has_multiple_response_callbacks_for_client(node: ros.Node) -> list[str]:
    """
    Report each client that has more than one response callback assigned through
    response objects.

    The Dust-model assumes fixed behavior of callbacks. As such, different responses for the same
    client would not be possible to model. 
    """
    requests: dict[str, set[str]] = {}
    for cb in node.callbacks:
        r = cb.request
        if r is not None:
            requests.setdefault(r.client,set())
            requests[r.client].add(r.response)
    return [f"[E202]: There are multiple response callbacks tied to the same client "
            "{client} in node {node.name}"
            for client, responseset in requests.items()
            if len(responseset) > 1]

def error_graph_unsupported_node_types(graph: RosGraphView) -> list[str]:
    if len(graph[NodeType.ACTION]) > 0:
        return ["[E203]: This model doesn't support ROS2 actions."]
    else:
        return []

def error_system_wt_and_msg_in_one_interface(system: ros.System) -> list[str]:
    """
    A valid subscription:
    - Only has wall_times if no other callback is sending messages to the triggering
      interface.
      This is because exactly 1 template template must be made for each callback.
      See Dust et al. (2025) - pp. 318, 322.
    """
    errors: list[str] = []
    graph = RosGraphView(system)
    errors += [f"[E204]: Subscription {sub.name} to {sub.topic} is triggered by "
               "wall_times, but publishers are also publishing to this topic. "
               "This cannot be modeled correctly by this model. Remove the wall_times "
               "from this subscription or make sure no other callback is publishing "
               "to this topic."
               for sub in system.get_subscriptions()
               if sub.wall_times is not None
               and len(graph[NodeType.SUBSCRIBER][sub.name].incoming) > 0 ]
    errors += [f"[E205]: Service {service.name} is triggered by wall_times of client-"
               "requests but other callbacks in the system are requesting this "
               "service. Remove the wall_times from this service or make sure no other "
               "callback is requesting this service."
               for service in system.get_subscriptions()
               if service.wall_times is not None
               and len(graph[NodeType.SERVICE][service.name].incoming) > 0 ]
    return errors

# ==================== Object validators ==========================

def validate_qos(qos: ros.QoS, component_name : str) -> Feedback:
    """A valid QoS must have the same qos-settings except depth as the default 
    qos-profile in ROS2 (rmw_qos_profile_default in
    https://github.com/ros2/rmw/blob/rolling/rmw/include/rmw/qos_profiles.h)
    """
    feedback = Feedback()
    errors = feedback.errors
    default_qos = quality.qos_profile_default()
    for config in vars(qos):
        if getattr(qos,config) is not getattr(default_qos,config) and config != "depth":
            errors += [f"[E206]: QoS policy {config} in {component_name} is "
                       "unsupported. The model only supports "
                       f"{getattr(default_qos,config)}"]
    return feedback

def validate_executor(executor : ros.Executor) -> Feedback:
    """
    a valid Executor:
    - Runs on a distribution of ROS2 released before Jazzy Jalizico
      (see VALID_ROS_DISTRIBUTIONS)
    - Is an implementation of the SingleThreadedExecutor
    """
    VALID_ROS_DISTRIBUTIONS: list[DISTRIBUTION] = [
            DISTRIBUTION.Iron,
            DISTRIBUTION.Humble,
            DISTRIBUTION.Galactic,
            DISTRIBUTION.Foxy,
            DISTRIBUTION.Eloquent,
            DISTRIBUTION.Dashing,
            DISTRIBUTION.Crystal,
            DISTRIBUTION.Bouncy,
            DISTRIBUTION.Ardent,
        ]
    feedback = Feedback()
    errors, warnings = feedback.errors, feedback.warnings

    VRD: str = ','.join([d.name for d in VALID_ROS_DISTRIBUTIONS])
    if executor.ros_distribution not in VALID_ROS_DISTRIBUTIONS:
        errors += [f"[E207]: Executor '{executor.name}' runs on a distribution not "
                   "supported by this model. Make sure that the distribution is one "
                   f"of the following: {VRD}"]
    if executor.implementation != types.EXECUTOR.SingleThreadedExecutor:
        errors += [f"[E208]: The implementation, {executor.implementation.name}, of "
                   f"'{executor.name}' is not supported. This model only supports "
                   "variants of the SingleThreadedExecutor implementation"]
    if len(executor.nodes) > 1:
        warnings += [f"[W203]: Executor {executor.name} has {len(executor.nodes)} "
                     "nodes. This model assumes that each executor has exactly one "
                     "node. The model produced will treat all nodes under this "
                     "executor as one. This should not cause wrong results."]
    return feedback

def validate_node(node : ros.Node) -> Feedback:
    feedback = Feedback()
    feedback.errors += error_node_has_multiple_response_callbacks_for_client(node)
    return feedback

def validate_subscription(subscription: ros.Subscription) -> Feedback:
    return Feedback()

def validate_service(service : ros.Service) -> Feedback:
    return Feedback()

def validate_callback(callback: ros.Callback) -> Feedback:
    feedback = Feedback()
    warnings = feedback.warnings
    if callback.bcet != callback.wcet:
        warnings += [
                f"[W205]: Callback {callback.name} has bcet different from wcet. "
                "This model does not support non-determinism. The callback will be "
                "modeled as if it always performs at the wcet."
                ]
    return feedback

def validate_variable(var: ros.Variable) -> Feedback:
    feedback = Feedback()
    errors = feedback.errors
    if var.condition:
        errors += [
                f"[E209]: Variable {var.name}: This model does not support conditions"]
    return feedback

def validate_timer(timer: ros.Timer) -> Feedback:
    feedback = Feedback()
    errors = feedback.errors
    if timer.probability != 100:
        errors += [f"[E210]: Timer {timer.name} has a non-100% probability of "
                   "triggering. This model only supports deterministic systems."]
    return feedback

def validate_host(host : ros.Host) -> Feedback:
    """
    Host-constraints:
    - Is abstracted away in the Dust-model
    - Assumes 100 % thread-availability for each executor (p. 311)
    """
    feedback = Feedback()
    warnings = feedback.warnings

    if host.operating_system != "Generic":
         warnings += unspecified_warning("operating system")
    if host.operating_system != "Generic":
         warnings += unspecified_warning("architecture")
    return feedback

# ============================== Main validation ====================================

def validate_system(system : ros.System) -> Feedback:
    """
    System-constraints:
    - Number of hosts and DDS-implementation is not taken account of in model
    - Each service can only be called from one source
    """
    feedback = Feedback()
    errors, warnings = feedback.errors, feedback.warnings

    warnings += ["[W206]: This model expects 100 % thread availability for each "
                 "executor in the host operating system. If this is not the case, "
                 "then there might be errors in the system not covered by this model"]
    if system.dds_implementation != DDS_IMPLEMENTATION.Generic:
        warnings += unspecified_warning("DDS-implementation")
    if len(system.hosts) > 1:
        warnings += unspecified_warning("distribution of the system between hosts")
    # TODO: Make into a check for one to one mapping of executor to hosts.

    graph = RosGraphView(system)
    warnings += warning_graph_unconsidered_node_types(graph)
    warnings += warning_system_disconnected_at_executor_level(graph)

    errors += error_graph_service_with_multiple_clients(graph)
    errors += error_graph_unsupported_node_types(graph)

    feedback += run_validation(system.hosts, validate_host)
    feedback += run_validation(system.get_executors(), validate_executor)
    feedback += run_validation(system.get_nodes(), validate_node)
    feedback += run_validation(system.get_callbacks(), validate_callback)
    feedback += run_validation(system.get_timers(), validate_timer)
    feedback += run_validation(system.get_subscriptions(), validate_subscription)
    feedback += run_validation(system.get_services(), validate_service)
    feedback += run_validation(system.get_variables(), validate_variable)
    for profile, parent in system.get_qos_profiles():
            feedback += validate_qos(profile, parent)

    return feedback

################ TRANSLATION ################

# cb_type encodings for the UPPAAL-model
TIMER = 0
SERVICE = 1
SUBSCRIBER = 2
CLIENT = 3
# (additional ones for counters)
SUB = "subscription"
PUBLISHER = "publisher"
REQUEST = "request"
SENDER = "sender"
RECEIVER = "receiver"
EXECUTOR = "executor"

# convert offset and end to wall-times (including 'end' timepoint)
def get_interval_times(timer : ros.Timer) -> list[int]:
    if timer.end is None:
        raise ValueError("Timer does not have finite lifetime")
    wall_times = []
    first_release = (timer.offset % timer.period) if timer.offset < 0 else timer.period + timer.offset
    for wt in range(first_release, timer.end+1, timer.period):
        wall_times.append(wt)
    return wall_times

# check
def map_data_sending(out: ds.System,
                     parent_node : ros.Node,
                     callback : ros.Callback,
                     system : ros.System,
                     graph : RosGraphView,
                     interface_count : int | None = None,
                     interface_id_list : list[int] | None  = None,
                     interface_release_times : list[int] | None = None,
                     wcet : int | None = None)-> tuple[int, list[int], list[int], int]:
    # counter for numbers of interfaces posted to
    if interface_count is None:
        interface_count = 0
    # the id's of interfaces posted to. Order doesn't matter for our use case,
    # except we want to have specific timestamps -> implementation-detail rather?
    if interface_id_list is None:
        interface_id_list = []
    # timestamp at which a given topic is posted to
    if interface_release_times is None:
        interface_release_times = []
    # net sum wcet of nested calls updated
    if wcet is None:
        wcet = callback.wcet
    else:
        wcet += callback.wcet
    # look for publishers
    for publisher in callback.publishers:
        # register sender
        interface_count += 1
        # create topic-template if publisher not yet mapped
        if not out.has_id(publisher, PUBLISHER):      
            sender_id = out.get_registered_id(publisher, PUBLISHER)
            interface_id_list.append(sender_id)
            interface_release_times.append(wcet)

            # find publisher-object with name <publisher>
            publisher_obj = parent_node.get_publisher(publisher)
            topic = publisher_obj.topic

            # Map communication to RECEIVING node 
            # 1 template per publisher, so will never be redundant
            map_topic(
                    out=out,
                    publisher=publisher_obj,
                    topic=topic,
                    sender_id=sender_id,
                    system=system,
                    graph=graph
                    )
        # else just register among publishers in template
        else:
            sender_id = out.get_registered_id(publisher, PUBLISHER)
            interface_id_list.append(sender_id)
            interface_release_times.append(wcet)

    # look for request
    if callback.request is not None:
        #register sender
        interface_count += 1
        # create request-server-response if not mapped already
        request = callback.request
        client = parent_node.get_client(request.client)
        if not out.has_id(client.name, REQUEST):
            sender_id = out.get_registered_id(client.name, REQUEST)
            interface_id_list.append(sender_id)
            interface_release_times.append(wcet)

            # map topic from client to server
            server_receiver_id = map_req_topic(
                    out=out,
                    client=client,
                    sender_id=sender_id
                    )

            # Map server-callback and topic back.
            # Must map (Topic X DataCallback X Topic) templates pr. client-server-
            # communication
            # get ros-graph-node for server
            server_g_node = graph[NodeType.SERVICE][client.service]
            client_receiver_id = map_server(
                    out=out,
                    server_g_node=server_g_node,
                    receiver_id=server_receiver_id,
                    system=system,
                    graph=graph)

            # map client's response-callback
            # only one will exist per client, as service can only be invoked from one client
            # TODO: could do this inside function?
            client_g_node = graph[NodeType.CLIENT][client.name]
            map_client(out=out, receiver_id=client_receiver_id, request=request, parent_node=parent_node, graph=graph, client_g_node=client_g_node, system=system)
        else:
            # else just register among client-requests in template
            sender_id = out.get_registered_id(client.name, REQUEST)
            interface_id_list.append(sender_id)
            interface_release_times.append(wcet)

    # if any nested calls: recursively map their sending and add it to parameters before return
    if callback.calls is not None: #TODO: check that circularity of calls are validated against!!!!
        nested_cb = parent_node.get_callback(callback.calls)
        call_interface_count, call_interface_id_list, call_interface_release_times, call_wcet = map_data_sending(
                out=out,
                parent_node=parent_node,
                callback=nested_cb,
                interface_count=interface_count,
                interface_id_list=interface_id_list,
                interface_release_times=interface_release_times,
                wcet=wcet,
                graph=graph,
                system=system
                )
        interface_count = call_interface_count
        interface_id_list = call_interface_id_list
        interface_release_times = call_interface_release_times
        wcet = call_wcet
    return interface_count, interface_id_list, interface_release_times, wcet

def map_subscription_cb(
        out: ds.System,
        receiver_id : int,
        system : ros.System,
        sub_g_node : GraphNode,
        graph: RosGraphView
        ):
    # get subscription-object
    parent_node = system.get_node(sub_g_node.parent.name)
    sub_obj = parent_node.get_subscription(sub_g_node.name)
    # # get node-object
    # subscription_g_nodes = [sub for sub in graph[NodeType.TOPIC][topic].outgoing]
    # all_subscriptions = 
    # node : ros.Node = validations.objects.callback[callback]
    callback_obj : ros.Callback = parent_node.get_callback(sub_obj.callback)
    # in case more subscriptions are using same callback
    # subscriptions : list[ros.Subscription] = [
    #         sub for sub in node.subscriptions if sub.callback == callback]

    #if subscription.topic == topic:
        # get sender info
    interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=parent_node,
                                                        callback=callback_obj, graph=graph, system=system)
    # create callback
    cb_id = out.get_cb_id(sub_g_node.parent.parent.name, sub_g_node.name)
    out.add_data_callback(id= cb_id,
                          exec_time=wcet,
                          topicID=receiver_id,
                          type=SUBSCRIBER,
                          buffersize=sub_obj.qos.depth,
                          amount_of_publishers=interface_count,
                          publisher_release_time=interface_release_times,
                          publisher_id=interface_id_list,
                          executorID= out.get_exe_register_id(parent_node.name),
                          name=sub_obj.name
                          )

# maps topic from client to server
def map_req_topic(
        out : ds.System,
        client : ros.Client,
        sender_id : int,
        ) -> int:
    # id for requesting from client to server-callback
    receiver_id = out.gen_id(RECEIVER) # TODO: make avoid duplicates?
    # add topic from client to server
    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=client.qos.depth
                  )

    return receiver_id

# maps server-callback and "topic" from client to server
def map_server(
        out: ds.System,
        server_g_node: GraphNode,
        receiver_id : int,
        graph: RosGraphView,
        system: ros.System
        ) -> int:
    ### UPPAAL-DataCallback in server ###
    # id for sending back to client
    sender_id = out.gen_id(SENDER) # TODO: avoid redundancies here, maybe?
    parent_node = system.get_node(server_g_node.parent.name)
    service = parent_node.get_service(server_g_node.name)
    server_callback_object = parent_node.get_callback(service.callback)
    # server_callback_object = parent_node.get_callback(server_g_node.name)

    # server_callback = validations.interfaces['services offered'][service][0] 
    # server_node : ros.Node = validations.objects.callback[server_callback]
    # server = parent_node.get_service(service)

    # get publishing-info (response to client included)
    interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=parent_node,
                                                        callback=server_callback_object, interface_count=1,
                                                        interface_id_list=[sender_id],
                                                        interface_release_times=[server_callback_object.wcet], graph=graph, system=system)


    # create data-callback for sending back to client (upon receiving request)
    cb_id = out.get_cb_id(server_g_node.parent.parent.name, service.name)
    out.add_data_callback(id=cb_id,
                          exec_time=wcet,
                          topicID=receiver_id,
                          type=SERVICE,
                          buffersize=service.qos.depth,
                          amount_of_publishers=interface_count,
                          publisher_release_time=interface_release_times,
                          publisher_id=interface_id_list,
                          executorID=out.get_exe_register_id(parent_node.name),
                          name=service.name)
    
    ### UPPAAL-Topic back from server to client ###
    # needs additional receiver_id for this
    # (callback in other end is unique to this relation)
    # id for sending back to client
    receiver_id = out.gen_id(RECEIVER)
    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=service.qos.depth)
                  #TODO: add docs that they are same to github-repo
    return receiver_id

# maps data-callback in client upon receiving response from service
def map_client(
        out: ds.System,
        request : ros.Request,
        parent_node : ros.Node,
        client_g_node : GraphNode,
        receiver_id : int,
        graph: RosGraphView,
        system: ros.System
        ):
    client_obj = parent_node.get_client(request.client)
    client_callback = parent_node.get_callback(request.response)
    interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=parent_node,
                                                        callback=client_callback, graph=graph, system=system)
    # add callback for client (upon receiving back from server)
    cb_id = out.get_cb_id(client_g_node.parent.parent.name, client_obj.name)
    out.add_data_callback(id=cb_id,
                          exec_time=wcet,
                          topicID=receiver_id,
                          type=CLIENT,
                          buffersize=client_obj.qos.depth,
                          amount_of_publishers=interface_count,
                          publisher_release_time=interface_release_times,
                          publisher_id= interface_id_list,
                          executorID=out.get_exe_register_id(parent_node.name),
                          name=client_obj.name) #TODO: check how qos (requst vs. offered) is resolved


def map_topic(
        out: ds.System,
        publisher : ros.Publisher,
        topic : str,
        sender_id : int,
        graph: RosGraphView,
        system : ros.System) -> None:

    # If subscribers for this topic hasn't been made already:
    if not out.has_id(topic, SUB):

        # get receiver_id from register
        receiver_id = out.get_registered_id(topic, SUB)
        # map subscribers:   
        sub_g_nodes = [sub for sub in graph[NodeType.TOPIC][topic].outgoing]
        for sub in sub_g_nodes:
            map_subscription_cb(out=out,
                                receiver_id=receiver_id,
                                system=system,
                                sub_g_node=sub, 
                                graph=graph)


        # # same callback can be here twice -> make it a set!!
        # #for callback in set(validations.interfaces['topics subscribed to'][topic]):
        #     # map_subscriber_cb(
        #     #         out=out,
        #     #         receiver_id=receiver_id,
        #     #         topic=topic,
        #     #         callback=callback,
        #     #         subscription=sub,
        #     #         validations=validations,
        #     #         graph=graph)
        # map_subscription_cbs(
        #              out=out,
        #              receiver_id=receiver_id,
        #              topic=topic,
        #              graph=graph)
    else: 
        receiver_id = out.get_registered_id(topic, SUB)
    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=publisher.qos.depth)

def map_node(out: ds.System, node: ros.Node, system: ros.System, graph: RosGraphView):
    # get name of owning executor to fetch cb_id below
    node_graph_node = graph[NodeType.NODE][node.name]
    exe_name = node_graph_node.parent.name
    # case 1) timers
    for timer in node.timers:
        timer_cb = node.get_callback(timer.callback)
        interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=node,
                                                        callback=timer_cb, system=system, graph=graph)
        cb_id = out.get_cb_id(exe_name, timer.name)
        if timer.end is not None: # ( end=0 okay)
            # convert interval to list of release-times
            wt = get_interval_times(timer)
            out.add_sporadic_callback(id=cb_id,
                                      exec_time=wcet,
                                      length=len(wt),
                                      releases=wt,
                                      type=TIMER,
                                      buffersize=1, #TODO: make sure that this is 100 % the case?
                                      amount_of_publishers=interface_count,
                                      publisher_release_time=interface_release_times,
                                      publisher_id=interface_id_list,
                                      executorID=out.get_exe_register_id(node.name),
                                      name=timer.name
                                      )
        else:
            first_release = (timer.offset % timer.period) if timer.offset < 0 else timer.period + timer.offset
            out.add_periodic_callback(id=cb_id,
                                      exec_time=wcet,
                                      period=timer.period,
                                      type=TIMER,
                                      offset=first_release,
                                      buffersize=1, #TODO: make sure that this is 100 % the case?
                                      amount_of_publishers=interface_count,
                                      publisher_release_time=interface_release_times,
                                      publisher_id=interface_id_list,
                                      executorID=out.get_exe_register_id(node.name),
                                      name=timer.name
                                      )
    # case 2) service with wall_times
    for service in node.services:
        if service.wall_times:
            service_callback = node.get_callback(service.callback)
            interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=node,
                                                        callback=service_callback, graph=graph, system=system)
            cb_id = out.get_cb_id(exe_name, service.name)
            out.add_sporadic_callback(id=cb_id,
                                      exec_time=wcet,
                                      length=len(service.wall_times),
                                      type=SERVICE,
                                      releases=service.wall_times,
                                      buffersize=service.qos.depth, #TODO: make sure that this is 100 % the case?
                                      amount_of_publishers=interface_count,
                                      publisher_release_time=interface_release_times,
                                      publisher_id=interface_id_list,
                                      executorID=out.get_exe_register_id(node.name),
                                      name=service.name
                                      )
    # case 3) subscriber with wall_times
    for subscription in node.subscriptions:
        if subscription.wall_times:
            subscription_callback = node.get_callback(subscription.callback)
            interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=node,
                                                        callback=subscription_callback, graph=graph, system=system)
            cb_id = out.get_cb_id(exe_name, subscription.name)
            out.add_sporadic_callback(id=cb_id,
                                      exec_time=wcet,
                                      length=len(subscription.wall_times),
                                      type=SUBSCRIBER,
                                      releases=subscription.wall_times,
                                      buffersize=subscription.qos.depth, #TODO: make sure that this is 100 % the case?
                                      amount_of_publishers=interface_count,
                                      publisher_release_time=interface_release_times,
                                      publisher_id=interface_id_list,
                                      executorID=out.get_exe_register_id(node.name),
                                      name=subscription.name
                                      )

# initiates executors (and maintain mapping from node_name to exec_id)
def map_executor(out: ds.System, executor: ros.Executor) -> None:
    VALID_ROS_DISTRIBUTIONS: dict[str,list[DISTRIBUTION]] = {
        "V2" :
        [
            DISTRIBUTION.Iron,
            DISTRIBUTION.Humble,
            DISTRIBUTION.Galactic,
            DISTRIBUTION.Foxy,
            DISTRIBUTION.Eloquent,
        ],
        "V1" :
        [
            DISTRIBUTION.Dashing,
            DISTRIBUTION.Crystal,
            DISTRIBUTION.Bouncy,
            DISTRIBUTION.Ardent,
        ]
        }
    # get id
    id = out.gen_id(EXECUTOR)
    if executor.ros_distribution in VALID_ROS_DISTRIBUTIONS["V2"]:
        out.add_executor_v2(id)
    else:
        out.add_executor_v1(id)
    timer_id = 0
    subscription_id = 0
    service_id = 0
    client_id = 0
    # register the executor_id for each node
    # and callback-id for timer/sub/service/client
    for node in executor.nodes:
        out.register_node(node.name, id)
        for timer in node.timers:
            out.register_callback(executor.name, timer.name, timer_id)
            timer_id += 1
        for subscription in node.subscriptions:
            out.register_callback(executor.name, subscription.name, subscription_id)
            subscription_id += 1
        for service in node.services:
            out.register_callback(executor.name, service.name, service_id)
            service_id +=1
        for client in node.clients:
            out.register_callback(executor.name, client.name, client_id)
            client_id+=1

def map_system(
        system: ros.System
        ) -> ds.System:
    out = ds.System(system.name)
    graph = RosGraphView(system)
    # first map all executors
    for host in system.hosts:
        for executor in host.executors:
            map_executor(out=out, executor=executor)
    # then map all callbacks contained in each node
    for host in system.hosts:
        for executor in host.executors:
            for node in executor.nodes:
                map_node(out=out,node=node, system=system, graph=graph)
                # TODO: maybe other name
    return out

# ===================== TRANSFORMATION ===========================

# TODO: this could maybe become common interface for our adapters?
def transform_system(system: ros.System) -> tuple[list[str] | ds.System, list[str]]:

    feedback = validator.validate_system(system)
    if feedback.errors != []:
        return (["System is not well formed, cannot start transformation. "
                 "Validation feedback:"] + feedback.errors, feedback.warnings)

    dust_feedback = validate_system(system)
    warnings = dust_feedback.warnings + feedback.warnings

    if dust_feedback.errors != []:
        return dust_feedback.errors, warnings

    return map_system(system), warnings
