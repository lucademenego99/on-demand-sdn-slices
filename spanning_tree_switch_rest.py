# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
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

import json
import requests

from webob import Response
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import dpid as dpid_lib
from ryu.lib import stplib
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.controller import dpset
from ryu.app import simple_switch_13

switch_instance_name = 'switch_api_app'
url = '/api/v1'

class SimpleSwitch13(simple_switch_13.SimpleSwitch13):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'stplib': stplib.Stp, 'wsgi': WSGIApplication, 'dpset': dpset.DPSet}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.dpset = kwargs['dpset']

        self.switches = []
        self.mac_to_port = {}
        self.stp = kwargs['stplib']

        self.SLICED = False
        self.slicing = False
        self.slice_to_port = {
            1: {1: [2,3,4,5], 2: [1,3,4,5], 3: [1,2,4,5], 4: [1,2,3,5], 5: [1,2,3,4]},
            2: {1: [2,3,4,5], 2: [1,3,4,5], 3: [1,2,4,5], 4: [1,2,3,5], 5: [1,2,3,4]},
            3: {1: [2,3,4,5], 2: [1,3,4,5], 3: [1,2,4,5], 4: [1,2,3,5], 5: [1,2,3,4]},
            4: {1: [2,3,4,5], 2: [1,3,4,5], 3: [1,2,4,5], 4: [1,2,3,5], 5: [1,2,3,4]},
            5: {1: [2,3,4,5], 2: [1,3,4,5], 3: [1,2,4,5], 4: [1,2,3,5], 5: [1,2,3,4]}
        }

        # Sample of stplib config.
        #  please refer to stplib.Stp.set_config() for details.
        config = {dpid_lib.str_to_dpid('0000000000000001'):
                  {'bridge': {'priority': 0x8000}},
                  dpid_lib.str_to_dpid('0000000000000002'):
                  {'bridge': {'priority': 0x9000}},
                  dpid_lib.str_to_dpid('0000000000000003'):
                  {'bridge': {'priority': 0xa000}}}
        self.stp.set_config(config)

        wsgi = kwargs['wsgi']
        wsgi.register(SwitchController, {switch_instance_name: self})

    def delete_flow(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        for dst in self.mac_to_port[datapath.id].keys():
            match = parser.OFPMatch(eth_dst=dst)
            mod = parser.OFPFlowMod(
                datapath, command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                priority=1, match=match)
            datapath.send_msg(mod)

    @set_ev_cls(stplib.EventPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if not self.slicing:
            msg = ev.msg
            datapath = msg.datapath
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            in_port = msg.match['in_port']

            pkt = packet.Packet(msg.data)
            eth = pkt.get_protocols(ethernet.ethernet)[0]

            dst = eth.dst
            src = eth.src

            dpid = datapath.id
            self.mac_to_port.setdefault(dpid, {})

            self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

            found_out = False
            if in_port in self.slice_to_port[dpid]:
                # learn a mac address to avoid FLOOD next time.
                self.mac_to_port[dpid][src] = in_port

                if dst in self.mac_to_port[dpid]:
                    out_port = self.mac_to_port[dpid][dst]
                    found_out = True
                else:
                    out_port = self.slice_to_port[dpid][in_port]

                # check if out_port is a list
                if isinstance(out_port, list):
                    actions = [parser.OFPActionOutput(p) for p in out_port]
                else:
                    actions = [parser.OFPActionOutput(out_port)]
            else:
                self.logger.info("Can't communicate due to slice restrictions, switch %s, in_port: %s, slice_to_port %s", dpid, in_port, self.slice_to_port)
                actions = []

            # install a flow to avoid packet_in next time
            if found_out:
                match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
                self.add_flow(datapath, 1, match, actions)

            #if out_port != ofproto.OFPP_FLOOD:
            #    match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            #    self.add_flow(datapath, 1, match, actions)

            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data

            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                    in_port=in_port, actions=actions, data=data)
            datapath.send_msg(out)

    @set_ev_cls(stplib.EventTopologyChange, MAIN_DISPATCHER)
    def _topology_change_handler(self, ev):
        dp = ev.dp
        dpid_str = dpid_lib.dpid_to_str(dp.id)
        msg = 'Receive topology change event. Flush MAC table.'
        self.logger.debug("[dpid=%s] %s", dpid_str, msg)

        if dp.id in self.mac_to_port:
            self.delete_flow(dp)
            del self.mac_to_port[dp.id]

    @set_ev_cls(stplib.EventPortStateChange, MAIN_DISPATCHER)
    def _port_state_change_handler(self, ev):
        dpid_str = dpid_lib.dpid_to_str(ev.dp.id)
        of_state = {stplib.PORT_STATE_DISABLE: 'DISABLE',
                    stplib.PORT_STATE_BLOCK: 'BLOCK',
                    stplib.PORT_STATE_LISTEN: 'LISTEN',
                    stplib.PORT_STATE_LEARN: 'LEARN',
                    stplib.PORT_STATE_FORWARD: 'FORWARD'}
        self.logger.debug("[dpid=%s][port=%d] state=%s",
                          dpid_str, ev.port_no, of_state[ev.port_state])
    
    def get_all_switches(self):
        response = requests.get('http://localhost:8080/stats/switches')
        return response.json()



class SwitchController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(SwitchController, self).__init__(req, link, data, **config)
        self.switch_app = data[switch_instance_name]

    @route('slice-1', url + "/slice/1", methods=['GET'])    
    def slice_1(self, req, **kwargs):
        switch = self.switch_app
        switch.slicing = True
        switch.SLICED = True
        switch.slice_to_port = {
            1: {5: 1, 1: 5},
            2: {1: 5, 5: 1},
            3: {},
            4: {},
            5: {}
        }

        # Get all switches available
        if switch.switches == []:
            switch.switches = switch.get_all_switches()
        
        # loop through all slice_to_port keys
        for switch_id in switch.slice_to_port.keys():
            # get the handle of the bridge from switch.stp.bridge_list
            bridge = switch.stp.bridge_list[switch_id]
            for port_id in switch.switches:
                # get port from bridge.ports where port.port_no == port_id
                port = switch.dpset.get_port(switch_id, port_id)
                if port_id not in switch.slice_to_port[switch_id].values():
                    # disable the port
                    bridge.link_down(port)
                else:
                    # enable the port
                    bridge.link_up(port)

        # Delete all flows from all switches with action drop
        # for switch_id in switch.switches:
        #     # delete all flows with actions drop or output
        #     for port in switch.dpset.get_ports(switch_id):
        #         requests.post("http://localhost:8080/stats/flowentry/delete", json={
        #             "dpid": switch_id,
        #             "match": {
        #                 "in_port": port.port_no
        #             },
        #             "actions": []
        #         })

        # for bridge in switch.stp.bridge_list.values():
        #     bridge.recalculate_spanning_tree()

        switch.slicing = False

        return Response(content_type='application/json', text=json.dumps({"status": "ok"}))

    @route('slice-2', url + "/slice/2", methods=['GET'])
    def slice_2(self, req, **kwargs):
        switch = self.switch_app
        switch.SLICED = True
        switch.slice_to_port = {
            1: {},
            2: {},
            3: {3: 5, 5: 3},
            4: {5: 3, 3: 5},
            5: {}
        }

        # Get all switches available
        if switch.switches == []:
            switch.switches = switch.get_all_switches()

        # loop through all slice_to_port keys
        for switch_id in switch.slice_to_port.keys():
            # get the handle of the bridge from switch.stp.bridge_list
            bridge = switch.stp.bridge_list[switch_id]
            for port_id in switch.switches:
                # get port from bridge.ports where port.port_no == port_id
                port = switch.dpset.get_port(switch_id, port_id)
                if port_id not in switch.slice_to_port[switch_id].values():
                    # disable the port
                    bridge.link_down(port)
                else:
                    # enable the port
                    bridge.link_up(port)

        # Delete all flows from all switches with action drop
        # for switch_id in switch.switches:
        #     # delete all flows with actions drop or output
        #     for port in switch.dpset.get_ports(switch_id):
        #         requests.post("http://localhost:8080/stats/flowentry/delete", json={
        #             "dpid": switch_id,
        #             "match": {
        #                 "in_port": port.port_no
        #             },
        #             "actions": []
        #         })

        return Response(content_type='application/json', text=json.dumps({"message": "Activated slice 2"}))
    
    @route('deactivate-slice', url + "/slice/deactivate", methods=['GET'])
    def deactivate_slice(self, req, **kwargs):
        switch = self.switch_app
        switch.slicing = True
        switch.slice_to_port = {
            1: {1: [2,3,4,5], 2: [1,3,4,5], 3: [1,2,4,5], 4: [1,2,3,5], 5: [1,2,3,4]},
            2: {1: [2,3,4,5], 2: [1,3,4,5], 3: [1,2,4,5], 4: [1,2,3,5], 5: [1,2,3,4]},
            3: {1: [2,3,4,5], 2: [1,3,4,5], 3: [1,2,4,5], 4: [1,2,3,5], 5: [1,2,3,4]},
            4: {1: [2,3,4,5], 2: [1,3,4,5], 3: [1,2,4,5], 4: [1,2,3,5], 5: [1,2,3,4]},
            5: {1: [2,3,4,5], 2: [1,3,4,5], 3: [1,2,4,5], 4: [1,2,3,5], 5: [1,2,3,4]}
        }

        # Get all switches available
        if switch.switches == []:
            switch.switches = switch.get_all_switches()

        # loop through all slice_to_port keys
        for switch_id in switch.slice_to_port.keys():
            # get the handle of the bridge from switch.stp.bridge_list
            bridge = switch.stp.bridge_list[switch_id]
            for port_id in switch.switches:
                # get port from bridge.ports where port.port_no == port_id
                port = switch.dpset.get_port(switch_id, port_id)
                # enable the port
                bridge.link_up(port)

        # Delete all flows from all switches with action drop
        # for switch_id in switch.switches:
        #     # delete all flows with actions drop or output
        #     for port in switch.dpset.get_ports(switch_id):
        #         requests.post("http://localhost:8080/stats/flowentry/delete", json={
        #             "dpid": switch_id,
        #             "match": {
        #                 "in_port": port.port_no
        #             },
        #             "actions": []
        #         })

        # for bridge in switch.stp.bridge_list.values():
        #     bridge.recalculate_spanning_tree()
        
        switch.slicing = False

        return Response(content_type='application/json', text=json.dumps({"message": "Deactivated slice"}))

