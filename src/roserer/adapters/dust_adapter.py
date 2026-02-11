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
# only 1 callback per service at the server-side


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

# adds trailing 0'es to list till it has size n
def adapt_list_size(l : list[int], n):
    if len(l) < n:
        l.extend([0] * (n - len(l)))
    return l

# id's for callbacks
cb_id_counter = itertools.count()
def next_cb():
  return next(cb_id_counter)

def map_data_sending(out: ds.System, parent_node : ros.Node, callback : ros.Callback, validations: validator.ValidationResult) -> tuple[int, list[int]]:
    # counter for numbers of interfaces posted to
    interface_count = 0
    # the id's of interfaces posted to (order doesn't matter for our use case (except we want to have specific timestamps -> implementation-detail rather?))
    interface_id_list = []
    # def register_sender():
    #     nonlocal interface_count
    #     interface_count += 1
    #     nonlocal interface_id_list
    #     sender_id = next_sender()
    #     interface_id_list.append(sender_id)
    #     return sender_id

    # look for publishers
    for publisher in callback.publishers:
        # register sender
        interface_count += 1
        sender_id = next_sender()
        interface_id_list.append(sender_id)

        # find publisher-object with name <publisher>
        publisher_obj = parent_node.get_publisher(publisher)
        topic = publisher_obj.topic
        
        # map communication to RECEIVING node (*1 template per publisher, so will never be redundant*)
        map_topic(out, topic, sender_id, validations)

    # look for request
    if callback.request is not None:
        #register sender
        interface_count += 1
        sender_id = next_sender()
        interface_id_list.append(sender_id)

        # get request and service
        request = callback.request
        service = parent_node.get_client(request.client).service

        # map server (must map (Topic X DataCallback X Topic) templates pr. client-server-communication)
        client_receiver_id = map_server(out=out, service=service, sender_id=sender_id, validations=validations)

        # map client-callback
        map_client(out=out, receiver_id=client_receiver_id, validations=validations, request=request)

    return interface_count, interface_id_list


#TODO : find way to reduce parameters and/or find utilities to make this easier
def map_subscriber_cb(out: ds.System, receiver_id : int, callback : str, topic : str, validations: validator.ValidationResult):
    # get node-object
    node : ros.Node = validations.objects.callback[callback]
    callback_obj : ros.Callback = next(cb for cb in node.callbacks if cb.name == callback)
    subscription_obj = next(sub for sub in node.subscriptions if sub.callback == callback)
    #TODO: Use interfaces indecing to lookup for what is posted to, if any
    # TODO: this should be refactored (together with code in map_node?)
    interface_count, interface_id_list = map_data_sending(out=out, parent_node=node,
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
# for getting receiver-id's
receiver_id_counter = itertools.count()
def next_receiver(topic : str, validations : validator.ValidationResult):
# if not receiver of topic create ID as normal
  if not topic in validations.interfaces['topics subscribed to']:
      return next(receiver_id_counter)
# (if subscriber) check if there is already an ID for receivers of topic
  elif topic in subscribers:
      return subscribers[topic]
# else create new one
  else:
    receiver_id = next(receiver_id_counter)
    subscribers[topic] = receiver_id
    return receiver_id


# maps server-callback and "topic" from client to server
def map_server(out: ds.System, service : str, sender_id : int, validations: validator.ValidationResult) -> int:
    server_callback = validations.interfaces['services offered'][service][0] # TODO: maybe just make 1 or validate that only 1 server exists
    server_node : ros.Node = validations.objects.callback[server_callback]
    server_callback_object = server_node.get_callback(server_callback) 
    server = server_node.get_service(service)

    ### UPPAAL-Topic from client to server ###
    # id for requesting from client to server-callback
    receiver_id = next_receiver(service, validations)
    # add topic from client to server
    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=server.qos.depth
                  )
    
    ### UPPAAL-DataCallback in server ###
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
                          executorID=nodes[server_node.name])
    
    ### UPPAAL-Topic back from server to client ###
        # needs additional receiver_id and sender_id for this (callback in other end is unique to this relation)
    # id for sending back to client
    receiver_id = next_receiver(service, validations)
    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=server.qos.depth) #TODO: add docs that they are same to github-repo
    return receiver_id

# maps data-callback in client upon receiving response from service
def map_client(out: ds.System, request : ros.Request, receiver_id : int, validations: validator.ValidationResult):
    parent_node = validations.objects.callback[request.response]
    client_obj = parent_node.get_client(request.client)
    client_callback = parent_node.get_callback(request.response)
    interface_count, interface_id_list = map_data_sending(out=out, parent_node=validations.objects.callback[client_callback.name],
                                                        callback=client_callback,validations=validations)
    # add callback for client (upon receiving back from server)
    out.add_data_callback(id=next_cb(), 
                          exec_time=client_callback.wcet,
                          topicID=receiver_id,
                          type=CLIENT,
                          buffersize=client_obj.qos.depth,
                          amount_of_publishers=interface_count,
                          publisher_release_time=[0 for i in range(10)],
                          publisher_id= adapt_list_size(interface_id_list,10),
                          executorID=nodes[validations.objects.client[client_obj.name].name]) #TODO: check how qos (requst vs. offered) is resolved


# id's for topics (sending to)
sender_id_counter = itertools.count()
def next_sender():
  return next(sender_id_counter)


def map_topic(out: ds.System, topic : str, sender_id : int, validations: validator.ValidationResult) -> None:
    # If subscribers for this topic hasn't been made already:
    if topic not in subscribers:
        # get receiver_id and record topic in subscribers-env:
        receiver_id = next_receiver(topic, validations)
        # map subscribers:
        for callback in validations.interfaces['topics subscribed to'][topic]:
            map_subscriber_cb(out=out, receiver_id=receiver_id, topic=topic, callback=callback, validations=validations)
    else: 
        receiver_id = subscribers[topic]
    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=10) # TODO: should this be a resolved qos rather?


def map_node(out: ds.System, node: ros.Node, validations: validator.ValidationResult):
    # case 1) timers
    for timer in node.timers:
        timer_cb = node.get_callback(timer.callback)
        interface_count, interface_id_list = map_data_sending(out=out, parent_node=node,
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
        out.add_executor_v2(id, -1)
    else:
        out.add_executor_v1(id, -1)
    # register the executor_id for each node
    for node in executor.nodes:
        nodes[node.name] = id

def map_system(system: ros.System, validations : validator.ValidationResult) -> ds.System:
    out = ds.System(system.name)
    # first map all executors
    for host in system.hosts:
        for executor in host.executors:
            map_executor(out=out, executor=executor)
    # then map all callbacks contained in each node
    for host in system.hosts: 
        for executor in host.executors:
            for node in executor.nodes:
                map_node(out=out,node=node,validations=validations) # TODO: maybe other name
    return out