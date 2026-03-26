import pytest
from functools import partial
from roserer.types import DDS_IMPLEMENTATION, DISTRIBUTION, OPERATING_SYSTEM, ARCHITECTURE, EXECUTOR
import roserer.ros2system as ros
import roserer.experiments.experimenter as exp
import roserer.experiments.backeman as be
import roserer.patterns.backeman as bmp
import roserer.patterns.reference_system as ars
from roserer.patterns.reference_system import (
        add_command_node,
        add_cyclic_node,
        add_fusion_node,
        add_intersection_node,
        add_sensor_node,
        add_transform_node,
        add_fusion_node_no_condition
        )

def scenario_autoware_reference_system_singlethreaded():
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

    assert exp.perform_reaction_time_experiment(s, "autoware_reference_system_singlethreaded", exp.dummy_experimenter) == 0

def scenario_autoware_reference_system_mod_sub_result():
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
    WCET = 10
    # Sensor nodes
    # FrontLidarDriver to VehicleDBWSystem
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
    CYCLE_TIME = 300 # Time in milliseconds. TODO: Make all time equivalent
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
                    ("LanePlanner", "Lanelet2MapLoader"),
                    ("EuclideanClusterDetector", "RayGroundFilter"), # Add
                    ("EuclideanIntersection", "EuclideanClusterSettings"), # Add
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
        add_fusion_node_no_condition(e, name, WCET, sub_topic1, sub_topic2)
        # add_cyclic_node(e, name, WCET, CYCLE_TIME, [sub_topic1, sub_topic2])

    # Cyclic node
    add_cyclic_node(e, "BehaviorPlanner", WCET, CYCLE_TIME,[
        "ObjectCollisionEstimator", "NDTLocalizer", "Lanelet2GlobalPlanner",
        "Lanelet2MapLoader", "ParkingPlanner", "LanePlanner"])

    # Intersection node
    # Replace with multiple transform nodes
    # ars.add_intersection_node_backeman(e, "EuclideanClusterDetector", WCET, [
    #     ("RayGroundFilter", "EuclideanClusterDetector"),
    #     ("EuclideanClusterSettings", "EuclideanIntersection")
    #     ])

    # Command node
    ars.add_command_node_with_pub(e, "VehicleDBWSystem", WCET, "VehicleInterface")
    ars.add_command_node_with_pub(e, "IntersectionOutput", WCET, "EuclideanIntersection")

    experiment = partial(
            # be.backeman_rt_experiment, monitor="FrontLidarDriver", actuator="VehicleDBWSystem")
            be.backeman_rt_experiment, monitor="FrontLidarDriver", actuator="ObjectCollisionEstimator")
    assert exp.perform_reaction_time_experiment(s, "autoware_reference_system_singlethreaded", experiment) == 280

def scenario_autoware_reference_system_mod_sub_overflow():
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
    WCET = 10
    CYCLE_TIME = 299 
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
                    ("LanePlanner", "Lanelet2MapLoader"),
                    ("EuclideanClusterDetector", "RayGroundFilter"), # Add
                    ("EuclideanIntersection", "EuclideanClusterSettings"), # Add
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
        add_fusion_node_no_condition(e, name, WCET, sub_topic1, sub_topic2)
        # add_cyclic_node(e, name, WCET, CYCLE_TIME, [sub_topic1, sub_topic2])

    # Cyclic node
    add_cyclic_node(e, "BehaviorPlanner", WCET, CYCLE_TIME,[
        "ObjectCollisionEstimator", "NDTLocalizer", "Lanelet2GlobalPlanner",
        "Lanelet2MapLoader", "ParkingPlanner", "LanePlanner"])
    # Command node
    ars.add_command_node_with_pub(e, "VehicleDBWSystem", WCET, "VehicleInterface")
    ars.add_command_node_with_pub(e, "IntersectionOutput", WCET, "EuclideanIntersection")

    experiment = partial(
            # be.backeman_rt_experiment, monitor="FrontLidarDriver", actuator="VehicleDBWSystem")
            be.backeman_rt_experiment, monitor="FrontLidarDriver", actuator="ObjectCollisionEstimator")
    with pytest.raises(ZeroDivisionError):
        exp.perform_reaction_time_experiment(s, "autoware_reference_system_singlethreaded", experiment)

def scenario_autoware_reference_system_mod_tim_overflow():
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
    WCET = 10
    CYCLE_TIME = 249
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
                    ("LanePlanner", "Lanelet2MapLoader"),
                    ("EuclideanClusterDetector", "RayGroundFilter"), # Add
                    ("EuclideanIntersection", "EuclideanClusterSettings"), # Add
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
        # add_fusion_node_no_condition(e, name, WCET, sub_topic1, sub_topic2)
        add_cyclic_node(e, name, WCET, CYCLE_TIME, [sub_topic1, sub_topic2])

    # Cyclic node
    add_cyclic_node(e, "BehaviorPlanner", WCET, CYCLE_TIME,[
        "ObjectCollisionEstimator", "NDTLocalizer", "Lanelet2GlobalPlanner",
        "Lanelet2MapLoader", "ParkingPlanner", "LanePlanner"])
    # Command node
    ars.add_command_node_with_pub(e, "VehicleDBWSystem", WCET, "VehicleInterface")
    ars.add_command_node_with_pub(e, "IntersectionOutput", WCET, "EuclideanIntersection")

    experiment = partial(
            # be.backeman_rt_experiment, monitor="FrontLidarDriver", actuator="VehicleDBWSystem")
            be.backeman_rt_experiment, monitor="FrontLidarDriver", actuator="ObjectCollisionEstimator")
    with pytest.raises(ZeroDivisionError):
        exp.perform_reaction_time_experiment(s, "autoware_reference_system_singlethreaded", experiment)

def scenario_autoware_reference_system_mod_tim_result():
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
    WCET = 10
    CYCLE_TIME = 250
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
                    ("LanePlanner", "Lanelet2MapLoader"),
                    ("EuclideanClusterDetector", "RayGroundFilter"), # Add
                    ("EuclideanIntersection", "EuclideanClusterSettings"), # Add
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
        # add_fusion_node_no_condition(e, name, WCET, sub_topic1, sub_topic2)
        add_cyclic_node(e, name, WCET, CYCLE_TIME, [sub_topic1, sub_topic2])

    # Cyclic node
    add_cyclic_node(e, "BehaviorPlanner", WCET, CYCLE_TIME,[
        "ObjectCollisionEstimator", "NDTLocalizer", "Lanelet2GlobalPlanner",
        "Lanelet2MapLoader", "ParkingPlanner", "LanePlanner"])
    # Command node
    ars.add_command_node_with_pub(e, "VehicleDBWSystem", WCET, "VehicleInterface")
    ars.add_command_node_with_pub(e, "IntersectionOutput", WCET, "EuclideanIntersection")

    experiment = partial(
            # be.backeman_rt_experiment, monitor="FrontLidarDriver", actuator="VehicleDBWSystem")
            be.backeman_rt_experiment, monitor="FrontLidarDriver", actuator="ObjectCollisionEstimator")
    assert exp.perform_reaction_time_experiment(s, "autoware_reference_system_singlethreaded", experiment) == 500
