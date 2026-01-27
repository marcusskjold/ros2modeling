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

#env from name (python) to id (Uppaal)
nodes = {}


#Should we discern between nodes under same executor?
# TODO: find smartest way to discern between callback-types in meaningful way?
def map_node(out: ds.System, executor: ros.Executor, node: ros.Node):
    return ""

# generate id for Executors
ex_id = itertools.count()
def next_exec():
  return next(ex_id)


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
        #source_object = system. # TODO: find way to fetch the actual callback (for wcet etc.)
        source_id = nodes[validations.objects[source]] #TODO: make sure that source-key is actually name of callback, and that value is name
        #out.add_periodic_callback(id=source_id,) # TODO: adapt to make sporadic possible??!
    return out