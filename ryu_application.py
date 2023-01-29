"""
Main application for the Ryu SDN controller.

This module is the main application for the Ryu SDN controller. It
contains the RyuApp class which is the base class for Ryu applications.

Run this application by executing:
- `sudo ovs-vsctl set-manager ptcp:6632`          # Necessary for QoS REST API to work properly
- `ryu run --observe-links ryu_application.py`    # Run application

The application will start a Ryu controller and a web server. The web
server will be accessible at http://localhost:8080. The Ryu controller
will expose a REST API at http://localhost:8080/api/v1. More information
about the REST API can be found in the README.md file or at http://localhost:8080/docs/index.html.

The application will also expose a WebSocket API at
ws://localhost:8080/v1.0/topology/ws allowing to subscribe
to topology changes.

More API routes are actually available, exposed by some pre-configured
Ryu applications:
- ryu.app.rest_qos
- ryu.app.rest_conf_switch
- ryu.app.rest_topology
- ryu.app.ofctl_rest
"""

from webob.static import DirectoryApp

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager


# Serving static files
class GUIServerApp(app_manager.RyuApp):
    """Ryu application for serving static files"""

    _CONTEXTS = {
        'wsgi': WSGIApplication,
    }
    """Contexts required by the Ryu application"""

    def __init__(self, *args, **kwargs):
        """Constructor"""
        super(GUIServerApp, self).__init__(*args, **kwargs)

        wsgi = kwargs['wsgi']
        wsgi.register(GUIServerController)


class GUIServerController(ControllerBase):
    """Controller for serving static files"""
    def __init__(self, req, link, data, **config):
        super(GUIServerController, self).__init__(req, link, data, **config)

        # Serve static files from the 'html' directory
        path = "./html/"
        self.static_app = DirectoryApp(path)
    
    @route('docs', '/docs/*filename')
    def docs_handler(self, req, **kwargs):
        """Handler for the /docs/*filename route, providing the documentation"""
        return self.static_app(req)

    @route('res', '/res/*filename')
    def res_handler(self, req, **kwargs):
        """Handler for the /res/*filename route, providing the resources"""
        return self.static_app(req)
            
    @route('topology', '/{filename:[^/]*}')
    def static_handler(self, req, **kwargs):
        """Handler for the /{filename} route, providing the main static files"""
        if kwargs['filename']:
            req.path_info = kwargs['filename']
        return self.static_app(req)

# Require the following Ryu applications to be loaded
# NOTE: The path to the applications must be absolute
# (see README.md for more information)
app_manager.require_app('/home/vagrant/comnetsemu/app/realizing_network_slicing/on-demand-sdn-slices/ws_topology.py')
app_manager.require_app('/home/vagrant/comnetsemu/app/realizing_network_slicing/on-demand-sdn-slices/switch_stp_rest.py')
app_manager.require_app('ryu.app.rest_qos')
app_manager.require_app('ryu.app.rest_topology')
app_manager.require_app('ryu.app.ofctl_rest')
app_manager.require_app('ryu.app.rest_conf_switch')
