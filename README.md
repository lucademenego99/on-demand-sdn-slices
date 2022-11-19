# on-demand-sdn-slices

Topology: mesh with 5 hosts and 5 switches.

Spanning_tree_switch taken from: /usr/lib/python3/dist-packages/ryu/app/simple_switch_stp_13.py


sudo ovs-vsctl set-manager ptcp:6632
ryu-manager ryu.app.rest_qos spanning_tree_switch_rest.py ryu.app.ofctl_rest ryu.app.rest_conf_switch
sudo ./mesh-network.py



### Slice test 1 - hosts 1 and 2

sudo ovs-vsctl set port s1-eth5 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000000 \
queues:1=@1q -- \
--id=@1q create queue other-config:min-rate=10000 other-config:max-rate=500000

sudo ovs-vsctl set port s2-eth5 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000000 \
queues:1=@1q -- \
--id=@1q create queue other-config:min-rate=10000 other-config:max-rate=500000

sudo ovs-ofctl add-flow s2 ip,priority=65500,nw_src=10.0.0.1,nw_dst=10.0.0.2,idle_timeout=0,actions=set_queue:1,normal

sudo ovs-ofctl add-flow s1 ip,priority=65500,nw_src=10.0.0.2,nw_dst=10.0.0.1,idle_timeout=0,actions=set_queue:1,normal
