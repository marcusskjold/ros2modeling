from __future__ import annotations
from typing import Iterable
from dataclasses import dataclass
import roserer.ros2system as ros
from roserer.types import NodeType

# Containers
SYSTEM = NodeType.SYSTEM
HOST = NodeType.HOST
EXECUTOR = NodeType.EXECUTOR
NODE = NodeType.NODE

# Elements
CALLBACK = NodeType.CALLBACK
EXTERNAL_INPUT = NodeType.EXTERNAL_INPUT
EXTERNAL_OUTPUT = NodeType.EXTERNAL_OUTPUT
TIMER = NodeType.TIMER
VARIABLE = NodeType.VARIABLE
PUBLISHER = NodeType.PUBLISHER
SUBSCRIBER = NodeType.SUBSCRIBER
CLIENT = NodeType.CLIENT

# Interface
SERVICE = NodeType.SERVICE
ACTION = NodeType.ACTION
TOPIC = NodeType.TOPIC

ALL_TYPES: set[NodeType] = set([
        SYSTEM, HOST, EXECUTOR, NODE,
        CALLBACK, EXTERNAL_INPUT, EXTERNAL_OUTPUT, TIMER,
        VARIABLE, PUBLISHER, SUBSCRIBER, CLIENT,
        SERVICE, ACTION, TOPIC
        ])

@dataclass
class GraphNode:
    name: str
    nodetype: NodeType
    parent: GraphNode | None
    children: list[GraphNode]
    incoming: list[GraphNode]
    outgoing: list[GraphNode]

    def __init__(
            self,
            name: str,
            nodetype: NodeType,
            parent: GraphNode | None = None,
            children: list[GraphNode] | None = None,
            incoming: list[GraphNode] | None = None,
            outgoing: list[GraphNode] | None = None,
            ):
        if children is None:
            children = []
        if incoming is None:
            incoming = []
        if outgoing is None:
            outgoing = []
        if parent is not None:
            parent.children.append(self)

        self.name = name
        self.nodetype = nodetype
        self.parent = parent
        self.children = children
        self.incoming = incoming
        self.outgoing = outgoing

    def __str__(self) -> str:
        return f"Type: {self.nodetype}, Name: {self.name}"
    
# for internal use
# this is a list of edges that should be added after all graph nodes are created
# First we have the type of the origin of the edge, then the origin object / name
# Then the type of the destination, and the destination name or object.
# A list can be provided if multiple edges from an origin should be added
Elem = GraphNode | str | list[str]
EdgeSpec = tuple[NodeType, Elem, NodeType, Elem]

RosGraphView = dict[NodeType, dict[str, GraphNode]]

def add_to_graph(graph: RosGraphView, node: GraphNode) -> GraphNode:
    _type = node.nodetype
    if graph[_type].get(node.name) is not None:
        raise ValueError(f"Name is not unique for {node.name} of type {_type} \
                or the object is contained by more than one parent.")
    graph[_type][node.name] = node
    return node

def string_resolve(graph: RosGraphView, e: str, t: NodeType) -> GraphNode:
    x = graph[t].get(e)
    if x is None:
        if t == TOPIC:
            x = GraphNode(e, TOPIC)
            graph[TOPIC][e] = x
        else:
            raise ValueError(f"Element {e} of type {t} does not exist.")
    return x

def resolve_element(graph: RosGraphView, e: Elem, t: NodeType) -> list[GraphNode]:
    """
    Returns a list of graph nodes based on the element passed.
    Used to narrow the union type Elem into the proper type GraphNode

    Parameters
    graph (RosGraphView):
        Reference graph to find element
    e (Elem):
        The element to resolve. Is either already a graph node, a string 
        or a list of strings
    t (NodeType):
        The type of the element. Used with the graph to resolve string elements
    """
    if isinstance(e, GraphNode):
        return [e]
    elif isinstance(e, str):
        return [string_resolve(graph, e, t)]
    else:
        return [string_resolve(graph, s, t) for s in e]

def add_edges(graph: RosGraphView, edge: EdgeSpec):
    froms = resolve_element(graph, edge[1], edge[0])
    tos = resolve_element(graph, edge[3], edge[2])
    for f in froms:
        for t in tos:
            f.outgoing.append(t)
            t.incoming.append(f)

def get_graph_view_from(system: ros.System) -> RosGraphView:
    """
    Create a graph representation of the given ROS2 system.
    The edges of the graph represents data flow.
    The graph is indexed by node type and then by name.
    Successful construction of the graph provides the following guarantees:

    - Each graph node is owned by zero or one other node (e.g. two nodes cannot have
      the same node listed in their `children` field.)
    - Each string reference of a ros system entity refers to another ros system entity
      (Except topics)
    - Each edge in the graph is represented in both directions (parent-child, 
      incoming-outgoing)
    """
    g: RosGraphView = {}
    _system = GraphNode(system.name, SYSTEM)
    g[SYSTEM] = {system.name: _system}
    edgeq: list[EdgeSpec] = []

    for t in NodeType:
        g[t] = {}

    for host in system.hosts:
        _host = add_to_graph(g, GraphNode(host.name, HOST, _system))
        for ex in host.executors:
            _executor = add_to_graph(g, GraphNode(ex.name, EXECUTOR, _host))
            for node in ex.nodes:
                _node = add_to_graph(g, GraphNode(node.name, NODE, _executor))
                for var in node.variables:
                    add_to_graph(g, GraphNode(var.name, VARIABLE, _node))
                for pub in node.publishers:
                    _pub = add_to_graph(g, GraphNode(pub.name, PUBLISHER, _node))
                    edgeq.append((PUBLISHER, _pub, TOPIC, pub.topic))
                for sub in node.subscriptions:
                    # TODO: Can we convert "wall times" into external input?
                    _sub = add_to_graph(g, GraphNode(sub.name, SUBSCRIBER, _node))
                    edgeq.append((TOPIC, sub.topic, SUBSCRIBER, _sub))
                    edgeq.append((SUBSCRIBER, _sub, CALLBACK, sub.callback))
                for service in node.services:
                    # TODO: Can we convert "wall times" into external input?
                    _service = add_to_graph(g, GraphNode(service.name, SERVICE, _node))
                    edgeq.append((SERVICE, _service, CALLBACK, service.callback))
                for timer in node.timers:
                    _timer = add_to_graph(g, GraphNode(timer.name, TIMER, _node))
                    edgeq.append((TIMER, _timer, CALLBACK, timer.callback))
                for action in node.actions:
                    _action = add_to_graph(g, GraphNode(action.name, ACTION, _node))
                    # TODO: Support actions when they are properly implemented
                for client in node.clients:
                    _client = add_to_graph(g, GraphNode(client.name, CLIENT, _node))
                    edgeq.append((CLIENT, _client, SERVICE, client.service))
                for output in node.external_outputs:
                    add_to_graph(g, GraphNode(output.name, EXTERNAL_OUTPUT, _node))
                for inp in node.external_inputs:
                    _inp = add_to_graph(g, GraphNode(inp.name, EXTERNAL_INPUT, _node))
                    edgeq.append((EXTERNAL_INPUT, _inp, CALLBACK, inp.callback))
                for cb in node.callbacks:
                    _cb = GraphNode(cb.name, CALLBACK, _node)
                    edgeq.append((CALLBACK, _cb, PUBLISHER, cb.publishers))
                    if cb.calls is not None:
                        edgeq.append((CALLBACK, _cb, CALLBACK, cb.calls))
                    edgeq.append((CALLBACK, _cb, EXTERNAL_OUTPUT, cb.external_outputs))
                    edgeq.append((CALLBACK, _cb, VARIABLE, cb.write_variables))
                    edgeq.append((VARIABLE, cb.read_variables, CALLBACK, _cb))
                    if cb.request is not None:
                        client = cb.request.client
                        edgeq.append((CALLBACK, _cb, CLIENT, client))
                        # Important - callbacks requires that clients are registered
                        service = g[CLIENT][client].outgoing[0]
                        edgeq.append((SERVICE, service, CALLBACK, cb.request.response))
                    edgeq.append((CALLBACK, _cb, VARIABLE, cb.write_variables))
        for e in edgeq:
            add_edges(g, e)
    return g

def get_all_nodes(graph: RosGraphView) -> list[GraphNode]:
    return [n for d in graph.values() for n in d.values()]

def index_graph_list(graph_nodes: list[GraphNode]) -> RosGraphView:
    graph: RosGraphView = {}
    for node in graph_nodes:
        graph.setdefault(node.nodetype, {})
        add_to_graph(graph, node)
    return graph

def clone(graph: RosGraphView) -> RosGraphView:
    newlist: list[GraphNode] = []

    oldlist = get_all_nodes(graph)
    for node in oldlist:
        newlist.append(GraphNode(node.name, node.nodetype))
    newgraph = index_graph_list(newlist)
    for new, old in zip(newlist, oldlist): 
        parent = old.parent
        if parent is not None:
            new.parent = newgraph[parent.nodetype][parent.name]
        for child in old.children:
            newchild = newgraph[child.nodetype][child.name]
            new.children.append(newchild)
        for target in old.outgoing:
            newtarget = newgraph[target.nodetype][target.name]
            new.outgoing.append(newtarget)
        for source in old.incoming:
            newsource = newgraph[source.nodetype][source.name]
            new.incoming.append(newsource)
    return newgraph

def contract(node: GraphNode) -> None:
    if node.parent:
        node.parent.children.remove(node)
    for child in node.children:
        child.parent = node.parent
    for source in node.incoming:
        source.outgoing.remove(node)
    for target in node.outgoing:
        source.incoming.remove(node)
        for source in node.incoming:
            if source != target and source not in target.incoming:
                target.incoming.append(source)
                source.outgoing.append(target)

def contract_graph(graph: RosGraphView, allowed_types: Iterable[NodeType]) -> RosGraphView:
    cgraph = clone(graph)
    tovisit = get_all_nodes(cgraph)

    while len(tovisit) > 0:
        node = tovisit.pop()
        if node.nodetype not in allowed_types:
            contract(node)
    
    return cgraph

def get_sinks(graph: RosGraphView) -> list[GraphNode]:
    return [node for node in get_all_nodes(graph) 
            if node.outgoing == [] and node.children == []]
        
def get_sources(graph: RosGraphView) -> list[GraphNode]:
    return [node for node in get_all_nodes(graph) 
            if node.incoming == [] and node.children == []]

def filter_type(list: list[GraphNode], types: Iterable[NodeType]) -> list[GraphNode]:
    return [node for node in list if node.nodetype in types]

def weakly_connected_with(node: GraphNode) -> set[GraphNode]:
        visited = set()
        def visit(node: GraphNode):
            visited.add(node)
            for neigh in node.outgoing and node.incoming:
                if neigh not in visited:
                    visit(neigh)
        visit(node)
        return visited

def check_for_cycles_from(node: GraphNode, settled: set[GraphNode], visited: set[GraphNode]) -> bool:
        if node in settled:
            return False
        if node in visited:
            return True
        visited.add(node)
        dependents = node.outgoing
        for dep in dependents:
            if check_for_cycles_from(dep, settled, visited):
                return True
        settled.add(node)
        return False

def check_for_cycles_in(graph: RosGraphView) -> bool:

    settled: set[GraphNode] = set()
    visited: set[GraphNode] = set()

    for node in get_all_nodes(graph):
        if check_for_cycles_from(node, settled, visited):
            return True

    return False

def get_paths_from(source: GraphNode, target: GraphNode) -> list[list[GraphNode]]:
    queue: list[tuple[GraphNode, list[GraphNode]]] = [(source, [source])]
    paths: list[list[GraphNode]] = []

    if check_for_cycles_from(source, set(), set()):
        raise Exception(f"There is a cycle in the graph from {source} callback, "
                        "cannot find chains")

    while len(queue) > 0:
        current, path = queue.pop()
        if current == target:
            paths.append(path)
            continue
        nexts = current.outgoing
        for n in nexts:
            queue.append((n, path + [n]))

    return paths

def get_all_chains(graph: RosGraphView) -> list[list[GraphNode]]:
    sources = get_sources(graph)
    sinks = get_sinks(graph)
    chains: list[list[GraphNode]] = []
    for source in sources:
        for sink in sinks:
            chains += get_paths_from(source, sink)
    return chains

