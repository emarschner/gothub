function formatCurrency(num) {
  num = num.toString().replace(/\$|\,/g,'');
  if(isNaN(num))
    num = "0";
  sign = (num == (num = Math.abs(num)));
  num = Math.floor(num*100+0.50000000001);
  num = Math.floor(num/100).toString();
  for (var i = 0; i < Math.floor((num.length-(1+i))/3); i++)
    num = num.substring(0,num.length-(4*i+3))+','+num.substring(num.length-(4*i+3));
  return (((sign)?'':'-') + '$' + num);
}

var state_dict = {'01':'Alabama', '02':'Alaska', '04':'Arizona', '05':'Arkansas', '06':'California', '08':'Colorado', '09':'Connecticut', '10':'Delaware', '12':'Florida', '13':'Georgia', '15':'Hawaii', '16':'Idaho', '17':'Illinois', '18':'Indiana', '19':'Iowa', '20':'Kansas', '21':'Kentucky', '22':'Louisiana', '23':'Maine', '24':'Maryland', '25':'Massachusetts', '26':'Michigan', '27':'Minnesota', '28':'Mississippi', '29':'Missouri', '30':'Montana', '31':'Nebraska', '32':'Nevada', '33':'New Hampshire', '34':'New Jersey', '35':'New Mexico', '36':'New York', '37':'North Carolina', '38':'North Dakota', '39':'Ohio', '40':'Oklahoma', '41':'Oregon', '42':'Pennsylvania', '44':'Rhode Island', '45':'South Carolina', '46':'South Dakota', '47':'Tennessee', '48':'Texas', '49':'Utah', '50':'Vermont', '51':'Virginia', '53':'Washington', '54':'West Virginia', '55':'Wisconsin', '56':'Wyoming', '72':'Puerto Rico'};
var latest_data = {};
String.prototype.capitalize = function(){
   return this.replace( /(^|\s)([a-z])/g , function(m,p1,p2){ return p1+p2.toUpperCase(); } );
  };

var po = org.polymaps;

var map = po.map()
    .container(document.getElementById("map").appendChild(po.svg("svg")))
    .center({lat: 39, lon: -96})
    .zoom(4)
    .zoomRange([3.51, 4.49])
    .add(po.interact());

map.add(po.image()
	.url(po.url("http://{S}tile.cloudmade.com"
    + "/1a1b06b230af4efdbb989ea99e9841af" // http://cloudmade.com/register
    + "/998/256/{Z}/{X}/{Y}.png")
    .hosts(["a.", "b.", "c.", ""])));

map.add(po.geoJson()
    .url("http://polymaps.appspot.com/county/{Z}/{X}/{Y}.json")
    .on("load", load)
    .id("county"));


map.add(po.geoJson()
    .url("http://polymaps.appspot.com/state/{Z}/{X}/{Y}.json")
    .on("load", loadState)
    .id("state"));
    

var metricType = '';
var counter = 0;
var fillColors = new Array();
var metricArray = new Array();

$('#about_link').click(function() {
  $('#about_popup').show();
});

$('#about_popup').click(function() {
  $('#about_popup').hide();
});

var revealSpotlight = function() {
  $('#filter_bottom_title').html('Top Lenders');
  $('#spotlight_body1').show();
}

function loadState(e) {
  for (var i = 0; i < e.features.length; i++) {
	var feature = e.features[i];
	var tempid = "state" + feature.data.id.substr(6);
	feature.element.setAttribute("class", "stateClass " + tempid);
	feature.element.setAttribute("stateid", tempid);
	
	counter++;
	feature.element.setAttribute("id", "state" + counter);
	if(typeof fillColors[tempid] == 'undefined') {
	  fillColors[tempid] = 'none';
	}
	if(fillColors[tempid] != 'none') {
	  if(typeof metricArray[tempid] == 'undefined') {
	    metricArray[tempid] = 'N/A';
      }
	  feature.element.setAttribute("style", "fill: " + fillColors[tempid]);
      $('#state' + counter).attr('oldcolor', fillColors[tempid]);
      $('#state' + counter).attr('metric', metricArray[tempid]);
	  $('#state' + counter).click(function() {
	    alert('click');
		$('#tooltip').html('CLICKED!');
	  });
	  $('#state' + counter).mouseover(function() {
		var userFriendlyMetric = 'Rate Spread';
		var metricAmount = $(this).attr('metric');
		if(metricType == 'rate_spread') { metricAmount += '%'; }
		else if(metricType == 'income') { userFriendlyMetric = 'Income'; metricAmount *= 1000; metricAmount = formatCurrency(metricAmount); }
		else if(metricType == 'loan_amount') { userFriendlyMetric = 'Loan Amount'; metricAmount *= 1000; metricAmount = formatCurrency(metricAmount); }
		$('#tooltip').html(state_dict[$(this).attr('stateid').substr(-2)] + ' - ' + userFriendlyMetric + ': ' + metricAmount);
		$('.' + $(this).attr('stateid')).css('fill', '#fff');
	  });
	  $('#state' + counter).mouseleave(function() {
		var oldcolor = $(this).attr('oldcolor');
		$('.' + $(this).attr('stateid')).css('fill', oldcolor);
	  });
	}
  }
}

function load(e) {
  for (var i = 0; i < e.features.length; i++) {
	var feature = e.features[i];
	var tempid = "county" + feature.data.id.substr(7);
	feature.element.setAttribute("class", "countyClass " + tempid);
	feature.element.setAttribute("countyid", tempid);
	if(typeof fillColors[tempid] == 'undefined') {
	  fillColors[tempid] = '#555';
	}
	feature.element.setAttribute("style", "fill: " + fillColors[tempid]);
	if(typeof metricArray[tempid] == 'undefined') {
	  metricArray[tempid] = 'N/A';
	}
	
	counter++;
	feature.element.setAttribute("id", "county" + counter);
	$('#county' + counter).attr('oldcolor', fillColors[tempid]);
	$('#county' + counter).attr('metric', metricArray[tempid]);
    $('#county' + counter).click(function() {
        revealSpotlight();
	    var id = $(this).attr('countyid').substr(-5);
	    $('#region_name').html(state_dict[$(this).attr('countyid').substr(6,2)] + ", county " + $(this).attr('countyid').substr(-3));
	    $('#summary').html('<img src="loading.gif" />');
	    $('#amount').html('');
	    $('#num_homes').html('');
		$.ajax({
		        url: 'http://204.232.210.102:5011/query/lar',
		        data: {fields:"state,income", state:id.substr(0,2), county:id.substr(2)},
		        dataType: "jsonp",
		        success: function(data, status){
					latest_data = data;
					var aggregates = aggregateData(data);
				}
		});
    })
    .mouseover(function() {
      var userFriendlyMetric = 'Rate Spread';
      var metricAmount = $(this).attr('metric');
      if(metricType == 'rate_spread') { metricAmount += '%'; }
      else if(metricType == 'income') { userFriendlyMetric = 'Income'; metricAmount *= 1000; metricAmount = formatCurrency(metricAmount); }
      else if(metricType == 'loan_amount') { userFriendlyMetric = 'Loan Amount'; metricAmount *= 1000; metricAmount = formatCurrency(metricAmount); }
	  $('.tipHeader').text(state_dict[$(this).attr('countyid').substr(6,2)] + ", county " + $(this).attr('countyid').substr(-3));
      $('.tipBody').text(userFriendlyMetric + ': ' + metricAmount);
      //Set the X and Y axis of the tooltip  
      $('#tooltip').css('top', e.pageY + 10 );  
      $('#tooltip').css('left', e.pageX + 20 );  

	  $('#tooltip').show();
	  $('.' + $(this).attr('countyid')).css('fill', '#fff');
    })
    .mouseleave(function() {
      var oldcolor = $(this).attr('oldcolor');
      $('.' + $(this).attr('countyid')).css('fill', oldcolor);
	  $('#tooltip').hide();
    })
	.mousemove(function(e) {  
        $('#tooltip').css('top', e.pageY + 10 );  
        $('#tooltip').css('left', e.pageX + 20 );  
  	});
  }
}

function loadHandlers() {

}

var aggregateData = function(arr,func)
{
	var agg = {"income": {}, "loan_amount" : {}, "sex" : {}, "respondent_name" : {}, "rate_spread" : {}};
	var num_homes = 0;
	$.each(arr, function(index, obj) {
		var val;
		if (!func || (func && func(obj)))
		{
			num_homes++;
		for (prop in obj)
		{
			if (typeof obj[prop] != 'undefined')
			{
				switch (prop)
				{
					case "rate_spread":
						val = Math.floor(parseFloat(obj[prop]));
						agg[prop][val] = (typeof agg[prop][val] == 'undefined') ? 1 : agg[prop][val]+1;
						break;
					case "loan_amount":
					case "income":
						val = parseInt(obj[prop])
						agg[prop]["max"] = (typeof agg[prop]["max"] == 'undefined') ? val : Math.max(val, agg[prop]["max"]);
						if (val != -1)
							agg[prop]["min"] = (typeof agg[prop]["min"] == 'undefined') ? val : Math.min(val, agg[prop]["min"]);
						break;
					case "sex": 
						val = parseInt(obj[prop]);
						agg[prop][val] = (typeof agg[prop][val] == 'undefined') ? 1 : agg[prop][val]+1;
						break;
					case "respondent_name":
						if (obj[prop] != "-1")
							agg[prop][obj[prop]] = (typeof agg[prop][obj[prop]] == 'undefined') ? 1 : agg[prop][obj[prop]]+1;
						break;
					default:
						break;
				}
			}
		}
		}
	});
	if (!func)
	{
	    /*
		$("#slider-range").slider({
		min: agg["income"]["min"],
		max: agg["income"]["max"],
		values: [agg["income"]["min"], agg["income"]["max"]],
		});
		*/
		$('#range_min').val(agg["income"]["min"] * 1000);
		$('#range_max').val(agg["income"]["max"] * 1000);
		$("#amount").text('Range: ' + formatCurrency(agg["income"]["min"]*1000) + ' - ' + formatCurrency(agg["income"]["max"]*1000));
	}
	$("#num_homes").text(num_homes + " homes");
	var respondents = agg['respondent_name'];
	// Hack to sort associative array
	var sortedArr = [];
	for (name in respondents)
	{
		sortedArr.push([respondents[name], name]);
	}
	sortedArr.sort(function(a,b){
		return b[0] - a[0];
	});
	var $el = $('<ol></ol>');
	for (var i = 0; i < Math.min(sortedArr.length, 6); i++)
	{
		$el.append($('<li>'+sortedArr[i][1].toLowerCase().capitalize() + ' (' + sortedArr[i][0] + ')</li>'));
	}
	$('#summary').children().remove();
	$('#summary').append($el);
	$('#summary').show();
	return agg;
}

setTimeout("loadHandlers()", 3500);
setTimeout("$('#loading').hide()", 3500);

var newdata;

	
var buildQuery = function(arr)
{
	var query = {};
	var group_by = ['state'];
	var fields = ['state', 'avg('+arr['metric']+')'];
	if (arr['geo'] == 'county')
	{
		fields.push('county');
		group_by.push('county');
	}
	query = {fields: fields.join(','), group_by: group_by.join(',')};
	return query;
	
};
var formChangeFunction = function() {
	//alert('awef');
	$('#loading').show();
	var arr = {};
	$.each($("#filter_form").serializeArray(), function(index, data) {
		arr[data.name] = data.value;
	});
	$.ajax({
			url: 'http://204.232.210.102:5011/query/lar',
			data: buildQuery(arr),
			dataType: "jsonp",
			success: function(data, status){
				aggregates = aggregateData(data);
				newdata = data;
				var k = 0;
				if(typeof newdata[0].rate_spread != 'undefined') {
				  metricType = 'rate_spread';
				}
				else if(typeof newdata[0].income != 'undefined') {
				  metricType = 'income';
				}
				else if(typeof newdata[0].loan_amount != 'undefined') {
				  metricType = 'loan_amount';
				}
				var min = 3.5;
				var interval = 0.5;
				if(metricType == 'rate_spread') {
				  min = 3.5;
				  interval = 0.5;
				  $('#legend_name1').html('0 - 3.5%');
				  $('#legend_name2').html('3.5 - 4.0%');
				  $('#legend_name3').html('4.0 - 4.5%');
				  $('#legend_name4').html('4.5 - 5.0%');
				  $('#legend_name5').html('5.0 - 5.5%');
				  $('#legend_name6').html('>5.5%');
				}
				else if(metricType == 'income') {
				  min = 60;
				  interval = 10;
				  $('#legend_name1').html('$0 - 60,000');
				  $('#legend_name2').html('$60,000 - 69,999');
				  $('#legend_name3').html('$70,000 - 79,999');
				  $('#legend_name4').html('$80,000 - 89,999');
				  $('#legend_name5').html('$90,000 - 99,999');
				  $('#legend_name6').html('>$100,000');
				}
				else if(metricType == 'loan_amount') {
				  min = 50;
				  interval = 20;
				  $('#legend_name1').html('$0 - 49,999');
				  $('#legend_name2').html('$50,000 - 69,999');
				  $('#legend_name3').html('$70,000 - 89,999');
				  $('#legend_name4').html('$90,000 - 109,999');
				  $('#legend_name5').html('$110,000 - 129,999');
				  $('#legend_name6').html('>$130,000');
				}
				var isCounty = false;
				if(typeof newdata[0].county != 'undefined') {
				  isCounty = true;
				}
				if(isCounty) {
				  $('.stateClass').unbind('click');
				  $('.stateClass').unbind('mouseover');
				  $('.stateClass').unbind('mouseleave');
				  $('.stateClass').css('fill', 'none');
				  $('.stateClass').attr('oldcolor', 'none');
				  for(i = 0; i < 100; i++) {
					if(i < 10) {
					  fillColors['state0' + i] = 'none';
					}
					else {
					  fillColors['state' + i] = 'none';
					}
				  }
				}
				else {
				  $('.stateClass').click(function() {
					revealSpotlight();
					var id = $(this).attr('stateid').substr(-2);
					//$('#spotlight_title').html('Spotlight: ' + state_dict[$(this).attr('stateid').substr(-2)]);
					$('#region_name').html(state_dict[$(this).attr('stateid').substr(-2)]);
					$('.range_input').val('');
					$('#summary').html('<img src="loading.gif" />');
					$('#amount').html('');
					$('#num_homes').html('');
					$.ajax({
							url: 'http://204.232.210.102:5011/query/lar',
							data: {fields:"state,income", state:id},
							dataType: "jsonp",
							success: function(data, status){
								latest_data = data;
								var aggregates = aggregateData(data);
							}
					});
				  })
				  .mouseover(function(e) {
					var userFriendlyMetric = 'Rate Spread';
					var metricAmount = $(this).attr('metric');
					if(metricType == 'rate_spread') { metricAmount += '%'; }
					else if(metricType == 'income') { userFriendlyMetric = 'Income'; metricAmount *= 1000; metricAmount = formatCurrency(metricAmount); }
					else if(metricType == 'loan_amount') { userFriendlyMetric = 'Loan Amount'; metricAmount *= 1000; metricAmount = formatCurrency(metricAmount); }
					$('.tipHeader').text(state_dict[$(this).attr('stateid').substr(-2)]);
					$('.tipBody').text(userFriendlyMetric + ': ' + metricAmount);
					//Set the X and Y axis of the tooltip  
					$('#tooltip').css('top', e.pageY + 10 );  
					$('#tooltip').css('left', e.pageX + 20 );  

					$('#tooltip').show();
					  
					$('.' + $(this).attr('stateid')).css('fill', '#fff');
				  })
				  .mouseleave(function() {
					var oldcolor = $(this).attr('oldcolor');
					$('.' + $(this).attr('stateid')).css('fill', oldcolor);
					$('#tooltip').hide();
				  })
				  .mousemove(function(e) {  
						$('#tooltip').css('top', e.pageY + 10 );  
						$('#tooltip').css('left', e.pageX + 20 );  

				  });
				}
				for(k = 0; k < newdata.length; k++) {
				  if(((isCounty && newdata[k].county != "-1") || !isCounty) && newdata[k].state != "-1") {
					var idname = '';
					if(isCounty) {
					  idname = "county" + newdata[k].state + newdata[k].county;
					}
					else {
					  idname = "state" + newdata[k].state;
					}
					var metric;
					
					if(metricType == 'rate_spread') {
					  metric = newdata[k].rate_spread;
					}
					else if(metricType == 'income') {
					  metric = newdata[k].income;
					}
					else if(metricType == 'loan_amount') {
					  metric = newdata[k].loan_amount;
					}
					
					$('.' + idname).attr('metric', metric); 
					
					var fillval = '#005';
					if(metric < min) {
					  fillval = '#005';
					}
					else if(metric < min + interval) {
					  fillval = '#027';
					}
					else if(metric < min + 2*interval) {
					  fillval = '#049';
					}
					else if(metric < min + 3*interval) {
					  fillval = '#16a';
					}
					else if(metric < min + 4*interval) {
					  fillval = '#37d';
					}
					else {
					  fillval = '#58f';
					}
					$('.' + idname).css('fill', fillval);
					$('.' + idname).attr('oldcolor', fillval);
					fillColors[idname] = fillval;
					metricArray[idname] = metric;
				  }
				}
				$('#loading').hide();
			}
		});
	return false;
};

setTimeout("formChangeFunction()", 3501);

$(function(){
	/*
	$("#slider-range").slider({
		range: true,
		min: 0,
		max: 500,
		values: [75, 300],
		slide: function(event, ui) {
			$("#amount").text('Range: ' + formatCurrency(ui.values[0]*1000) + ' - ' + formatCurrency(ui.values[1]*1000));
		}
	});
	$( "#slider-range" ).bind( "slidestop", function(event, ui) {
	  var values = $(this).slider("option", "values");
	  var func = function(obj) { 
		var val = parseInt(obj['income']);
		return (values[0] <= val && val <= values[1]);
	  };
	  var newData = aggregateData(latest_data, func);
	});
	*/
	$(".range_input").change(function() {
	  valMin = $('#range_min').val();
	  valMax = $('#range_max').val();
	  $("#amount").text('Range: ' + formatCurrency(valMin) + ' - ' + formatCurrency(valMax));
	  var func = function(obj) { 
		var val = parseInt(obj['income']);
		return (valMin / 1000 <= val && val <= valMax / 1000);
	  };
	  var newData = aggregateData(latest_data, func);
	});

	
	$("#filter_form input").change(formChangeFunction);
});
