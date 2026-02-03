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

#env from created subscribers to receiver-id (if more sending to same topic)
subscribers : dict[str,int] = {}

def adapt_list_size(l : list[int], n):
    if len(l) < n:
        l.extend([0] * (n - len(l)))

# TODO: probably make env out of these, as multiple nodes can publish to same topic
# (is it necessary to discern???)
def map_subscriber_cb(out: ds.System, receiver_id : int, topic : str, validations: validator.ValidationResult):
    # out.add_data_callback()
    return ""


receiver_id = itertools.count()
def next_receiver():
  return next(receiver_id)

# id's for topics (sending to)
sender_id_counter = itertools.count()
def next_sender():
  return next(sender_id_counter)


# TODO: watch out that recursion will not get in way of needing sender_id
# should return id of topic
def map_topic(out: ds.System, topic : str, sender_id : int, validations: validator.ValidationResult) -> None:
    # TODO: this should be called based on whether some already exists (e.g. check presence in subscribers (don't know if service))
        # then use function if not already exists.
    receiver_id = next_receiver()
    # case 1) going to subscriber
    if topic in validations.interfaces['topic subscribed to']:
        for node in validations.interfaces['topic subscribed to'][topic]:
            map_subscriber_cb(out, receiver_id, validations)
    # case 2) going to server
    elif topic in validations.interfaces['services offered']:
        for node in validations.interfaces['services offered'][topic]:
            map_service_cb(out, receiver_id, validations)
    # case 3) going (back) to client
    elif topic in validations.interfaces['services requested']:
        for node in validations.interfaces['services requested'][topic]:
            map_service_cb(out, receiver_id, validations)

    out.add_topic(receiver_id=receiver_id,
                  sender_id=sender_id,
                  delay=0,
                  max_jitter=0,
                  buffersize=10) # TODO: should this be a resolved qos rather?

# id's for callbacks
cb_id = itertools.count()
def next_cb():
  return next(cb_id)

#Should we discern between nodes under same executor?
# TODO: find smartest way to discern between callback-types in meaningful way?
def map_node(out: ds.System, node: ros.Node, validations: validator.ValidationResult):
    # case 1) timers
    for timer in node.timers:
        # finds callback from the timer-name
        timer_cb = next(callback for callback in node.callbacks if callback.name == timer.callback)
        # counter for numbers of interfaces posted to
        interface_count = 0
        # the id's of interfaces posted to (order doesn't matter for our use case (except we want to have specific timestamps -> implementation-detail rather?))
        interface_id_list = []
        # look for publishers
        for publisher in timer_cb.publishers:
            interface_count += 1
            # find publisher-object with name <publisher>
            publisher_obj = next(pub for pub in node.publishers if pub.name == publisher)
            topic = publisher_obj.topic
            # (*1 template per publisher, so will never be redundant*)
            sender_id = next_sender()
            interface_id_list.append(sender_id)
            map_topic(out, topic, sender_id, validations)
        for request in timer_cb.requests:
            interface_count += 1
            # get corresponding client-object
            client_obj = next(client for client in node.clients if client.name == request.client)
            service = client_obj.service
            # TODO: this might need to be own method because of service? (or maybe create one already?)
            sender_id = next_sender()
            interface_id_list.append(sender_id)
            map_topic(out, service, sender_id, validations)
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
