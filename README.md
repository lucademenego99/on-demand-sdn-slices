# On Demand SDN Slices in ComNetsEmu
This is an academic project for the Softwarized and Virtualized Mobile Networks course at the University of Trento, taught by Prof. Fabrizio Granelli.

## Project Goal
The main goal of the project is to implement a network slicing approach to enable dynamic activation/de-activation of network slices via CLI/GUI commands

## Setup the environment
The project relies on ComNetsEmu, a testbed and network emulator that already provides all the dependencies we need to start the Ryu application and the MiniNET topology. More information about it can be found [here](https://git.comnets.net/public-repo/comnetsemu). We personally installed it by cloning the repository and using Vagrant. If installed in this way, the project can be easily started by following these steps:

1. Start the Virtual Machine and get access to a shell
2. Navigate to the directory:
    ```
    cd comnetsemu/app/realizing_network_slicing/
    ```
3. Clone the repository: 
    ```
    git clone https://github.com/lucademenego99/on-demand-sdn-slices.git
    ```
4. Move inside the repo directory: 
    ```
    cd on-demand-sdn-slices
    ```
5. Start the main ryu application by executing
    ```
    sudo ovs-vsctl set-manager ptcp:6632        # Necessary for QoS REST API to work correctly
    ryu run --observe-links ryu_application.py  # Main ryu application
    ```
6. Open another terminal to create the mininet topology
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

## Web application functionalities
The web application consists of two pages namely, the *Homepage* and the *New slice* page. 
On the *Homepage*, the user is able to perform the following tasks:
- View the network topology and the configurations of the various switches in case slices have been applied.
- Apply predefined slices, which simulate common network topologies such as *Bus*, *Tree* and *Star*.
- Apply custom slices, which can be created in the New slice page.
- Deactivate applied slices, allowing the network to revert back to a mesh network configuration.

When the user navigates to the *New slice* he has the following capabilities:
- Create new flow by specifying source and destination hosts.
- Preview the created flow.
- Name the custom slice to make it easier to identify and locate later.
- Save custom slices for future use.

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
The list of available endpoints exposed by `switch_stp_rest` have been defined following the OpenAPI 3.0.0 standard. The YAML file containing the list is available in `resources/docs.yaml`. Otherwise, after having started the application, a webpage showcasing all endpoints can be accessed at [http://localhost:8080/docs/index.html](http://localhost:8080/docs/index.html).

As a last alternative, the docs are also served by SwaggerHub: [https://app.swaggerhub.com/apis/lucademenego99/on-demand-sdn-slices/1.0.0](https://app.swaggerhub.com/apis/lucademenego99/on-demand-sdn-slices/1.0.0).

#### Examples
Get all hosts:
```
curl -X GET http://127.0.0.1:8080/api/v1/hosts
```

Activate a slice:
```
curl -X GET http://127.0.0.1:8080/api/v1/slice/1
```

Delete a slice:
```
curl -X DELETE http://127.0.0.1:8080/api/v1/slice/2
```

Deactivate a slice:
```
curl -X GET http://127.0.0.1:8080/api/v1/slice/deactivate
```
