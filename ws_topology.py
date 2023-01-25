# Copyright (C) 2014 Stratosphere Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Usage example

1. Run this application (see README.md)

2. Connect to this application by WebSocket (use your favorite client):
$ wscat -c ws://localhost:8080/v1.0/topology/ws

3. Create your topology (e.g. use mesh_network.py)

4. Topology change is notified, e.g.:
< {"params": [{"ports": [{"hw_addr": "56:c7:08:12:bb:36", "name": "s1-eth1", "port_no": "00000001", "dpid": "0000000000000001"}, {"hw_addr": "de:b9:49:24:74:3f", "name": "s1-eth2", "port_no": "00000002", "dpid": "0000000000000001"}], "dpid": "0000000000000001"}], "jsonrpc": "2.0", "method": "event_switch_enter", "id": 1}
> {"id": 1, "jsonrpc": "2.0", "result": ""}

< {"params": [{"ports": [{"hw_addr": "56:c7:08:12:bb:36", "name": "s1-eth1", "port_no": "00000001", "dpid": "0000000000000001"}, {"hw_addr": "de:b9:49:24:74:3f", "name": "s1-eth2", "port_no": "00000002", "dpid": "0000000000000001"}], "dpid": "0000000000000001"}], "jsonrpc": "2.0", "method": "event_switch_leave", "id": 2}
> {"id": 2, "jsonrpc": "2.0", "result": ""}
...
"""

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

    # TODO It seems that sometimes this handler blocks everything - don't know why
    # I don't even think we need it because the number of switches is not dynamic, maybe we should just remove it
    # @set_ev_cls(event.EventSwitchEnter)
    # def _event_switch_enter_handler(self, ev):
    #     msg = ev.switch.to_dict()
    #     self._rpc_broadcall('event_switch_enter', msg)
    
    @set_ev_cls(custom_events.EventTest)
    def _event_test(self, ev):
        print("test")
        # Handle the custom event (sent with `self.send_event("wstopology", EventTest(4))`)
        # NOTE: this event will fire an exception because there is no event_test method on the websocket handler
        self._rpc_broadcall('event_test', None)

    @set_ev_cls(custom_events.SliceUpdateEvent)
    def _event_slice_update(self, ev):
        # Handle the custom event (sent with `self.send_event("wstopology", EventTest(4))`)
        # NOTE: this event will fire an exception because there is no event_test method on the websocket handler
        self._rpc_broadcall('event_slice_update', ev.slice_template)
    
    # Example of how to listen for events from stplib
    # @set_ev_cls(stplib.EventPacketIn, MAIN_DISPATCHER)
    # def _packet_in_handler(self, ev):
    #    pass
    #    # handle packet in
    #    self._rpc_broadcall('event_packet_in', {'method': "packet-in", 'params': "test"})

    @set_ev_cls(event.EventSwitchLeave)
    def _event_switch_leave_handler(self, ev):
        msg = ev.switch.to_dict()
        self._rpc_broadcall('event_switch_leave', msg)

    @set_ev_cls(event.EventLinkAdd)
    def _event_link_add_handler(self, ev):
        msg = ev.link.to_dict()
        self._rpc_broadcall('event_link_add', msg)

    @set_ev_cls(event.EventLinkDelete)
    def _event_link_delete_handler(self, ev):
        print("event delete")
        msg = ev.link.to_dict()
        self._rpc_broadcall('event_link_delete', msg)

    @set_ev_cls(event.EventHostAdd)
    def _event_host_add_handler(self, ev):
        msg = ev.host.to_dict()
        self._rpc_broadcall('event_host_add', msg)

    def _rpc_broadcall(self, func_name, msg):
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

    def __init__(self, req, link, data, **config):
        super(WebSocketTopologyController, self).__init__(
            req, link, data, **config)
        self.app = data['app']

    @websocket('topology', '/v1.0/topology/ws')
    def _websocket_handler(self, ws):
        rpc_client = WebSocketRPCClient(ws)
        self.app.rpc_clients.append(rpc_client)
        rpc_client.serve_forever()
