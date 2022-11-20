# on-demand-sdn-slices

## Run the example topology
Open two terminals. In the first, start the main ryu application by executing:
```
sudo ovs-vsctl set-manager ptcp:6632        # Necessary for QoS REST API to work correctly
ryu run --observe-links ryu_application.py  # Main ryu application
```

In the other terminal, create the example topology by executing:
```
sudo ./mesh-network.py
```

This will create a mesh topology with 5 hosts and 5 switches, called respectively `h1, h2, h3, h4, h5` and `s1, s2, s3, s4, s5`.

At this point, in the first terminal you will see the STP protocol in action: when ports are in `BLOCK` or `FORWARD` state it means the initialization is completed.
From now on, you can:
- try to ping hosts from the mininet console:
  - `<host-1> ping <host-2>     # ping between two specific hosts`
  - `pingall                    # ping all hosts`
- check the currently available bandwidth from the mininet console:
  - `iperf <host-1> <host-2>`
- use the exposed REST API to manage the network (all routes are documented in the next sections)
- use the exposed web application by opening - using a browser - `http://localhost:8080`.

The web application allows you to...


## Ryu application components

The ryu application relies on different components exposed by the ryu library, namely:
- `ryu.app.rest_qos` for handling virtual queues in an easy-to-maintain way;
- `ryu.app.ofctl_rest` to retrieve and update switch stats;
- `ryu.app.rest_conf_switch` to set the *ovsdb_addr* to the switches, essential to create virtual queues;
- `ryu.app.rest_topology` to get information about the current topology (i.e. hosts, switches and links);
- `ryu.app.ws_topology` allowing to connect by WebSocket and listen to topology changes;

The main business logic of the application is inside the file `switch_stp_rest.py`, exposing a switch extended from `SimpleSwitch13_stp` and a **Controller** offering the actual *REST API*.

Some ryu components have been modified a bit to meet this project's requirements, namely the `stplib` and the main `hub`.

## REST API routes
Following are the routes exposed by the `switch_stp_rest` Controller.

...
...

#### Examples
...


Create a new slice:
```
curl -X POST -d '{"slice": {"1": {"5": 1, "1": 5}, "2": {"1": 5, "5": 1}, "3": {}, "4": {}, "5": {}}, "qos": [{"queue": "3", "switch_id": 1, "port_name": "s1-eth5", "max_rate": "500000", "nw_dst": "10.0.0.2", "nw_src": "10.0.0.1"}]}'  http://127.0.0.1:8080/api/v1/slice
```

