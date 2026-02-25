import roserer.ros2system as ros
import roserer.systemvalidator as sv
import roserer.adapters.backeman_adapter as ba
import logging


def backeman_rt_experiment(s: ros.System, r: sv.ValidationResult) -> int:
    logger = logging.getLogger(__name__)
    chain = r.get_paths_from("SENSOR1_cb0", "ACTUATOR1_cb0")[0]
    logger.info(f"Chain to monitor: {chain}")
    logger.info("Transforming system")
    errors, warnings, bksystem = ba.transform_system(s, chain)
    for ln in errors:
        logger.error(ln)
    for ln in warnings:
        logger.warning(ln)
    if bksystem is not None:
        ba.monitor(bksystem, "sensor1", "actuator1")
        logger.info("Measuring max reaction time of chain")
        time, _, _ = bksystem.max_reaction_time(gen_graph=False)
        if time is not None:
            logger.info(f"Max reaction time: {time}")
            return time
    return -1
