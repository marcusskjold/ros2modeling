import pygraphviz as pgv
from roserer.systemvalidator import validate_system
from roserer.systemvalidator import ValidationResult as Result
from pygraphviz import AGraph
import roserer.systemvalidator as sv
import roserer.ros2system as ros


Graph = dict[str, list[str]]
def transform_cb_graph(graph: Graph) -> AGraph:
    A = pgv.AGraph(directed=True, strict=True, rankdir="TB")
    for node, links in graph.items():
        for link in links:
            A.add_edge(node, link)
    return A


def transform_and_save_cb_graph(graph: Graph, file: str) -> AGraph:
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
                pub
                )
    for var in cb.read_variables:
        graph.add_edge(
                var.name,
                cb.name
                )

    for var in cb.write_variables:
        graph.add_edge(
                cb.name,
                var.name,
                )

def add_pub(graph: AGraph, pub: ros.Publisher):
    graph.add_node(
            pub.name,
            label=f"{pub.name}",
            shape="invhouse",
            fontsize="8",
            width=".2"
            )
    graph.add_edge(
            pub.name,
            pub.topic
            )

def add_sub(graph: AGraph, sub: ros.Subscription):
    graph.add_node(
            sub.name,
            label=f"{sub.name}",
            shape="house",
            fontsize="8",
            )
    graph.add_edge(
            sub.topic,
            sub.name,
            )
    graph.add_edge(
            sub.name,
            sub.callback
            )

def add_var(graph:AGraph, var: ros.Variable):
    graph.add_node(
            var.name,
            shape="diamond",
            fontsize="8",
            )

def add_node(graph: AGraph, node: ros.Node):
    subgraph = graph.add_subgraph(
            name=node.name,
            label=f"Node: {node.name}",
            color="black",
            cluster="true",
            rank="same",
            )
    for pub in node.publishers:
        add_pub(subgraph, pub)
    for var in node.variables:
        add_var(subgraph, var)
    for cb in node.callbacks:
        add_cb(subgraph, cb)
    for sub in node.subscriptions:
        add_sub(subgraph, sub)


def add_executor(graph: AGraph, executor: ros.Executor):
    graph.add_subgraph(
            name=executor.name,
            cluster="true",
            label=f"Executor: {executor.name}",
            )
    subgraph = graph.subgraphs()[-1]
    for node in executor.nodes:
        add_node(subgraph, node)

def add_host(graph: AGraph, host: ros.Host):
    graph.add_subgraph(
            name=host.name,
            cluster="true",
            label=f"Host: {host.name}",
            )
    subgraph = graph.subgraphs()[-1]
    for executor in host.executors:
        add_executor(subgraph, executor)

def transform_system(sys: ros.System) -> AGraph:
    result = validate_system(sys)
    A = pgv.AGraph(
            name=sys.name,
            directed=True,
            strict=True,
            rankdir="TB",
            concentrate="true",
            splines="ortho",
            # newrank="true",
            # ratio="0.5",
            nodesep=".4",
            ranksep="0.2"
            )

    for topic, subs in result.interfaces["topics subscribed to"].items():
        A.add_node(topic, shape="parallelogram")
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
