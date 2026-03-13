from pprint import pprint
import roserer.ros2system as ros
import roserer.printers.graph_printer as gp
#import roserer.yamlPrinter as yprint
import roserer.yamlParser as yparse
import roserer.systemvalidator as sv
import roserer.adapters.backeman_adapter as tb
#import roserer.dust.dust_system as ds
#import roserer.dust.dust_uppaal as du
# import roserer.adapters.dust_adapter as da

from dotenv import load_dotenv
load_dotenv()

# system = ros.System("test", dds_implementation="Generic")
# system.default_qos.depth = 20

# host = system.add_host(operating_system="Generic")
# executor = host.add_executor(
#         implementation="SingleThreadedExecutor", ros_distribution="Eloquent")

# s1 = executor.add_node(name="sensor1")
# s2 = executor.add_node(name="sensor2")
# f1 = executor.add_node(name="filter1")
# f2 = executor.add_node(name="filter2")
# fu = executor.add_node(name="fusion1")
# f3 = executor.add_node(name="filter3")
# act = executor.add_node(name="actuator1")

# # One

# # s1p, s2p, f1p, f2p, fup, f3p = system.add_publishers([
# #     (s1, "sensor1"),
# #     (s2, "sensor2"),
# #     (f1, "filter1"),
# #     (f2, "filter2"),
# #     (fu, "fusion"),
# #     (f3, "filter3"),
# # ])


# # Another

# # s1c, s2c, f1c, f2c, fuc, f3c = system.add_callbacks([
# #     (s1, 30, "sensor1"),
# #     (s2, 40, "sensor2"),
# #     (f1, 40, "filter1"),
# #     (f2, 30, "filter2"),
# #     (fu, 60, "fusion"),
# #     (f3, 20, "filter3"),
# #     (act, 40, extout)
# # ])

# # case st

# pub1 = s1.add_publisher(topic="sensor1")
# cb1 = s1.add_callback(wcet=10, publishers=[pub1])
# s1.add_timer(period=360, callback=cb1)

# pub2 = s2.add_publisher(topic="sensor2")
# cb2 = s2.add_callback(wcet=20, publishers=[pub2])
# s2.add_timer(period=360, callback=cb2)

# pub3 = f1.add_publisher(topic="filter1")
# cb3 = f1.add_callback(wcet=10, publishers=[pub3])
# f1.add_subscription(topic="sensor1", callback=cb3)


# pub4 = f2.add_publisher(topic="filter2")
# cb4 = f2.add_callback(wcet=20, publishers=[pub4])
# f2.add_subscription(topic="sensor2", callback=cb4)

# # subscription variant
# var1 = fu.add_variable()
# cb5 = fu.add_callback(wcet=30, write_variables=[var1])
# fu.add_subscription(topic="filter2", callback=cb5)
# pub5 = fu.add_publisher(topic="fusion1")
# cb6 = fu.add_callback(wcet=30, publishers=[pub5], read_variables=[var1])
# fu.add_subscription(topic="filter1", callback=cb6)


# # timer variant
# # var1 = fu.add_variable()
# # cb5 = fu.add_callback(wcet=30, write_variables=[var1])
# # fu.add_subscription(topic="filter1", callback=cb5)
# # var2 = fu.add_variable()
# # cb6 = fu.add_callback(wcet=30, write_variables=[var2])
# # fu.add_subscription(topic="filter2", callback=cb6)
# # pub5 = fu.add_publisher(topic="fusion1")
# # cb61 = fu.add_callback(wcet=30, read_variables=[var1, var2], publisher=[pub5])
# # fu.add_timer(topic="fusion1", period=100, callback=cb7)

# pub6 = f3.add_publisher(topic="filter3")
# cb7 = f3.add_callback(wcet=30, publishers=[pub6])
# f3.add_subscription(topic="fusion1", callback=cb7)
# # serv1 = f3.add_service()

# # extout = act.add_external_output()
# # cb8 = act.add_callback(wcet=30, outputs=[extout])
# pub7 = act.add_publisher(topic="actuator1")
# cb8 = act.add_callback(wcet=30, publishers=[pub7])
# # cb8 = act.add_callback(wcet=30)
# act.add_subscription(topic="filter3", callback=cb8)


# pprint(system, width=120, indent=1, compact=False)
# sv.validate_system(system)
# result = sv.validate_system(system)
# result: sv.ValidationResult
# if result.errors != []:
#     for ln in result.errors:
#         print(ln)
# else:
#     print(result.get_all_cb_chains())
#     print(result.sinks)
#     print(result.sources)
#     chain = result.get_paths_from("sensor1_cb0", "actuator1_cb0")[0]
#     print(chain)
#     errors, warnings, bksystem = tb.transform_system(system, chain)
#     if result.graph is not None:
#         gp.transform_and_save_cb_graph(result.graph, "testgraph.svg")
#     for ln in errors:
#         print(ln)
#     for ln in warnings:
#         print(ln)
#     if bksystem is not None:
#         tb.monitor(bksystem, "sensor1", "actuator1")
#         print(bksystem.gen_declaration())
#         print(bksystem.gen_system())
#         print(bksystem.max_reaction_time(gen_graph=False))


# yprint.save_to_yaml(system, "src/tests/output/out")
#pprint(yparse.parse_yaml("src/tests/input/example.yaml"))

###debug-example for dust####
# Exv1 = ds.ExecutorV1(5, 10)
# PeriodicCallback = ds.PeriodicCallback(5,5,5,1,2,10,10,[1,2,3],[1,2,3],5)
# print(Exv1.name())
# print(Exv1.system())
# print(PeriodicCallback.name())
# print(PeriodicCallback.declaration())
# print(PeriodicCallback.system())
# sys = ds.System("mySystem")
# sys.add_component("executor_v1",1,90)
# sys.add_component("executor_v2",2,90)
# sys.add_sporadic_callback(
#         id=1,
#         exec_time=50,
#         length=10,
#         releases=[10,20,30,40,50,60,70,80,90,100],
#         type=2,
#         buffersize=10,
#         amount_of_publishers=0,
#         publisher_release_time=[0,0,0,0,0,0,0,0,0,0],
#         publisher_id=[0,0,0,0,0,0,0,0,0,0],executorID=1
#         )
# sys.add_sporadic_callback(
#         id=2,
#         exec_time=100,
#         length=10,
#         releases=[10,20,30,40,50,60,70,80,90,100],
#         type=2,
#         buffersize=10,
#         amount_of_publishers=0,
#         publisher_release_time=[0,0,0,0,0,0,0,0,0,0],
#         publisher_id=[0,0,0,0,0,0,0,0,0,0],
#         executorID=2
#         )
# print(sys)
# print(sys.buffer_overflow())
# print(sys.max_buffer_size())

# ####Example system transformed to Dust-model and checked for max-latency###
test_sys = ros.System(name="test_system")
test_sys.default_distribution = "Humble"
test_sys.default_qos.depth = 10
host_1 = test_sys.add_host()
host_2 = test_sys.add_host()
exec_1 = host_1.add_executor(name="exec_1",ros_distribution="Humble")
exec_2 = host_2.add_executor(name="exec_2",ros_distribution="Humble")
node_1 = exec_1.add_node(name="node_1")
node_2 = exec_2.add_node(name="node_2")

# node_1.add_client(name="client_1",service="service_1")
# test_timer_callback = node_1.add_callback(wcet=5,name="timer_1_cb",request=ros.Request(client="client_1",response="response_cb"))

# #topic-addition
test_pub_1 = node_1.add_publisher(topic="topic_1",name="pub_1")
# cb_test= node_1.add_callback(wcet=5, name="response_cb", publishers=[test_pub_1])
## without explicit publishing 
cb_nested_nested= node_1.add_callback(wcet=2, publishers=[test_pub_1], name="nested_nested_cb")
cb_nested= node_1.add_callback(wcet=2, publishers=[test_pub_1, test_pub_1], name="nested_cb", calls="nested_nested_cb")
cb_test= node_1.add_callback(wcet=5, name="response_cb", publishers=[test_pub_1], calls="nested_cb")
node_1.add_timer(period=10,callback=cb_test)


# #without topic (line below)
# node_1.add_callback(wcet=5, name="response_cb")

# node_1.add_timer(period=5,callback=test_timer_callback,name="timer_1")
cb_1 = node_2.add_callback(wcet=5)
node_2.add_subscription(topic="topic_1", callback=cb_1)
#node_2.add_subscription(topic="topic_1", callback=cb_1, wall_times=[1,2,3])
#service_cb = node_2.add_callback(wcet=5,name="server_cb")
#node_2.add_service(callback=service_cb, name="service_1")
#node_2.add_timer(period=10, callback=cb_1, offset=2, interval=(5,40))

#### tryout:
# 1) implicit creation of ext_input from add_service
#node_2.add_service(name="service_1", callback=service_cb, wall_times=[0,40])

# srv = node_2.add_service(name="service_1", callback=service_cb)

# # 2) additional parameters for creating source inside External_input
# # pros - transparent about being external_input
# # cons - many parameters
#       #- type checking might be complicated
# node_2.add_external_input(name="service_1", 
#                           src_name="new_input", 
#                           src_type="subscription", 
#                           src_cb=service_cb,
#                           src_qos="qos", 
#                           wall_times=[5,10,17])
# # 3) Creating source-object inside arguments:
# # pros - no changes required
# #       - pretty transparent that subscription doesn't exist outside
# # cons - bit excessive
#     #  - it must be decided whether this subscription should be added or not
# node_2.add_external_input(name="service_1", 
#                           wall_times=[5,10,17],
#                           source=ros.Subscription(name="bla",
#                                                   topic="blabla",
#                                                   callback=service_cb))



##topic-addition
# test_sub_cb= node_2.add_callback(wcet=5,name="sub_cb_1")
# node_2.add_subscription(topic="topic_1",callback=test_sub_cb)

test_result = sv.validate_system(test_sys)
test_result: sv.ValidationResult
if test_result.errors != []:
    for ln in test_result.errors:
        print(ln)
else:
    print(test_result.get_all_cb_chains())
    print(test_result.sinks)
    print(test_result.sources)
    #test_chain = test_result.get_paths_from("timer_1_cb", "response_cb")[0]
    #print(test_chain)
    errors, warnings, dust_system = da.transform_system(system=test_sys, validationresult=test_result)
    for ln in errors:
        print(ln)
    for ln in warnings:
        print(ln)
    if dust_system is not None:
        print(dust_system.gen_declaration())
        print(dust_system)
        print(dust_system.gen_system())
    
        #print(dust_system.max_latency())

    #pprint(yparse.parse_yaml("src/tests/input/example_debug_1.yaml"))
    #print(gp.transform_and_save_system(system, "testsys.svg").string())
