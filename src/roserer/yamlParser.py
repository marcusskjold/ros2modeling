import roserer.ros2system as ros
# from roserer.qos import QoS
from ruamel.yaml import YAML
from roserer.types import (
        EXECUTOR, DISTRIBUTION, ARCHITECTURE, OPERATING_SYSTEM, DDS_IMPLEMENTATION,
        TimeUnit)

VALID_ATTRIBUTES = {
    'system' : ['system', 'dds_implementation', 'default_qos', 'default_distribution', 'default_time_unit', 'hosts'],
    'host' : ['host', 'architecture', 'operating_system', 'default_qos', 'default_distribution', 'executors'],
    'executor' : ['executor', 'ros_distribution', 'implementation', 'default_qos', 'nodes'],
    'node' : ['node', 'default_qos', 'publishers','callbacks', 'subscriptions', 'variables', 'timers', 'services', 'external_inputs', 'external_outputs', 'clients'],
    'callback' : ['callback', 'wcet', 'read_variables', 'write_variables', 'calls', 'publishers', 'external_outputs', 'request'],
    'publisher' : ['publisher', 'topic', 'qos'],
    'timer' : ['timer', 'period', 'offset', 'callback', 'end'],
    'subscription' : ['subscription', 'topic', 'callback', 'qos', 'wall_times'],
    'service' : ['service', 'callback', 'qos', 'wall_times'],
    'client' : ['client', 'service', 'qos'],
    'request' : ['client', 'response'],
    'external_input' : ['external_input', 'callback'],
    'external_output' : ['external_output'],
    'variable' : ['variable', 'reset_after_read', 'condition'],
}

VALID_TIME_UNITS = ['nanoseconds', 'ns', 'microseconds', 'us', 'milliseconds', 'ms', 'seconds', 'sec', 'minutes', 'min']


def validate_yaml_attributes(component_type : str, yaml_object : dict) -> None:
    '''
    checks that the attributes of the yaml_object of type 'component_type' are all valid.
    '''
    for attribute in yaml_object.keys():
        if attribute not in VALID_ATTRIBUTES[component_type]:
            raise TypeError(f"One {component_type} contains invalid attribute-name, '{attribute}'. "
                            f"Only the following attributes are valid for a {component_type}: "
                            f"{VALID_ATTRIBUTES[component_type]}")

def parse_services(ros_node: ros.Node, yaml_services: dict) -> None:
    for service in yaml_services:
        validate_yaml_attributes("service", service)
        service_args = {k: service[k] for k in service.keys()
                        & {'qos', 'wall_times'}}
        if 'service' in service:
            service_args['name'] = service['service']
        if 'callback' in service:
            service_args['callback'] = next(
                (callback for callback in ros_node.callbacks
                    if callback.name == service['callback']),
                None)
        ros_node.add_service(**service_args)


def parse_subscriptions(ros_node: ros.Node, yaml_subscriptions: dict) -> None:
    for subscription in yaml_subscriptions:
        validate_yaml_attributes("subscription", subscription)
        subscription_args = {k: subscription[k] for k in subscription.keys()
                             & {'topic', 'qos', 'wall_times'}}
        if 'subscription' in subscription:
            subscription_args['name'] = subscription['subscription']
        if 'callback' in subscription:
            subscription_args['callback'] = next(
                (callback for callback in ros_node.callbacks
                    if callback.name == subscription['callback']),
                None)
        ros_node.add_subscription(**subscription_args)


def parse_timers(ros_node: ros.Node, yaml_timers: dict) -> None:
    for timer in yaml_timers:
        validate_yaml_attributes("timer", timer)
        timer_args = {k: timer[k] for k in timer.keys()
                      & {'period', 'offset', 'end'}}
        if 'timer' in timer:
            timer_args['name'] = timer['timer']
        # find callback that has the specified name
        if 'callback' in timer:
            timer_args['callback'] = next(
                    (callback for callback in ros_node.callbacks
                        if callback.name == timer['callback']),
                    None)
        ros_node.add_timer(**timer_args)


def parse_external_inputs(ros_node: ros.Node, yaml_external_inputs: dict) -> None:
    for external_input in yaml_external_inputs:
        validate_yaml_attributes("external_input", external_input)
        external_input_args = {
                'name' : external_input['external_input']
                } if 'external_input' in external_input else {}
        if 'callback' in external_input:
            external_input_args['callback'] = next(
                    (callback for callback in ros_node.callbacks
                         if callback.name == external_input['callback']),
                    None)
        ros_node.add_external_input(**external_input_args)


def parse_external_outputs(ros_node: ros.Node, yaml_external__outputs: dict) -> None:
    for external_output in yaml_external__outputs:
        validate_yaml_attributes("external_output", external_output)
        external_output_args = {
                'name' : external_output['external_output']
                } if 'external_output' in external_output else {}
        ros_node.add_external_output(**external_output_args)


def parse_variables(ros_node: ros.Node, yaml_variables: dict) -> None:
    for variable in yaml_variables:
        validate_yaml_attributes("variable", variable)
        variable_args = {k: variable[k] for k in variable.keys()
                         & {'reset_after_read', 'condition'}}
        if 'variable' in variable:
            variable_args['name'] = variable['variable']
        ros_node.add_variable(**variable_args)


def parse_callbacks(ros_node: ros.Node, yaml_callbacks: dict) -> None:
    for callback in yaml_callbacks:
        validate_yaml_attributes("callback", callback)
        callback_args = {k: callback[k] for k in callback.keys()
                         & {'wcet', 'calls'}}
        if 'callback' in callback:
            callback_args['name'] = callback['callback']
        if 'publishers' in callback: 
            callback_args['publishers'] = [ros_node.get_publisher(pub_name) for pub_name in callback['publishers']]
        if 'external_outputs' in callback:
            # get list of output-names in current yaml-callback
            yaml_names = [external_output
                          for external_output in callback['external_outputs']]
            # add external outputs from node to args, if present among callbacks of node
            callback_args['outputs'] = [eo for eo in ros_node.external_outputs
                                        if eo.name in yaml_names]
        if 'read_variables' in callback:
            yaml_names = [read_variable for read_variable in callback['read_variables']]
            callback_args['read_variables'] = [rv for rv in ros_node.variables
                                               if rv.name in yaml_names]
        if 'write_variables' in callback:
            yaml_names = [write_variable
                          for write_variable in callback['write_variables']]
            callback_args['write_variables'] = [wv for wv in ros_node.variables
                                                if wv.name in yaml_names]
        if 'request' in callback:
            # add the request with the key-value pair of its content
            request_yaml = callback['request']
            validate_yaml_attributes("request", request_yaml)
            request_args = {k: request_yaml[k] for k in request_yaml.keys()
                         & {'client', 'response'}}
            callback_args['request'] = ros.Request(**request_args)
        ros_node.add_callback(**callback_args)


def parse_clients(ros_node: ros.Node, yaml_clients: dict) -> None:
    for client in yaml_clients:
        validate_yaml_attributes("client", client)
        client_args = {k: client[k] for k in client.keys() & {'service', 'qos'}}
        if 'client' in client:
            client_args['name'] = client['client']
        ros_node.add_client(**client_args)


def parse_publishers(ros_node: ros.Node, yaml_publishers: dict) -> None:
    for publisher in yaml_publishers:
        validate_yaml_attributes("publisher", publisher)
        publisher_args = {k: publisher[k] for k in publisher.keys() & {'qos','topic'}}
        if 'publisher' in publisher:
            publisher_args['name'] = publisher['publisher']
        ros_node.add_publisher(**publisher_args)


def parse_nodes(ros_executor: ros.Executor, yaml_nodes: dict) -> None:
    for node in yaml_nodes:
        validate_yaml_attributes("node", node)
        node_args = {k: node[k] for k in node.keys() & {'default_qos'}}
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
        if 'external_outputs' in node:
            yaml_external_outputs = node['external_outputs']
            parse_external_outputs(ros_node, yaml_external_outputs)
        if 'callbacks' in node:
            yaml_callbacks = node['callbacks']
            parse_callbacks(ros_node, yaml_callbacks)
        if 'external_inputs' in node:
            yaml_external_inputs = node['external_inputs']
            parse_external_inputs(ros_node, yaml_external_inputs)
        if 'timers' in node:
            yaml_timers = node['timers']
            parse_timers(ros_node, yaml_timers)
        if 'subscriptions' in node:
            yaml_subscriptions = node['subscriptions']
            parse_subscriptions(ros_node, yaml_subscriptions)
        if 'services' in node:
            yaml_services = node['services']
            parse_services(ros_node, yaml_services)

def parse_distribution(dist : str) -> DISTRIBUTION:
        """
        Helper for converting ros-distribution to corresponding enum
        """
        match dist.lower():
            case 'kilted' | 'kilted kaiju':
                return DISTRIBUTION.Kilted
            case 'jazzy' | 'jazzy jalisco':
                return DISTRIBUTION.Jazzy
            case 'iron' | 'iron irwini':
                return DISTRIBUTION.Iron
            case 'humble' | 'humble hawksbill':
                return DISTRIBUTION.Humble
            case 'galactic' | 'galactic geochelone':
                return DISTRIBUTION.Galactic
            case 'foxy' | 'foxy fitzroy':
                return DISTRIBUTION.Foxy
            case 'eloquent' | 'eloquent elusor':
                return DISTRIBUTION.Eloquent
            case 'dashing' | 'dashing diademata':
                return DISTRIBUTION.Dashing
            case 'crystal' | 'crystal clemmys':
                return DISTRIBUTION.Crystal
            case 'bouncy' | 'bouncy bolson':
                return DISTRIBUTION.Bouncy
            case 'ardent' | 'ardent apalone':
                return DISTRIBUTION.Ardent
            case _:
                raise ValueError(f"Unspecified distribution chosen. Choose among the following: "
                                 f"{[dist.name for dist in DISTRIBUTION]}."
                                 f"Or don't specify at all")

#recursively call this with current ros-object and current part of yaml-dict
def parse_executors(ros_host: ros.Host, yaml_execs: dict) -> None:
    def parse_implementation(impl : str) -> EXECUTOR:
        """
        Helper for converting executor-implementation to corresponding enum
        """
        match impl.lower():
            case 'singlethreadedexecutor':
                return EXECUTOR.SingleThreadedExecutor
            case 'multithreadedexecutor':
                return EXECUTOR.MultiThreadedExecutor
            case 'staticsinglethreadedexecutor':
                return EXECUTOR.StaticSingleThreadedExecutor
            case 'eventsexecutor':
                return EXECUTOR.EventsExecutor
            case _:
                raise ValueError(f"Unspecified executor-version chosen. Choose among the following: "
                                 f"{[i.name for i in EXECUTOR]}.")
    for executor in yaml_execs:
        validate_yaml_attributes("executor", executor)
        exec_args = {k: executor[k] for k in executor.keys() 
                     & {'default_qos'}}
        if 'implementation' in executor:
            exec_args['implementation'] = parse_implementation(executor['implementation'])
        if 'ros_distribution' in executor:
            exec_args['ros_distribution'] = parse_distribution(executor['ros_distribution'])
        if 'executor' in executor:
            exec_args['name'] = executor['executor']
        ros_executor = ros_host.add_executor(**exec_args)
        yaml_nodes = executor['nodes']
        parse_nodes(ros_executor, yaml_nodes)


def parse_hosts(ros_system: ros.System, yaml_hosts: dict) -> None:
    def parse_operating_system(os : str) -> OPERATING_SYSTEM:
        """
        Helper for converting operating system to corresponding enum
        """
        match os.lower():
            case 'windows':
                return OPERATING_SYSTEM.Windows
            case 'debian':
                return OPERATING_SYSTEM.Debian
            case 'macos' | 'mac' | 'mac_os':
                return OPERATING_SYSTEM.MacOS
            case 'ubuntu':
                return OPERATING_SYSTEM.Ubuntu
            case 'openembedded' | "open_embedded":
                return OPERATING_SYSTEM.OpenEmbedded
            case 'rtlinuxkernel' | 'rt_linux_kernel':
                return OPERATING_SYSTEM.RTLinuxKernel
            case _:
                raise ValueError(f"Unspecified operating system chosen. Choose among the following: "
                                 f"{[o.name for o in OPERATING_SYSTEM]}."
                                 f"Or don't specify at all")
    def parse_architecture(arc : str) -> ARCHITECTURE:
        """
        Helper for converting architecture to corresponding enum
        """
        match arc.lower():
            case 'amd64':
                return ARCHITECTURE.amd64
            case 'arm64':
                return ARCHITECTURE.arm64
            case 'arm32':
                return ARCHITECTURE.arm32
            case _:
                raise ValueError(f"Unspecified architecture chosen. Choose among the following: "
                                 f"{[ar.name for ar in ARCHITECTURE]}."
                                 f"Or don't specify at all")
    for host in yaml_hosts:
        # checks that all attributes are valid
        validate_yaml_attributes("host", host)
        #conditionally populating arguments for adding host
        host_args = {k: host[k] for k in host.keys()
                     & {'default_qos'}}
        if 'operating_system' in host:
            host_args['operating_system'] = parse_operating_system(host['operating_system'])
        if 'architecture' in host:
            host_args['architecture'] = parse_architecture(host['architecture'])
        if 'default_distribution' in host:
            host_args['default_distribution'] = parse_distribution(host['default_distribution'])
        #change key 'name' to 'host'
        if 'host' in host:
            host_args['name'] = host['host']
        #instantiate system-instance from args
        ros_host = ros_system.add_host(**host_args)

        #recursively parse other
        yaml_executors = host['executors']
        parse_executors(ros_host, yaml_executors)

    #helper-method for correctly parsing default_time_unit
def parse_time_unit(unit : str) -> TimeUnit:
    """
    Helper for converting default-time-unit to corresponding enum
    """
    match unit.lower():
        case 'nanoseconds' | 'ns':
            return TimeUnit.NANOSECONDS
        case 'microseconds' | 'us':
            return TimeUnit.MICROSECONDS
        case 'milliseconds' | 'ms':
            return TimeUnit.MILLISECONDS
        case 'seconds' | 'sec':
            return TimeUnit.SECONDS
        case 'minutes' | 'min':
            return TimeUnit.MINUTES
        case _:
            raise ValueError(f"Unspecified timeunit chosen. Choose among the following: "
                             f"{VALID_TIME_UNITS}."
                             f"Or don't specify at all")

def parse_system(yaml_system: dict) -> ros.System: 

    def parse_dds(dds : str) -> DDS_IMPLEMENTATION:
        """
        Helper for converting dds-implementation to corresponding enum
        """
        match dds.lower():
            case 'cyclone' | 'cyclonedds' | 'cyclone_dds':
                return DDS_IMPLEMENTATION.Cyclone
            case 'fast' | 'fastdds' | 'fast_dds':
                return DDS_IMPLEMENTATION.Fast
            case 'connext' | 'rticonnext' | 'rti_connext':
                return DDS_IMPLEMENTATION.Connext
            case 'gurum' | 'gurumdds' | 'gurum_dds':
                return DDS_IMPLEMENTATION.Gurum
            case _:
                raise ValueError(f"Unspecified dds-implementation chosen. Choose among the following: "
                                 f"{[dd.name for dd in DDS_IMPLEMENTATION]}."
                                 f"Or don't specify at all")

    validate_yaml_attributes("system", yaml_system)
    system_args = {k: yaml_system[k] for k in yaml_system.keys()
                   & {'default_qos'}}
    if 'dds_implementation' in yaml_system:
        system_args['dds_implementation'] = parse_dds(yaml_system['dds_implementation'])
    if 'default_distribution' in yaml_system:
        system_args['default_distribution'] = parse_distribution(yaml_system['default_distribution'])
    if 'default_time_unit' in yaml_system:
        system_args['default_time_unit'] = parse_time_unit(yaml_system['default_time_unit'])
    if 'system' in yaml_system:
         system_args['name'] = yaml_system['system']
    ros_sys = ros.System(**system_args)
    #adding hosts
    yaml_hosts = yaml_system['hosts']
    parse_hosts(ros_sys, yaml_hosts)
    return ros_sys


#TODO: check that argument order is preserved
    #check that using C-version of ruamel is okay(see website)
    # maybe add actions to parser
def parse_yaml(file: str) -> ros.System:
    with open(file, 'r') as f:
        yaml = YAML(typ='safe')
        yaml_object = yaml.load(f)
        if(len(yaml_object)!=1 or ('System' not in yaml_object)):
            raise SyntaxError("file must have single outer-key 'System'")
        yaml_system = yaml_object['System']
        return parse_system(yaml_system)
