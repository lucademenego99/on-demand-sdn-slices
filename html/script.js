var CONF = {
    image: {
        width: 50,
        height: 40
    },
    margin : {top: 10, right: 30, bottom: 30, left: 40},
    width : 800,
    height : 800
};
// append the svg object to the body of the page, basically inserting a canvas in which add the other objects
var svg = d3.select("#network_graph")
.append("svg")
  .attr("width", "100%")
  .attr("height", "100%")
.append("g")
  .attr("transform",
        "translate(" + CONF.margin.left + "," + CONF.margin.top + ")");
function get_topology(topo_id) {
    d3.json("/api/v1/get_slice_topology/"+topo_id, function(error, data) {
        //console.log(data)
        // Initialize the links
        var link = svg
            .selectAll("line")
            .data(data.links)
            .enter()
            .append("line")
            .style("stroke", function(d){return d.active?"#00cc00":"#aaa"})
            .attr("stroke-width", function(d) { return ((d.active+1) * 1.5); })
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
        .attr("class", "switch");
        switches.append("image")
            .attr("xlink:href", "./router.svg")
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
        
        
    });
}

function main() {
    get_topology(0);
}
function load_topology(topo_id){

    svg.selectAll("*").remove()
    if(topo_id>0){
        fetch("http://localhost:8080/api/v1/slice/"+topo_id)
    }
    else{
        fetch("http://localhost:8080/api/v1/slice/deactivate")
    }
    get_topology(topo_id);

}
main();
