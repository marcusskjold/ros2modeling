from roserer.types import NodeType
import roserer.rosgraph as rosgraph
from roserer.rosgraph import RosGraphView
from typing import Callable
import roserer.ros2system as ros
import roserer.systemvalidator as sv
import roserer.printers.graph_printer as gp
import logging

def dummy_experimenter(s: ros.System) -> int:
    return 0

def perform_reaction_time_experiment(
        s: ros.System,
        title: str,
        rt_experiment: Callable[[ros.System], int]
        ) -> int:
    logger = logging.getLogger(__name__)
    logger.info("Drawing graph of system")
    gp.transform_and_save_system(s, f"results/{title}-system-graph.svg")
    logger.info("System graph saved in local results folder")

    logger.info("Validating system")
    feedback = sv.validate_system(s)
    if feedback.errors != []:
        for ln in feedback.errors:
            logger.error(ln)
        return -1
    graph = RosGraphView(s)
    logger.info(f"Callback chains: {len(graph.get_all_chains())}")
    logger.info(f"Sinks: {[n.name for n in graph.get_sinks()]}")
    logger.info(f"Sources: {[n.name for n in graph.get_sources()]}")
    logger.info("Drawing callback graph")
    cbgraph = rosgraph.filter_list_by_type(graph.get_all_nodes(), [NodeType.CALLBACK])
    gp.transform_and_save_cb_graph(cbgraph, f"results/{title}-cb-graph.svg")
    logger.info("Callback graph saved in local results folder")
    return rt_experiment(s)
