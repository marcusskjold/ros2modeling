from pathlib import Path
from typing import Iterable
from roserer.types import NodeType
from roserer.rosgraph import RosGraphView, GraphNode
import pygraphviz as pgv
from roserer.systemvalidator import validate_system
from pygraphviz import AGraph
import roserer.ros2system as ros

Graph = dict[str, list[str]]

# ---------------------------------

# def add_cb(graph: AGraph, cb: ros.Callback):
#     if cb.read_variables != []:
#         subg = graph.add_subgraph(
#                 [var for var in cb.read_variables] + [cb.name],
#                 rank="source",
#                 style="invis",
#                 )
#
#     for var in cb.write_variables:
#         graph.add_edge(
#                 cb.name,
#                 var,
#                 arrowsize=ARWSZ,
#                 color="tomato4",
#                 style="dashed",
#                 penwidth=SPEN,
#                 )

class GraphDrawer():
    ARWSZ = "0.5"
    ARWCLR = "black"
    PENWDTH = "0.7"
    SPEN = "0.4"
    VECLR = "steelblue"
    A: AGraph
    edgeconfig: dict[NodeType, dict[str,str]] = {
            NodeType.CALLBACK: {
                "arrowsize": ARWSZ,
                "color": ARWCLR,
                "penwidth": PENWDTH,
                },
            NodeType.PUBLISHER: {
                "arrowsize": ARWSZ,
                "color": ARWCLR,
                "penwidth": PENWDTH,
                },
            NodeType.NODE: {
                "arrowsize": ARWSZ,
                "color": ARWCLR,
                "penwidth": PENWDTH,
                },
            NodeType.EXECUTOR: {},
            NodeType.HOST: {},
            NodeType.CLIENT: {},
            NodeType.SUBSCRIBER: {
                "arrowsize": ARWSZ,
                "color": ARWCLR,
                "penwidth": PENWDTH,
                },
            NodeType.ACTION: {},
            NodeType.EXTERNAL_INPUT: {},
            NodeType.EXTERNAL_OUTPUT: {},
            NodeType.TIMER: {
                "arrowsize": ARWSZ,
                "color": ARWCLR,
                "penwidth": PENWDTH,
                },
            NodeType.SERVICE: {},
            NodeType.SYSTEM: {},
            NodeType.VARIABLE: {
                "arrowsize": ARWSZ,
                "color": VECLR,
                "penwidth": SPEN,
                "constraint": "false",
                "arrowhead": "inv",
                "style": "dashed",
                },
            NodeType.TOPIC: {
                "arrowsize": ARWSZ,
                "color": ARWCLR,
                "penwidth": PENWDTH,
                }
            }
    nodeconfig: dict[NodeType, dict[str,str]] = {
            NodeType.CALLBACK: {
                "shape": "rect",
                "style": "filled"
                },
            NodeType.PUBLISHER: {
                "shape": "invhouse",
                "margin": "0.01",
                "fontsize": "8",
                "width": ".2",
                "style": "filled",
                "fillcolor": "lightpink",
                },
            NodeType.NODE: {
                "cluster": "true",
                "rank": "same",
                "style": "dashed,rounded",
                "color": "lavenderblush3",
                },
            NodeType.EXECUTOR: {
                "cluster": "true",
                "style": "dotted",
                "color": "dimgrey"
                },
            NodeType.HOST: {
                "cluster": "true",
                "style": "solid",
                "color": "dimgrey"
                },
            NodeType.CLIENT: {},
            NodeType.SUBSCRIBER: {
                "shape": "house",
                "fillcolor": "lightblue",
                "style": "filled",
                "fontsize": "8",
                },
            NodeType.ACTION: {},
            NodeType.EXTERNAL_INPUT: {},
            NodeType.EXTERNAL_OUTPUT: {},
            NodeType.TIMER: {
                "shape": "diamond",
                "fontsize": "8",
                "fillcolor": "lightblue",
                "style": "filled"
                },
            NodeType.SERVICE: {},
            NodeType.SYSTEM: {},
            NodeType.VARIABLE: {
                "shape": "oval",
                "style": "filled",
                "fillcolor": "beige",
                "fontsize": "8",
                "margin": "0.01",
                },
            NodeType.TOPIC: {
                "shape":"parallelogram", 
                "style":"filled,dashed", 
                "fillcolor":"beige",
                "margin":"0",
                "height":"0.3",
                "fontsize":"8",
                }
        }
    added: list[GraphNode]

    def __init__(self, sys: ros.System | RosGraphView | list[GraphNode], filter: Iterable[NodeType] | None = None) -> None:
        if isinstance(sys, ros.System):
            feedback = validate_system(sys)
            if feedback.errors != []:
                raise ValueError(f"Invalid system. Feedback: {feedback.errors}")
            graph = RosGraphView(sys)
        elif isinstance(sys, RosGraphView):
            graph = sys
        else:
            graph = RosGraphView(sys)
        if filter is not None:
            graph = graph.get_contracted_view(filter)
        self.added = []
        self.A = pgv.AGraph(
            directed=True,
            strict=True,
            rankdir="TB",
            concentrate="true",
            splines="ortho",
            nodesep=".3",
            ranksep="0.2"
            )
        for node in graph.get_all_nodes():
            self.draw_node(self.A, node)
        for node in graph.get_all_nodes():
            self.draw_edges(node)

    def save_to_file(self, filename: str) -> AGraph:
        path = Path(filename)
    
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        self.A.layout("dot")
        self.A.draw(filename)
        return self.A

    def draw_edges(self, node: GraphNode) -> None:
        for n in node.outgoing:
            self.A.add_edge(
                    f"{node.nodetype.name} {node.name}",
                    f"{n.nodetype.name} {n.name}",
                    **self.edgeconfig[node.nodetype]
                    )

    def draw_node(self, A: AGraph, node: GraphNode) -> None:
        if node in self.added:
            return
        if node.parent is not None and node.parent not in self.added:
            self.draw_node(A, node.parent)
            return
        if node.children != [] and node.outgoing == []:
            subgraph = A.add_subgraph(
                    label=f"{node.name}",
                    name=node.name,
                    **self.nodeconfig[node.nodetype]
                    )
            self.added.append(node)
            for child in node.children:
                self.draw_node(subgraph, child)
        else:
            A.add_node(
                    n=f"{node.nodetype.name} {node.name}",
                    label=f"{node.name}",
                    **self.nodeconfig[node.nodetype],
                    )
            self.added.append(node)
            for neigh in node.outgoing:
                if neigh.parent is None:
                    A.add_edge(
                            f"{node.nodetype.name} {node.name}",
                            f"{neigh.nodetype.name} {neigh.name}",
                            **self.edgeconfig[node.nodetype]
                            )
            
            for child in node.children:
                self.draw_node(A, child)
