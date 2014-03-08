'use strict';

// This lets use use d3.scale.time for a nice time interval scale.
function secondsToRefDate(secs) {
  return new Date(2012, 0, 1, 0, 0, secs);
}

function findSelectedPhases() {
  return $.makeArray($('.phaseoption')
      .filter(':checked')
      .map(function(i, el) { return $(el).attr("id"); }))
      .join(",");
}

// For an array d sorted in ascending order, return [q1, median, q3]
function boxQuartiles(d) {
  return [
    d3.quantile(d, 0.25),
    d3.quantile(d, 0.50),
    d3.quantile(d, 0.75)
  ];
}

// Returns a function to compute the indices of values just inside
// k times the interquartile range (above, below) the (q3, q1) value
// (to be used as whiskers in a box plot)
function boxWhiskers(d) {
  var q1 = d3.quantile(d, 0.25),
      q3 = d3.quantile(d, 0.75),
      k = 1.5,
      iqr = (q3 - q1) * k,
      i = -1,
      j = d.length;
  while (d[++i] < q1 - iqr);
  while (d[--j] > q3 + iqr);
  return [i, j];
}

function fetchDataAndCreateBoxPlot() {
  var urlString = "/perfdash/data";
  d3.tsv(urlString, function(error, data) {
    /******************
     * Data preparation
     ******************/
    // TODO(hammer): sort by median in descending order
    var stepTimes = {};
    data.filter(function(x) { return x.step != "sample name"; }).forEach(function(d) {
      stepTimes[d["step"]] = d3.values(d).map(parseFloat)
                                         .filter(function(x) { return !isNaN(x); })
                                         .sort(d3.ascending);
    });
    var stepEntries = d3.entries(stepTimes);
    var maxTime = d3.max([].concat.apply([], d3.values(stepTimes)));

    /*****
     * SVG
     *****/
    var p_t = 20;
    var p_b = 50;
    var p_l = 50;
    var p_r = 50;
    var p_box_l = 25;
    var p_box_r = 25;
    var box_width = 20;
    var num_boxes = d3.entries(stepTimes).length;

    var box_x_l = function(i) {
      return p_l + (i + 1) * (p_box_l + box_width + p_box_r) - p_box_r;
    }
    var box_x_m = function(i) { return box_x_l(i) + box_width / 2; };
    var box_x_r = function(i) { return box_x_l(i) + box_width; };

    var h = 500 - p_t - p_b;
    var w = (num_boxes + 1) * (p_box_l + box_width + p_box_r);

    var vis = d3.select("div#box")
                .append("svg")
                .attr("width", w + p_l + p_r)
                .attr("height", h + p_t + p_b)
                .append("g")
                .attr("class", "boxplot_content")
                .attr("transform", "translate(" + p_l + "," + p_t + ")");

    /********
     * Y Rule
     ********/
    // TODO(hammer): use a time scale
    var y = d3.scale.linear()
                    .domain([0, maxTime])
                    .range([0, h]);

    var yrule = vis.selectAll("g.y")
                   .data(y.ticks(5))
                   .enter()
                   .append("g")
                   .attr("class", "y");

    yrule.append("line")
         .attr("x1", p_l + 5)
         .attr("x2", w)
         .attr("y1", function(d) { return h - y(d); })
         .attr("y2", function(d) { return h - y(d); });

    yrule.append("text")
         .attr("x", p_l)
         .attr("y", function(d) { return h - y(d); })
         .attr("dy", "0.5ex")
         .attr("text-anchor", "end")
         .text(y.tickFormat(5, "s"));

    /********
     * X Axis
     ********/
    var xrule = vis.selectAll("g.x")
                   .data(d3.keys(stepTimes))
                   .enter()
                   .append("g")
                   .attr("class", "x");

    xrule.append("line")
         .attr("x1", function(d, i) { return box_x_m(i); })
         .attr("x2", function(d, i) { return box_x_m(i); })
         .attr("y1", h)
         .attr("y2", h + 4);

    xrule.append("text")
         .attr("x", function(d, i) { return box_x_m(i); })
         .attr("y", function(d, i) { return h + 5 + 15 * (i % 2); })
         .attr("dy", ".71em")
         .attr("text-anchor", "middle")
         .text(String);

    /**********
     * Box Plot
     **********/
    for (var i = 0; i < num_boxes; i++) {
      var stepName = stepEntries[i].key;
      var times = stepEntries[i].value;
      var quartiles = boxQuartiles(times);
      var whisker_indices = boxWhiskers(times);

      var box = vis.append("g").attr("class", "box_" + i);

      // draw the box representing the IQR
      box.append("rect")
         .attr("class", "iqr_" + i)
         .attr("x", box_x_l(i))
         .attr("y", h - y(quartiles[2]))
         .attr("width", box_width)
         .attr("height", y(quartiles[2] - quartiles[0]));

      // draw the median
      box.append("line")
         .attr("class", "median_" + i)
         .attr("x1", box_x_l(i))
         .attr("x2", box_x_r(i))
         .attr("y1", h - y(quartiles[1]))
         .attr("y2", h-y(quartiles[1]));

      // draw the whiskers
      // NB: quartiles[i*2] is a little bit of trickery
      //     to get q1 for the lower whisker and q3 for the upper whisker
      box.selectAll(".whiskers_" + i + " line")
         .data(whisker_indices)
         .enter()
         .append("line")
         .attr("class", "whiskers_" + i)
         .attr("x1", box_x_m(i))
         .attr("x2", box_x_m(i))
         .attr("y1", function(d, i) { return h - y(quartiles[i * 2]); })
         .attr("y2", function(d) { return h - y(times[d]); });

      // TODO(hammer): fix the hover text by adding a class per box
      // draw the outliers
      box.selectAll(".outliers_" + i + " circle")
         .data(times.filter(function(d, i) {
           return i < boxWhiskers(times)[0] || i > boxWhiskers(times)[1];
         }))
         .enter()
         .append("circle")
         .attr("class", "outliers_" + i)
         .attr("cx", box_x_m(i))
         .attr("cy", function(d) { return h - y(d); })
         .attr("r", 2)
         .on("mouseover", function(d) {
           d3.select("div#box g.boxplot_content")
             .append("text")
             .attr("id", "tip")
             .attr("x", this.cx.baseVal.value + 5)
             .attr("y", h - y(d))
             .attr("text-anchor", "start")
             .attr("font-size", "8")
             .text(d3.format(",")(d));
           d3.select(this).attr("fill", "red");
         })
         .on("mouseout", function() {
           d3.select("div#box g.boxplot_content #tip").remove();
           d3.select(this).attr("fill", "black");
         });
    }
  });
}

function fetchDataAndCreateBarChart() {
  // Configuration
  var phases = findSelectedPhases();
  var color = d3.scale.category10();
  var shouldSort = $('#sort').is(':checked');
  var urlString = "/perfdash/data";

  if (phases != "") {
     urlString = urlString + "?requested_steps=" + phases;
  }
  d3.tsv(urlString, function(error, data) {
    /******************
     * Data preparation
     ******************/
    var seriesNames = d3.keys(data[0]).filter(function(key) {
      return key !== "step";
    });

    var stepNames = data
        .map(function(d) { return d.step })
        .filter(function(x) { return x !== 'sample name' });
    color.domain(stepNames);

    var sampleNames = data.shift();  // remove "sample name" row.
    data.forEach(function(d, i) {
      d.stepTimes = seriesNames.map(function(name) { return {name: name, value: +d[name]}; });
    });

    // Rotate the data so that it's run-major, step-minor.
    var seriesMap = {};
    seriesNames.forEach(function(name) {
      seriesMap[name] = {steps: [], sum: 0.0, label: ''};
    });
    data.forEach(function(d) {
      d.stepTimes.forEach(function(pt) {
        var s = seriesMap[pt.name];
        s.steps.push({step: d.step, value: pt.value, x0: s.sum});
        s.sum += pt.value;
      });
    });
    seriesNames.forEach(function(name) {
      seriesMap[name].label = sampleNames[name];
    });

    if (shouldSort) {
      seriesNames.sort(function(a, b) {
        return seriesMap[b].sum - seriesMap[a].sum;
      });
    }

    var series = seriesNames.map(function(seriesName) {
      var entry = seriesMap[seriesName];
      return {
        steps: entry.steps,
        sum: entry.sum,
        name: seriesName,
        label: entry.label
      }
    });

    /*****
     * SVG
     *****/
    var margin = {top: 20, right: 20, bottom: 30, left: 200};
    var width = 1280 - margin.left - margin.right;
    var height = 500 - margin.top - margin.bottom;

    d3.select("#chart").select("svg").remove();
    var svg = d3.select("#chart").append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    /********
     * X axis
     ********/
    var x = d3.time.scale().range([0, width * 0.8]);
    var xAxis = d3.svg.axis()
                      .scale(x)
                      .orient("bottom")
                      .tickFormat(d3.time.format("%H:%M"))
                      .tickSize(-height, 1);
    var nx = function(secs) { return x(secondsToRefDate(secs)) };
    x.domain([secondsToRefDate(0),
              secondsToRefDate(d3.max(series.map(function(s) { return s.sum; })))]);
    svg.append("g")
       .attr("class", "x axis")
       .attr("transform", "translate(0," + height + ")")
       .call(xAxis)
       .append("text")
       .text("Time (hours, minutes)")
       .attr("y", "28");

    /********
     * Y axis
     ********/
    var y = d3.scale.ordinal().rangeRoundBands([0, height], .1);
    var yAxis = d3.svg.axis().scale(y).orient("left");
    y.domain(seriesNames);
    svg.append("g")
       .attr("class", "y axis")
       .call(yAxis);

    /***********
     * Bar Chart
     ***********/
    var seriesG = svg.selectAll(".series")
                    .data(series, function(s) { return s.name })
                    .enter().append("g")
                    .attr("class", "series")
                    .attr("transform", function(d) { return "translate(0," + y(d.name) + ")"; });

    seriesG.selectAll("rect")
         .data(function(s) { return s.steps })
         .enter()
         .append("rect")
         .attr("height", y.rangeBand())
         .attr("x", function(pt) { return nx(pt.x0); })
         .attr("width", function(pt) { return nx(pt.x0 + pt.value) - nx(pt.x0) })
         .style("fill", function(pt) { return color(pt.step); });

    /********
     * Legend
     ********/
    var legend = svg.selectAll(".legend")
                    .data(stepNames.slice())
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
  $(".phaseoption").click(function(event) {
    fetchDataAndCreateBarChart();
  });
  $("#All").click(function() {
    $('.phaseoption').attr('checked', true);
    fetchDataAndCreateBarChart();
  });
  $('#sort').click(function() {
    fetchDataAndCreateBarChart();
  });

  fetchDataAndCreateBarChart();
  fetchDataAndCreateBoxPlot();
});
