import roserer.dust.dust_system as ds
import roserer.ros2system as ros
import roserer.systemvalidator as validator
import roserer.qos as quality



############################----VALIDATION----############################

def unspecified_warning(component : str) -> list[str]:
    return [f"Be aware that this model doesn't take account of {component}. "
            f"Use another model, if you want {component} to be taken account of"]


def validate_qos(component_name : str, qos : ros.QoS) -> list[str]:
    """A valid QoS:
    - has history > 0
    - all other qos-settings are same as in the default qos-profile in ROS2 (rmw_qos_profile_default in https://github.com/ros2/rmw/blob/rolling/rmw/include/rmw/qos_profiles.h)
    """
    errors: list[str] = []
    default_qos = quality.qos_profile_default()
    for config in vars(qos):
        if getattr(qos,config) is not getattr(default_qos,config):
            errors += [f"Policy {config} in {component_name} isn't the same as in qos_profile_default. Make sure it is"
                       f" set to {getattr(default_qos,config)}"]
    return errors
    


#TODO: This could perhaps return an object that can have validations (and maybe counters) etc. as fields
def validate_system(system : ros.System,
                    validations : validator.ValidationResult
                    )-> tuple[list[str],list[str]]:
    """
    System-constraints:
    - Number of hosts and DDS-implementation is not taken account of in model
    - Each service can only be called from one source
    """
    errors : list[str]= ["Errors:"]
    warnings : list[str] = ["Warnings:"]
    if system.default_distribution not in VALID_ROS_DISTRIBUTIONS["V1"] \
    and system.default_distribution not in VALID_ROS_DISTRIBUTIONS["V2"]:
        warnings += [f"You have chosen the ROS2-distribution, {system.default_distribution}, as your"
                     f"default distribution. Be aware that it is not supported by this model"]
    if system.dds_implementation != "Generic":
        warnings += unspecified_warning("DDS-implementation")
    if len(system.hosts) > 1:
        warnings += unspecified_warning("distribution of the system between hosts")
        warnings += [f"This model expects 100 % thread availability for each executor in the host operating system. "
                     f"If this is not the case, then there might be errors in the system not "
                     f"covered by this model"]
    for host in system.hosts:
        errs, warns = validate_host(host, validations)
        errors += errs
        warnings += warns
    
    # TODO: consider refactoring
    requested_services = []
    # get all potential triggers for requesting service
    triggers = system.get_subscriptions() + system.get_timers() + system.get_services()
    for trigger in triggers:
        # get parent on trigger, dependent on type
        if isinstance(trigger, ros.Subscription):
            prnt = validations.objects.subscription[trigger.name]
        elif isinstance(trigger, ros.Timer):
            prnt = validations.objects.timer[trigger.name]
        else:
            prnt = validations.objects.service[trigger.name]
        prnt : ros.Node
        # get cb_object
        callback_obj = prnt.get_callback(trigger.callback)
        # do-while loop, going through cb and nested calls
        while True:
            # if cb_object
            if callback_obj.request is not None:
                # add the requested service to list
                client = prnt.get_client(callback_obj.request.client)
                requested_services.append(client.service)
            if callback_obj.calls is not None:
                callback_obj = prnt.get_callback(callback_obj.calls)
            else:
                break

    # if the same service requested more than once
    if len(requested_services) != len(set(requested_services)):
        errors += [f"The same service is being requested from multiple sources. "
                   f"This model only support a service being requested from one place."]

    return errors, warnings

def validate_host(host : ros.Host,
                  validations : validator.ValidationResult
                  )-> tuple[list[str],list[str]]:
    """
    Host-constraints:
    - Is abstracted away in the Dust-model
    - Assumes 100 % thread-availability for each executor (p. 311)
    """
    errors: list[str] = []
    warnings: list[str] = []

    if host.default_distribution not in VALID_ROS_DISTRIBUTIONS["V1"] \
    and host.default_distribution not in VALID_ROS_DISTRIBUTIONS["V2"]:
        warnings += [f"You have chosen the ROS2-distribution, {host.default_distribution}, as your "
                     f"default distribution. Be aware that it is not supported by this model"]
    if host.operating_system != "Generic":
         warnings += unspecified_warning("operating system")
    if host.operating_system != "Generic":
         warnings += unspecified_warning("architecture")
    for executor in host.executors:
        errs, warns = validate_executor(executor, validations)
        errors += errs
        warnings += warns
    return errors, warnings


def validate_executor(executor : ros.Executor,
                      validations : validator.ValidationResult
                      ) -> tuple[list[str],list[str]]:
    """
    a valid Executor:
    - Runs on a distribution of ROS2 released before Jazzy Jalizico 
      (see VALID_ROS_DISTRIBUTIONS)
    - Is an implementation of the SingleThreadedExecutor
    - Doesn't discern between what nodes different callbacks belongs to 
      TODO: is this ever the case?
    """
    errors: list[str] = []
    warnings: list[str] = []
    if executor.ros_distribution not in VALID_ROS_DISTRIBUTIONS["V1"] \
    and executor.ros_distribution not in VALID_ROS_DISTRIBUTIONS["V2"]:
        errors += [f"Executor '{executor.name}' runs on a distribution not supported by this model. "
                   f"Make sure that the distribution is one of the following: "
                     + ', '.join(map(str, VALID_ROS_DISTRIBUTIONS["V1"]))
                     + " "
                     + ', '.join(map(str, VALID_ROS_DISTRIBUTIONS["V2"]))
                     + "."]
    if executor.implementation != "SingleThreadedExecutor":
        errors += [f"The implementation, {executor.implementation}, of '{executor.name}' is not supported. "
                   f"This model only supports variants of the SingleThreadedExecutor implementation"]
    if len(executor.nodes) > 1: # TODO: is this ever the case.
        warnings += [f"This models doesn't discern between nodes under the same executor. Use another model "
                     f"if this distinction is relevant to you."]
    for node in executor.nodes:
        errs, warns = validate_node(node, validations)
        errors += errs
        warnings += warns
    return errors, warnings

def validate_node(node : ros.Node,
                  validations : validator.ValidationResult
                  )-> tuple[list[str],list[str]]:
    """
    a valid Node:
    - Doesn't contain any actions (TODO: is this the case?)
    - Doesn't consider read/write-variables
    - Doesn't consider external i/o
    """
    errors: list[str] = []
    warnings: list[str] = []
    if node.actions:
        errors += [f"This model doesn't support ROS2 actions. Please remove any actions from your system in order "
                   f"to use this model."]
    if node.variables:
        warnings += unspecified_warning("read/write variables")
    for callback in node.callbacks:
        errs, warns = validate_callback(callback, validations)
        errors += errs
        warnings += warns
    for timer in node.timers:
        errs, warns = validate_timer(timer, validations)
        errors += errs
        warnings += warns
    if node.external_outputs:
        warnings += unspecified_warning("external output")
    if node.external_inputs:
        warnings += unspecified_warning("external input")
    for subscription in node.subscriptions:
        errs, warns = validate_subscription(subscription, validations)
        errors += errs
        warnings += warns
    for service in node.services:
        errs, warns = validate_service(service, validations)
        errors += errs
        warnings += warns
    return errors, warnings

def validate_timer(timer : ros.Timer,
                   validations : validator.ValidationResult
                   )-> tuple[list[str],list[str]]:
    """
    A valid Timer:
    - Has a period larger than the wcet of its callback
    """
    # gets sum of wcet of nested calls
    def full_wcet(cb : ros.Callback, prnt : ros.Node) -> int:
        wcet = cb.wcet
        while cb.calls is not None:
            nested_cb = prnt.get_callback(cb.calls)
            cb = nested_cb
            wcet+= cb.wcet
        return wcet

    errors: list[str] = []
    warnings: list[str] = []
    parent = validations.objects.timer[timer.name]
    timer_callback = parent.get_callback(timer.callback)
    wcet = full_wcet(timer_callback, parent)
    if timer.period < wcet:
        errors += [f"This model assumes fixed execution-time (equal to wcet). Make sure that {timer.name} has wcet < period,"
                   f"or otherwise a bufferoverflow will trivially occur."]
    return errors, warnings

def validate_subscription(subscription : ros.Subscription, 
                          validations : validator.ValidationResult
                          )-> tuple[list[str],list[str]]:
    """
    A valid subscription:
    - Only has wall_times if no other callback is sending messages to the triggering 
      interface. 
      This is because exactly 1 template template must be made for each callback.
    """
    errors: list[str] = []
    warnings: list[str] = []
    if subscription.wall_times \
        and subscription.topic in validations.interfaces["topics published to"] \
              and len(validations.interfaces["topics published to"][subscription.topic]) > 0:
        errors += [f"Subscription, {subscription.name}, is triggered by wall_times by messages from "
                   f"topic, {subscription.topic}, but other callbacks are publishing to this topic. "
                   f"Remove the wall_times from this subscription or make sure no other callback is publishing "
                   f"to this topic."]
    errors += validate_qos(subscription.name, subscription.qos)
    return errors, warnings

def validate_service(service : ros.Service,
                     validations : validator.ValidationResult
                     ) -> tuple[list[str],list[str]]:
    """
    A valid service:
    - Only has wall_times if no other callback is sending messages to the triggering
      interface. This is because exactly 1 template template must be made for each 
      callback, due to the input-buffer being modeled here.
      See Dust et al. (2025) - pp. 318, 322.
    """
    errors: list[str] = []
    warnings: list[str] = []
    if service.wall_times \
          and service.name in validations.interfaces["services requested"] \
              and len(validations.interfaces["services requested"][service.name]) > 0:
        errors += [f"Service, {service.name}, is triggered by wall_times of client-requests "
                   f"but other callbacks in the system are requesting this service. "
                   f"Remove the wall_times from this service or make sure no other callback is requesting "
                   f"this service."]
    errors += validate_qos(service.name, service.qos)
    return errors, warnings

def validate_callback(callback : ros.Callback,
                      validations : validator.ValidationResult
                      )-> tuple[list[str],list[str]]:
    """
    A valid Callback:
    - does not consider read-variables and write-variables
    """
    errors: list[str] = []
    warnings: list[str] = []
    if callback.read_variables or callback.write_variables:
        warnings += unspecified_warning("read/write variables")
    return errors, warnings
    


####All callbacks
# a callback must be associated to exactly 1 executor
# only 1 callback per service at the server-side



####Sporadic callback
# INVARIANT: length must correspond to non-zero values in releases-array 
#            (except if first is zero?)



################ TRANSLATION ################

VALID_ROS_DISTRIBUTIONS = {
    "V2" : 
    [
        "Iron", # TODO: is this the case?
        "Iron Irwini", 
        "Humble",
        "Humble Hawksbill"
        "Galactic",
        "Galactic Geochelone",
        "Foxy",
        "Foxy Fitzroy",
        "Eloquent",
        "Eloquent Elusor",
    ],
    "V1" :
    [
        "Dashing",
        "Crystal",
        "Bouncy",
        "Ardent",
        "Dashing Diademata",
        "Crystal Clemmys",
        "Bouncy Bolson",
        "Ardent Apalone",
    ]
}



# cb_type encodings for the UPPAAL-model
TIMER = 0
SERVICE = 1
SUBSCRIBER = 2
CLIENT = 3
# (additional ones for counter)
SENDER = 4
RECEIVER = 5
EXECUTOR = 6

# convert offset and end to wall-times (including 'end' timepoint)
def get_interval_times(timer : ros.Timer) -> list[int]:
    if timer.end is None:
        raise ValueError("Timer does not have finite lifetime")
    wall_times = []
    first_release = (timer.offset % timer.period) if timer.offset < 0 else timer.period + timer.offset
    for wt in range(first_release, timer.end+1, timer.period):
        wall_times.append(wt)
    return wall_times


def map_data_sending(out: ds.System,
                     parent_node : ros.Node,
                     callback : ros.Callback, 
                     validations: validator.ValidationResult,
                     interface_count : int = None, 
                     interface_id_list : list[int] = None, 
                     interface_release_times : list[int] = None,
                     wcet : int = None)-> tuple[int, list[int], list[int], int]:
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
        if not out.has_id(publisher, "publisher"):      
            sender_id = out.get_registered_id(publisher, "publisher")
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
                    validations=validations
                    )
        # else just register among publishers in template
        else:
            sender_id = out.get_registered_id(publisher, "publisher")
            interface_id_list.append(sender_id)
            interface_release_times.append(wcet)

    # look for request
    if callback.request is not None:
        #register sender
        interface_count += 1
        sender_id = out.gen_id("request") # TODO: avoid duplicates here
        interface_id_list.append(sender_id)
        interface_release_times.append(wcet)

        # map topic from client to server
        request = callback.request
        client = parent_node.get_client(request.client)
        server_receiver_id = map_req_topic(
                out=out,
                client=client,
                sender_id=sender_id,
                validations=validations
                )

        # Map server-callback and topic back.
        # Must map (Topic X DataCallback X Topic) templates pr. client-server-
        # communication
        service = client.service
        client_receiver_id = map_server(
                out=out,
                service=service,
                receiver_id=server_receiver_id,
                validations=validations)

        # map client's response-callback
        # only one will exist, as service can only be invoked from one place
        map_client(out=out, receiver_id=client_receiver_id, validations=validations, request=request)
    
    # if any nested calls: recursively map their sending and add it to parameters before return
    if callback.calls is not None: #TODO: check that circularity of calls are validated against!!!!
        nested_cb = parent_node.get_callback(callback.calls)
        call_interface_count, call_interface_id_list, call_interface_release_times, call_wcet = map_data_sending(out=out,
                                                                                                       parent_node=parent_node,
                                                                                                       callback=nested_cb,
                                                                                                       validations=validations,
                                                                                                       interface_count=interface_count,
                                                                                                       interface_id_list=interface_id_list,
                                                                                                       interface_release_times=interface_release_times,
                                                                                                       wcet=wcet
                                                                                                       )
        interface_count = call_interface_count
        interface_id_list = call_interface_id_list
        interface_release_times = call_interface_release_times
        wcet = call_wcet 
    return interface_count, interface_id_list, interface_release_times, wcet


def map_subscriber_cb(
        out: ds.System,
        receiver_id : int,
        callback : str,
        topic : str,
        validations: validator.ValidationResult
        ):
    # get node-object
    node : ros.Node = validations.objects.callback[callback]
    callback_obj : ros.Callback = node.get_callback(callback)
    # in case more subscriptions are using same callback
    subscriptions : list[ros.Subscription] = [
            sub for sub in node.subscriptions if sub.callback == callback]
    for subscription in subscriptions:
        if subscription.topic == topic:
            # get sender info
            interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=node,
                                                                callback=callback_obj,validations=validations)
            # create callback
            cb_id = out.get_cb_id(validations.objects.node[node.name].name, subscription.name)
            out.add_data_callback(id= cb_id,
                                  exec_time=wcet,
                                  topicID=receiver_id,
                                  type=SUBSCRIBER,
                                  buffersize=subscription.qos.depth,
                                  amount_of_publishers=interface_count,
                                  publisher_release_time=interface_release_times,
                                  publisher_id=interface_id_list,
                                  executorID= out.get_exe_register_id(node.name)
                                  )

# maps topic from client to server
def map_req_topic(
        out : ds.System,
        client : ros.Client,
        sender_id : int,
        validations : validator.ValidationResult
        ) -> int:
    # id for requesting from client to server-callback
    receiver_id = out.gen_id("response") # TODO: make avoid duplicates?
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
        service : str,
        receiver_id : int,
        validations: validator.ValidationResult
        ) -> int:
    ### UPPAAL-DataCallback in server ###
    # id for sending back to client
    sender_id = out.gen_id("server") # TODO: avoid redundancies here, maybe?
    server_callback = validations.interfaces['services offered'][service][0] 
    server_node : ros.Node = validations.objects.callback[server_callback]
    server_callback_object = server_node.get_callback(server_callback) 
    server = server_node.get_service(service)

    # get publishing-info (response to client included)
    interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=server_node,
                                                        callback=server_callback_object,validations=validations, interface_count=1,
                                                        interface_id_list=[sender_id],
                                                        interface_release_times=[server_callback_object.wcet])


    # create data-callback for sending back to client (upon receiving request)
    cb_id = out.get_cb_id(validations.objects.node[server_node.name].name, service)
    out.add_data_callback(id=cb_id,
                          exec_time=wcet,
                          topicID=receiver_id,
                          type=SERVICE,
                          buffersize=server.qos.depth,
                          amount_of_publishers=interface_count,
                          publisher_release_time=interface_release_times,
                          publisher_id=interface_id_list,
                          executorID=out.get_exe_register_id(server_node.name))
    
    ### UPPAAL-Topic back from server to client ###
    # needs additional receiver_id for this 
    # (callback in other end is unique to this relation)
    # id for sending back to client
    receiver_id = out.gen_id("response")
    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=server.qos.depth) 
                  #TODO: add docs that they are same to github-repo
    return receiver_id

# maps data-callback in client upon receiving response from service
def map_client(
        out: ds.System,
        request : ros.Request,
        receiver_id : int,
        validations: validator.ValidationResult
        ):
    parent_node = validations.objects.callback[request.response]
    client_obj = parent_node.get_client(request.client)
    client_callback = parent_node.get_callback(request.response)
    interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=validations.objects.callback[client_callback.name],
                                                        callback=client_callback,validations=validations)
    # add callback for client (upon receiving back from server)
    cb_id = out.get_cb_id(validations.objects.node[parent_node.name].name, client_obj.name)
    out.add_data_callback(id=cb_id, 
                          exec_time=wcet,
                          topicID=receiver_id,
                          type=CLIENT,
                          buffersize=client_obj.qos.depth,
                          amount_of_publishers=interface_count,
                          publisher_release_time=interface_release_times,
                          publisher_id= interface_id_list,
                          executorID=out.get_exe_register_id(parent_node.name)) #TODO: check how qos (requst vs. offered) is resolved


def map_topic(
        out: ds.System,
        publisher : ros.Publisher,
        topic : str,
        sender_id : int,
        validations: validator.ValidationResult) -> None:
    
    # If subscribers for this topic hasn't been made already:
    if not out.has_id(topic, "subscription"):

        # get receiver_id from register
        receiver_id = out.get_registered_id(topic,"subscription")
        # map subscribers:   
        # same callback can be here twice -> make it a set!!
        for callback in set(validations.interfaces['topics subscribed to'][topic]):
            map_subscriber_cb(
                    out=out,
                    receiver_id=receiver_id,
                    topic=topic,
                    callback=callback,
                    validations=validations)
    else: 
        receiver_id = out.get_registered_id(topic,"subscription")
    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=publisher.qos.depth)


def map_node(out: ds.System, node: ros.Node, validations: validator.ValidationResult):
    # case 1) timers
    for timer in node.timers:
        timer_cb = node.get_callback(timer.callback)
        interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=node,
                                                        callback=timer_cb,validations=validations)
        cb_id = out.get_cb_id(validations.objects.node[node.name].name, timer.name)
        if timer.end:
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
                                      executorID=out.get_exe_register_id(node.name)
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
                                      executorID=out.get_exe_register_id(node.name)
                                      )
    # case 2) service with wall_times 
    for service in node.services:
        if service.wall_times:
            service_callback = node.get_callback(service.callback)
            interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=node,
                                                        callback=service_callback,validations=validations)
            cb_id = out.get_cb_id(validations.objects.node[node.name].name, service.name)
            out.add_sporadic_callback(id=cb_id,
                                      exec_time=wcet,
                                      length=len(service.wall_times),
                                      type=SERVICE,
                                      releases=service.wall_times,
                                      buffersize=service.qos.depth, #TODO: make sure that this is 100 % the case?
                                      amount_of_publishers=interface_count,
                                      publisher_release_time=interface_release_times,
                                      publisher_id=interface_id_list,
                                      executorID=out.get_exe_register_id(node.name)
                                      )
    # case 3) subscriber with wall_times 
    for subscription in node.subscriptions:
        if subscription.wall_times:
            subscription_callback = node.get_callback(subscription.callback)
            interface_count, interface_id_list, interface_release_times, wcet = map_data_sending(out=out, parent_node=node,
                                                        callback=subscription_callback,validations=validations)
            cb_id = out.get_cb_id(validations.objects.node[node.name].name, subscription.name)
            out.add_sporadic_callback(id=cb_id,
                                      exec_time=wcet,
                                      length=len(subscription.wall_times),
                                      type=SUBSCRIBER,
                                      releases=subscription.wall_times, 
                                      buffersize=subscription.qos.depth, #TODO: make sure that this is 100 % the case?
                                      amount_of_publishers=interface_count,
                                      publisher_release_time=interface_release_times,
                                      publisher_id=interface_id_list,
                                      executorID=out.get_exe_register_id(node.name)
                                      )


# initiates executors (and maintain mapping from node_name to exec_id)
def map_executor(out: ds.System, executor: ros.Executor) -> None:
    # get id
    id = out.gen_id("executor")
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
        system: ros.System,
        validations : validator.ValidationResult
        ) -> ds.System:
    out = ds.System(system.name)
    # first map all executors
    for host in system.hosts:
        for executor in host.executors:
            map_executor(out=out, executor=executor)
    # then map all callbacks contained in each node
    for host in system.hosts: 
        for executor in host.executors:
            for node in executor.nodes:
                map_node(out=out,node=node,validations=validations) 
                # TODO: maybe other name
    return out


# ===================== TRANSFORMATION ===========================

# TODO: this could maybe become common interface for our adapters?
def transform_system(
        system: ros.System,
        validationresult: validator.ValidationResult | None = None
        ) -> tuple[list[str], list[str], ds.System | None]:

    if validationresult is None:
        validationresult = validator.validate_system(system)
        validationresult: validator.ValidationResult
        if validationresult.errors != []:
            return ([
                "System is not well formed, cannot start transformation. "
                "Validation feedback:"] + validationresult.errors,
                [],
                None)

    errors, warnings = validate_system(
        system, validationresult)

    if errors != ["Errors:"]:
        return errors, warnings, None
    if warnings == ["Warnings:"]:
        warnings = []

    return [], warnings, map_system(system, validationresult)
