from __future__ import annotations
import logging
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

@dataclass
class GraphNode:
    name: str
    nodetype: NodeType
    parent: GraphNode | None
    children: list[GraphNode]
    incoming: list[GraphNode]
    outgoing: list[GraphNode]

    def __init__(self, name: str, nodetype: NodeType, parent: GraphNode | None = None):
        if parent is not None:
            parent.children.append(self)

        self.name = name
        self.nodetype = nodetype
        self.parent = parent
        self.children = []
        self.incoming = []
        self.outgoing = []

    def __str__(self) -> str:
        return f"Type: {self.nodetype}, Name: {self.name}"

    def equivalent(self, other) -> bool:
        if other is None or not isinstance(other, GraphNode):
            return False
        if (self.name == other.name
            and self.nodetype == other.nodetype):
            return True
        else:
            return False

    def weakly_connected_with(self) -> list[GraphNode]:
            visited = []
            def visit(node: GraphNode):
                visited.append(node)
                for neigh in node.outgoing + node.incoming:
                    if neigh not in visited:
                        visit(neigh)
            visit(self)
            return visited

    def add_edge_to(self, other: GraphNode) -> None:
        self.outgoing.append(other)
        other.incoming.append(self)

    def check_for_cycles(
            self,
            settled: list[GraphNode] | None = None,
            visited: list[GraphNode] | None = None
            ) -> bool:
        if settled is None:
            settled = []
        if visited is None:
            visited = []
        if self in settled:
            return False
        if self in visited:
            return True
        visited.append(self)
        dependents = self.outgoing
        for dep in dependents:
            if dep.check_for_cycles(settled, visited):
                return True
        settled.append(self)
        return False

    def get_paths_to(self, target: GraphNode) -> list[list[GraphNode]]:
        queue: list[tuple[GraphNode, list[GraphNode]]] = [(self, [self])]
        paths: list[list[GraphNode]] = []
        logger = logging.getLogger(__name__)

        if self.check_for_cycles([], []):
            raise Exception(f"There is a cycle in the graph from {self.name} callback, "
                            "cannot find chains")

        logger.debug("No cycles found.")
        while len(queue) > 0:
            current, path = queue.pop()
            logger.debug(f"Path: {[p.name for p in path]}")
            logger.debug(f"Exploring {current.name}")
            if current == target:
                logger.debug(f"{current.name} is target")
                paths.append(path)
                logger.debug("Path added to results")
                continue
            nexts = current.outgoing
            logger.debug(f"Outgoing edges from {current.name}: {[n.name for n in nexts]}")

            for n in nexts:
                logger.debug(f"Adding {n.name} to queue.")
                queue.append((n, path + [n]))

        logger.debug("Got all paths")
        return paths

    def contract(self) -> None:
        if self.parent:
            self.parent.children.remove(self)
        for child in self.children:
            child.parent = self.parent
        for source in self.incoming:
            source.outgoing.remove(self)
        for target in self.outgoing:
            target.incoming.remove(self)
            for source in self.incoming:
                if source != target and source not in target.incoming:
                    target.incoming.append(source)
                    source.outgoing.append(target)

# for internal use
# this is a list of edges that should be added after all graph nodes are created
# First we have the type of the origin of the edge, then the origin object / name
# Then the type of the destination, and the destination name or object.
# A list can be provided if multiple edges from an origin should be added
Elem = GraphNode | str | list[str]
EdgeSpec = tuple[NodeType, Elem, NodeType, Elem]

# For external use
@dataclass
class RosGraphView(dict[NodeType, dict[str, GraphNode]]):
    # graph: dict[NodeType, dict[str, GraphNode]]

    def __init__(self, from_object: ros.System | list[GraphNode] | None = None) -> None:
        self.graph = {}
        for t in NodeType:
            self[t] = {}
        if from_object is not None:
            if isinstance(from_object, ros.System):
                self._add_system(from_object)
            elif isinstance(from_object, list):
                self.add_list(from_object)

    def add_list(self, list: list[GraphNode]) -> RosGraphView:
        for node in list:
            self.add(node)
        return self

    def add(self, node: GraphNode) -> GraphNode:
        # TODO: Write docs
        _type = node.nodetype
        if self[_type].get(node.name) is not None:
            raise ValueError(f"Name is not unique for {node.name} of type {_type}"
                             " or the object is contained by more than one parent.")
        self[_type][node.name] = node
        return node

    def string_resolve(self, e: str, t: NodeType) -> GraphNode:
        # TODO: Write docs
        x = self[t].get(e)
        if x is None:
            if t == TOPIC:
                x = GraphNode(e, TOPIC)
                self[TOPIC][e] = x
            else:
                raise ValueError(f"Element {e} of type {t} does not exist. Graph nodes"
                                 " registered: {[n.name for n in self.get_all_nodes()]}")
        return x

    def resolve_element(self, e: Elem, t: NodeType) -> list[GraphNode]:
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
            return [self.string_resolve(e, t)]
        else:
            return [self.string_resolve(s, t) for s in e]

    def add_edges(self, edge: EdgeSpec):
        froms = self.resolve_element(edge[1], edge[0])
        tos = self.resolve_element(edge[3], edge[2])
        for f in froms:
            for t in tos:
                f.add_edge_to(t)

    def get_all_nodes(self) -> list[GraphNode]:
        return [n for d in self.values() for n in d.values()]

    def clone(self) -> RosGraphView:
        newlist: list[GraphNode] = []

        oldlist = self.get_all_nodes()
        for node in oldlist:
            newlist.append(GraphNode(node.name, node.nodetype))
        newgraph = RosGraphView(newlist)
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

    def get_sinks(self) -> list[GraphNode]:
        return [node for node in self.get_all_nodes() 
                if node.outgoing == [] and node.children == []]
            
    def get_sources(self) -> list[GraphNode]:
        return [node for node in self.get_all_nodes() 
                if node.incoming == [] and node.children == []]

    def check_for_cycles(self) -> bool:
        logger = logging.getLogger(__name__)

        settled: list[GraphNode] = []
        visited: list[GraphNode] = []

        for node in self.get_all_nodes():
            logger.debug(f"Checking for cycles from {node.name}")
            if node.check_for_cycles(settled, visited):
                return True

        return False

    def get_all_chains(self) -> list[list[GraphNode]]:
        sources = self.get_sources()
        sinks = self.get_sinks()
        chains: list[list[GraphNode]] = []
        for source in sources:
            for sink in sinks:
                chains += source.get_paths_to(sink)
        return chains

    def find_equivalent_chain(self, chain: list[GraphNode]
                                 ) -> list[GraphNode]:
        log = logging.getLogger(__name__)
        out: list[GraphNode] = []
        for node in chain:
            other = self[node.nodetype].get(node.name)
            if other is None or not node.equivalent(other):
                raise ValueError(f"Graph and chain does not refer to equivalent systems. \
                        There is no equivalent to {node.name} in graph")
            log.debug(f"Appending {other.name} to chain")
            out.append(other)
        return out

    def get_contracted_view(self, allowed_types: Iterable[NodeType]) -> RosGraphView:
        tovisit: list[GraphNode] = self.clone().get_all_nodes()
        newlist: list[GraphNode] = []

        while len(tovisit) > 0:
            node = tovisit.pop()
            if node.nodetype not in allowed_types:
                node.contract()
            else:
                newlist.append(node)
        
        return RosGraphView(newlist)

    @staticmethod
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
        return RosGraphView(system)

    def _add_system(self, system: ros.System) -> None:
        g = self

        _system = GraphNode(system.name, SYSTEM)
        edgeq: list[EdgeSpec] = []
        requests: list[ros.Request] = []

        g[SYSTEM] = {system.name: _system}
        for host in system.hosts:
            _host = g.add(GraphNode(host.name, HOST, _system))
            for ex in host.executors:
                _executor = g.add(GraphNode(ex.name, EXECUTOR, _host))
                for node in ex.nodes:
                    _node = g.add(GraphNode(node.name, NODE, _executor))
                    for var in node.variables:
                        g.add(GraphNode(var.name, VARIABLE, _node))
                    for pub in node.publishers:
                        _pub = g.add(GraphNode(pub.name, PUBLISHER, _node))
                        edgeq.append((PUBLISHER, _pub, TOPIC, pub.topic))
                    for sub in node.subscriptions:
                        # TODO: Can we convert "wall times" into external input?
                        _sub = g.add(GraphNode(sub.name, SUBSCRIBER, _node))
                        edgeq.append((TOPIC, sub.topic, SUBSCRIBER, _sub))
                        edgeq.append((SUBSCRIBER, _sub, CALLBACK, sub.callback))
                    for service in node.services:
                        # TODO: Can we convert "wall times" into external input?
                        _service = g.add(GraphNode(service.name, SERVICE, _node))
                        edgeq.append((SERVICE, _service, CALLBACK, service.callback))
                    for timer in node.timers:
                        _timer = g.add(GraphNode(timer.name, TIMER, _node))
                        edgeq.append((TIMER, _timer, CALLBACK, timer.callback))
                    for action in node.actions:
                        _action = g.add(GraphNode(action.name, ACTION, _node))
                        # TODO: Support actions when they are properly implemented
                    for client in node.clients:
                        _client = g.add(GraphNode(client.name, CLIENT, _node))
                        edgeq.append((CLIENT, _client, SERVICE, client.service))
                    for output in node.external_outputs:
                        g.add(GraphNode(output.name, EXTERNAL_OUTPUT, _node))
                    for inp in node.external_inputs:
                        _inp = g.add(GraphNode(inp.name, EXTERNAL_INPUT, _node))
                        edgeq.append((EXTERNAL_INPUT, _inp, CALLBACK, inp.callback))
                    for cb in node.callbacks:
                        _cb = g.add(GraphNode(cb.name, CALLBACK, _node))
                        edgeq.append((CALLBACK, _cb, PUBLISHER, cb.publishers))
                        if cb.calls is not None:
                            edgeq.append((CALLBACK, _cb, CALLBACK, cb.calls))
                        edgeq.append((CALLBACK, _cb, EXTERNAL_OUTPUT, cb.external_outputs))
                        edgeq.append((CALLBACK, _cb, VARIABLE, cb.write_variables))
                        edgeq.append((VARIABLE, cb.read_variables, CALLBACK, _cb))
                        if cb.request is not None:
                            # Important - callbacks requires that clients are registered
                            requests.append(cb.request)
            for e in edgeq:
                g.add_edges(e)
            for r in requests:
                client = r.client
                edgeq.append((CALLBACK, _cb, CLIENT, client))
                service = g[CLIENT][client].outgoing[0]
                edgeq.append((SERVICE, service, CALLBACK, r.response))
            for e in edgeq:
                g.add_edges(e)

def filter_list_by_type(list: list[GraphNode], types: Iterable[NodeType]) -> list[GraphNode]:
    return [node for node in list if node.nodetype in types]

def find_in_list(list: list[GraphNode], nodetype: NodeType, name: str
                  ) -> GraphNode | None:
    for node in list:
        if node.nodetype == nodetype and node.name == name:
            return node
    return None

