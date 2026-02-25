from typing import Callable
import roserer.ros2system as ros
import roserer.systemvalidator as sv
import roserer.printers.graph_printer as gp
import logging

def dummy_experimenter(s: ros.System, r: sv.ValidationResult) -> int:
    return 0

def perform_reaction_time_experiment(
        s: ros.System,
        title: str,
        rt_experiment: Callable[[ros.System, sv.ValidationResult], int]
        ) -> int:
    logger = logging.getLogger(__name__)
    logger.info("Drawing graph of system")
    gp.transform_and_save_system(s, f"results/{title}-system-graph.svg")
    logger.info("System graph saved in local results folder")

    logger.info("Validating system")
    r = sv.validate_system(s)
    r: sv.ValidationResult
    if r.errors != []:
        for ln in r.errors:
            logger.error(ln)
        return -1
    else:
        logger.info(f"Callback chains: {len(r.get_all_cb_chains())}")
        logger.info(f"Sinks: {r.sinks}")
        logger.info(f"Sources: , {r.sources}")
        if r.graph is not None:
            logger.info("Drawing callback graph")
            gp.transform_and_save_cb_graph(r.graph, f"results/{title}-cb-graph.svg")
            logger.info("Callback graph saved in local results folder")
        return rt_experiment(s, r)
