import ros2system as ros
##old version (handles order of dict improperly and overwrites in case of duplicates)
#import yaml #external library for parsing yaml into object (defacto standard, it seems)
from ruamel.yaml import YAML
from pprint import pprint

#TODO:might integrate this
#non-object and non-name attributes
ATTRIBUTES = {
     'system' : {'dds_implementation'},
     'host' : {'operating_system', 'architecture'},
     'executor' : {'ros_distribution','implementation'},
     'node' : {},
     'callback' : {},
}
##TODO:
# def parse_timers(ros_node, yaml_timers) -> None:
#      for timer in yaml_timers:
#           timer_args = {}



def parse_callbacks(ros_node: ros.Node, yaml_callbacks: dict) -> None:
     for callback in yaml_callbacks:
          callback_args = {k: callback[k] for k in callback.keys() & {'wcet', 'calls', 'publishers'}}
          if 'callback' in callback:
               callback_args['name'] = callback['callback']
          if 'external_outputs' in callback:
               #get list of output-names in current yaml-callback
               yaml_names = [external_output['external_output'] for external_output in callback['external_outputs']]
               #add external outputs from node to args, if present among callbacks of the node
               callback_args['outputs'] = [eo for eo in ros_node.external_outputs if eo.name in yaml_names]
          if 'read_variables' in callback:
               yaml_names = [read_variable['read_variable'] for read_variable in callback['read_variables']]
               callback_args['read_variable'] = [rv for rv in ros_node.variables if rv.name in yaml_names]
          if 'write_variables' in callback:
               yaml_names = [write_variable['write_variable'] for write_variable in callback['write_variables']]
               callback_args['write_variable'] = [wv for wv in ros_node.variables if wv.name in yaml_names]
          if 'requests' in callback:
               #callback_args['requests'] = [ros.Request(client=cli, timeout=service.timeout) for cli in ros_node.clients for service in callback['requests']]
               #yaml_clients = [request['client'] for request in callback['requests']]
               #1)
               # callback_args['requests'] = []
               # for request in callback['requests']:
               #      for client in ros_node.clients:
               #           if(client.name == request['client']):
               #                callback_args['requests'].append(ros.Request(client=client, timeout=request['timeout']))
               #                break #assumes no duplicate clients -> or redundant ones will be called??
               #2)
               callback_args['requests'] = [ros.Request(client=client, timeout=request['timeout']) for client in ros_node.clients for request in callback['requests'] if client.name == request['client']]
          ros_node.add_callback(**callback_args)

def parse_external_outputs(ros_node: ros.Node, yaml_external__outputs: dict) -> None:
     for external_output in yaml_external__outputs:
          external_output_args = {}
          if 'external_output' in external_output:
               external_output_args['name'] = external_output['external_output']
          ros_node.add_external_output(**external_output_args)

def parse_external_inputs(ros_node: ros.Node, yaml_external_inputs: dict) -> None:
     for external_input in yaml_external_inputs:
          external_input_args = {}
          if 'external_input' in external_input:
               external_input_args['name'] = external_input['external_input']
          ros_node.add_external_input(**external_input_args)

def parse_variables(ros_node: ros.Node, yaml_variables: dict) -> None:
     for variable in yaml_variables:
          variable_args = {}
          if 'variable' in variable:
               variable_args['name'] = variable['variable']
          ros_node.add_variable(**variable_args)

def parse_clients(ros_node: ros.Node, yaml_clients: dict) -> None:
     for client in yaml_clients:
          client_args = {k: client[k] for k in client.keys() & {'service', 'qos_profile'}}
          if 'client' in client:
               client_args['name'] = client['client']
          ros_node.add_client(**client_args)

##TODO: parse services!!! -> and constraint that service shouldn't call itself!!!

def parse_publishers(ros_node: ros.Node, yaml_publishers: dict) -> None:
     for publisher in yaml_publishers:
          publisher_args = {k: publisher[k] for k in publisher.keys() & {'qos_offered','topic'}}
          if 'publisher' in publisher:
                publisher_args['name'] = publisher['publisher']
          ros_node.add_publisher(**publisher_args)

def parse_nodes(ros_executor: ros.Executor, yaml_nodes: dict) -> None:
     for node in yaml_nodes:
        node_args = {}
        if 'node' in node:
                node_args['name'] = node['node']
        ros_node = ros_executor.add_node(**node_args)
        if 'publishers' in node:
             yaml_publishers = node['publishers']
             parse_publishers(ros_node, yaml_publishers)
        if 'clients' in node:
             yaml_clients = node['clients']
             parse_clients(ros_node, yaml_clients)
        if 'variables' in node:
             yaml_variables = node['variables']
             parse_variables(ros_node, yaml_variables)
        if 'external_inputs' in node:
             yaml_external_inputs = node['external_inputs']
             parse_external_inputs(ros_node, yaml_external_inputs)
        if 'external_outputs' in node:
             yaml_external_outputs = node['external_outputs']
             parse_external_outputs(ros_node, yaml_external_outputs)     
        if 'callbacks' in node:
             yaml_callbacks = node['callbacks']
             parse_callbacks(ros_node, yaml_callbacks)
        # if 'timers' in node:
        #      yaml_timers = node['timers']
        #      parse_timers(ros_node, yaml_timers)
        #if ''
        ##At this point maybe create a number of nodes and e.g. their publishers etc. (non-recursively),
        #then go on to define other things for each (even before parsing node) -> in order for references to be there?
        #the lazy evaluation stuff, where system could create these if not present would be nice feature here?

#recursively call this with current ros-object and current part of yaml-dict
def parse_executors(ros_host: ros.Host, yaml_execs: dict) -> None:
    for executor in yaml_execs:
        exec_args = {k: executor[k] for k in executor.keys() & {'ros_distribution','implementation', 'default_qos'}}
        if 'executor' in executor:
                exec_args['name'] = executor['executor']
        ros_executor = ros_host.add_executor(**exec_args)
        yaml_nodes = executor['nodes']
        parse_nodes(ros_executor, yaml_nodes)

def parse_hosts(ros_system, yaml_hosts) -> None:
     for host in yaml_hosts:
            #conditionally populating arguments for adding host
            #host_args = {k: host.get(k,None) for k in ('operating_system', 'architecture')}
            host_args = {k: host[k] for k in host.keys() & {'operating_system', 'architecture', 'default_qos'}}
            #change key 'name' to 'host'
            if 'host' in host:
                host_args['name'] = host['host']
            #instantiate system-instance from args
            ros_host = ros_system.add_host(**host_args)

            yaml_executors = host['executors']
            parse_executors(ros_host, yaml_executors)

def parse_system(yaml_system: dict) -> ros.System:
    ros_sys = ros.System(yaml_system['system'], yaml_system['dds_implementation'])
    #adding hosts
    yaml_hosts = yaml_system['hosts']
    parse_hosts(ros_sys, yaml_hosts)

    return ros_sys

#load the yaml-file
with open('example_debug_1.yaml','r') as file:
    #yaml_object = yaml.safe_load(file)
    yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
    yaml_object = yaml.load(file)
    ##debug ex
    print(yaml_object['System']['hosts'][0]['executors'][0]['implementation'])
    if(len(yaml_object)!=1 or not ('System' in yaml_object)):
        raise SyntaxError("file must have single outer-key 'System'")
    pprint(yaml_object, sort_dicts=False)
    ##TODO: Make function for parsing system-part itself
    #try:
        #creating sys
    yaml_system = yaml_object['System']
    ros_system = parse_system(yaml_system)
    #except (Exception) as e:
    #    print(str(e))
    pprint(ros_system)



#TODO: check that argument order is preserved
    #check that using C-version of ruamel is okay(see website)
    #check that white-space in front of field is treated as None