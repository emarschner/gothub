//----------------------------------------------------------------------------
var degree = function(name, type) {
  var nodeIndex = undefined;
  $.each(data.nodes, function(index, node) {
    if (node.nodeName == name) {
      nodeIndex = index;
      return false;
    }
  });
  var degree = $.grep(data.links, function(link, index) {
    if (link[type] == nodeIndex) return true;
    return false;
  }).length;
  return degree;
};

var complement = function(source, target) {
  var results = $.grep(data.links, function(link, index) {
    if (link.source == target && link.target == source) {
      return true;
    }
  });
  var sum = 0;
  if (results.length > 0) {
    $.each(results, function(index, link) {
      sum += link.value;
    });
    //console.log(sum);
    return sum;
  } else {
    //console.log(0);
    return 0;
  }
}

var maxValue = Number.MIN_VALUE;
var minValue = Number.MAX_VALUE;

$.each(data.links, function(index, link) {
  maxValue = Math.max(maxValue, link.value);
  minValue = Math.min(minValue, link.value)
});

var absExtreme = Math.max(Math.abs(maxValue), Math.abs(minValue));

var maxDiff = 0;
$.each(data.links, function(index, link) {
  maxDiff = Math.max(maxDiff, Math.abs(link.value - complement(link.source, link.target)));
});

//----------------------------------------------------------------------------
// METRIC-SPECIFIC STUFF
/* diverging: map within [-1,+1], using 9 colors from red to blue */
var colorDivergent = function(v) {
  if (v < -4.0 / 4) return "#B2182B";
  if (v < -3.0 / 4) return "#D6604D";
  if (v < -2.0 / 4) return "#F4A582";
  if (v < -1.0 / 4) return "#FDDBC7";
  if (v < 1.0 / 4) return "#F7F7F7";
  if (v < 2.0 / 4) return "#D1E5F0";
  if (v < 3.0 / 4) return "#92C5DE";
  if (v < 4.0 / 4) return "#4393C3";
  return "#2166AC";
};

/* sequential: map within [0-, 1+], using 7 shades of blue. */
/*
var colorSequential = function(v) {
  if (v < 1/7) return "#F1EEF6";
  if (v < 2/7) return "#D0D1E6";
  if (v < 3/7) return "#A6BDDB";
  if (v < 4/7) return "#74A9CF";
  if (v < 5/7) return "#3690C0";
  if (v < 6/7) return "#0570B0";
  return "#034E7B";
};
*/
var colorSequential = function(v) {
  if (v < 1/9) return "#FFF7FB";
  if (v < 2/9) return "#ECE7F2";
  if (v < 3/9) return "#D0D1E6";
  if (v < 4/9) return "#A6BDDB";
  if (v < 5/9) return "#74A9CF";
  if (v < 6/9) return "#3690C0";
  if (v < 7/9) return "#0570B0";
  if (v < 8/9) return "#045A8D";
  return "#023858";
};

var maxRange;
var scale;
var scaleToDataRange;
var getLegendText;
var ranges = [];
var color;
var getLegendColor;
var tiny = 0.000001;

if (metric_type == 'seq') {
    maxRange = 9;
    var scaleByMax = function(value, adjust) {
        return value / maxValue * adjust;
    }
    scale = function(value) {
        return scaleByMax(value, scaleFactor)
    }
    scaleToDataRange = function(i) {
        return i / maxRange / scaleFactor * maxValue;
    };
    getLegendText = function(i) {
        value = scaleToDataRange(i).toFixed(1);
        valuePlusOne = scaleToDataRange(i + 1).toFixed(1);
        if (i == 0) {return "<\t" + valuePlusOne};
        if (i == maxRange - 1) {return ">\t" + value};
        return "[\t" + value + ",\t" + valuePlusOne + "\t)";
    };
    for (i = 0; i < maxRange; i++) {
        ranges[i] = scaleToDataRange(i);
    }
    color = colorSequential;
    getLegendColor = function(i) {
        color_map = {
            0: color(1/9 - tiny),
            1: color(2/9 - tiny),
            2: color(3/9 - tiny),
            3: color(4/9 - tiny),
            4: color(5/9 - tiny),
            5: color(6/9 - tiny),
            6: color(7/9 - tiny),
            7: color(8/9 - tiny),
            8: color(1 - tiny),
        }
        return color_map[i];
    }
} else {
    maxRange = 4;
    var scaleByAbsExtreme = function(value, adjust) {
        return value / absExtreme * adjust;
    }
    scale = function(value) {
        return scaleByAbsExtreme(value, scaleFactor)
    }
    scaleToDataRange = function(i) {
        return (i - maxRange) / maxRange / scaleFactor * absExtreme;
    };
    getLegendText = function(i) {
        // Ugly as sin, but at least it gets this working.
        value = scaleToDataRange(i).toFixed(1);
        valueMinusOne = scaleToDataRange(i - 1).toFixed(1);
        valuePlusOne = scaleToDataRange(i + 1).toFixed(1);
        if (i == 0) {return "<\t" + value}
        else if (i == maxRange) {return "[\t" + valueMinusOne + ",\t" + valuePlusOne + "\t)"}
        else if (i == maxRange * 2) {return ">\t" + value}
        else if (i < maxRange) {return "[\t" + valueMinusOne + ",\t" + value + "\t)"}
        else {return "[\t" + value + ",\t" + valuePlusOne + "\t)"}
    };
    for (i = 0; i < maxRange * 2 + 1; i++) {
        ranges[i] = scaleToDataRange(i);
    }
    color = colorDivergent;
    getLegendColor = function(i) {
        color_map = {
            0: color(-1.0 - tiny),
            1: color(-3.0 / 4.0 - tiny),
            2: color(-2.0 / 4.0 - tiny),
            3: color(-1.0 / 4.0 - tiny),
            4: color(-0.0 / 4.0 - tiny),
            5: color(1.0 / 4.0 + tiny),
            6: color(2.0 / 4.0 + tiny),
            7: color(3.0 / 4.0 + tiny),
            8: color(4.0 / 4.0 + tiny),
        }
        return color_map[i];
    }
}

//----------------------------------------------------------------------------
// PROTOVIS DISPLAY
var gap = 15; // separates top and bottom panels

var main = new pv.Panel().canvas('fig')
    .width(550)
    .height(430);

var topPanel = main.add(pv.Panel)
    .width(275)
    .height(275)
    .top(140)
    .left(140);

/* Main Matrix display */
var layout = topPanel.add(pv.Layout.Matrix)
    .directed(true)
    .nodes(data.nodes)
    .links(data.links);

layout.link.add(pv.Bar)
  .fillStyle(function(l) { /*console.log(l);*/ return color(scale(l.linkValue)); })
  /* for asym matrix: */
  //.fillStyle(function(l) { /*console.log(l);*/ return color(l.linkValue / 2); })
    .antialias(false)
    .lineWidth(2);

layout.label.add(pv.Label)
    //.font("12px sans-serif")
    .textStyle('black');

/* Legend */
var bottomPanel = main.add(pv.Panel)
    .width(200)
    .height(200)
    .left(430 + gap)
    .top(180);

var legend = bottomPanel.add(pv.Dot)
    .data(function() {return ranges})
    .left(0)
    .top(function() {return 0 + this.index * 15})
    .size(15)
    .strokeStyle(null)
    .fillStyle(function(d) {return getLegendColor(this.index)})
  .anchor("right").add(pv.Label)
    .left(15)
    //.font("10px sans-serif")
    .textStyle('black')
    .text(function(d) {return getLegendText(this.index)})

main.render();
