import roserer.ros2system as ros
from roserer.rosgraph import RosGraphView
import roserer.rosgraph as rosgraph
from roserer.types import NodeType
import roserer.printers.graph_printer as gp
import roserer.systemvalidator as sv
from roserer.printers.graph_printer import GraphDrawer

# TODO: retrieve graph of this (with some components abstracted away)
system = ros.System(name="simple_system")
host = system.add_host()
executor = host.add_executor()

# Node 1
node_1 = executor.add_node(name="node_1")
pub_1 = node_1.add_publisher(topic="topic_1", name="pub_1")
timer_callback = node_1.add_callback(wcet=1, name="timer_1_callback", publishers=[pub_1])
timer_1 = node_1.add_timer(period=5, callback=timer_callback, name="timer_1")

# Node 2
node_2 = executor.add_node(name="node_2")
x = node_2.add_variable(name="x")
subscription_callback = node_2.add_callback(wcet=1,write_variables=[x], name="subscription_callback")
subscription_1 = node_2.add_subscription(name="subscription_1", callback=subscription_callback, topic="topic_1")
service_callback = node_2.add_callback(wcet=1, name="service_callback", read_variables=[x])
server_1 = node_2.add_service(name="service_1", callback=service_callback)

# Node 3
node_3 = executor.add_node(name="node_3")
y = node_3.add_variable(name="y")
client_1 = node_3.add_client(name="client_1", service="service_1")
timer_2_callback = node_3.add_callback(wcet=1, name="timer_2_callback", request=[ros.Request(client="client_1", response="response_callback")])
response_cb = node_3.add_callback(wcet=1, name="response_callback", write_variables=[y])
timer_2 = node_3.add_timer(period=10, callback=timer_2_callback, name="timer_2")

feedback = sv.validate_system(system)
if feedback.errors != []:
    print(feedback.errors)
    raise ValueError("Validation went wrong!")

graph = RosGraphView(system)
# graph_overview = graph.get_contracted_view().get_all_nodes()
gd = GraphDrawer(graph, [NodeType.NODE, NodeType.CALLBACK, NodeType.VARIABLE, NodeType.TIMER, NodeType.SUBSCRIBER, NodeType.PUBLISHER, NodeType.SERVICE, NodeType.CLIENT])
gd.save_to_file("results/simple_system_graph.pdf")
#gp.transform_and_save_cb_graph(graph_overview, f"results/simple_system_graph.svg")
