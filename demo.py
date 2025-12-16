import ros2system as ros
from pprint import pprint
import backeman.system as bk


def validation_ss():
    system = bk.System("ss")
    system.add_datagenerator("SENSOR1", 360, 10, 0, True)
    system.add_datagenerator("SENSOR2", 360, 20, 0, False)
    system.add_subscriber("FILTER1", "SENSOR1", 10, [], [], "pd")
    system.add_subscriber("FILTER2", "SENSOR2", 20, [], [], "pd")
    system.add_subscriber("FUSION1", "SENSOR1", 30, ["SENSOR2"], [30], "pd")
    system.add_subscriber("FILTER3", "FUSION1", 30, [], [], "pd")
    system.add_subscriber("ACTUATOR1", "FILTER3", 30, [], [], "pd")
    system.monitor("ACTUATOR1", 360)
    return system


sys1 = bk.System("sys")
sys2 = ros.System("sys", dds_implementation="Standard")
h = sys2.add_host(operating_system="Ubuntu")
e = h.add_executor(implementation="SingleThreadedExecutor")


def transform_system(system: ros.System) -> bk.System:
    if len(system.hosts) != 1:
        raise ValueError("must only have one host")
    return sys1


transform_system(sys2)
print("First transformation successful")
sys2.add_host(operating_system="Ubuntu")
# transform_system(sys2)
print("Second transformation successful")

system = ros.System("test", dds_implementation="super")

host = system.add_host(operating_system="ubuntu 1")
executor = host.add_executor(implementation="EventExecutor")

# node1 = host.add_node("MIchael")

# s1, s2, f1, f2, fu, f3, act = executor.add_nodes([
#     "sensor1", "sensor2", "filter1", "filter2", "fusion", "filter3", "actuator"
# ])

s1 = executor.add_node(name="sensor1")
s2 = executor.add_node(name="sensor2")
f1 = executor.add_node(name="filter1")
f2 = executor.add_node(name="filter2")
fu = executor.add_node(name="fusion")
f3 = executor.add_node(name="filter3")
act = executor.add_node(name="actuator")

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

# case st

pub1 = s1.add_publisher(topic="sensor1")
cb1 = s1.add_callback(wcet=30, publishers=[pub1])
s1.add_timer(period=50, callback=cb1)

pub2 = s2.add_publisher(topic="sensor2")
cb2 = s2.add_callback(wcet=30, publishers=[pub2])
s2.add_timer(period=50, callback=cb2)

pub3 = f1.add_publisher(topic="filter1")
cb3 = f1.add_callback(wcet=30, publishers=[pub3])
f1.add_subscription(topic="sensor1", callback=cb3)


pub4 = f2.add_publisher(topic="filter2")
cb4 = f2.add_callback(wcet=30, publishers=[pub4])
f2.add_subscription(topic="sensor2", callback=cb4)

# subscription variant
var1 = fu.add_variable()
cb5 = fu.add_callback(wcet=30, write_variables=[var1])
fu.add_subscription(topic="filter2", callback=cb5)
pub5 = fu.add_publisher(topic="fusion")
cb6 = fu.add_callback(wcet=30, publishers=[pub5], read_variables=[var1])
fu.add_subscription(topic="filter1", callback=cb6)


# timer variant
# var1 = fu.add_variable()
# cb5 = fu.add_callback(wcet=30, write_variables=[var1])
# fu.add_subscription(topic="filter1", callback=cb5)
# var2 = fu.add_variable()
# cb6 = fu.add_callback(wcet=30, write_variables=[var2])
# fu.add_subscription(topic="filter2", callback=cb6)
# pub5 = fu.add_publisher(topic="fusion")
# cb61 = fu.add_callback(wcet=30, read_variables=[var1, var2], publisher=[pub5])
# fu.add_timer(topic="fusion", period=100, callback=cb7)

pub6 = f3.add_publisher(topic="filter3")
cb7 = f3.add_callback(wcet=30, publishers=[pub6])
f3.add_subscription(topic="fusion", callback=cb7)
# serv1 = f3.add_service()

extout = system.add_external_output()
cb8 = act.add_callback(wcet=30, outputs=[extout])
act.add_subscription(topic="filter3", callback=cb7)


pprint(system, width=120, indent=1, compact=False)

