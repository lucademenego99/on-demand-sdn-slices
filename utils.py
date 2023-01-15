import json

TEMPLATES_PATH="resources/slice_templates.json"
""" Path to the slice templates json file """

QOS_PATH="resources/slice_qos.json"
""" Path to the slice qos json file """

TOPO_SLICES_PATH="resources/topologies_templates.json"
""" Path to the slice topology json file """

def load_slice_templates():
    """ Load the slice templates from the json file """
    return json.load(open(TEMPLATES_PATH))

def load_slice_qos():
    """ Load the slice qos from the json file """
    return json.load(open(QOS_PATH))

def load_topo_slice():
    """ Load the slice topology from the json file """
    return json.load(open(TOPO_SLICES_PATH))


def test():
    """ Test function for the utils module """
    slice_templates=load_slice_templates()
    print(slice_templates)
    slice_qos=load_slice_qos()
    print(slice_qos)

if __name__=="__main__":
    """ Main function testing the utils module """
    test()
