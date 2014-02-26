function markPhaseSelected(event) {
  var phaseSelectedClassname = "phaseselected";
  var regex = new RegExp("(?:^|\\s)" + phaseSelectedClassname + "(?!\\S)", '');
  var el = event.target
  if (el.className.match(regex)) {
    el.className = el.className.replace(regex, '')
  } else {
    el.className += " " + phaseSelectedClassname;
  }
}


var margin = {top: 20, right: 20, bottom: 30, left: 40};
var width = 960 - margin.left - margin.right;
var height = 500 - margin.top - margin.bottom;

var x0 = d3.scale.ordinal()
                 .rangeRoundBands([0, width], .1);

var x1 = d3.scale.ordinal();

var y = d3.scale.linear()
                .range([height, 0]);

var color = d3.scale.ordinal()
                    .range(["#98abc5", "#8a89a6", "#7b6888", "#6b486b",
                            "#a05d56", "#d0743c", "#ff8c00"]);

var xAxis = d3.svg.axis()
                  .scale(x0)
                  .orient("bottom");

var yAxis = d3.svg.axis()
                  .scale(y)
                  .orient("left")
                  .tickFormat(d3.format(".2s"));

function findSelectedPhases() {
  return jQuery.makeArray($(".phaseselected").map(function (i, val) { return val.innerText; }))
               .join(",")
}

function fetchDataAndCreateBarChart(phases) {
  var phases = findSelectedPhases();
  url_string = "/perfdash/data";
  if (phases != "") {
     url_string = url_string + "?requested_steps=" + phases;
  }
  d3.tsv(url_string, function(error, data) {
    d3.select("#chart").select("svg").remove();
    var svg = d3.select("#chart").append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var otherColumns = d3.keys(data[0]).filter(function(key) { return key !== "step"; });

    data.forEach(function(d) {
      d.stepTimes = otherColumns.map(function(name) { return {name: name, value: +d[name]}; });
    });

    x0.domain(data.map(function(d) { return d.step; }));
    x1.domain(otherColumns).rangeRoundBands([0, x0.rangeBand()]);
    y.domain([0, d3.max(data, function(d) { return d3.max(d.stepTimes, function(d) { return d.value; }); })]);

    svg.append("g")
       .attr("class", "x axis")
       .attr("transform", "translate(0," + height + ")")
       .call(xAxis);

    svg.append("g")
       .attr("class", "y axis")
       .call(yAxis)
       .append("text")
       .attr("transform", "rotate(-90)")
       .attr("y", 6)
       .attr("dy", ".71em")
       .style("text-anchor", "end")
       .text("Step Time (s)");

    var state = svg.selectAll(".state")
                   .data(data)
                   .enter().append("g")
                   .attr("class", "g")
                   .attr("transform", function(d) { return "translate(" + x0(d.step) + ",0)"; });

    state.selectAll("rect")
         .data(function(d) { return d.stepTimes; })
         .enter()
         .append("rect")
         .attr("width", x1.rangeBand())
         .attr("x", function(d) { return x1(d.name); })
         .attr("y", function(d) { return y(d.value); })
         .attr("height", function(d) { return height - y(d.value); })
         .style("fill", function(d) { return color(d.name); });

    var legend = svg.selectAll(".legend")
                    .data(otherColumns.slice())
                    .enter()
                    .append("g")
                    .attr("class", "legend")
                    .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

    legend.append("rect")
          .attr("x", width - 18)
          .attr("width", 18)
          .attr("height", 18)
          .style("fill", color);

    legend.append("text")
          .attr("x", width - 24)
          .attr("y", 9)
          .attr("dy", ".35em")
          .style("text-anchor", "end")
          .text(function(d) { return d; });
  });
}

$(document).ready(function() {
  $("h3.phaseoption").click(function(event) {
    markPhaseSelected(event);
    fetchDataAndCreateBarChart();
  });

  fetchDataAndCreateBarChart();
});
