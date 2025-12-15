import ros2system as ros
import yaml #external library for parsing yaml into object (defacto standard, it seems)

#load the yaml-file
with open('example.yaml','r') as file:
    yaml_object = yaml.safe_load(file)
    ##debug ex
    #print(yaml_object['System']['hosts'][0]['executors'][0]['implementation'])
    if(len(yaml_object)!=1 or not ('System' in yaml_object)):
        raise SyntaxError("file must have single outer-key 'System'")
    print(yaml_object)

#TODO: should probably use ruamel.yaml instead to avoid duplicate key errors etc.? (and preserving order of arguments) 