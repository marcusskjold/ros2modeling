import ros2system as ros
from pprint import pprint

system = ros.System("super")

host = system.add_host(operating_system="ubuntu 1")
executor = host.add_executor(implementation="EventExecutor")
dds = system.dds

s1, s2, f1, f2, fu, f3, act = executor.add_nodes([
    "sensor1", "sensor2", "filter1", "filter2", "fusion", "filter3", "actuator"
])

topic1 = dds.add_topic()
# dds.add_publisher(node=s1)

pprint(system, width=120, indent=1, compact=False)
