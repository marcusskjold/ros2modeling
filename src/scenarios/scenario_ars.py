import pytest
from functools import partial
from roserer.types import DDS_IMPLEMENTATION, DISTRIBUTION, OPERATING_SYSTEM, ARCHITECTURE, EXECUTOR, NodeType
import roserer.ros2system as ros
import roserer.systemvalidator as systemvalidator
import roserer.experiments.experimenter as exp
import roserer.experiments.backeman as be
import roserer.adapters.dust_adapter as da
import roserer.patterns.backeman as bmp
import roserer.adapters.backeman_adapter as ba
import roserer.patterns.reference_system as ars
from roserer.printers.graph_printer import GraphDrawer
from roserer.patterns.reference_system import (
        add_command_node,
        add_cyclic_node,
        add_fusion_node,
        add_intersection_node,
        add_sensor_node,
        add_transform_node,
        add_fusion_node_no_condition
        )

def create_autoware_reference_system_singlethreaded() -> ros.System:
    """ This function creates a model of the original Autoware Reference System """
    s = ros.System(
            name="Autoware Reference System",
            dds_implementation=DDS_IMPLEMENTATION.Connext,
            default_distribution=DISTRIBUTION.Humble
            # Based on the timing of ros2 releases:
            # https://docs.ros.org/en/rolling/Releases.html
            # Where Connext 6 is the default DDS implementation:
            # https://docs.ros.org/en/humble/Releases/Release-Humble-Hawksbill.html#use-connext-6-by-default
            # And the latest version of ars (1.1.0 at Sep 14, 2023):
            # https://github.com/ros-realtime/reference-system/releases/tag/v1.1.0
            # Note that version 1.0.0 is the only listed release - this is released before Humble.
            # However releases before Humble are no longer supported, and so we assume v1.1.0
            # TODO: Double check the default QoS profiles for this version
            )

    # This is following the implementation for the single threaded executor, where every node is assigned to the same executor.
    # https://ros-realtime.github.io/reference-system/main/the-autoware-reference-system/#ros-2-benchmarks
    h = s.add_host(
            name="host",
            operating_system=OPERATING_SYSTEM.RTLinuxKernel,
            architecture=ARCHITECTURE.arm64
            )

    e = h.add_executor(
            name="SingleThreadedExecutor",
            implementation=EXECUTOR.SingleThreadedExecutor
            )

    WCET = 10

    # Sensor nodes
    CYCLE_TIME = 100 # Time in milliseconds. TODO: Make all time equivalent
    # Specs copied from 
    # https://ros-realtime.github.io/reference-system/main/the-autoware-reference-system/
    # and
    # https://github.com/ros-realtime/reference-system/blob/main/autoware_reference_system/include/autoware_reference_system/autoware_system_builder.hpp

    # Sensors
    sensors = ["FrontLidarDriver",
               "RearLidarDriver",
               "PointCloudMap", 
               "EuclideanClusterSettings",
               "Visualizer",
               "Lanelet2Map"]
    for name in sensors:
        add_sensor_node(e, name, WCET, CYCLE_TIME)

    # Transform nodes
    transformers = [("PointsTransformerFront", "FrontLidarDriver"),
                    ("PointsTransformerRear", "RearLidarDriver"),
                    ("VoxelGridDownsampler", "PointCloudFusion"),
                    ("PointCloudMapLoader", "PointCloudMap"),
                    ("RayGroundFilter", "PointCloudFusion"),
                    ("ObjectCollisionEstimator", "EuclideanClusterDetector"),
                    ("MPCController", "BehaviorPlanner"),
                    ("ParkingPlanner", "Lanelet2MapLoader"),
                    ("LanePlanner", "Lanelet2MapLoader")]
    for name, input_topic in transformers:
        add_transform_node(e, name, WCET, input_topic)

    # Fusion nodes
    fusions = [("PointCloudFusion", "PointsTransformerFront", "PointsTransformerRear"),
               ("NDTLocalizer", "VoxelGridDownsampler", "PointCloudMapLoader"),
               ("VehicleInterface", "MPCController", "BehaviorPlanner"),
               ("Lanelet2GlobalPlanner", "Visualizer", "NDTLocalizer"),
               ("Lanelet2MapLoader", "Lanelet2Map", "Lanelet2GlobalPlanner")]
    for name, sub_topic1, sub_topic2 in fusions:
        add_fusion_node(e, name, WCET, sub_topic1, sub_topic2)

    # Cyclic node
    add_cyclic_node(e, "BehaviorPlanner", WCET, CYCLE_TIME,[
        "ObjectCollisionEstimator", "NDTLocalizer", "Lanelet2GlobalPlanner",
        "Lanelet2MapLoader", "ParkingPlanner", "LanePlanner"])

    # Intersection node
    add_intersection_node(e, "EuclideanClusterDetector", WCET, [
        ("RayGroundFilter", "EuclideanClusterDetector"),
        ("EuclideanClusterSettings", "EuclideanIntersection")
        ])

    # Command node
    add_command_node(e, "VehicleDBWSystem", WCET, "VehicleInterface")
    add_command_node(e, "IntersectionOutput", WCET, "EuclideanIntersection")
    return s

def scenario_ars_passes_validation() -> None:
    s = create_autoware_reference_system_singlethreaded()
    feedback = systemvalidator.validate_system(s)
    assert feedback.errors == []
   
def scenario_ars_draw_graphs() -> None:
    s = create_autoware_reference_system_singlethreaded()
    systemgraph = GraphDrawer(s)
    systemgraph.save_to_file("ars_system_graph.pdf")
    systemgraph = GraphDrawer(s, [NodeType.NODE])
    systemgraph.save_to_file("ars_node_graph.pdf")

def scenario_ars_fails_backeman_validation() -> None:
    s = create_autoware_reference_system_singlethreaded()
    feedback = ba.validate_system(s, [])
    errorcodes = ["[E114]", "[E116]", "[E117]", "[E118]", "[E120]"]
    for error in feedback.errors:
        assert any([ec in error for ec in errorcodes])

def scenario_ars_fails_dust_validation() -> None:
    s = create_autoware_reference_system_singlethreaded()
    feedback = da.validate_system(s)
    errorcodes = ["E209"]
    for error in feedback.errors:
        assert any([ec in error for ec in errorcodes])

# MODEL CHECKING EXPERIMENTS
# ===============================================================================
# From here, we experiment with a modified version of the ARS
# This replaces the problematic fusion nodes and instersection nodes with variations
# We have created two versions of of the modified system, one using subscriptions
# to replace fusion nodes, and another using timers.
# There are four 

    # NOTE: FOR TIMER VERSION: 250 / 10 runs fast (1470), also 251 / 10. 249 / 10 crashes
    #                          224 / 9 crashes, but 225 / 9 runs
    #                          Buffer overflow (+20) happens at a ratio of CYCLE_TIME / WCET < 25
    #       FOR SUB VERSION:   300 / 10 gives result (1100), 299 fails
    # Nondeterminism is impractical because it does not use statistical model checking.

    # FrontLidarDriver to ObjectCollisionEstimator
    # TIMER: 250/10: 750
    # FUSION: 300/10: 580

    # Remember that all times are including worst case event arrival, so to compare to ARS, the period should be subtracted.
    # Note also that if the offsets are randomized, different results are observed.
    # One randomization resulted in Front to ObjectC FUSION version 300/10 to fall to 520.
    # An improvement would be to randomize the offset and running SMC
    # This can be fixed 
    # or running this query:
    # E[<=1000;100](max: monitor.x[lm] * monitor.measure)
    #       

def get_ars_mod(wcet: int, cycle_time: int, subscription: bool = True):
    """
    Creates a modified version of the Autoware Reference System.
    If subscription is True, then the modification will be based on a replacing fusion conditions
    with subscription triggers.
    Otherwise the modification will be based on timers
    """
    s = ros.System(
            name="Autoware Reference System",
            dds_implementation=DDS_IMPLEMENTATION.Connext,
            default_distribution=DISTRIBUTION.Humble
            )

    h = s.add_host(
            name="host",
            operating_system=OPERATING_SYSTEM.RTLinuxKernel,
            architecture=ARCHITECTURE.arm64)
    e = h.add_executor(
            name="SingleThreadedExecutor",
            implementation=EXECUTOR.SingleThreadedExecutor)
    WCET = wcet
    CYCLE_TIME = cycle_time # Time in milliseconds. 
    # Sensors
    sensors = ["FrontLidarDriver",
               "RearLidarDriver",
               "PointCloudMap", 
               "EuclideanClusterSettings",
               "Visualizer",
               "Lanelet2Map"]
    for name in sensors:
        add_sensor_node(e, name, WCET, CYCLE_TIME)

    # Transform nodes
    transformers = [
            ("PointsTransformerFront", "FrontLidarDriver"),
            ("PointsTransformerRear", "RearLidarDriver"),
            ("VoxelGridDownsampler", "PointCloudFusion"),
            ("PointCloudMapLoader", "PointCloudMap"),
            ("RayGroundFilter", "PointCloudFusion"),
            ("ObjectCollisionEstimator", "EuclideanClusterDetector"),
            ("MPCController", "BehaviorPlanner"),
            ("ParkingPlanner", "Lanelet2MapLoader"),
            ("LanePlanner", "Lanelet2MapLoader"),
            ("EuclideanClusterDetector", "RayGroundFilter"), # Replaces intersection node
            ("EuclideanIntersection", "EuclideanClusterSettings"), # Replaces intersection node
            ]
    for name, input_topic in transformers:
        add_transform_node(e, name, WCET, input_topic)

    # Fusion nodes
    fusions = [("PointCloudFusion", "PointsTransformerFront", "PointsTransformerRear"),
               ("NDTLocalizer", "VoxelGridDownsampler", "PointCloudMapLoader"),
               ("VehicleInterface", "MPCController", "BehaviorPlanner"),
               ("Lanelet2GlobalPlanner", "Visualizer", "NDTLocalizer"),
               ("Lanelet2MapLoader", "Lanelet2Map", "Lanelet2GlobalPlanner")]
    for name, sub_topic1, sub_topic2 in fusions:
        if subscription:
            add_fusion_node_no_condition(e, name, WCET, sub_topic1, sub_topic2)
        else:
            add_cyclic_node(e, name, WCET, CYCLE_TIME, [sub_topic1, sub_topic2])

    # Cyclic node
    add_cyclic_node(e, "BehaviorPlanner", WCET, CYCLE_TIME,[
        "ObjectCollisionEstimator", "NDTLocalizer", "Lanelet2GlobalPlanner",
        "Lanelet2MapLoader", "ParkingPlanner", "LanePlanner"])

    # Command node
    ars.add_command_node_with_pub(e, "VehicleDBWSystem", WCET, "VehicleInterface")
    ars.add_command_node_with_pub(e, "IntersectionOutput", WCET, "EuclideanIntersection")

    return s

ars_mod_experiment = [
    (10, 100, True, -1),
    (10, 200, True, -1),
    (10, 299, True, -1),
    (10, 300, True, 280),
    (10, 400, True, 280),
    (10, 449, True, 280),
    (10, 450, True, 280),
    (10, 500, True, 280),
    (10, 599, True, 280),
    (10, 600, True, 280),
    (10, 700, True, 280),
    (10, 800, True, 280),
    (15, 100, True, -1),
    (15, 200, True, -1),
    (15, 299, True, -1),
    (15, 300, True, -1),
    (15, 400, True, -1),
    (15, 449, True, -1),
    (15, 450, True, 420),
    (15, 500, True, 420),
    (15, 599, True, 420),
    (15, 600, True, 420),
    (15, 700, True, 420),
    (15, 800, True, 420),
    (20, 100, True, -1),
    (20, 200, True, -1),
    (20, 299, True, -1),
    (20, 300, True, -1),
    (20, 400, True, -1),
    (20, 449, True, -1),
    (20, 500, True, -1),
    (20, 599, True, -1),
    (20, 600, True, 560),
    (20, 700, True, 560),
    (20, 800, True, 560),
    (10, 100, False, -1),
    (10, 200, False, -1),
    (10, 249, False, -1),
    (10, 250, False, 500),
    (10, 300, False, 550),
    (10, 350, False, 600),
    (10, 400, False, 650),
    (10, 600, False, 850),
    (10, 800, False, 1050),
        ]

@pytest.mark.parametrize("wcet,period,subscription,expected_result", ars_mod_experiment)
def scenario_ars_mod_result(wcet, period, subscription, expected_result):
    s = get_ars_mod(wcet, period, subscription)

    experiment = partial(
            be.backeman_rt_experiment, monitor="FrontLidarDriver", actuator="ObjectCollisionEstimator", external_event=False)
    try:
        assert exp.perform_reaction_time_experiment(s, f"ars_mod_{wcet}_{period}_{subscription}", experiment) == expected_result
    except ZeroDivisionError:
        assert expected_result == -1
