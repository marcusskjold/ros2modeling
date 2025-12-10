import ros2system as ros
from pprint import pprint


system = ros.System("super")
extout = ros.ExternalOutput()

host = system.add_host(operating_system="ubuntu 1")
executor = host.add_executor(implementation="EventExecutor")

# node1 = host.add_node("MIchael")

s1, s2, f1, f2, fu, f3, act = executor.add_nodes([
    "sensor1", "sensor2", "filter1", "filter2", "fusion", "filter3", "actuator"
])

# One

# s1p, s2p, f1p, f2p, fup, f3p = system.add_publishers([
#     (s1, "sensor1"),
#     (s2, "sensor2"),
#     (f1, "filter1"),
#     (f2, "filter2"),
#     (fu, "fusion"),
#     (f3, "filter3"),
# ])


# Another

# s1c, s2c, f1c, f2c, fuc, f3c = system.add_callbacks([
#     (s1, 30, "sensor1"),
#     (s2, 40, "sensor2"),
#     (f1, 40, "filter1"),
#     (f2, 30, "filter2"),
#     (fu, 60, "fusion"),
#     (f3, 20, "filter3"),
#     (act, 40, extout)
# ])

pub1 = s1.add_publisher(topic="sensor1")
cb1 = s1.add_callback(wcet=30, publisher=pub1)
s1.add_timer(period=50, callback=cb1)


pub2 = s2.add_publisher(topic="sensor2")
cb2 = s2.add_callback(wcet=30, publisher=pub2)
s2.add_timer(period=50, callback=cb2)

pub3 = f1.add_publisher(topic="filter1")
cb3 = f1.add_callback(wcet=30, publisher=pub3)
f1.add_subscription(topic="sensor1", callback=cb3)


pprint(system, width=120, indent=1, compact=False)
