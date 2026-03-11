from roserer.dust.dust_uppaal import UPPAAL # * added '.' in front of imports
from abc import ABC, abstractmethod # for creating abstract class
import os # * added to support proper pathing
import itertools

# input- and output-files for creating UPPAAL-system
INPUT_UPPAAL_FILE = 'STTT_Full.xml'
OUTPUT_UPPAAL_FILE = 'TEST-dust.xml'

# the size for a given array-parameter
ARRAY_SIZES = {
    'releases' : 'MAXX',
    'publisher_release_time' : 'MAXPUB',
    'publisher_id' : 'MAXPUB'
}

# cb_type encodings for the UPPAAL-model
cb_types = ("TIMER", "SERVICE", "SUBSCRIBER", "CLIENT")

# adds trailing 0'es to list till it has size n
def adapt_list_size(li: list[int], n: int) -> list[int]:
    if len(li) < n:
        li.extend([0] * (n - len(li)))
    return li

# common functionality for all python-UPPAAL-mappings
class UppaalTemplate(ABC):
    # the name of template (must be implemented in subclass)
    @abstractmethod
    def name(self):
        pass

    # the name of given list-parameter, list_param
    def param_name(self, list_name: str) -> str:
        return self.name() + "_" + list_name

    # convert python list-param to UPPAAL-style array
    def toUpArray(self, list_param: list, length : int) -> str:
        adapt_list_size(list_param, length)
        ar = "{"
        ar += ",".join([str(elem) for elem in list_param])
        return ar + "}"
    
    # generate declaration for declarations-file in UPPAAL (necessary arrays)
    def declaration(self, const_sizes : dict = None) -> str:
        decl = ""
        variables = vars(self).items()
        for var, val in variables:
            if type(val) is list:
                size_constant = ARRAY_SIZES[str(var)]
                const_value = const_sizes[size_constant]
                decl += "const int " + self.param_name(var) + "[" + size_constant + "]" + "=" + self.toUpArray(val, const_value) + ";\n"
        return decl

    # get template-instance for system-declaration
    def system(self) -> str: 
        s = self.name() + "=" + type(self).__name__ + "("
        variables = vars(self).items()
        for var, val in variables:
            if type(val) is list:
                s+= self.param_name(var) + ","
            else:
                s+= str(val) + ","
        return s[:-1] + ");\n"
    
    # for printing
    def __str__(self):
        s = "" +type(self).__name__ + "("
        variables = vars(self).items()
        for var, val in variables:
            if type(val) is list:
                s+= str(var) + " = " + self.param_name(var) + ","
            else:
                s+= str(var) + " = " + str(val) + ","
        return s[:-1] + ");\n"


class ExecutorV1(UppaalTemplate):
    def __init__(self, id : int):
        self.id = id
        self.stopTime = "StopTime"
    
    def name(self) -> str:
        return "ExecV1_" + str(self.id)

class ExecutorV2(UppaalTemplate):
    def __init__(self, id : int):
        self.id = id
        self.stopTime = "StopTime"
    
    def name(self) -> str:
        return "ExecV2_" + str(self.id)

class Topic(UppaalTemplate):
    def __init__(self, receiver_id : int, sender_id : int,
                  delay : int, max_jitter : int, buffersize : int):
        self.receiver_id = receiver_id
        self.sender_id = sender_id
        self.delay = delay
        self.max_jitter = max_jitter
        self.buffersize = buffersize

    def name(self) -> str:
        return "Topic_" + str(self.sender_id) + "to" + str(self.receiver_id)

class PeriodicCallback(UppaalTemplate):
    def __init__(
            self, id : int,
            exec_time : int,
            period : int,
            type : int,
            offset : int, 
            buffersize : int,
            amount_of_publishers : int,
            publisher_release_time : list[int],
            publisher_id : list[int],
            executorID : int
            ):
        self.id = id
        self.exec_time = exec_time
        self.period = period
        self.type = cb_types[type]
        self.offset = offset
        self.buffersize = buffersize
        self.amount_of_publishers = amount_of_publishers
        self.publisher_release_time = publisher_release_time
        self.publisher_id = publisher_id
        self.executorID = executorID

    def name(self) -> str:
        return self.type + str(self.id)


class SporadicCallback(UppaalTemplate):
    def __init__(
            self,
            id : int,
            exec_time : int,
            length : int,
            releases : list[int],
            type : int,
            buffersize : int,
            amount_of_publishers : int,
            publisher_release_time : list[int],
            publisher_id : list[int], executorID : int
            ):
        self.id = id
        self.exec_time = exec_time
        self.length = length
        self.releases = releases
        self.type = cb_types[type]
        self.buffersize = buffersize
        self.amount_of_publishers = amount_of_publishers
        self.publisher_release_time = publisher_release_time
        self.publisher_id = publisher_id
        self.executorID = executorID
    
    def name(self):
        return self.type + str(self.id)

class DataCallback(UppaalTemplate):
    def __init__(
            self,
            id : int,
            exec_time : int,
            topicID : int,
            type : int,
            buffersize : int,
            amount_of_publishers : int,
            publisher_release_time : list[int],
            publisher_id : list[int],
            executorID : int
            ):
        self.id = id
        self.exec_time = exec_time
        self.topicID = topicID
        self.type = cb_types[type]
        self.buffersize = buffersize
        self.amount_of_publishers = amount_of_publishers
        self.publisher_release_time = publisher_release_time
        self.publisher_id = publisher_id
        self.executorID = executorID
    
    def name(self):
        return self.type + str(self.id)


## Class representing a ROS system
class System():
    def __init__(self, name):
        self.name = name
        self.executors = []
        self.topics = []
        self.callbacks = []
        self.const_sizes = {}
        ### internal variables for mapping ###
        # id's for topics (sending to and receiving from)
        self._sender_id_counter = itertools.count()
        self._receiver_id_counter = itertools.count()
        # id's for executors
        self._ex_id_counter = itertools.count()
        # env for which subscribers has been mapped
        self._sub_register : dict[str,int] = {}
        # env for nodes registered to executor-id
        self._node_register : dict[str,int] = {}
        # env for id's for each callback tied to given executor
        self._callback_ids : dict[str,dict[str,int]] = {}


    # gets next id for a callback with type 'typ'
    def gen_id(self, typ : int) -> int:
        match typ:
            case 4: # SENDER
                return next(self._sender_id_counter)
            case 5: # RECEIVER
                return next(self._receiver_id_counter)
            case 6: # EXECUTOR
                return next(self._ex_id_counter)

    # checks whether given receiver id exist for subs to 'topic'
    def has_receiver_id(self, topic: str) -> bool:
        return topic in self._sub_register

    # gets id registered for receivers of this topic
    # if no id is registered, creates a new one and registers it
    def get_sub_register_id(self, topic : str) -> int:
        if topic in self._sub_register:
            return self._sub_register[topic]
        else:
            new_id = self.gen_id(5)
            self._sub_register[topic] = new_id
            return new_id

    # register an executor-id for a given node
    def register_node(self, node_name, exe_id) -> None:
        self._node_register[node_name] = exe_id

    # get executor-id for a given node 
    def get_exe_register_id(self, node_name : str) -> int:
        if node_name in self._node_register:
            return self._node_register[node_name]
        else:
            raise KeyError(f"The node, f{node_name}, hasn't been registered")
    
    # registers the id for a callback within a given executor
    def register_callback(self, executor : str, component: str, id : int) -> None:
        self._callback_ids.setdefault(executor,{})[component] = id

    def get_cb_id(self, executor : str, component) -> int:
        return self._callback_ids[executor][component]

    # for printing
    def __str__(self):
        s = "System: "
        components = self.executors + self.topics + self.callbacks
        for c in components:
            s += "\n  -" + str(c)
        return s
    
    # generalized version of below methods (harder to use)
    def add_component(self, component_t : str, *args) -> None:
        match component_t:
            case "executor_v1":
                self.executors.append(ExecutorV1(*args))
            case "executor_v2":
                self.executors.append(ExecutorV2(*args))
            case "topic":
                self.topics.append(Topic(*args))
            case "periodic_callback":
                self.callbacks.append(PeriodicCallback(*args))
            case "sporadic_callback":
                self.callbacks.append(SporadicCallback(*args))
            case "data_callback":
                self.callbacks.append(DataCallback(*args))
            case _:
                raise ValueError("provided component_type not included among templates \
                        in this model!")

    def add_executor_v1(self, id : int):
        self.executors.append(ExecutorV1(id))

    def add_executor_v2(self, id : int):
        self.executors.append(ExecutorV2(id))
    
    def add_topic(self,
                  receiver_id : int,
                  sender_id : int,
                  delay : int,
                  max_jitter : int,
                  buffersize : int
                  ) -> None:
        self.topics.append(Topic(
            receiver_id=receiver_id,
            sender_id=sender_id,
            delay=delay,
            max_jitter=max_jitter,
            buffersize=buffersize
            ))

    def add_periodic_callback(
            self,
            id : int,
            exec_time : int,
            period : int,
            type : int,
            offset : int,
            buffersize : int,
            amount_of_publishers : int,
            publisher_release_time : list[int],
            publisher_id : list[int],
            executorID : int
            ) -> None:
        self.callbacks.append(PeriodicCallback(
            id, exec_time, period, type, offset, buffersize, amount_of_publishers,
            publisher_release_time, publisher_id, executorID))
        
    def add_sporadic_callback(
            self,
            id : int,
            exec_time : int,
            length : int,
            releases : list[int],
            type : int,
            buffersize : int,
            amount_of_publishers : int,
            publisher_release_time : list[int],
            publisher_id : list[int],
            executorID : int
            ) -> None:
        self.callbacks.append(SporadicCallback(
            id, exec_time, length, releases, type, buffersize, amount_of_publishers, 
            publisher_release_time, publisher_id, executorID))
    
    def add_data_callback(
            self,
            id : int,
            exec_time : int,
            topicID : int,
            type : int,
            buffersize : int,
            amount_of_publishers : int,
            publisher_release_time : list[int],
            publisher_id : list[int],
            executorID : int
            ) -> None:
        self.callbacks.append(DataCallback(
            id, exec_time, topicID, type, buffersize, amount_of_publishers,
            publisher_release_time, publisher_id, executorID))
        
    def add_data_callback(self, id : int, exec_time : int, topicID : int, type : int, buffersize : int,
                  amount_of_publishers : int, publisher_release_time : list[int],
                    publisher_id : list[int], executorID : int):
        self.callbacks.append(DataCallback(id, exec_time, topicID, type, buffersize,
                  amount_of_publishers, publisher_release_time, publisher_id, executorID))


    # for sizeconstants: if size is 0, makes it 1 instead
    def adapt_to_min(self, const_size : int) -> int:
        if const_size == 0:
            return 1
        else:
            return const_size
          
    # get the maximum number of callbacks of a single type in the system
    def get_max_cb_type(self)-> int:
        # group callbacks by their types
        cb_types ={}
        for cb in self.callbacks:
            cb_types[cb.type] = cb_types.get(cb.type, 0) + 1
        return self.adapt_to_min(max(cb_types.values()))
        
    
    # get maximum amount of releases for a wall-timer
    def get_max_wt_releases(self) -> int:
        #get list of releases
        wall_timers = [cb.releases for cb in self.callbacks if isinstance(cb,SporadicCallback)]
        #return longest instance
        return self.adapt_to_min(len(max(wall_timers, key=len, default=[0])))
    
    # get number of topics (set to one if no occurences)
    def get_topics_size(self) -> int:
        return self.adapt_to_min(len(self.topics))
    
    # get number of executors (set to one if no occurences)
    def get_execs_size(self) -> int:
        return self.adapt_to_min(len(self.executors))

    # get maximum amount of publishers in a single callback
    def get_max_pubs(self) -> int:
        publisher_amounts = [cb.amount_of_publishers for cb in self.callbacks]
        return self.adapt_to_min(max(publisher_amounts, default=1))
    
    # updates constant-sizes in environment
    def gen_const_sizes(self) -> None:
        self.const_sizes["MAX"] = self.get_max_cb_type()
        self.const_sizes["MAXX"] = self.get_max_wt_releases()
        self.const_sizes["MAXTOPICS"] = self.get_topics_size()
        self.const_sizes["MAXEXEC"] = self.get_execs_size()
        self.const_sizes["MAXPUB"] = self.get_max_pubs()


    # generates constant-declarations for system
    def gen_declaration(self, stop_time : int = -1) -> str:
        # updates environment of constant-sizes
        self.gen_const_sizes()
        s = ""
        # applies constant sizes
        s += "const int StopTime = " + str(stop_time) + ";\n"
        s += "const int MAX = " + str(self.const_sizes["MAX"]) + ";\n"
        s += "const int MAXX = " + str(self.const_sizes["MAXX"]) + ";\n"
        s += "const int MAXTOPICS = " + str( self.const_sizes["MAXTOPICS"]) + ";\n" #TODO: maybe 0 not very good?
        s += "const int MAXEXEC = " + str(self.const_sizes["MAXEXEC"]) + ";\n"
        s += "const int MAXPUB = " + str(self.const_sizes["MAXPUB"]) + ";\n"
        components : list[UppaalTemplate] = self.executors + self.topics + self.callbacks
        for c in components:
            s += c.declaration(self.const_sizes)
        return s

    # generates instantiations in system-declaration
    def gen_system(self, prioritized=True) -> str:
        s = ""
        components: list[UppaalTemplate] = self.executors + self.topics + self.callbacks
        for c in components:
            s += c.system()
        s += "system "
        # if callbacks released at scheduling time
        if prioritized:
            components = self.topics + self.callbacks
            exec_names = [exe.name() for exe in self.executors]
            s += ','.join(exec_names) + " &lt; " # translates to "<" in UPPAAL
        component_names = [c.name() for c in components]
        s += ','.join(component_names) + ";\n"
        return s

    def buffer_overflow(self, prioritized : bool = True, stop_time : int = -1) -> dict:
        self.write(infile=INPUT_UPPAAL_FILE, outfile=OUTPUT_UPPAAL_FILE, prioritized=prioritized, stop_time=stop_time)
        checkables : list[UppaalTemplate] = self.topics + self.callbacks
        checkables_names = [c.name() for c in checkables]
        return UPPAAL.buffer_overflow(OUTPUT_UPPAAL_FILE, checkables_names)
    
    # assumes NO bufferoverflow or result will be trivially the size of the buffer
    def max_buffer_size(self, prioritized : bool = True, stop_time : int = -1) -> dict[str,int]:
        self.write(infile=INPUT_UPPAAL_FILE, outfile=OUTPUT_UPPAAL_FILE, prioritized=prioritized, stop_time=stop_time)
        checkables = self.topics + self.callbacks
        checkables_names = [c.name() for c in checkables]
        return UPPAAL.max_buffer_size(OUTPUT_UPPAAL_FILE, checkables_names)
    
    def max_latency(self, prioritized : bool = True, stop_time : int = -1) -> dict[str,int]:
        self.write(infile=INPUT_UPPAAL_FILE, outfile=OUTPUT_UPPAAL_FILE, prioritized=prioritized, stop_time=stop_time)
        checkables_names = [c.name() for c in self.callbacks]
        return UPPAAL.max_latency(OUTPUT_UPPAAL_FILE, checkables_names)
    
    def max_latency_trace(self, max_latencies : dict | None = None, prioritized : bool = True, stop_time : int = -1):
        self.write(infile=INPUT_UPPAAL_FILE, outfile=OUTPUT_UPPAAL_FILE, prioritized=prioritized, stop_time=stop_time)
        checkables_names = [c.name() for c in self.callbacks]
        return UPPAAL.max_latency_trace(
                OUTPUT_UPPAAL_FILE, checkables_names, max_latencies)
    
    #TODO: Extract into common utils lib
    def write(self, infile : str, outfile : str, prioritized : bool = True, stop_time : int = -1):
        output = ""
        declarations_xml = self.gen_declaration(stop_time)
        system_xml = self.gen_system(prioritized)

        # *Added to make sure location is read properly as per
        __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))

        f = open(os.path.join(__location__, infile), 'r')
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
