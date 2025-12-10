import ros2system as ros
from pprint import pprint


system = ros.System("super")

host = system.add_host(operating_system="ubuntu 1")
# executor = host.add_executor(implementation="EventExecutor")

node1 = host.add_node("MIchael")

s1, s2, f1, f2, fu, f3, act = host.executors[0].add_nodes([
    "sensor1", "sensor2", "filter1", "filter2", "fusion", "filter3", "actuator"
])

dummyqos = {}
topic1 = system.add_topic()
# dds.add_publisher(node=s1)

cb1 = ros.Callback(
    read_variable=[],
    results={0: ros.Callback.Result(
        write_variables=[],
        wcet=30,
        calls=[],
        outputs=ros.Publisher(
            topic=topic1,
            qos_offered=dummyqos))})
# s1.add_timer()

# s1.add_publisher(topic1)
# f1.subscribeto(s1)


pprint(system, width=120, indent=1, compact=False)
