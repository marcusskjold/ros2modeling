import roserer.backeman
import importlib.resources
from roserer.backeman.uppaal import UPPAAL
from roserer.backeman.grapher import Grapher

import time

Trace = list[tuple[str, str, str, str]]
TMP_FILE = "-backeman.xml"

## Class representing a Node in the ROS system
class Node():
    name: str
    nid: int
    wcet: int
    prio: int

    def const_id(self) -> str:
        return "const int " + self.name + " = " + str(self.nid) + ";\n"

    def int_id(self) -> str:
        return "int " + self.name + "_data = " + str(self.nid) + ";\n"

    def const_wcet(self) -> str:
        return "const int " + self.name + "_WCET = " + str(self.wcet) + ";\n"

    def priority(self) -> int:
        if self.prio:
            return self.prio
        else:
            return -self.nid

    def system(self) -> str:
        return "<>"


## Class representing a DataGenerator in the ROS system
class DataGenerator(Node):
    def __init__(self, nid, name, period, wcet, delay, monitored, prio):
        self.nid = nid
        self.name = name
        self.period = period
        self.wcet = wcet
        self.monitored = monitored
        self.prio = prio
        self.delay = delay

    def declaration(self) -> str:
        s = ""
        s += self.const_id()
        s += self.int_id()
        s += self.const_wcet()
        s += "const int " + self.name + "_PERIOD = " + str(self.period) + ";\n"

        return s

    def system(self) -> str:
        if self.monitored:
            return (self.name.lower()) + " = MonitoredDataGenerator(" \
                + self.name + ", " \
                + self.name + "_PERIOD" + ", " \
                + str(self.delay) + ");\n"
        else:
            return (self.name.lower()) + " = DataGenerator(" \
                + self.name + ", " \
                + self.name + "_PERIOD" + ", " \
                + str(self.delay) + ");\n"

    def __str__(self) -> str:
        if self.monitored:
            return "MonitoredDataGenerator(" \
                + str(self.nid) + ", " \
                + self.name + ", " \
                + str(self.period) + ", " \
                + str(self.wcet) + ", " \
                + str(self.delay) + ")"
        else:
            return "DataGenerator(" \
                + str(self.nid) + ", " \
                + self.name + ", " \
                + str(self.period) + ", " \
                + str(self.wcet) + ", " \
                + str(self.delay) + ")"


class ProbabilisticDataGenerator(Node):
    def __init__(self, nid, name, period, wcet, delay, prob, monitored, prio):
        self.nid = nid
        self.name = name
        self.period = period
        self.wcet = wcet
        self.monitored = monitored
        self.prio = prio
        self.delay = delay
        self.prob = prob

    def declaration(self) -> str:
        s = ""
        s += self.const_id()
        s += self.int_id()
        s += self.const_wcet()
        s += "const int " + self.name + "_PERIOD = " + str(self.period) + ";\n"

        return s

    def system(self) -> str:
        if self.monitored:
            return (
                self.name.lower()) + " = MonitoredProbabilisticDataGenerator(" \
                + self.name + ", " \
                + self.name + "_PERIOD" + ", " \
                + str(self.delay) + ", " \
                + str(self.prob) + ");\n"
        else:
            return (
                self.name.lower()) + " = ProbabilisticDataGenerator(" \
                + self.name + ", " \
                + self.name + "_PERIOD" + ", " \
                + str(self.delay) + ", " \
                + str(self.prob) + ");\n"

    def __str__(self) -> str:
        if self.monitored:
            return "ProbabilisticMonitoredDataGenerator(" \
                + str(self.nid) + ", " \
                + self.name + ", " \
                + str(self.period) + ", " \
                + str(self.wcet) + ", " \
                + str(self.delay) + ", " \
                + str(self.prob) + ")"
        else:
            return "ProbabilisticDataGenerator(" \
                + str(self.nid) + ", " \
                + self.name + ", " \
                + str(self.period) + ", " \
                + str(self.wcet) + ", " \
                + str(self.delay) + ", " \
                + str(self.prob) + ")"


## Class representing a Subscriber in the ROS system
class Subscriber(Node):
    def __init__(self, nid, name, topic, wcet, data_source, prio):
        self.nid = nid
        self.name = name
        self.topic = topic
        self.wcet = wcet
        self.data_source = data_source
        self.prio = prio

    def declaration(self):
        s = ""
        s += self.const_id()
        s += self.int_id()
        s += self.const_wcet()
        return s

    def system(self) -> str:
        return (
            self.name.lower()) + " = Subscriber(" \
            + self.name + ", publish[" \
            + self.topic + "], " \
            + self.data_source + ");\n"

    def __str__(self) -> str:
        return "Subscriber(" \
            + str(self.nid) + "," \
            + self.name + ", " \
            + str(self.topic) + ", " \
            + str(self.wcet) + ", " \
            + self.data_source + ")"


## Class representing a Timer in the ROS system
class Timer(Node):
    def __init__(self, nid, name, period, delay, wcet, data_source, prio):
        self.nid = nid
        self.name = name
        self.period = period
        self.delay = delay
        self.wcet = wcet
        self.data_source = data_source
        self.prio = prio

    def declaration(self) -> str:
        s = ""
        s += self.const_id()
        s += self.int_id()
        s += self.const_wcet()
        s += "const int " + self.name + "_PERIOD = " + str(self.period) + ";\n"
        return s

    def system(self) -> str:
        return (
            self.name.lower()) + " = Timer(" \
            + self.name + ", " \
            + str(self.period) + ", " \
            + str(self.delay) + ", " \
            + self.data_source + ");\n"

    def __str__(self):
        return "Timer(" \
            + str(self.nid) + "," \
            + self.name + ", " \
            + str(self.period) + ", " \
            + str(self.delay) + ", " \
            + str(self.wcet) + ", " \
            + self.data_source + ")"


## Class representing a ROS system
class System():
    actuator: str
    period: int
    name: str
    node: list[Node]
    det_hosts: bool

    def __init__(self, name: str):
        self.name = name
        self.nodes = []
        self.det_hosts = True

    def __str__(self) -> str:
        s = "System: " + self.name
        for n in self.nodes:
            s += "\n  -" + str(n)
        s += "\n  Monitoring: " + self.actuator + " (+" + str(self.period) + ")"
        return s


    def next_id(self) -> int:
        return len(self.nodes)

    def deterministic_hosts(self, det_hosts: bool) -> None:
        self.det_hosts = det_hosts

    def add_dependencies(
            self,
            name: str, 
            subscribers: list[str],
            wcets: list[int],
            subprios: list[int | None] | None
    ) -> None:
        if not subprios:
            subprios = [None]*len(subscribers)
        for s, w, p in zip(subscribers, wcets, subprios):
           self.nodes.append(Subscriber(self.next_id(), name + "x" + s, s, w, "pd", p))

    def add_datagenerator(self, name, period, wcet, delay, monitored=False, prio=None
                          ) -> None:
        self.nodes.append(
            DataGenerator(self.next_id(), name, period, wcet, delay, monitored, prio))

    def add_probalisticdatagenerator(
            self,
            name,
            period,
            wcet,
            delay,
            prob,
            monitored=False,
            prio=None
    ) -> None:
        self.nodes.append(ProbabilisticDataGenerator(
            self.next_id(), name, period, wcet, delay, prob, monitored, prio))

    def add_subscriber(
            self,
            name,
            topic,
            wcet,
            subscribers,
            wcets,
            data_source,
            prio=None,
            subprios=None
    ) -> None:
        self.add_dependencies(name, subscribers, wcets, subprios)
        self.nodes.append(Subscriber(
            self.next_id(), name, topic, wcet, data_source, prio))

    def add_timer(
            self,
            name,
            period,
            delay,
            wcet,
            subscribers,
            wcets,
            data_source,
            prio=None,
            subprios=None
    ) -> None:
        self.nodes.append(Timer(
            self.next_id(), name, period, delay, wcet, data_source, prio))
        self.add_dependencies(name, subscribers, wcets, subprios)

    def monitor(self, actuator: str, period: int) -> None:
        self.actuator = actuator
        self.period = period

    def gen_declaration(self) -> str:
        s = ""
        if self.det_hosts:
            s += "const int deterministic_host = true;\n"
        else:
            s += "const int deterministic_host = false;\n"
        s += "const int C = " + str(len(self.nodes)) + ";\n"
        for n in self.nodes:
            s += n.declaration()

        s += "int DATA[C] = {" + ','.join(["EMPTY"]*len(self.nodes)) + "};\n"
        s += "int PRIO[C] = {" + ','.join([str(n.priority()) for n in self.nodes]) + "};\n"
        s += "int WCET[C] = {" + ','.join([n.name + "_WCET" for n in self.nodes]) + "};\n"
        return s

    def gen_system(self) -> str:
        s = ""
        for n in self.nodes:
            s += n.system()
        s += "monitor = Monitor(" + self.actuator + ", " + str(self.period) + ");\n"
        node_names = [n.name.lower() for n in self.nodes]
        node_names += ['host', 'monitor']
        s += "system " + ','.join(node_names) + ";\n"

        return s

    # Lets find the reaction time, also with a trace so we can generate a graph
    def max_reaction_time(self, gen_graph=True
                          ) -> tuple[int | None, Trace | None, list[str] | None]:
        self.write(self.name + TMP_FILE)
        mrt: int | None = UPPAAL.sup(self.name + TMP_FILE)
        trace, graph = None, None
        if gen_graph:
            query = "E<> monitor.measure && monitor.x[lm] == " + str(mrt)
            trace: Trace = UPPAAL.get_trace(self.name + TMP_FILE, query)
            nodes: list[str] = list(map(lambda x : x.name, self.nodes))
            graph = Grapher.gen_mrt(nodes, trace)
        return mrt, trace, graph

    def get_graph(self, mrt: int) -> tuple[int, Trace, list[str]]:
        print("Get graph...")
        start = time.time()
        self.write(self.name
                   )
        trace, graph = None, None
        query = "E<> monitor.measure && monitor.x[lm] >= " + str(mrt)
        trace = UPPAAL.get_trace(self.name + TMP_FILE, query)
        nodes = list(map(lambda x : x.name, self.nodes))
        graph = Grapher.gen_mrt(nodes, trace)
        end = time.time()
        print("Query time: ", end - start)
        return mrt, trace, graph

    def measure_load(self, load_threshold: int, percentage: int, upper_limit: int
                     ) -> tuple[str, bool | str]:
        self.write(self.name + TMP_FILE)
        data = UPPAAL.measure_load(
            self.name + TMP_FILE, load_threshold, percentage, upper_limit)

        return data

    def trace(self, query: str) -> Trace:
        self.write(self.name + TMP_FILE)
        return UPPAAL.get_trace(self.name + TMP_FILE, query)

    def random_trace(self, upper_limit: int) -> Trace:
        self.write(self.name + TMP_FILE)
        return UPPAAL.random_trace(self.name + TMP_FILE, upper_limit)

    def write(self, outfile: str) -> None:
        output = ""
        declarations_xml = self.gen_declaration()
        system_xml = self.gen_system()

        f = importlib.resources.open_text(roserer.backeman, 'template.xml')
        for ln in f.readlines():
            if "!!!DECLARATIONS!!!" in ln:
                output += declarations_xml
            elif "!!!SYSTEM!!!" in ln:
                output += system_xml
            else:
                output += ln


        fout = open(outfile, 'w')
        for o in output:
            fout.write(o)
        fout.close()

    def print_nodes(self) -> None:
        for n in self.nodes:
            print("-", n)
