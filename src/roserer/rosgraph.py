from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
import roserer.ros2system as ros

class NodeType(Enum):
    SYSTEM = auto()
    HOST = auto()
    EXECUTOR = auto()
    NODE = auto()
    CALLBACK = auto()
    EXTERNAL_INPUT = auto()
    EXTERNAL_OUTPUT = auto()
    TIMER = auto()
    SERVICE = auto()
    CLIENT = auto()
    VARIABLE = auto()
    PUBLISHER = auto()
    SUBSCRIBER = auto()
    ACTION = auto()
    TOPIC = auto()

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
        raise ValueError(f"Name is not unique for {node.name} of type {_type}")
    graph[_type][node.name] = node
    return node

def resolve_element(graph: RosGraphView, e: Elem, t: NodeType) -> list[GraphNode]:
    if isinstance(e, GraphNode):
        return [e]
    elif isinstance(e, str):
        return [graph[t][e]]
    else:
        return [graph[t][s] for s in e]

def add_edges(graph: RosGraphView, edge: EdgeSpec):
    froms = resolve_element(graph, edge[1], edge[0])
    tos = resolve_element(graph, edge[3], edge[2])
    for f in froms:
        for t in tos:
            f.outgoing.append(t)
            t.incoming.append(f)

def get_graph_view_from(system: ros.System) -> RosGraphView:
    g: RosGraphView = {}
    systemnode = GraphNode(system.name, SYSTEM)
    g[SYSTEM] = {system.name: systemnode}
    edgeq: list[EdgeSpec] = []

    for t in NodeType:
        g[t] = {}

    for host in system.hosts:
        _host = add_to_graph(g, GraphNode(host.name, HOST, systemnode))
        g[HOST][host.name] = _host
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
                    _sub = add_to_graph(g, GraphNode(sub.name, SUBSCRIBER, _node))
                    edgeq.append((TOPIC, sub.topic, SUBSCRIBER, _sub))
                    edgeq.append((SUBSCRIBER, _sub, CALLBACK, sub.callback))
                for service in node.services:
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

