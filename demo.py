import roserer.ros2system as ros
import roserer.yamlPrinter as yprint
import roserer.yamlParser as yparse
import roserer.systemvalidator as sv
from pprint import pprint
import roserer.backeman.system as bk
import roserer.adapters.backeman_adapter as tb
import roserer.backeman.dust_system as ds

from dotenv import load_dotenv
load_dotenv()

system = ros.System("test", dds_implementation="Generic")
system.default_qos.depth = 20

host = system.add_host(operating_system="Generic")
executor = host.add_executor(implementation="SingleThreadedExecutor", ros_distribution="Eloquent")

s1 = executor.add_node(name="sensor1")
s2 = executor.add_node(name="sensor2")
f1 = executor.add_node(name="filter1")
f2 = executor.add_node(name="filter2")
fu = executor.add_node(name="fusion1")
f3 = executor.add_node(name="filter3")
act = executor.add_node(name="actuator1")

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
cb1 = s1.add_callback(wcet=10, publishers=[pub1])
s1.add_timer(period=360, callback=cb1)

pub2 = s2.add_publisher(topic="sensor2")
cb2 = s2.add_callback(wcet=20, publishers=[pub2])
s2.add_timer(period=360, callback=cb2)

pub3 = f1.add_publisher(topic="filter1")
cb3 = f1.add_callback(wcet=10, publishers=[pub3])
f1.add_subscription(topic="sensor1", callback=cb3)


pub4 = f2.add_publisher(topic="filter2")
cb4 = f2.add_callback(wcet=20, publishers=[pub4])
f2.add_subscription(topic="sensor2", callback=cb4)

# subscription variant
var1 = fu.add_variable()
cb5 = fu.add_callback(wcet=30, write_variables=[var1])
fu.add_subscription(topic="filter2", callback=cb5)
pub5 = fu.add_publisher(topic="fusion1")
cb6 = fu.add_callback(wcet=30, publishers=[pub5], read_variables=[var1])
fu.add_subscription(topic="filter1", callback=cb6)


# timer variant
# var1 = fu.add_variable()
# cb5 = fu.add_callback(wcet=30, write_variables=[var1])
# fu.add_subscription(topic="filter1", callback=cb5)
# var2 = fu.add_variable()
# cb6 = fu.add_callback(wcet=30, write_variables=[var2])
# fu.add_subscription(topic="filter2", callback=cb6)
# pub5 = fu.add_publisher(topic="fusion1")
# cb61 = fu.add_callback(wcet=30, read_variables=[var1, var2], publisher=[pub5])
# fu.add_timer(topic="fusion1", period=100, callback=cb7)

pub6 = f3.add_publisher(topic="filter3")
cb7 = f3.add_callback(wcet=30, publishers=[pub6])
f3.add_subscription(topic="fusion1", callback=cb7)
# serv1 = f3.add_service()

# extout = act.add_external_output()
# cb8 = act.add_callback(wcet=30, outputs=[extout])
pub7 = act.add_publisher(topic="actuator1")
cb8 = act.add_callback(wcet=30, publishers=[pub7])
# cb8 = act.add_callback(wcet=30)
act.add_subscription(topic="filter3", callback=cb8)


# pprint(system, width=120, indent=1, compact=False)
# sv.validate_system(system)
result = sv.validate_system(system)
result: sv.ValidationResult
if result.errors != []:
    for ln in result.errors:
        print(ln)
else:
    print(result.get_all_cb_chains())
    print(result.sinks)
    print(result.sources)
    chain = result.get_paths_from("sensor1_cb0", "actuator1_cb0")[0]
    print(chain)
    errors, warnings, bksystem = tb.transform_system(system, chain)
    for ln in errors:
        print(ln)
    for ln in warnings:
        print(ln)
    bksystem: bk.System
    tb.monitor(bksystem, "sensor1", "actuator1")
    print(bksystem.gen_declaration())
    print(bksystem.gen_system())
    print(bksystem.max_reaction_time(gen_graph=False))


yprint.save_to_yaml(system, "src/tests/output/out")
yparse.parse_yaml("src/tests/input/example.yaml")

Exv1 = ds.ExecutorV1(5, 10)
PeriodicCallback = ds.PeriodicCallback(5,5,5,1,2,10,10,[1,2,3],[1,2,3],5)
print(Exv1.name())
print(Exv1.system())
print(PeriodicCallback.name())
print(PeriodicCallback.declaration())
print(PeriodicCallback.system())