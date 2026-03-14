from roserer.types import NodeType
from roserer.rosgraph import RosGraphView, GraphNode
import pygraphviz as pgv
from roserer.systemvalidator import validate_system
from pygraphviz import AGraph
import roserer.systemvalidator as sv
import roserer.ros2system as ros

ARWSZ = "0.5"
ARWCLR = "black"
PENWDTH = "0.7"
SPEN = "0.4"
VECLR = "steelblue"

Graph = dict[str, list[str]]
def transform_cb_graph(graph: list[GraphNode]) -> AGraph:
    A = pgv.AGraph(directed=True, strict=True, rankdir="TB")
    for cb in graph:
        A.add_node(cb.name)
        for link in cb.outgoing:
            A.add_edge(cb.name, link)
    return A


def transform_and_save_cb_graph(graph: list[GraphNode], file: str) -> AGraph:
    A = transform_cb_graph(graph)
    A.layout("dot")
    A.draw(file)
    return A

# ---------------------------------

def add_cb(graph: AGraph, cb: ros.Callback):
    graph.add_node(
            cb.name,
            label=f"{cb.name}",
            shape="rect",
            style="filled"
            )
    for pub in cb.publishers:
        graph.add_edge(
                cb.name,
                pub,
                arrowsize=ARWSZ,
                color=ARWCLR,
                penwidth=PENWDTH,
                )
    if cb.read_variables != []:
        subg = graph.add_subgraph(
                [var for var in cb.read_variables] + [cb.name],
                rank="source",
                style="invis",
                )
    for var in cb.read_variables:
        subg
        graph.add_edge(
                var,
                cb.name,
                arrowsize=ARWSZ,
                color=VECLR,
                penwidth=SPEN,
                constraint="false",
                arrowhead="inv",
                style="dashed",
                )

    for var in cb.write_variables:
        graph.add_edge(
                cb.name,
                var,
                arrowsize=ARWSZ,
                color="tomato4",
                style="dashed",
                penwidth=SPEN,
                )
    if cb.calls is not None:
        graph.add_edge(
                cb.name,
                cb.calls,
                arrowsize=ARWSZ,
                color=ARWCLR,
                penwidth=PENWDTH,
                )

def add_pub(graph: AGraph, pub: ros.Publisher):
    graph.add_node(
            pub.name,
            label=f"{pub.name}",
            shape="invhouse",
            margin="0.01",
            fontsize="8",
            width=".2",
            style="filled",
            fillcolor="lightpink",
            )
    graph.add_edge(
            pub.name,
            pub.topic,
            arrowsize=ARWSZ,
            color=ARWCLR,
            penwidth=PENWDTH,
            )

def add_sub(graph: AGraph, sub: ros.Subscription):
    graph.add_node(
            sub.name,
            label=f"{sub.name}",
            shape="house",
            fillcolor="lightblue",
            style="filled",
            fontsize="8",
            )
    graph.add_edge(
            sub.topic,
            sub.name,
            arrowsize=ARWSZ,
            color=ARWCLR,
            penwidth=PENWDTH,
            )
    graph.add_edge(
            sub.name,
            sub.callback,
            arrowsize=ARWSZ,
            color=ARWCLR,
            penwidth=PENWDTH,
            )

def add_var(graph:AGraph, var: ros.Variable):
    graph.add_node(
            var.name,
            shape="oval",
            style="filled",
            fillcolor="beige",
            fontsize="8",
            margin="0.01",
            )

def add_tim(graph: AGraph, tim: ros.Timer):
    graph.add_node(
            tim.name,
            shape="diamond",
            fontsize="8",
            fillcolor="lightblue",
            style="filled"
            )
    graph.add_edge(
            tim.name,
            tim.callback,
            arrowsize=ARWSZ,
            color=ARWCLR,
            penwidth=PENWDTH,
            )

def add_node(graph: AGraph, node: ros.Node):
    subgraph = graph.add_subgraph(
            name=node.name,
            label=f"Node: {node.name}",
            cluster="true",
            rank="same",
            style="dashed,rounded",
            color="lavenderblush3",
            )
    for pub in node.publishers:
        add_pub(subgraph, pub)
    for var in node.variables:
        add_var(subgraph, var)
    for cb in node.callbacks:
        add_cb(subgraph, cb)
    for sub in node.subscriptions:
        add_sub(subgraph, sub)
    for tim in node.timers:
        add_tim(subgraph, tim)


def add_executor(graph: AGraph, executor: ros.Executor):
    graph.add_subgraph(
            name=executor.name,
            cluster="true",
            label=f"Executor: {executor.name}",
            style="dotted",
            color="dimgrey"
            )
    subgraph = graph.subgraphs()[-1]
    for node in executor.nodes:
        add_node(subgraph, node)

def add_host(graph: AGraph, host: ros.Host):
    graph.add_subgraph(
            name=host.name,
            cluster="true",
            label=f"Host: {host.name}",
            style="solid",
            color="dimgrey"
            )
    subgraph = graph.subgraphs()[-1]
    for executor in host.executors:
        add_executor(subgraph, executor)

def add_topic(A: AGraph, name: str):
    A.add_node(
            name, 
            shape="parallelogram", 
            style="filled,dashed", 
            fillcolor="beige",
            margin="0",
            height="0.3",
            fontsize="8",
            )

def transform_system(sys: ros.System) -> AGraph:
    feedback = validate_system(sys)
    if feedback.errors != []:
        raise ValueError(f"Invalid system. Feedback: {feedback.errors}")
    graph = RosGraphView(sys)
    A = pgv.AGraph(
            name=sys.name,
            directed=True,
            strict=True,
            rankdir="TB",
            concentrate="true",
            splines="ortho",
            # newrank="true",
            # ratio="0.5",
            nodesep=".3",
            ranksep="0.2"
            )

    for topic in graph[NodeType.TOPIC]:
        add_topic(A, topic)

    #     for sub in subs:
    #         A.add_edge(topic, sub)
    for host in sys.hosts:
        add_host(A, host)
    return A

def transform_and_save_system(sys: ros.System, file: str) -> AGraph:
    A = transform_system(sys)
    A.layout("dot")
    A.draw(file)
    return A

