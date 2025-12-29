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

def parse_publishers(ros_node, yaml_publishers) -> None:
     for publisher in yaml_publishers:
          publisher_args = {}
          publisher_args = {k: publisher[k] for k in publisher.keys() & {'qos_offered','topic'}}
          if 'publisher' in publisher:
                publisher_args['name'] = publisher['executor']
          ros_node.add_publisher(**publisher_args)

def parse_nodes(ros_executor: ros.Executor, yaml_nodes: dict) -> None:
     for node in yaml_nodes:
        node_args = {}
        if 'node' in node:
                node_args['name'] = node['node']
        ros_node = ros_node.add_node(**node_args)
        if 'publishers' in node:
             yaml_publishers = node['publishers']
             parse_publishers(ros_node, yaml_publishers)
        #if ''
        ##At this point maybe create a number of nodes and e.g. their publishers etc. (non-recursively),
        #then go on to define other things for each (even before parsing node) -> in order for references to be there?
        #the lazy evaluation stuff, where system could create these if not present would be nice feature here?
        yaml_nodes = executor['nodes']
        parse_nodes(ros_executor, yaml_nodes)

#recursively call this with current ros-object and current part of yaml-dict
def parse_executors(ros_host: ros.Host, yaml_execs: dict) -> None:
    for executor in yaml_execs:
        exec_args = {k: executor[k] for k in executor.keys() & {'ros_distribution','implementation'}}
        if 'executor' in executor:
                exec_args['name'] = executor['executor']
        ros_executor = ros_host.add_executor(**exec_args)
        yaml_nodes = executor['nodes']
        parse_nodes(ros_executor, yaml_nodes)

def parse_hosts(ros_system, yaml_hosts) -> None:
     for host in yaml_hosts:
            #conditionally populating arguments for adding host
            #host_args = {k: host.get(k,None) for k in ('operating_system', 'architecture')}
            host_args = {k: host[k] for k in host.keys() & {'operating_system', 'architecture'}}
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
with open('example_simpler.yaml','r') as file:
    #yaml_object = yaml.safe_load(file)
    yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
    yaml_object = yaml.load(file)
    ##debug ex
    print(yaml_object['System']['hosts'][0]['executors'][0]['implementation'])
    if(len(yaml_object)!=1 or not ('System' in yaml_object)):
        raise SyntaxError("file must have single outer-key 'System'")
    #pprint(yaml_object, sort_dicts=False)
    ##TODO: Make function for parsing system-part itself
    try:
        #creating sys
        yaml_system = yaml_object['System']
        ros_system = parse_system(yaml_system)
    except (Exception) as e:
        print(str(e))
    pprint(ros_system)



#TODO: check that argument order is preserved
    #check that using C-version of ruamel is okay(see website)
    #check that white-space in front of field is treated as None