import ros2system as ros
##old version (handles order of dict improperly and overwrites in case of duplicates)
#import yaml #external library for parsing yaml into object (defacto standard, it seems)
from ruamel.yaml import YAML
from pprint import pprint


#load the yaml-file
with open('example_simpler.yaml','r') as file:
    #yaml_object = yaml.safe_load(file)
    yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
    yaml_object = yaml.load(file)
    ##debug ex
    #print(yaml_object['System']['hosts'][0]['executors'][0]['implementation'])
    if(len(yaml_object)!=1 or not ('System' in yaml_object)):
        raise SyntaxError("file must have single outer-key 'System'")
    pprint(yaml_object, sort_dicts=False)
    # try:
    #     ros_sys = ros.System(name=yaml_object['system'],
    #                          dds_implementation=yaml_object['dds_implementation'],
    #                          default=)
    # except:


#TODO: check that argument order is preserved
    #check that using C-version of ruamel is okay(see website)