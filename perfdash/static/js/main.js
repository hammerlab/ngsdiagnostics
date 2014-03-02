'use strict';

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

var y = d3.scale.ordinal()
                .rangeRoundBands([0, height], .1);

var x = d3.scale.linear()
                .range([0, width]);

var color = d3.scale.ordinal()
                    .range(["#98abc5", "#8a89a6", "#7b6888", "#6b486b",
                            "#a05d56", "#d0743c", "#ff8c00"]);

var xAxis = d3.svg.axis()
                  .scale(x)
                  .orient("bottom")
                  .tickFormat(d3.format(".2s"));

var yAxis = d3.svg.axis()
                  .scale(y)
                  .orient("left");

function findSelectedPhases() {
  return jQuery.makeArray($(".phaseselected").map(function (i, val) { return val.innerText; }))
               .join(",")
}

function fetchDataAndCreateBarChart() {
  var phases = findSelectedPhases();
  var url_string = "/perfdash/data";
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
    color.domain(otherColumns);

    data.forEach(function(d) {
      d.stepTimes = otherColumns.map(function(name) { return {name: name, value: +d[name]}; });
    });

    // Rotate the data so that it's run-major, step-minor.
    var seriesMap = {};
    otherColumns.forEach(function(name) {
      seriesMap[name] = {steps: [], sum: 0.0};
    });
    data.forEach(function(d) {
      d.stepTimes.forEach(function(pt) {
        var s = seriesMap[pt.name];
        s.steps.push({step: d.step, value: pt.value, x0: s.sum});
        s.sum += pt.value;
      });
    });

    var series = d3.keys(seriesMap).map(function(seriesName) {
      var entry = seriesMap[seriesName];
      return {
        steps: entry.steps,
        sum: entry.sum,
        name: seriesName
      }
    });

    y.domain(d3.keys(seriesMap).sort());
    x.domain([0, d3.max(series.map(function(s) { return s.sum; }))]);

    svg.append("g")
       .attr("class", "x axis")
       .attr("transform", "translate(0," + height + ")")
       .call(xAxis)
       .append("text")
       .text("Time (s)");

    svg.append("g")
       .attr("class", "y axis")
       .call(yAxis);

    var series = svg.selectAll(".series")
                    .data(series)
                    .enter().append("g")
                    .attr("class", "g")
                    .attr("transform", function(d) { return "translate(0," + y(d.name) + ")"; });

    series.selectAll("rect")
         .data(function(s) { return s.steps })
         .enter()
         .append("rect")
         .attr("height", y.rangeBand())
         .attr("x", function(pt) { return x(pt.x0); })
         .attr("width", function(pt) { return x(pt.x0 + pt.value) })
         .style("fill", function(pt) { return color(pt.step); });

    /*
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
    */
  });
}

$(document).ready(function() {
  $("h3.phaseoption").click(function(event) {
    markPhaseSelected(event);
    fetchDataAndCreateBarChart();
  });

  fetchDataAndCreateBarChart();
});
