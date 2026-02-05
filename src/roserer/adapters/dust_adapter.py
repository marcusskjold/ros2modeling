import roserer.dust.dust_system as ds
import roserer.ros2system as ros
import roserer.systemvalidator as validator
import itertools



############################----VALIDATION----############################

####All templates
# id's must be unique (with respect to other callbacks of same type under same executor, and between executors)
# the system should only use distributions that has the relevant executors (not newer than Humble?)
# read/write variables can not be used -> should prob generate warning, at least.
# calls doesn't make sense either. (maybe not even external i/o)


####All callbacks
# INVARIANT: Timer-buffer size 1?
# is the type-parameter within bounds (0 - 3)
# two last arrays should (probably/preferably) be all 0 when no subscribers
# the release-times for subscribers should be (weakly?) increasing
# all referenced id's should correspond to something (maybe checked in validator already?)
# if Timer-type, then buffersize should be 1
# must have a wcet?
# a callback must be associated to exactly 1 executor


#### Executor
# If more nodes are associated under the same executor, it doesn't seem like the model will recognize?
## there should at least be a warning

#### datacallback
# can not be a timer-callback?


####Sporadic callback
# INVARIANT: length must correspond to non-zero values in releases-array (except if first is zero?)

####Periodic callback
# invariant: period should be less than execution-time -> else overflow is more or less guaranteed?

###services (ROS-side) -> maybe for general validator
# wcet in server-callback must not exceed timeout (or it will never get response) (as of now????)



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


#env from (python) name to exec-id (Uppaal)
nodes : dict[str,int] = {}


def adapt_list_size(l : list[int], n):
    if len(l) < n:
        l.extend([0] * (n - len(l)))

# id's for callbacks
cb_id_counter = itertools.count()
def next_cb():
  return next(cb_id_counter)

def map_sending_callbacks(out: ds.System, parent_node : ros.Node, callback : ros.Callback, validations: validator.ValidationResult) -> tuple[int, list[int]]:
    # counter for numbers of interfaces posted to
    interface_count = 0
    # the id's of interfaces posted to (order doesn't matter for our use case (except we want to have specific timestamps -> implementation-detail rather?))
    interface_id_list = []
    # look for publishers
    for publisher in callback.publishers:
        interface_count += 1
        # find publisher-object with name <publisher>
        publisher_obj = next(pub for pub in parent_node.publishers if pub.name == publisher)
        topic = publisher_obj.topic # TODO: avoid variable-overloading (give other name?)
        # (*1 template per publisher, so will never be redundant*)
        sender_id = next_sender()
        interface_id_list.append(sender_id)
        # map communication to RECEIVING node.
        map_topic(out, topic, sender_id, validations)
    # TODO: maybe fix other way of service communication here!!!
    for request in callback.requests:
        interface_count += 1
        # get corresponding client-object
        client_obj = next(client for client in parent_node.clients if client.name == request.client)
        service = client_obj.service
        # TODO: this might need to be own method because of service? (or maybe create one already?)
        sender_id = next_sender()
        interface_id_list.append(sender_id)
        # # map the request
        # map_topic(out, service, sender_id, validations)
        # # map the server-response
        # sender_id = next_sender()
        # map_topic(out, service, sender_id, validations)
        
        # new idea!: define separate map_topic method (albeit wrapper)
        client_sender_id = map_server(out, service, request, sender_id, validations)
        map_client(client_sender_id, topic, validations, request, client_obj, callback)

        ##!!!!!!!! could return from this and just call map client here!!!!!!!!!


    return interface_count, interface_id_list

# TODO: probably delete this
# #TODO: think about special service constraints(?). maybe that there will (almost always be something the other way around?)
# # TODO: can these be same method, but with type-parameter provided?
# # TODO: probably create separate for server and client (as sendback will be implicit for service?)
# # TODO: maybe ideal that callback the other way is handled here (or before the call, as other way around is deduced from request.)
# # TODO: !!!! This might be made redundant soon
# def map_service_cb(out: ds.System, receiver_id : int, callback : str, topic : str, validations: validator.ValidationResult):
#     node : ros.Node = validations.objects[callback]
#     callback_obj : ros.Callback = next(callback for callback in node.callbacks if callback.name == callback)
#     for request in callback_obj.requests:

#     request_obj = next(req for req in node.callbacks if sub.callback == callback)
#     interface_count, interface_id_list = map_sending_callbacks(out=out, parent_node=node,
#                                                         callback=callback_obj,validations=validations)
#     #TODO: callback other way around (and topic could maybe be added in the map_topic-method)

#     out.add_data_callback(id= next_cb(),
#                           exec_time=callback_obj.wcet,
#                           topicID=receiver_id,
#                           type=SERVICE,
#                           buffersize=service_obj.qos.depth,
#                           amount_of_publishers=interface_count,
#                           publisher_release_time=[0 for i in range(10)],
#                           publisher_id=adapt_list_size(interface_id_list, 10),
#                           executorID=nodes[node.name]
#                           )
#     return ""


#TODO : find way to reduce parameters and/or find utilities to make this easier
# TODO: maybe pass type as argument - maybe evenfind way to have object easilier
def map_subscriber_cb(out: ds.System, receiver_id : int, callback : str, topic : str, validations: validator.ValidationResult):
    # get node-object
    node : ros.Node = validations.objects[callback]
    callback_obj : ros.Callback = next(callback for callback in node.callbacks if callback.name == callback)
    subscription_obj = next(sub for sub in node.subscriptions if sub.callback == callback)
    #TODO: Use interfaces indecing to lookup for what is posted to, if any
    # TODO: this should be refactored (together with code in map_node?)
    interface_count, interface_id_list = map_sending_callbacks(out=out, parent_node=node,
                                                        callback=callback_obj,validations=validations)
    out.add_data_callback(id= next_cb(),
                          exec_time=callback_obj.wcet,
                          topicID=receiver_id,
                          type=SUBSCRIBER,
                          buffersize=subscription_obj.qos.depth,
                          amount_of_publishers=interface_count,
                          publisher_release_time=[0 for i in range(10)],
                          publisher_id=adapt_list_size(interface_id_list, 10),
                          executorID=nodes[node.name]
                          )



#env from created topic-name to receiver-id (handling if more sending to same topic)
subscribers : dict[str,int] = {}
#TODO: adapt to service
receiver_id_counter = itertools.count()
def next_receiver(topic : str, validations : validator.ValidationResult):
# if receiver of topic create ID as normal
  if not topic in validations.interfaces['topic subscribed to']:
      return next(receiver_id_counter)
# (if subscriber) check if there is already an ID for receivers of topic
  elif topic in subscribers:
      return subscribers[topic]
# else create new one
  else:
    receiver_id = next(receiver_id_counter)
    subscribers[topic] = receiver_id
    return next(receiver_id)

# maps server-callback and "topic" from client to server
def map_server(out: ds.System, topic : str, sender_id : int, validations: validator.ValidationResult) -> int:
    server_callback = validations.interfaces['services offered'][topic]
    server_node : ros.Node = validations.objects[server_callback]
    server_callback_object = next(cb for cb in server_node.callbacks if cb.name == server_callback)
    server = next(server for server in server_node.services if server.callback == server_callback)

    ### part 1)
    # id for requesting from client to server-callback
    receiver_id = next_receiver(topic, validations)
    # add topic from client to server
    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=server.qos.depth
                  )
    
    # id for sending back to client
    sender_id = next_sender()
    # create data-callback for sending back to client (upon receiving request)
    out.add_data_callback(id=next_cb(),
                          exec_time=server_callback_object.wcet,
                          topicID=receiver_id,
                          type=SERVICE,
                          buffersize=server.qos.depth,
                          amount_of_publishers=1,
                          publisher_release_time=[0 for i in range(10)],
                          publisher_id=adapt_list_size([sender_id], 10),
                          executorID=nodes[server_node])

    # TODO: return sender_id (and maybe buffer-size of server)
    return sender_id

    # TODO: probably delete this
    # ### part 2)
    # ## TODO: this part (or part of it) can be delegated back to map_topic (needs other name)

    # # add topic back from server to client
    # # needs additional receiver_id and sender_id for this (callback in other end is unique to this relation)
    # # id for sending back to client
    # receiver_id = next_receiver(topic, validations)
    # out.add_topic(receiver_id=receiver_id,
    #               sender_id=sender_id,
    #               delay=0,
    #               max_jitter=0,
    #               buffersize=server.qos.depth) #TODO: add docs that they are same to github-repo

    # # add callback for client (upon receiving back from server) -> so no wcet (as already contained in the sender?)
    # out.add_data_callback(id=next_cb(), #TODO: needs the client object
    #                       exec_time=client_callback.wcet,
    #                       topicID=receiver_id,
    #                       type=CLIENT,
    #                       buffersize=client.qos.depth,
    #                       amount_of_publishers=...,
    #                       publisher_release_time=[0 for i in range(10)],
    #                       executorID=nodes[client]) #TODO: check how qos (requst vs. offered) is resolved


#TODO: reduce number of parameters
def map_client(out: ds.System, topic : str, client_request : ros.Request, sender_id : int, validations: validator.ValidationResult, client_obj : ros.Client, client_callback : ros.Callback):
    # get server-object (TODO : make utility-method)
    server_callback = validations.interfaces['services offered'][topic]
    server_node : ros.Node = validations.objects[server_callback]
    server = next(server for server in server_node.services if server.callback == server_callback)
    # add topic back from server to client
    # needs additional receiver_id and sender_id for this (callback in other end is unique to this relation)
    # id for sending back to client
    receiver_id = next_receiver(topic, validations)
    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=server.qos.depth) #TODO: add docs that they are same to github-repo
    # TODO: make it not recurse infinitely (ignore current request/don't repeat it, somehow)
    interface_count, interface_id_list = map_sending_callbacks(out=out, parent_node=validations.objects[client_callback],
                                                        callback=client_callback,validations=validations)
    # add callback for client (upon receiving back from server) -> so no wcet (as already contained in the sender?)
    out.add_data_callback(id=next_cb(), #TODO: needs the client object
                          exec_time=client_callback.wcet,
                          topicID=receiver_id,
                          type=CLIENT,
                          buffersize=client_obj.qos.depth,
                          amount_of_publishers=interface_count,
                          publisher_release_time=[0 for i in range(10)],
                          publisher_id= adapt_list_size(interface_id_list,10),
                          executorID=nodes[client_obj.name]) #TODO: check how qos (requst vs. offered) is resolved



# id's for topics (sending to)
sender_id_counter = itertools.count()
def next_sender():
  return next(sender_id_counter)


# TODO: watch out that recursion will not get in way of needing sender_id
# should return id of topic
def map_topic(out: ds.System, topic : str, sender_id : int, validations: validator.ValidationResult) -> None:
    # If subscribers for this topic hasn't been made already:
    if topic not in subscribers:
        # get receiver_id and record topic in subscribers-env
        receiver_id = next_receiver(topic, validations)
        for callback in validations.interfaces['topic subscribed to'][topic]: #TODO: this is a callback and not a node
            # map subscribers
            map_subscriber_cb(out=out, receiver_id=receiver_id, topic=topic, callback=callback, validations=validations)
    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=10) # TODO: should this be a resolved qos rather?


#Should we discern between nodes under same executor?
# TODO: find smartest way to discern between callback-types in meaningful way?
def map_node(out: ds.System, node: ros.Node, validations: validator.ValidationResult):
    # case 1) timers
    for timer in node.timers:
        # finds callback from the timer-name
        timer_cb = next(callback for callback in node.callbacks if callback.name == timer.callback)
        interface_count, interface_id_list = map_sending_callbacks(out=out, parent_node=node,
                                                        callback=timer_cb,validations=validations)
        #TODO: for now 10 hardcoded as max-pub-size
        out.add_periodic_callback(id=next_cb(),
                                  exec_time=timer_cb.wcet,
                                  period=timer.period,
                                  type=TIMER,
                                  offset=timer.offset,
                                  buffersize=1, #TODO: make sure that this is 100 % the case?
                                  amount_of_publishers=interface_count,
                                  publisher_release_time=[0 for i in range(10)],
                                  publisher_id=adapt_list_size(interface_id_list, 10),
                                  executorID=nodes[node.name]
                                  )
    # case 2) external input (# TODO:)

# generate id for Executors
ex_id_counter = itertools.count()
def next_exec():
  return next(ex_id_counter)


# initiates executors (and maintain mapping from node_name to exec_id)
def map_executor(out: ds.System, executor: ros.Executor) -> None:
    id = next_exec()
    if executor.ros_distribution in VALID_ROS_DISTRIBUTIONS["V2"]:
        # TODO: specify executor-id properly (maybe with env-dict?)
        out.add_executor_v2(id, -1)
    else:
        out.add_executor_v1(id, -1)
    for node in executor.nodes:
        nodes[node.name] = id
        #map_node(out, executor, node) #TODO: to be removed

def map_system(system: ros.System, validations : validator.ValidationResult) -> ds.System:
    out = ds.System(system.name)
    for host in system.hosts: # TODO: this loop could be inside function and return the whole env ??!!
        for executor in host.executors:
            map_executor(out, executor)
    #Start from each source and create the callbacks gradually
    for source in validations.sources:
        types = get_cb_types
        #source_object = system. # TODO: find way to fetch the actual callback (for wcet etc.)
        source_id = nodes[validations.objects[source]] #TODO: make sure that source-key is actually name of callback, and that value is name
        #out.add_periodic_callback(id=source_id,) # TODO: adapt to make sporadic possible??!
    return out

#def get_nodes()

###Maybe actually create topics dynamically somehow and save env (dict of already created callbacks etc.?)

#TODO: this will probably just end up getting deleted
# returns list of types for the callback (depending on where it is used)
def get_cb_types(cb_name : str, res : validator.ValidationResult, sys : ros.System) -> list[str]:
    node_parent = res.objects.callback[cb_name]
    types = []
    for timer in node_parent.timers:
        if timer.callback == cb_name:
            types.append("Timer")
    for subscription in node_parent.subscriptions:
        if subscription.callback == cb_name:
            types.append("Topic")
    for service in node_parent.services:
        if service.callback == cb_name:
            types.append("Service")
    for cb in node_parent.callbacks:
        if cb.requests != None and cb.name == cb_name:
            types.append("Client")
    return types        
