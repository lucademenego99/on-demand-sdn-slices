from socket import error as SocketError
from tinyrpc.exc import InvalidReplyError,RPCError
from ryu.app.wsgi import (
    ControllerBase,
    WSGIApplication,
    websocket,
    WebSocketRPCClient
)
from ryu.base import app_manager
from ryu.topology import event, switches
from ryu.ofproto import ofproto_v1_3
from ryu.controller.handler import set_ev_cls
import custom_events
import stplib

class WebSocketTopology(app_manager.RyuApp):
    _CONTEXTS = {
        'stplib': stplib.Stp,
        'wsgi': WSGIApplication,
        'switches': switches.Switches
    }
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(WebSocketTopology, self).__init__(*args, **kwargs)

        self.name = 'wstopology'
        self.rpc_clients = []

        self.stp = kwargs['stplib']

        wsgi = kwargs['wsgi']
        wsgi.register(WebSocketTopologyController, {'app': self})
    
    @set_ev_cls(custom_events.EventTest)
    def _event_test(self, ev):
        """Test event handler"""
        print("A test event was received")

    @set_ev_cls(custom_events.SliceUpdateEvent)
    def _event_slice_update(self, ev):
        """Slice update event handler"""
        self._rpc_broadcall('event_slice_update', ev.slice_template)


    @set_ev_cls(event.EventSwitchLeave)
    def _event_switch_leave_handler(self, ev):
        """Switch leave event handler"""
        msg = ev.switch.to_dict()
        self._rpc_broadcall('event_switch_leave', msg)

    @set_ev_cls(event.EventLinkAdd)
    def _event_link_add_handler(self, ev):
        """Link add event handler"""
        msg = ev.link.to_dict()
        self._rpc_broadcall('event_link_add', msg)

    @set_ev_cls(event.EventLinkDelete)
    def _event_link_delete_handler(self, ev):
        """Link delete event handler"""
        print("event delete")
        msg = ev.link.to_dict()
        self._rpc_broadcall('event_link_delete', msg)

    @set_ev_cls(event.EventHostAdd)
    def _event_host_add_handler(self, ev):
        """Host add event handler"""
        msg = ev.host.to_dict()
        self._rpc_broadcall('event_host_add', msg)

    def _rpc_broadcall(self, func_name, msg):
        """Broadcast RPC call to all clients"""
        disconnected_clients = []
        for rpc_client in self.rpc_clients:
            # NOTE: Although broadcasting is desired,
            #       RPCClient#get_proxy(one_way=True) does not work well
            rpc_server = rpc_client.get_proxy()
            try:
                getattr(rpc_server, func_name)(msg)
            except SocketError:
                self.logger.debug('WebSocket disconnected: %s', rpc_client.ws)
                disconnected_clients.append(rpc_client)
            except InvalidReplyError as e:
                self.logger.error(e)
            except RPCError as e:
                self.logger.error(e)
                self.logger.error(str(func_name))

        for client in disconnected_clients:
            self.rpc_clients.remove(client)


class WebSocketTopologyController(ControllerBase):
    """WebSocket topology controller used to handle WebSocket requests"""
    def __init__(self, req, link, data, **config):
        super(WebSocketTopologyController, self).__init__(
            req, link, data, **config)
        self.app = data['app']

    @websocket('topology', '/v1.0/topology/ws')
    def _websocket_handler(self, ws):
        """WebSocket handler registered to WSGIApplication"""
        rpc_client = WebSocketRPCClient(ws)
        self.app.rpc_clients.append(rpc_client)
        rpc_client.serve_forever()
