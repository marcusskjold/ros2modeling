# Copyright (c) 2024 Peter Backeman
# All rights reserved.
#
# This software is provided "as is," without warranty of any kind, express or implied,
# including but not limited to the warranties of merchantability, fitness for a particular purpose,
# and noninfringement. In no event shall the authors or copyright holders be liable for any claim,
# damages, or other liability, whether in an action of contract, tort, or otherwise, arising from,
# out of, or in connection with the software or the use or other dealings in the software.


from .uppaal import UPPAAL # * added '.' in front of imports
from .grapher import Grapher
import os # * added to support proper pathing
from abc import ABC, abstractmethod # for creating abstract class

import time

############From Backeman########################

class UppaalTemplate(ABC):
    #the name of template (must be implemented in subclass)
    @abstractmethod
    def name(self):
        pass

    #get template-instance for system-declaration
    def system(self):
        s = self.name() + "=" + type(self).__name__ + "("
        variables = vars(self)
        for var in variables.values():
            s += str(var) + ","
        return s[:-1] + ");"
    
    #TODO: reformat a list


class ExecutorV1(UppaalTemplate):
    def __init__(self, id, stopTime):
        self.id = id
        self.stopTime = stopTime
    
    def name(self):
        return "ExecV1_" + str(self.id)

class ExecutorV2(UppaalTemplate):
    def __init__(self, id, stopTime):
        self.id = id
        self.stopTime = stopTime
    
    def name(self):
        return "ExecV2_" + str(self.id)
    
    # def system(self):
    #     return self.name() + " = " + "ExecutorV2(" + self.id + "," + self.stopTime + ");"

class Topic(UppaalTemplate):
    def __init__(self, receiver_id, sender_id, delay, max_jitter, buffersize):
        self.receiver_id = receiver_id
        self.sender_id = sender_id
        self.delay = delay
        self.max_jitter = max_jitter
        self.buffersize = buffersize
    
    def name(self):
        return "Topic_" + str(self.sender_id) + "to" + str(self.receiver_id)

class PeriodicCallback(UppaalTemplate):
    def __init__(self, id, exec_time, period, type, offset, buffersize,
                  amount_of_publishers, publisher_release_time, publisher_id, executorID):
        self.id = id
        self.exec_time = exec_time
        self.period = period
        self.type = type
        self.offset = offset
        self.buffersize = buffersize
        self.amount_of_publishers = amount_of_publishers
        self.publisher_release_time = publisher_release_time
        self.publisher_id = publisher_id
        self.executorID = executorID
    
    def name(self):
        return "PeriodicCallback" + str(self.id)


#TODO: consider just correcting period-attr-name here and in UPPAAL-template (see my notes in Template)
class SporadicCallback(UppaalTemplate):
    def __init__(self, id, exec_time, length, period, type, buffersize,
                  amount_of_publishers, publisher_release_time, publisher_id, executorID):
        self.id = id
        self.exec_time = exec_time
        self.length = length
        self.period = period
        self.type = type
        self.buffersize = buffersize
        self.amount_of_publishers = amount_of_publishers
        self.publisher_release_time = publisher_release_time
        self.publisher_id = publisher_id
        self.executorID = executorID
    
    def name(self):
        return "SporadicCallback" + str(self.id)

class DataCallback(UppaalTemplate):
    def __init__(self, id, exec_time, topicID, type, buffersize,
                  amount_of_publishers, publisher_release_time, publisher_id, executorID):
        self.id = id
        self.exec_time = exec_time
        self.topicID = topicID
        self.type = type
        self.buffersize = buffersize
        self.amount_of_publishers = amount_of_publishers
        self.publisher_release_time = publisher_release_time
        self.publisher_id = publisher_id
        self.executorID = executorID
    
    def name(self):
        return "DataCallback" + str(self.id)

        

## Class representing a Node in the ROS system
# class Node():
#     def const_id(self):
#         return "const int " + self.name + " = " + str(self.nid) + ";\n"

#     def int_id(self):
#         return "int " + self.name + "_data = " + str(self.nid) + ";\n"

#     def const_wcet(self):
#         return "const int " + self.name + "_WCET = " + str(self.wcet) + ";\n"

#     def priority(self):
#         if self.prio:
#             return self.prio
#         else:
#             return -self.nid

#     def system(self):
#         return "<>"


# ## Class representing a DataGenerator in the ROS system
# class DataGenerator(Node):
#     def __init__(self, nid, name, period, wcet, delay, monitored, prio):
#         self.nid = nid
#         self.name = name
#         self.period = period
#         self.wcet = wcet
#         self.monitored = monitored
#         self.prio = prio
#         self.delay = delay

#     def declaration(self):
#         s = ""
#         s += self.const_id()
#         s += self.int_id()
#         s += self.const_wcet()
#         s += "const int " + self.name + "_PERIOD = " + str(self.period) + ";\n"

#         return s

#     def system(self):
#         if self.monitored:
#             return (self.name.lower()) + " = MonitoredDataGenerator(" + self.name + ", " + self.name + "_PERIOD" + ", " + str(self.delay) + ");\n"
#         else:
#             return (self.name.lower()) + " = DataGenerator(" + self.name + ", " + self.name + "_PERIOD" + ", " + str(self.delay) + ");\n"


#     def __str__(self):
#         if self.monitored:
#             return "MonitoredDataGenerator(" + str(self.nid) + ", " + self.name + ", " + str(self.period) + ", " + str(self.wcet) + ", " + str(self.delay) + ")"
#         else:
#             return "DataGenerator(" + str(self.nid) + ", " + self.name + ", " + str(self.period) + ", " + str(self.wcet) + ", " + str(self.delay) + ")"


# class ProbabilisticDataGenerator(Node):
#     def __init__(self, nid, name, period, wcet, delay, prob, monitored, prio):
#         self.nid = nid
#         self.name = name
#         self.period = period
#         self.wcet = wcet
#         self.monitored = monitored
#         self.prio = prio
#         self.delay = delay
#         self.prob = prob

#     def declaration(self):
#         s = ""
#         s += self.const_id()
#         s += self.int_id()
#         s += self.const_wcet()
#         s += "const int " + self.name + "_PERIOD = " + str(self.period) + ";\n"

#         return s

#     def system(self):
#         if self.monitored:
#             return (self.name.lower()) + " = MonitoredProbabilisticDataGenerator(" + self.name + ", " + self.name + "_PERIOD" + ", " + str(self.delay) + ", " + str(self.prob) + ");\n"
#         else:
#             return (self.name.lower()) + " = ProbabilisticDataGenerator(" + self.name + ", " + self.name + "_PERIOD" + ", " + str(self.delay) + ", " + str(self.prob) + ");\n"


#     def __str__(self):
#         if self.monitored:
#             return "ProbabilisticMonitoredDataGenerator(" + str(self.nid) + ", " + self.name + ", " + str(self.period) + ", " + str(self.wcet) + ", " + str(self.delay) + ", " + str(self.prob) + ")"
#         else:
#             return "ProbabilisticDataGenerator(" + str(self.nid) + ", " + self.name + ", " + str(self.period) + ", " + str(self.wcet) + ", " + str(self.delay) + ", " + str(self.prob) + ")"



# ## Class representing a Subscriber in the ROS system
# class Subscriber(Node):
#     def __init__(self, nid, name, topic, wcet, data_source, prio):
#         self.nid = nid
#         self.name = name
#         self.topic = topic
#         self.wcet = wcet
#         self.data_source = data_source
#         self.prio = prio

#     def declaration(self):
#         s = ""
#         s += self.const_id()
#         s += self.int_id()
#         s += self.const_wcet()
#         return s

#     def system(self):
#         return (self.name.lower()) + " = Subscriber(" + self.name + ", publish[" + self.topic + "], " + self.data_source + ");\n"


#     def __str__(self):
#         return "Subscriber(" + str(self.nid) + "," + self.name + ", " + str(self.topic) + ", " + str(self.wcet) + ", " + self.data_source + ")"


# ## Class representing a Timer in the ROS system
# class Timer(Node):
#     def __init__(self, nid, name, period, delay, wcet, data_source, prio):
#         self.nid = nid
#         self.name = name
#         self.period = period
#         self.delay = delay
#         self.wcet = wcet
#         self.data_source = data_source
#         self.prio = prio

#     def declaration(self):
#         s = ""
#         s += self.const_id()
#         s += self.int_id()
#         s += self.const_wcet()
#         s += "const int " + self.name + "_PERIOD = " + str(self.period) + ";\n"
#         return s

#     def system(self):
#         return (self.name.lower()) + " = Timer(" + self.name + ", " + str(self.period) + ", " + str(self.delay) + ", " + self.data_source + ");\n"

#     def __str__(self):
#         return "Timer(" + str(self.nid) + "," + self.name + ", " + str(self.period) + ", " + str(self.delay) + ", " + str(self.wcet) + ", " + self.data_source + ")"



# ## Class representing a ROS system
# class System():
#     def __init__(self, name):
#         self.name = name
#         self.nodes = []
#         self.det_hosts = True

#     def __str__(self):
#         s = "System: " + self.name
#         for n in self.nodes:
#             s += "\n  -" + str(n)
#         s += "\n  Monitoring: " + self.actuator + " (+" + str(self.period) + ")"
#         return s


#     def next_id(self):
#         return len(self.nodes)

#     def deterministic_hosts(self, det_hosts):
#         self.det_hosts = det_hosts

#     def add_dependencies(self, name, subscribers, wcets, subprios):
#         if not subprios:
#             subprios = [None]*len(subscribers)
#         for s, w, p in zip(subscribers, wcets, subprios):
#            self.nodes.append(Subscriber(self.next_id(), name + "x" + s, s, w, "pd", p))

#     def add_datagenerator(self, name, period, wcet, delay, monitored=False, prio=None):
#         self.nodes.append(DataGenerator(self.next_id(), name, period, wcet, delay, monitored, prio))

#     def add_probalisticdatagenerator(self, name, period, wcet, delay, prob, monitored=False, prio=None):
#         self.nodes.append(ProbabilisticDataGenerator(self.next_id(), name, period, wcet, delay, prob, monitored, prio))


#     def add_subscriber(self, name, topic, wcet, subscribers, wcets, data_source, prio=None, subprios=None):
#         self.add_dependencies(name, subscribers, wcets, subprios)
#         self.nodes.append(Subscriber(self.next_id(), name, topic, wcet, data_source, prio))

#     def add_timer(self, name, period, delay, wcet, subscribers, wcets, data_source, prio=None, subprios=None):
#         self.nodes.append(Timer(self.next_id(), name, period, delay, wcet, data_source, prio))
#         self.add_dependencies(name, subscribers, wcets, subprios)


#     def monitor(self, actuator, period):
#         self.actuator = actuator
#         self.period = period

#     def gen_declaration(self):
#         s = ""
#         if self.det_hosts:
#             s += "const int deterministic_host = true;\n"
#         else:
#             s += "const int deterministic_host = false;\n"
#         s += "const int C = " + str(len(self.nodes)) + ";\n"
#         for n in self.nodes:
#             s += n.declaration()

#         s += "int DATA[C] = {" + ','.join(["EMPTY"]*len(self.nodes)) + "};\n"
#         s += "int PRIO[C] = {" + ','.join([str(n.priority()) for n in self.nodes]) + "};\n"
#         s += "int WCET[C] = {" + ','.join([n.name + "_WCET" for n in self.nodes]) + "};\n"
#         return s

#     def gen_system(self):
#         s = ""
#         for n in self.nodes:
#             s += n.system()
#         s += "monitor = Monitor(" + self.actuator + ", " + str(self.period) + ");\n"
#         node_names = [n.name.lower() for n in self.nodes]
#         node_names += ['host', 'monitor']
#         s += "system " + ','.join(node_names) + ";\n"

#         return s

#     # Lets find the reaction time, also with a trace so we can generate a graph
#     def max_reaction_time(self, gen_graph=True):
#         modelfile = "tmp.xml"
#         self.write(modelfile)
#         mrt = UPPAAL.sup(modelfile)
#         trace, graph = None, None
#         if gen_graph:
#             query = "E<> monitor.measure && monitor.x[lm] == " + str(mrt)
#             trace = UPPAAL.get_trace(modelfile, query)
#             nodes = list(map(lambda x : x.name, self.nodes))
#             graph = Grapher.gen_mrt(nodes, trace)
#         return mrt, trace, graph

#     def get_graph(self, mrt):
#         print("Get graph...")
#         start = time.time()
#         modelfile = "tmp.xml"
#         self.write(modelfile)
#         trace, graph = None, None
#         query = "E<> monitor.measure && monitor.x[lm] >= " + str(mrt)
#         trace = UPPAAL.get_trace(modelfile, query)
#         nodes = list(map(lambda x : x.name, self.nodes))
#         graph = Grapher.gen_mrt(nodes, trace)
#         end = time.time()
#         print("Query time: ", end - start)
#         return mrt, trace, graph




#     def measure_load(self, load_threshold, percentage, upper_limit):
#         modelfile = "tmp.xml"
#         self.write(modelfile)
#         data = UPPAAL.measure_load(modelfile, load_threshold, percentage, upper_limit)

#         return data

#     def trace(self, query):
#         modelfile = "tmp.xml"
#         self.write(modelfile)
#         return UPPAAL.get_trace(modelfile, query)

#     def random_trace(self, upper_limit):
#         modelfile = "tmp.xml"
#         self.write(modelfile)
#         return UPPAAL.random_trace(modelfile, upper_limit)


#     def write(self, outfile):
#         output = ""
#         declarations_xml = self.gen_declaration()
#         system_xml = self.gen_system()

#         # *Added to make sure location is read properly as per
#         __location__ = os.path.realpath(
#         os.path.join(os.getcwd(), os.path.dirname(__file__)))

#         f = open(os.path.join(__location__, 'template.xml'), 'r')
#         for l in f.readlines():
#             if "!!!DECLARATIONS!!!" in l:
#                 output += declarations_xml
#             elif "!!!SYSTEM!!!" in l:
#                 output += system_xml
#             else:
#                 output += l


#         fout = open(outfile, 'w')
#         for o in output:
#             fout.write(o)
#         fout.close()

#     def print_nodes(self):
#         for n in self.nodes:
#             print("-", n)
