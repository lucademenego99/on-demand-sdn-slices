import json

TEMPLATES_PATH="resources/slice_templates.json"
""" Path to the slice templates json file """

def get_template_path():
    """ Return the path to the slice templates json file """
    return TEMPLATES_PATH

def load_slice_templates():
    """ Load the slice templates from the json file """
    return json.load(open(TEMPLATES_PATH))


def test():
    """ Test function for the utils module """
    slice_templates=load_slice_templates()
    print(slice_templates)

if __name__=="__main__":
    """ Main function testing the utils module """
    test()
