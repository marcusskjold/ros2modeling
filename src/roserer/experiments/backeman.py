from roserer.types import NodeType
import roserer.ros2system as ros
import roserer.adapters.backeman_adapter as ba
from roserer.rosgraph import RosGraphView
import logging


def backeman_rt_experiment(
        s: ros.System,
        monitor: str,
        actuator: str,
        ) -> int:
    logger = logging.getLogger(__name__)
    graph = RosGraphView(s)
    monitor_cb: str = ""
    actuator_cb: str = ""
    logger.info("Starting experiment")
    for n in s.get_nodes():
        if n.name == monitor:
            for cb in n.callbacks:
                if ba.is_main_task(cb):
                    monitor_cb = cb.name
            assert monitor_cb != ""
        if n.name == actuator:
            for cb in n.callbacks:
                if ba.is_main_task(cb):
                    actuator_cb = cb.name
            assert actuator_cb != ""
    logger.info(f"Finding paths from {monitor_cb} to {actuator_cb}")
    chain = graph[NodeType.CALLBACK][monitor_cb].get_paths_to(
            graph[NodeType.CALLBACK][actuator_cb])[0]
    logger.info(f"Chain to monitor: {[n.name for n in chain]}")
    logger.info("Transforming system")
    feedback, bksystem = ba.transform_system(s, chain)
    for ln in feedback.errors:
        logger.error(ln)
    for ln in feedback.warnings:
        logger.warning(ln)
    if bksystem is not None:
        ba.monitor(bksystem, monitor, actuator)
        logger.info("Measuring max reaction time of chain")
        time, trace, graph = bksystem.max_reaction_time(gen_graph=True)
        print("Max reaction time: ", str(time))
        if graph is not None:
            logger.info("\n\n\nGraph:")
            logger.info('\n'.join(graph))
        if time is not None:
            logger.info(f"Max reaction time: {time}")
            return time
    return -1
