from roserer.qos import Duration
import roserer.ros2system as ros
import roserer.printers.graph_printer as gp
import roserer.systemvalidator as sv

ars = ros.System(
        name="Autoware Reference System",
        dds_implementation="Connext",
        default_distribution="Humble",
        # Based on the timing of ros2 releases:
        # https://docs.ros.org/en/rolling/Releases.html
        # Where Connext 6 is the default DDS implementation:
        # https://docs.ros.org/en/humble/Releases/Release-Humble-Hawksbill.html#use-connext-6-by-default
        # And the latest version of arf (1.1.0 at Sep 14, 2023):
        # https://github.com/ros-realtime/reference-system/releases/tag/v1.1.0
        # Note that version 1.0.0 is the only listed release - this is released before Humble.
        # However releases before Humble are no longer supported, and so we assume v1.1.0
        # TODO: Double check the default QoS profiles for this version
        )

# This is following the implementation for the single threaded executor, where every node is assigned to the same executor.
# https://ros-realtime.github.io/reference-system/main/the-autoware-reference-system/#ros-2-benchmarks
h = ars.add_host(
        name="host",
        operating_system="Raspberry Pi RT Linux kernel",
        architecture="arm64",
        )

e = h.add_executor(
        name="SingleThreadedExecutor",
        implementation="SingleThreadedExecutor",
        )

WCET = 10

# Sensor nodes
CYCLE_TIME = 100 # Time in milliseconds. TODO: Make all time equivalent
# Specs copied from 
# https://ros-realtime.github.io/reference-system/main/the-autoware-reference-system/
# and
# https://github.com/ros-realtime/reference-system/blob/main/autoware_reference_system/include/autoware_reference_system/autoware_system_builder.hpp


def add_sensor_node(e: ros.Executor, name: str):
    n = e.add_node(name=name)
    p = n.add_publisher(topic=name)
    cb = n.add_callback(WCET, publishers=[p])
    n.add_timer(CYCLE_TIME, cb)
    return n

FrontLidarDriver = add_sensor_node(e, name="FrontLidarDriver")

RearLidarDriver = add_sensor_node(e, name="RearLidarDriver")
PointCloudMap = add_sensor_node(e, name="PointCloudMap")
Visualizer = add_sensor_node(e, name="Visualizer")
Lanelet2Map = add_sensor_node(e, name="Lanelet2Map")

# Transform nodes

def add_transform_node(e: ros.Executor, name: str, input_topic: str):
    n = e.add_node(name=name)
    p = n.add_publisher(topic=name)
    cb = n.add_callback(WCET, publishers=[p])
    n.add_subscription(topic=input_topic, callback=cb)
    return n

PointsTransformerFront = add_transform_node(e, "PointsTransformerFront", "FrontLidarDriver")
PointsTransformerRear = add_transform_node(e, "PointsTransformerRear", "RearLidarDriver")
VoxelGridDownsampler = add_transform_node(e, "VoxelGridDownsampler", "PointCloudFusion")
PointCloudMapLoader = add_transform_node(e, "PointCloudMapLoader", "PointCloudMap")
RayGroundFilter = add_transform_node(e, "RayGroundFilter", "PointCloudFusion")
ObjectCollisionEstimator = add_transform_node(e, "ObjectCollisionEstimator", "EuclideanClusterDetector")
MPCController = add_transform_node(e, "MPCController", "BehaviorPlanner")
ParkingPlanner = add_transform_node(e, "ParkingPlanner", "Lanelet2MapLoader")
LanePlanner = add_transform_node(e, "LanePlanner", "Lanelet2MapLoader")


# Fusion nodes

def add_fusion_node(e: ros.Executor, name: str, sub_topic1: str, sub_topic2: str) -> ros.Node:
    n = e.add_node(name=name)
    p = n.add_publisher(topic=name)
    v1 = n.add_variable(reset_after_read=True, condition=True)
    v2 = n.add_variable(reset_after_read=True, condition=True)
    cb3 = n.add_callback(wcet=WCET, read_variables=[v1, v2], publishers=[p])
    cb1 = n.add_callback(0, write_variables=[v1], calls=[cb3.name])
    cb2 = n.add_callback(0, write_variables=[v2], calls=[cb3.name])
    n.add_subscription(topic=sub_topic1, callback=cb1)
    n.add_subscription(topic=sub_topic2, callback=cb2)
    return n

PointCloudFusion = add_fusion_node(e, "PointCloudFusion", "PointsTransformerFront", "PointsTransformerRear")
NDTLocalizer = add_fusion_node(e, "NDTLocalizer", "VoxelGridDownsampler", "PointCloudMapLoader")
VehicleInterface = add_fusion_node(e, "VehicleInterface", "MPCController", "BehaviorPlanner")
Lanelet2GlobalPlanner = add_fusion_node(e, "Lanelet2GlobalPlanner", "Visualizer", "NDTLocalizer")
Lanelet2MapLoader = add_fusion_node(e, "Lanelet2MapLoader", "Lanelet2Map", "Lanelet2GlobalPlanner")


# Cyclic node

def add_cyclic_node(e: ros.Executor, name: str, inputs: list[str]) -> ros.Node:
    # Refer to line 83 of:
    # https://github.com/ros-realtime/reference-system/blob/main/reference_system/include/reference_system/nodes/rclcpp/cyclic.hpp
    # And see that it is resets the cache after each read
    n = e.add_node(name=name)
    variables = []
    for inp in inputs:
        varname = inp + "_cache"
        v = n.add_variable(varname, reset_after_read=True)
        variables.append(v)
        cbb = n.add_callback(0, write_variables=[v])
        n.add_subscription(topic=inp, callback=cbb)

    p = n.add_publisher(topic=name)
    cb = n.add_callback(WCET, publishers=[p], read_variables=variables)
    n.add_timer(CYCLE_TIME, cb)
    return n

BehaviorPlanner = add_cyclic_node(e, "BehaviorPlanner", [
    "ObjectCollisionEstimator", "NDTLocalizer", "Lanelet2GlobalPlanner",
    "Lanelet2MapLoader", "ParkingPlanner", "LanePlanner"])


# Intersection node

def add_intersection_node(e: ros.Executor, name: str, connections: list[tuple[str, str]]) -> ros.Node:
    n = e.add_node(name=name)
    for sub, pub in connections:
        p = n.add_publisher(topic=pub)
        cb = n.add_callback(WCET, publishers=[p])
        n.add_subscription(topic=sub, callback=cb)
    return n

EuclideanClusterDetector = add_intersection_node(e, "EuclideanClusterDetector", [
    ("RayGroundFilter", "EuclideanClusterDetector"),
    ("EuclideanClusterSettings", "EuclideanIntersection")
    ])

# Command node

def add_command_node(e: ros.Executor, name: str, input_topic: str):
    n = e.add_node(name=name)
    cb = n.add_callback(WCET)
    n.add_subscription(topic=input_topic, callback=cb)
    return n

VehicleDBWSystem = add_command_node(e, "VehicleDBWSystem", "VehicleInterface")
IntersectionOutput = add_command_node(e, "IntersectionOutput", "EuclideanIntersection")

# Finally


result = sv.validate_system(ars)
print(result.errors)
gp.transform_and_save_system(ars, "ars.svg")

