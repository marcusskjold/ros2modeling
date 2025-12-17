import ros2system as ros
##old version (handles order of dict improperly and overwrites in case of duplicates)
#import yaml #external library for parsing yaml into object (defacto standard, it seems)
from ruamel.yaml import YAML
from pprint import pprint



##TODO: Should this be generalized to function for each step in recursion?
#recursively call this with current ros-object and current part of yaml-dict
def parse_executors(ros_host: ros.Host, yaml_execs: dict) -> None:
    print("Converting executors!")
    for executor in yaml_execs:
        exec_args = {k: executor[k] for k in executor.keys() & {'ros_distribution','implementation'}}
        if 'executor' in executor:
                exec_args['name'] = executor['executor']
        ros_executor = ros_host.add_executor(**exec_args)
        print("executor handled!")
    
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