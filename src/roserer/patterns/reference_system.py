import roserer.ros2system as ros

def add_sensor_node(e: ros.Executor, name: str, wcet: int, cycle_time: int):
    n = e.add_node(name=name)
    p = n.add_publisher(topic=name)
    cb = n.add_callback(wcet, publishers=[p])
    n.add_timer(cycle_time, cb)
    return n

def add_transform_node(e: ros.Executor, name: str, wcet: int, input_topic: str):
    n = e.add_node(name=name)
    p = n.add_publisher(topic=name)
    cb = n.add_callback(wcet, publishers=[p])
    n.add_subscription(topic=input_topic, callback=cb)
    return n

def add_fusion_node(e: ros.Executor, name: str, wcet: int, sub_topic1: str, sub_topic2: str) -> ros.Node:
    n = e.add_node(name=name)
    p = n.add_publisher(topic=name)
    v1 = n.add_variable(reset_after_read=True, condition=True)
    v2 = n.add_variable(reset_after_read=True, condition=True)
    cb3 = n.add_callback(wcet=wcet, read_variables=[v1, v2], publishers=[p])
    cb1 = n.add_callback(0, write_variables=[v1], calls=cb3.name)
    cb2 = n.add_callback(0, write_variables=[v2], calls=cb3.name)
    n.add_subscription(topic=sub_topic1, callback=cb1)
    n.add_subscription(topic=sub_topic2, callback=cb2)
    return n

def add_cyclic_node(e: ros.Executor, name: str, wcet: int, cycle_time: int, inputs: list[str]) -> ros.Node:
    # Refer to line 83 of:
    # https://github.com/ros-realtime/reference-system/blob/main/reference_system/include/reference_system/nodes/rclcpp/cyclic.hpp
    # And see that it is resets the cache after each read
    n = e.add_node(name=name)
    p = n.add_publisher(topic=name)
    variables = []
    for inp in inputs:
        varname = inp + "_cache"
        v = n.add_variable(varname, reset_after_read=True)
        variables.append(v)
        cbb = n.add_callback(0, write_variables=[v])
        n.add_subscription(topic=inp, callback=cbb)

    cb = n.add_callback(wcet, publishers=[p], read_variables=variables)
    n.add_timer(cycle_time, cb)
    return n

def add_intersection_node(e: ros.Executor, name: str, wcet: int, connections: list[tuple[str, str]]) -> ros.Node:
    n = e.add_node(name=name)
    for sub, pub in connections:
        p = n.add_publisher(topic=pub)
        cb = n.add_callback(wcet, publishers=[p])
        n.add_subscription(topic=sub, callback=cb)
    return n

def add_command_node(e: ros.Executor, name: str, wcet: int, input_topic: str):
    n = e.add_node(name=name)
    cb = n.add_callback(wcet)
    n.add_subscription(topic=input_topic, callback=cb)
    return n
