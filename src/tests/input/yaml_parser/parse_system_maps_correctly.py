import roserer.ros2system as ros
import roserer.qos as qos
import roserer.types as typ

sys = ros.System(name='test_parse_system_maps_correctly',
                 dds_implementation=typ.DDS_IMPLEMENTATION.Fast,
                 default_qos={'history': 'keep_all'},
                 default_distribution=typ.DISTRIBUTION.Humble,
                 default_time_unit=typ.TimeUnit.MILLISECONDS
                 )

host = sys.add_host(name='host_1',
                    operating_system=typ.OPERATING_SYSTEM.Windows,
                    architecture=typ.ARCHITECTURE.amd64,
                    default_qos={'reliability': 'reliable'},
                    default_distribution=typ.DISTRIBUTION.Eloquent)

executor = host.add_executor(name='exe_1',
                  implementation=typ.EXECUTOR.SingleThreadedExecutor,
                  ros_distribution=typ.DISTRIBUTION.Humble,
                  default_qos={'durability': 'volatile'}
                  )

node = executor.add_node(name='node_1',
                         default_qos={'deadline': qos.Duration(seconds=5, nanoseconds=10)})

publisher = node.add_publisher(topic='topic_1', qos={'history': 'keep_last'}, name='pub_1')

variable_1 = node.add_variable(name='v_1', reset_after_read=True, condition=False)

variable_2 = node.add_variable(name='v_2')

e_output = node.add_external_output(name='eo_1')

callback_1 = node.add_callback(wcet=1, name='cb_1', 
                  read_variables=[variable_1], 
                  write_variables=[variable_2],
                  calls='cb_2',
                  outputs=[e_output],
                  publishers=[publisher],
                  requests=[ros.Request(client='client_1', response='cb_2')]
                  )

e_input= node.add_external_input(name='ei_1', callback=callback_1)

callback_2 = node.add_callback(name='cb_2', wcet=5)

node.add_subscription(topic='topic_1',
                      callback=callback_1,
                      name='sub_1',
                      qos={'history': 'keep_last'},
                      wall_times=[1,2,3],
                      )

node.add_timer(period=5, offset=-5, end=10, callback=callback_1,name='timer_1')

node.add_service(name='service_1',
                 callback=callback_1,
                 qos={'history': 'keep_last'},
                 wall_times=[4,5,6])

node.add_client(name='client_1',service='service_1', qos={'history': 'keep_all'})