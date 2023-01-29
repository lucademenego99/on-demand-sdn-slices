var CONF = {
    image: {
        width: 50,
        height: 40
    },
    margin : {top: 10, right: 30, bottom: 30, left: 40},
    width : 800,
    height : 800
};
var topology_template={
    "hosts":[
        {
            "host_id":"h1",
            "posx":510,
            "posy":20
        },
        {
            "host_id":"h2",
            "posx":750,
            "posy":200
        },
        {
            "host_id":"h3",
            "posx":650,
            "posy":500
        },
        {
            "host_id":"h4",
            "posx":370,
            "posy":500
        },
        {
            "host_id":"h5",
            "posx":270,
            "posy":200
        }
    ],
    "switches":[
        {
            "host_id":"s1",
            "posx":510,
            "posy":110
        },
        {
            "host_id":"s2",
            "posx":670,
            "posy":230
        },
        {
            "host_id":"s3",
            "posx":610,
            "posy":430
        },
        {
            "host_id":"s4",
            "posx":410,
            "posy":430
        },
        {
            "host_id":"s5",
            "posx":350,
            "posy":230
        }
    ],
    "links":[
        {
            "src":["hosts",0],
            "dst":["switches",0],
            "active":false
        },
        {
            "src":["hosts",1],
            "dst":["switches",1],
            "active":false
        },
        {
            "src":["hosts",2],
            "dst":["switches",2],
            "active":false
        },
        {
            "src":["hosts",3],
            "dst":["switches",3],
            "active":false
        },
        {
            "src":["hosts",4],
            "dst":["switches",4],
            "active":false
        },
        {//s1eth1-s2eth1
            "src":["switches",0],
            "dst":["switches",1],
            "active":false
        },
        {//s1eth2-s3eth1
            "src":["switches",0],
            "dst":["switches",2],
            "active":false
        },
        {//s1eth3-s4eth1
            "src":["switches",0],
            "dst":["switches",3],
            "active":false
        },
        {//s1eth4-s5eth1
            "src":["switches",0],
            "dst":["switches",4],
            "active":false
        },
        {//s2eth2-s3eth2
            "src":["switches",1],
            "dst":["switches",2],
            "active":false
        },
        {//s2eth3-s4eth2
            "src":["switches",1],
            "dst":["switches",3],
            "active":false
        },
        {
            "src":["switches",1],
            "dst":["switches",4],
            "active":false
        },
        {
            "src":["switches",2],
            "dst":["switches",3],
            "active":false
        },
        {
            "src":["switches",2],
            "dst":["switches",4],
            "active":false
        },
        {
            "src":["switches",3],
            "dst":["switches",4],
            "active":false
        }
    ]
}
// append the svg object to the body of the page, basically inserting a canvas in which add the other objects
var svg = d3.select("#network_graph")
.append("svg")
  .attr("width", "100%")
  .attr("height", "100%")
.append("g")
  .attr("transform",
        "translate(" + CONF.margin.left + "," + CONF.margin.top + ")");

var rpc = {
    event_switch_enter: function (params) {
        return "";
    },
    event_switch_leave: function (params) {
        return "";
    },
    event_link_add: function (links) {
        return "";
    },
    event_link_delete: function (links) {
        return "";
    },
    event_test: function (topo_id) {
        get_topology(1);
        console.log("event",topo_id)
        return "";
    },
    event_slice_update: function(slice){
        update_view(slice[0])
    }
}
function update_view(slice){
    r= Array.from(document.getElementsByClassName("activeLink")).forEach((el)=> el.classList.remove("activeLink"))
    /*console.log(r)
    for(var line of r){
        console.log(line)
        line.classList.remove("activeLink")
    }*/
    console.log(slice)
    for(const switch_id in slice){
        console.log(slice[switch_id])
        for(const eth in slice[switch_id]){
            console.log("s"+switch_id+"eth"+eth)
            line=document.getElementsByClassName("s"+switch_id+"eth"+eth)[0]
            if(line && slice[switch_id][eth].length>0){
                console.log(slice[switch_id][eth])
                line.classList.add("activeLink");
            }
        }
    }
    document.getElementById("loadingLayer").style.visibility = "hidden";
}  
function load_view(){
    fetch("http://localhost:8080/api/v1/slice_topology")
    .then((response) => response.json())
    .then((data) => update_view(data));
}
var ws = new WebSocket("ws://" + location.host + "/v1.0/topology/ws");
ws.onmessage = function(event) {
    console.log("Received message: " + event.data);
    var data = JSON.parse(event.data);

    if (rpc[data.method]) {
        var result = rpc[data.method](data.params);

        var ret = {"id": data.id, "jsonrpc": "2.0", "result": result};
        this.send(JSON.stringify(ret));
    } else {
        this.send(JSON.stringify({"id": data.id, "jsonrpc": "2.0", "error": {"message": "unknown method", "code": 34}}));
    }
}
function generateID(link){
    
    let src_host="s"+(link.src[1]+1)
    let src_eth="eth"+(link.dst[1])
    let dst_host="s"+(link.dst[1]+1)
    let dst_eth="eth"+(link.src[1]+1)
    if(link.src[0]=="hosts"){
        src_host="h"+(link.src[1]+1)
        src_eth="eth0"
        dst_host="s"+(link.dst[1]+1)
        dst_eth="eth5"
    }
    return src_host+src_eth+" "+dst_host+dst_eth
}
function load_topology(data){
    svg.selectAll("*").remove()
    console.log("requesting topo", data)
        //console.log(data)
        // Initialize the links
        var link = svg
            .selectAll("line")
            .data(data.links)
            .enter()
            .append("line")
            //.attr("id",function(d){return generateID(d)})
            //.attr("class", "link")
            .attr("class",function(d){return "link "+generateID(d)})
            .style("stroke", function(d){return d.active?"#00cc00":"#aaa"})
            .attr("stroke-width", function(d) { return ((d.active+1) * 2.5); })
            .on("click", function(d) { document.getElementById("details").innerText="link "+data[d.src[0]][d.src[1]].host_id +" "+ data[d.dst[0]][d.dst[1]].host_id; })
        link
            .attr("x1", function(d) { return data[d.src[0]][d.src[1]].posx; })
            .attr("y1", function(d) { return data[d.src[0]][d.src[1]].posy; })
            .attr("x2", function(d) { return data[d.dst[0]][d.dst[1]].posx; })
            .attr("y2", function(d) { return data[d.dst[0]][d.dst[1]].posy; });
        
        // Initialize the nodes
        var switches = svg
        .selectAll("switch")
        .data(data.switches)
        .enter().append("g")
        .attr("class", "switch")
        .on("click", function(d) { 
            switch_id=String(d.host_id[1]).padStart(16, '0');
            fetch("http://localhost:8080/qos/rules/"+switch_id)
            .then((res_rules) => res_rules.json())
            .then((rules) => {
                console.log(rules)
                fetch("http://localhost:8080/qos/queue/"+switch_id)
                .then((res_queue) => res_queue.json())
                .then((queues) =>{
                    document.getElementById("details").innerHTML=""
                    console.log(queues);
                    tbl = document.createElement('table');
                    try{
                    rules=rules[0]["command_result"][0]["qos"]
                    queues=queues[0]["command_result"]["details"][Object.keys(queues[0]["command_result"]["details"])[0]]
                    console.log("2",queues);
                    console.log("2",rules);
                    
                    head=document.createElement("tr")
                    head.innerHTML="<th>src_IP</th><th>dst_IP</th><th>max-rate</th>"

                    tbl.appendChild(head)
                    for(let i=0;i<rules.length;i++){
                        tr=document.createElement("tr")
                        src=document.createElement("td")
                        dst=document.createElement("td")
                        config=document.createElement("td")
                        src.innerText=rules[i]["nw_src"]
                        dst.innerText=rules[i]["nw_dst"]
                        config.innerText=queues[rules[i]["actions"][0]["queue"]]["config"]["max-rate"]+" bps"

                        tr.appendChild(src)
                        tr.appendChild(dst)
                        tr.appendChild(config)
                        tbl.appendChild(tr)
                    }
                    document.getElementById("details").innerHTML="<p>QoS rules defined on switch "+d.host_id[1]+"</p>"
                    document.getElementById("details").appendChild(tbl)
                }
                catch{
                    document.getElementById("details").innerHTML="<p>No QoS rules defined on switch "+d.host_id[1]+"</p>"
                }
                });
            });
            
            

         })
        ;
        switches.append("image")
            .attr("xlink:href", "./res/switch.svg")
            .attr("width", CONF.image.width)
            .attr("height", CONF.image.height);
        switches.append("text")
            .attr("dx", CONF.image.width/2)
            .attr("dy", CONF.image.height)
            .attr("text-anchor", "middle")
            .attr("alignment-baseline", "before-edge")
            .text(function(d) { return d.host_id });
        switches.attr("transform", 
            function(d) {
                return "translate(" +(d.posx-CONF.image.width/2) + "," +(d.posy-CONF.image.height/2) + ")"; 
            });

        var hosts = svg
        .selectAll("host")
        .data(data.hosts)
        .enter().append("g")
        .attr("class", "host");

        hosts.append("image")
            .attr("xlink:href", "./res/host.svg")
            .attr("width", CONF.image.width)
            .attr("height", CONF.image.height);
        hosts.append("text")
            .attr("dx", CONF.image.width/2)
            .attr("dy", CONF.image.height)
            .attr("text-anchor", "middle")
            .attr("alignment-baseline", "before-edge")
            .text(function(d) { return d.host_id });
        hosts.attr("transform", 
            function(d) {
                return "translate(" +(d.posx-CONF.image.width/2) + "," +(d.posy-CONF.image.height/2) + ")"; 
            });
        
        
}
function get_topology(topo_id) {
   // d3.json("/api/v1/get_slice_topology/"+topo_id
}
function delete_template(id){
    console.log("called")
    fetch("http://localhost:8080/api/v1/slice/"+id, {
        method: 'delete',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({sliceid: 5})
      }).then((res)=>res.json()).then((r)=>{
        if(r["status"]=="ok"){
           populate_menu()
        }
      })
}
function populate_menu(){
    let separator=document.getElementById("templates_separator")
    let spans=document.querySelectorAll(".template")
    console.log(spans)
    spans.forEach(span =>span.remove())
    fetch("http://localhost:8080/api/v1/slices")
    .then((templates) => templates.json())
    .then((templatesJson) =>{
        console.log(templatesJson)
        templatesJson=templatesJson["slices"]
        for(let i=0;i<templatesJson.length;i++){
            let temp_container=document.createElement("span")
            temp_container.classList.add("template")
            temp_container.style.position="relative"
            let temp=document.createElement("a");
            temp.setAttribute("href","javascript:load_slice("+(i+1)+")")
            temp.innerText=templatesJson[i]["name"]
            
            temp_container.appendChild(temp)
            separator.parentNode.appendChild(temp_container)
            if(i<4){
                separator.parentNode.insertBefore(temp_container,separator)
            }else{
                let delete_temp=document.createElement("button")
                delete_temp.classList.add("deleteSliceBtn")
                delete_temp.style.position="absolute"
                delete_temp.style.top="0"
                delete_temp.style.right="0"
                delete_temp.style.padding="5px"
                delete_temp.style.backgroundColor="transparent"
                delete_temp.style.border="0"
                delete_temp.onclick=function f(){if(confirm("Permanently delete slice '"+temp_container.innerText+"'?"))delete_template((i+1))}
                let svg=document.createElement("img")
                svg.setAttribute("src", "res/trash_red.svg");
                svg.style.width="20px"
                svg.style.height="20px"
                svg.style.cursor="pointer"
                delete_temp.addEventListener("mouseover",function(){delete_temp.style.backgroundColor="#eee";temp.style.backgroundColor="#bbb" })
                delete_temp.addEventListener("mouseout",function(){delete_temp.style.backgroundColor="transparent";temp.style.removeProperty("background-color")  })
                delete_temp.appendChild(svg)

                temp_container.appendChild(delete_temp)
            }
        }
    })
}
function main() {
    populate_menu()
    load_topology(topology_template);
    load_view();
}
function load_slice(topo_id){

    if(topo_id>0){
        document.getElementById("details").innerHTML=""
        document.getElementById("loadingLayer").style.visibility = "visible";
        fetch("http://localhost:8080/api/v1/slice/"+topo_id).then(console.log("loaded"))
    }
    else{
        fetch("http://localhost:8080/api/v1/slice/deactivate")
    }
    get_topology(topo_id);


}
main();
