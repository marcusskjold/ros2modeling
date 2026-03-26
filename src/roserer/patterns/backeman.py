from roserer.types import EXECUTOR, DISTRIBUTION
import roserer.ros2system as ros

def new_default_backeman_system(name: str) -> tuple[ros.System, ros.Executor]:
    s = ros.System(name)
    s.default_qos.depth = 20

    h = s.add_host()
    e = h.add_executor(
            implementation=EXECUTOR.SingleThreadedExecutor,
            ros_distribution=DISTRIBUTION.Eloquent)
    return s, e

def make_nondeterministic(system: ros.System | ros.Executor) -> None:
    cbs: list[ros.Callback]
    if isinstance(system, ros.Executor):
        cbs = [cb for node in system.nodes for cb in node.callbacks]
    elif isinstance(system, ros.System):
        cbs = system.get_callbacks()
    else:
        raise ValueError("Invalid system object")
    for cb in cbs:
        cb.bcet = cb.wcet // 2

def add_node(e: ros.Executor, name: str) -> tuple[ros.Node, ros.Publisher]:
    n = e.add_node(name=name)
    p = n.add_publisher(topic=name)
    return n, p

def add_dependencies(
        n: ros.Node,
        subscribers: list[str],
        wcets: list[int]
        ) -> list[ros.Variable]:
    var = []
    for s, w in zip(subscribers, wcets):
        v = n.add_variable()
        var.append(v)
        cb = n.add_callback(wcet=w, write_variables=[v])
        n.add_subscription(topic=s, callback=cb)
    return var

def add_dependent_node(
        e: ros.Executor,
        name: str,
        wcet: int,
        subscribers: list[str] | None = None,
        wcets: list[int] | None = None,
        ) -> tuple[ros.Node, ros.Callback]:
    n, p = add_node(e, name)
    var = []
    if subscribers is not None and wcets is not None:
        var = add_dependencies(n, subscribers, wcets)
    c = n.add_callback(wcet=wcet, publishers=[p], read_variables=var)
    return n, c

def add_datagenerator(
        e: ros.Executor,
        name: str,
        wcet: int,
        period: int,
        delay: int
        ) -> ros.Node:
    n, p = add_node(e, name)
    c = n.add_callback(wcet=wcet, publishers=[p])
    n.add_timer(period=period, offset=delay, callback=c)
    return n

def add_probabilistic_datagenerator(
        e: ros.Executor,
        name: str,
        wcet: int,
        period: int,
        delay: int,
        probability: int
        ) -> ros.Node:
    n, p = add_node(e, name)
    c = n.add_callback(wcet=wcet, publishers=[p])
    n.add_timer(period=period, offset=delay, callback=c, probability=probability)
    return n

def add_subscriber(
        e: ros.Executor,
        name: str,
        wcet: int,
        topic: str,
        subscribers: list[str] | None = None,
        wcets: list[int] | None = None,
        ) -> ros.Node:
    n, c = add_dependent_node(e, name, wcet, subscribers, wcets)
    n.add_subscription(topic=topic, callback=c)
    return n

def add_timer(
        e: ros.Executor,
        name: str,
        wcet: int,
        period: int,
        delay: int,
        subscribers: list[str],
        wcets: list[int]
        ) -> ros.Node:
    n, c = add_dependent_node(e, name, wcet, subscribers, wcets)
    n.add_timer(period=period, offset=delay, callback=c)
    return n
