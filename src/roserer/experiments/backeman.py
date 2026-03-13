import roserer.ros2system as ros
import roserer.systemvalidator as sv
import roserer.adapters.backeman_adapter as ba
import roserer.rosgraph as rosgraph
import logging


def backeman_rt_experiment(
        s: ros.System,
        monitor: str,
        actuator: str,
        ) -> int:
    logger = logging.getLogger(__name__)
    graph = rosgraph.get_graph_view_from(s)
    monitor_cb: str = ""
    actuator_cb: str = ""
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
    chain = rosgraph.get_paths_from(monitor_cb , actuator_cb)[0]
    logger.info(f"Chain to monitor: {chain}")
    logger.info("Transforming system")
    feedback, bksystem = ba.transform_system(s, chain)
    for ln in feedback.errors:
        logger.error(ln)
    for ln in feedback.warnings:
        logger.warning(ln)
    if bksystem is not None:
        ba.monitor(bksystem, monitor, actuator)
        logger.info("Measuring max reaction time of chain")
        time, _, _ = bksystem.max_reaction_time(gen_graph=False)
        if time is not None:
            logger.info(f"Max reaction time: {time}")
            return time
    return -1
