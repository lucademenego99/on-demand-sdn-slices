var CONF = {
    image: {
        width: 25,
        height: 20
    },
    margin : {top: 10, right: 10, bottom: 10, left: 10},
    width : 400,
    height : 400
};
var topology_template={
    "hosts":[
        {
            "host_id":"h1",
            "posx":200,
            "posy":10
        },
        {
            "host_id":"h2",
            "posx":380,
            "posy":150
        },
        {
            "host_id":"h3",
            "posx":305,
            "posy":380
        },
        {
            "host_id":"h4",
            "posx":95,
            "posy":380
        },
        {
            "host_id":"h5",
            "posx":20,
            "posy":150
        }
    ],
    "switches":[
        {
            "host_id":"s1",
            "posx":200,
            "posy":80
        },
        {
            "host_id":"s2",
            "posx":320,
            "posy":170
        },
        {
            "host_id":"s3",
            "posx":275,
            "posy":325
        },
        {
            "host_id":"s4",
            "posx":125,
            "posy":325
        },
        {
            "host_id":"s5",
            "posx":80,
            "posy":170
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
  .style("width", CONF.width)
  .style("height", CONF.height)
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
    for( const switch_id in slice){
        console.log(slice[switch_id])
        for(const eth in slice[switch_id]){
            console.log("s"+switch_id+"eth"+eth)
            line=document.getElementById("s"+switch_id+"eth"+eth)
            if(line)
            line.classList.add("activeLink");
        }
    }
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
        src_host="s"+(link.src[1]+1)
        src_eth="eth5"
    }
    return src_host+src_eth
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
            .attr("id",function(d){return generateID(d)})
            .attr("class", "link")
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
                        config.innerText=queues[i]["config"]["max-rate"]+" bps"

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
            .attr("xlink:href", "./switch.svg")
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
            .attr("xlink:href", "./host.svg")
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

function main() {
    load_topology(topology_template);
}
function load_slice(topo_id){

    if(topo_id>0){
        fetch("http://localhost:8080/api/v1/slice/"+topo_id)
    }
    else{
        fetch("http://localhost:8080/api/v1/slice/deactivate")
    }
    get_topology(topo_id);


}
main();
/* Set the width of the side navigation to 250px */
function openNav() {
    document.getElementById("mySidenav").style.width = "420px";
    document.getElementById("navOpen").style.opacity="0%"
  }
  
  /* Set the width of the side navigation to 0 */
  function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
    document.getElementById("navOpen").style.opacity="100%"
  }
function addNode(container,node_type,id,position=0){
    // Create the div element
    var node = document.createElement("div");
    node.style.width = "50px";
    node.style.height = "50px";
    node.classList.add("node");

    // Create the image element
    var newImg = document.createElement("img");
    newImg.src = node_type+".svg";
    newImg.style.width = "50px";
    newImg.style.height = "50px";

    // Create the text element
    var newDropDown = document.createElement("select");
    for(let i=1;i<6;i++){
        var newOption = document.createElement("option");
        newOption.value=node_type[0]+i
        newOption.innerText=node_type[0]+i
        newDropDown.appendChild(newOption)
    }
    newDropDown.selectedIndex=id-1
    
    // Append the image and text to the div
    node.appendChild(newImg);
    node.appendChild(newDropDown);

    container.insertBefore(node,container.children[position])
    if(position==0){
        newDropDown.disabled=true
    }else{
        previousSwitch=node.previousSibling
        previousSelect=previousSwitch.children[1]
        newDropDown.remove(previousSelect.value[1]-1)
        lastSwitch=node.nextSibling.nextSibling
        lastSelect=lastSwitch.children[1]
        /*Array.from(newDropDown.children).forEach((el)=>{
            if(el.value==lastSelect.value){
                newDropDown.remove(el)
            }
        })*/
        newDropDown.removeChild(newDropDown.querySelector('option[value="'+lastSelect.value+'"]'))
    }
}
function addInsert(container){
    insertBtn=document.createElement("button")
    insertBtn.onclick=function jsFunc() {
        Array.from(container.children).forEach((el)=>{ Array.from(el.children).forEach((el2)=>{ el2.disabled=true; console.log(el2)})})
        addNode(container,"switch",1,container.children.length-5)
    }
    insertBtn.classList.add("insertBtn")
    svg=document.createElement("img")
    svg.setAttribute("src", "plus_symbol.svg");
    svg.style.width = "20px";
    svg.style.height = "20px";
    insertBtn.appendChild(svg)
    container.insertBefore(insertBtn,container.children[0])
}
function addFlow(){

    src_sel=document.getElementById("src")
    dst_sel=document.getElementById("dst")
    max_rate=document.getElementById("rate")
    if(src.value==dst.value){
        alert("Source and destination must be different")
        return;
    }
    if(max_rate.value<0 || max_rate>10000000000){
        alert("max-rate value out of range")
        return;
    }

    flowsTable=document.getElementById("flowsTable")
    flowcontainer=document.createElement("div")

    addNode(flowcontainer,"host",dst_sel.value[1])
    addNode(flowcontainer,"switch",dst_sel.value[1])
    addInsert(flowcontainer)
    addNode(flowcontainer,"switch",src_sel.value[1])
    addNode(flowcontainer,"host",src_sel.value[1])

    delBtn=document.createElement("button")
    delBtn.classList.add("delButton")
    delBtn.onclick=function jsFunc() {
        document.getElementById("flowsTable").removeChild(flowcontainer)
    }
    
    confirmBtn=document.createElement("button")
    confirmBtn.classList.add("confirmButton")
    confirmBtn.onclick=function jsFunc() {
        console.log("confirmed")
    }

    flowcontainer.append(delBtn)
    flowcontainer.append(confirmBtn)
    flowcontainer.classList.add("flow")
    flowsTable.append(flowcontainer)
}