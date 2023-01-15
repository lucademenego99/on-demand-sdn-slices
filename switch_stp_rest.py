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
import time
import utils
from webob import Response
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.controller import event
from ryu.lib.packet import ether_types
from ryu.lib import dpid as dpid_lib
import stplib
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.controller import dpset
from ryu.app import simple_switch_13

switch_instance_name = 'switch_api_app'
"""Switch application name, used to link the REST API controller to the switch"""

_PORTNO_LEN = 8

url = '/api/v1'
"""Base URL for the REST API"""

class EventTest(event.EventBase):
    def __init__(self, dp):
        super(EventTest, self).__init__()
        self.dp = dp

class SimpleSwitch13(simple_switch_13.SimpleSwitch13):
    """Base Switch class, called via ryu-manager"""

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    """OpenFlow protocol version"""

    _CONTEXTS = {'stplib': stplib.Stp, 'wsgi': WSGIApplication, 'dpset': dpset.DPSet}
    """Contexts that this Ryu application wants to use."""

    def __init__(self, *args, **kwargs):
        """Initialize the switch
        
        Get references to the STP instance, register the REST API and initialize some variables
        """
        super(SimpleSwitch13, self).__init__(*args, **kwargs)

        self.name = switch_instance_name

        # TODO can it be replaced with the topology ryu app?
        self.dpset = kwargs['dpset']
        """Manage switches"""

        self.switches = []
        """List of switches in the network"""

        self.hosts = []
        """List of hosts in the network"""
        
        self.links = []
        """List of links in the network"""

        self.mac_to_port = {}
        """Dictionary of MAC addresses to port numbers"""

        self.slice_templates=utils.load_slice_templates()
        """List of slice templates"""

        self.slice_qos=utils.load_slice_qos()
        """List of slice QoS rules"""

        self.stp = kwargs['stplib']
        """Spanning Tree Protocol instance"""

        self.slicing = False
        """Whether there is a slice currently activating"""

        self.no_slice_configuration = {
            "1": {"1": [2,3,4,5], "2": [1,3,4,5], "3": [1,2,4,5], "4": [1,2,3,5], "5": [1,2,3,4]},
            "2": {"1": [2,3,4,5], "2": [1,3,4,5], "3": [1,2,4,5], "4": [1,2,3,5], "5": [1,2,3,4]},
            "3": {"1": [2,3,4,5], "2": [1,3,4,5], "3": [1,2,4,5], "4": [1,2,3,5], "5": [1,2,3,4]},
            "4": {"1": [2,3,4,5], "2": [1,3,4,5], "3": [1,2,4,5], "4": [1,2,3,5], "5": [1,2,3,4]},
            "5": {"1": [2,3,4,5], "2": [1,3,4,5], "3": [1,2,4,5], "4": [1,2,3,5], "5": [1,2,3,4]}
        }
        """Default configuration when no slice is active"""

        self.slice_to_port = self.no_slice_configuration
        """Current slice configuration"""

        config = {dpid_lib.str_to_dpid('0000000000000001'):
                  {'bridge': {'priority': 0x8000, 'fwd_delay': 2}},
                  dpid_lib.str_to_dpid('0000000000000002'):
                  {'bridge': {'priority': 0x9000, 'fwd_delay': 2}},
                  dpid_lib.str_to_dpid('0000000000000003'):
                  {'bridge': {'priority': 0xa000, 'fwd_delay': 2}},
                  dpid_lib.str_to_dpid('0000000000000004'):
                  {'bridge': {'priority': 0xb000, 'fwd_delay': 2}},
                  dpid_lib.str_to_dpid('0000000000000005'):
                  {'bridge': {'priority': 0xc000, 'fwd_delay': 2}}}
        """STP configuration"""

        # Register the STP configuration
        self.stp.set_config(config)

        wsgi = kwargs['wsgi']
        """WSGI application instance"""

        # Register the REST API
        wsgi.register(SwitchController, {switch_instance_name: self})
    def get_slice_topology(self,id):
        return utils.load_topo_slice()[id]
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        """Add a flow to the switch

        This function is a modified version of the one in simple_switch_13.py.
        It sends flow_mod messages with table_id set to 1, instead of 0.
        This is needed for the QoS REST API to work properly.

        Args:
            datapath: The switch to add the flow to
            priority: The priority of the flow, from 0 to 65535
            match: The match of the flow, a dictionary of fields and values
            actions: The actions of the flow, a list of dictionaries of fields and values
            buffer_id: The buffer ID of the flow, if any
        """

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, table_id=1, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, table_id=1, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def delete_flow(self, datapath):
        """Delete a from from the switch"""

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        for dst in self.mac_to_port[datapath.id].keys():
            match = parser.OFPMatch(eth_dst=dst)
            mod = parser.OFPFlowMod(
                datapath, command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                priority=1, match=match, table_id=1)
            datapath.send_msg(mod)

    @set_ev_cls(stplib.EventPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """Handle packet in messages from the switch, learning the MAC address of the source and adding a flow if possible.
        Eventually the packet is forwarded to the destination, or flooded.

        Args:
            ev: The EventPacketIn object
        """
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

            # Ignore LLDP packets - they are used for topology discovery
            if eth.ethertype == ether_types.ETH_TYPE_LLDP:
                return

            dpid = datapath.id
            self.mac_to_port.setdefault(dpid, {})

            if str(in_port) in self.slice_to_port[str(dpid)]:
                # learn a mac address to avoid FLOOD next time.
                self.mac_to_port[dpid][src] = in_port

                if dst in self.mac_to_port[dpid]:
                    out_port = self.mac_to_port[dpid][dst]
                else:
                    out_port = ofproto.OFPP_FLOOD

                actions = [parser.OFPActionOutput(out_port)]
            else:
                self.logger.info("Can't communicate due to slice restrictions, switch %s, in_port: %s, slice_to_port %s", dpid, in_port, self.slice_to_port)
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                    in_port=in_port, actions=[], data=None)
                datapath.send_msg(out)
                return

            # install a flow to avoid packet_in next time
            if out_port != ofproto.OFPP_FLOOD:
                match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
                self.add_flow(datapath, 1, match, actions)

            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data

            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                    in_port=in_port, actions=actions, data=data)
            datapath.send_msg(out)

    @set_ev_cls(stplib.EventTopologyChange, MAIN_DISPATCHER)
    def _topology_change_handler(self, ev):
        """Handle topology change events from the STP library.

        Args:
            ev: The EventTopologyChange object
        """

        # Send test event to websocket
        self.send_event("wstopology", EventTest(4))

        dp = ev.dp
        dpid_str = dpid_lib.dpid_to_str(dp.id)
        msg = 'Receive topology change event. Flush MAC table.'
        self.logger.debug("[dpid=%s] %s", dpid_str, msg)

        if dp.id in self.mac_to_port:
            self.delete_flow(dp)
            del self.mac_to_port[dp.id]

    @set_ev_cls(stplib.EventPortStateChange, MAIN_DISPATCHER)
    def _port_state_change_handler(self, ev):
        """Handle port state change events from the STP library.

        Args:
            ev: The EventPortStateChange object
        """
        dpid_str = dpid_lib.dpid_to_str(ev.dp.id)
        of_state = {stplib.PORT_STATE_DISABLE: 'DISABLE',
                    stplib.PORT_STATE_BLOCK: 'BLOCK',
                    stplib.PORT_STATE_LISTEN: 'LISTEN',
                    stplib.PORT_STATE_LEARN: 'LEARN',
                    stplib.PORT_STATE_FORWARD: 'FORWARD'}
        self.logger.debug("[dpid=%s][port=%d] state=%s",
                          dpid_str, ev.port_no, of_state[ev.port_state])
    
    def get_switches(self):
        """Get the list of switches in the network"""
        
        if self.switches == []:
            self.switches = requests.get('http://localhost:8080/v1.0/topology/switches').json()
        return self.switches
    
    def get_hosts(self):
        """Get the list of hosts in the network"""

        if self.hosts == []:
            self.hosts = requests.get('http://localhost:8080/v1.0/topology/hosts').json()
        return self.hosts

    def get_links(self):
        """Get the list of links in the network"""

        if self.links == []:
            self.links = requests.get('http://localhost:8080/v1.0/topology/links').json()
        return self.links
    
    # TODO move it to a separate specially-crafted class
    def str_to_port_no(self, port_no_str):
        assert len(port_no_str) == _PORTNO_LEN
        return int(port_no_str, 8)
    
    def restore_topology(self):
        """Restore the topology of the network"""

        # Restore slice to port - every switch has all ports available
        self.slice_to_port = self.no_slice_configuration

        for switch in self.get_switches():
            switch_id = dpid_lib.str_to_dpid(switch["dpid"])
            bridge = self.stp.bridge_list[switch_id]
            for port in switch["ports"]:
                port = self.dpset.get_port(switch_id, self.str_to_port_no(port["port_no"]))
                bridge.link_up(port)

        # Recalculate the spanning tree with the new topology
        for bridge in self.stp.bridge_list.values():
            bridge.recalculate_spanning_tree()

    def update_topology_slice(self):
        """Update the topology of the network, applying the slice restrictions"""

        def flatten(l):
            """Flatten a list of lists to a single list"""
            res = []
            for item in l:
                if type(item) is list:
                    res.extend(item)
                else:
                    res.append(item)
            return res
        
        for switch in self.get_switches():
            switch_id = dpid_lib.str_to_dpid(switch["dpid"])
            bridge = self.stp.bridge_list[switch_id]
            for port in switch["ports"]:
                port_id = self.str_to_port_no(port["port_no"])
                port = self.dpset.get_port(switch_id, port_id)
                if port_id not in flatten(list(self.slice_to_port[str(switch_id)].values())) and str(port_id) not in list(self.slice_to_port[str(switch_id)].keys()):
                    # disable the port
                    bridge.link_down(port)
                else:
                    # enable the port
                    bridge.link_up(port)


class SwitchController(ControllerBase):
    """Basic controller exposing the REST API"""
    
    def __init__(self, req, link, data, **config):
        """Initialize the controller"""
        super(SwitchController, self).__init__(req, link, data, **config)
        self.switch_app = data[switch_instance_name]
    
    @route('get-switches', url + '/switches', methods=['GET'])
    def get_switches(self, req, **kwargs):
        """Get the list of switches in the network"""
        return Response(text=json.dumps(self.switch_app.get_switches()), content_type='application/json')

    @route('get-slice-topology', url + "/get_slice_topology/{topoid}", methods=['GET'], requirements={'sliceid': r'\d+'})
    def get_slice_topology(self, req, topoid, **kwargs):
        """Get the current applied slice"""
        return Response(text=json.dumps(self.switch_app.get_slice_topology(int(topoid))), content_type='application/json')
    
    @route('get-hosts', url + '/hosts', methods=['GET'])
    def get_hosts(self, req, **kwargs):
        """Get the list of hosts in the network"""
        return Response(text=json.dumps(self.switch_app.get_hosts()), content_type='application/json')
    
    @route('get-links', url + '/links', methods=['GET'])
    def get_links(self, req, **kwargs):
        """Get the list of links in the network"""
        return Response(text=json.dumps(self.switch_app.get_links()), content_type='application/json')
    
    @route('get-slices', url + "/slices", methods=['GET'])
    def get_slices(self, req, **kwargs):
        """Get the list of slices"""
        return Response(content_type='application/json', text=json.dumps({"slices": self.switch_app.slice_templates, "qos": self.switch_app.slice_qos}))

    @route('apply-slice', url + "/slice/{sliceid}", methods=['GET'], requirements={'sliceid': r'\d+'})
    def apply_slice(self, req, sliceid, **kwargs):
        """Apply the slice restrictions to the network
        
        Args:
            req: The request object
            sliceid: The slice ID
        """
        switch = self.switch_app
        switch.slicing = True

        # Check if the slice is valid
        if len(switch.slice_templates) < int(sliceid):
            return Response(status=404)

        # set qos
        for qos_configuration in switch.slice_qos[int(sliceid)-1]:
            # Set the ovsdb_addr to the switch
            requests.put('http://localhost:8080/v1.0/conf/switches/' + dpid_lib.dpid_to_str(qos_configuration['switch_id']) + '/ovsdb_addr', data='"tcp:127.0.0.1:6632"')

            # Wait for the switch to be configured before applying the qos
            time.sleep(0.1)

            res = requests.post('http://localhost:8080/qos/queue/' + dpid_lib.dpid_to_str(qos_configuration['switch_id']), json.dumps({
                "port_name": qos_configuration["port_name"],
                "type": "linux-htb",
                "max_rate": "10000000000",
                "queues": [{"max_rate": qos_configuration['max_rate']}]
            }))

            requests.post('http://localhost:8080/qos/rules/' + dpid_lib.dpid_to_str(qos_configuration['switch_id']), json.dumps({
                "match": {
                    "nw_dst": qos_configuration["nw_dst"],
                    "nw_src": qos_configuration["nw_src"],
                },
                "actions": {
                    "queue": qos_configuration["queue"]
                }
            }))

        # Define the new slicing
        switch.slice_to_port = switch.slice_templates[int(sliceid)-1]
        
        # Update the topology based on the updated slice
        switch.update_topology_slice()

        switch.slicing = False

        return Response(content_type='application/json', text=json.dumps({"status": "ok", "slice": sliceid}))
    
    @route('deactivate-slice', url + "/slice/deactivate", methods=['GET'])
    def deactivate_slice(self, req, **kwargs):
        """Deactivate the slice restrictions to the network
        
        Args:
            req: The request object
        """

        switch = self.switch_app
        switch.slicing = True

        # Delete all qos rules
        requests.delete('http://localhost:8080/qos/rules/all', data=json.dumps({"rule_id": "all", "qos_id": "all"}))

        # Delete all queues
        requests.delete('http://localhost:8080/qos/queue/all')

        # Restore the topology - all ports are available
        switch.restore_topology()
        
        switch.slicing = False

        return Response(content_type='application/json', text=json.dumps({"status": "ok"}))
    
    @route('create-slice', url + "/slice", methods=['POST'])
    def create_slice(self, req, **kwargs):
        """Create a new slice template
        
        Args:
            req: The request object with slice and qos configuration
        """
        switch = self.switch_app

        try:
            req = req.json if req.body else {}
        except ValueError:
            return Response(status=400, content_type='application/json', text=json.dumps({"status": "error", "message": "Invalid JSON"}))

        slice_configuration = req["slice"]
        qos_configuration = req["qos"]

        # convert all keys of slice_configuration to str
        slice_configuration = {str(k): v for k, v in slice_configuration.items()}

        # For each value in slice_configuration, convert all keys to str
        for k, v in slice_configuration.items():
            slice_configuration[k] = {str(k2): v2 for k2, v2 in v.items()}

        # Add the slice to the slice_templates
        switch.slice_templates.append(slice_configuration)

        # Add the slice to the slice_qos
        switch.slice_qos.append(qos_configuration)

        return Response(content_type='application/json', text=json.dumps({"status": "ok", "slice": slice_configuration, "qos": qos_configuration}))
    
    @route('delete-slice', url + "/slice/{sliceid}", methods=['DELETE'], requirements={'sliceid': r'\d+'})
    def delete_slice(self, req, sliceid, **kwargs):
        """Delete a slice template
        
        Args:
            req: The request object
            sliceid: The slice ID
        """
        switch = self.switch_app

        # Check if the slice is valid
        if len(switch.slice_templates) < int(sliceid):
            return Response(status=404)

        # Delete the slice from the slice_templates
        del switch.slice_templates[int(sliceid)-1]

        # Delete the slice from the slice_qos
        del switch.slice_qos[int(sliceid)-1]

        return Response(content_type='application/json', text=json.dumps({"status": "ok", "slices": switch.slice_templates, "qos": switch.slice_qos}))
