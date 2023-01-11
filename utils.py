import json
templates_path="resources/slice_templates.json"
qos_path="resources/slice_qos.json"
topo_slices_path="resources/topologies_templates.json"
def load_slice_templates():
    return json.load(open(templates_path))
def load_slice_qos():
    return json.load(open(qos_path))
def load_topo_slice():
    return json.load(open(topo_slices_path))

def test():
    slice_templates=load_slice_templates()
    print(slice_templates)
    slice_qos=load_slice_qos()
    print(slice_qos)
if __name__=="__main__":
    test()
