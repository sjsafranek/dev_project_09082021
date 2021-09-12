
// It has been a little while since I played with D3.
// One of these days I will need to start using a later version.

/*

    PieChart class to display 'status' values within selection.

    I am hoping this will qualify for item 1 in the feature requirements:

        A set of 37 status values (fail, warn, pass) to be displayed in a single page.
        This is a page that is meant to show the status values "at a glance".

*/

var PieChart = function(handlers) {
    let self = this;

    this.handlers = handlers;

    // We can make most of these items 'private' attributes.
    let svg = d3.select("svg#chart")
        .append("g");

    svg.append("g")
        .attr("class", "slices");

    svg.append("g")
        .attr("class", "labels");

    svg.append("g")
        .attr("class", "lines");

    let width = 960/2,
        height = 450/2,
    	radius = Math.min(width, height) / 2;

    let pie = d3.layout.pie()
    	.sort(null)
    	.value(function(d) {
    		return d.value;
    	});

    let arc = d3.svg.arc()
    	.outerRadius(radius * 0.8)
    	.innerRadius(radius * 0.4);

    let outerArc = d3.svg.arc()
    	.innerRadius(radius * 0.9)
    	.outerRadius(radius * 0.9);

    svg.attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

    let key = function(d){ return d.data.label; };
    let colorScale = d3.scale.category10();

    // Function to update chart. D3 will trigger css transitions
    // to nicely animate the chart during the update.
    this.update = function(raw) {

        // Reformat data
        let values = d3.set(raw).values();

        let color = d3.scale.ordinal()
        	.domain(values)
            .range(values.map(function(d,i) {
                return colorScale(i);
            }));

        function formatData (){
        	let labels = color.domain();
        	return values.map(function(label){
        		return {
                    label: label,
                    value: raw.filter(function(d) {
                        return label == d;
                    }).length
                }
        	});
        }

        let data = formatData(raw);


    	// Build the pie chart slices
    	let slice = svg.select(".slices").selectAll("path.slice")
            .data(pie(data), key);

    	slice.enter()
    		.insert("path")
    		.style("fill", function(d) { return color(d.data.label); })
    		.attr("class", "slice")
            .on('click', function(d) {
                self.handlers.click && self.handlers.click(d.data.label);
            })
            .on('contextmenu', function(d) {
                d3.event.preventDefault();
                self.handlers.contextmenu && self.handlers.contextmenu(d.data.label);
            });

    	slice.transition().duration(1000)
    		.attrTween("d", function(d) {
    			this._current = this._current || d;
    			var interpolate = d3.interpolate(this._current, d);
    			this._current = interpolate(0);
    			return function(t) {
    				return arc(interpolate(t));
    			};
    		})

    	slice.exit().remove();


    	// Add labels for 'status' values
    	let text = svg.select(".labels").selectAll("text")
            .data(pie(data), key);

    	text.enter()
    		.append("text")
    		.attr("dy", ".35em")
    		.text(function(d) {
                return `${d.data.value} ${d.data.label}`;
    		});

    	function midAngle(d){
    		return d.startAngle + (d.endAngle - d.startAngle)/2;
    	}

    	text.transition().duration(1000)
    		.attrTween("transform", function(d) {
    			this._current = this._current || d;
    			var interpolate = d3.interpolate(this._current, d);
    			this._current = interpolate(0);
    			return function(t) {
    				var d2 = interpolate(t);
    				var pos = outerArc.centroid(d2);
    				pos[0] = radius * (midAngle(d2) < Math.PI ? 1 : -1);
    				return "translate("+ pos +")";
    			};
    		})
    		.styleTween("text-anchor", function(d) {
    			this._current = this._current || d;
    			var interpolate = d3.interpolate(this._current, d);
    			this._current = interpolate(0);
    			return function(t) {
    				var d2 = interpolate(t);
    				return midAngle(d2) < Math.PI ? "start":"end";
    			};
    		})
            .text(function(d) {
                return `${d.data.value} ${d.data.label}`;
    		});

    	text.exit().remove();


        // Draw line from label to slice
    	var polyline = svg.select(".lines").selectAll("polyline")
    		.data(pie(data), key);

    	polyline.enter().append("polyline");

    	polyline.transition().duration(1000)
    		.attrTween("points", function(d){
    			this._current = this._current || d;
    			var interpolate = d3.interpolate(this._current, d);
    			this._current = interpolate(0);
    			return function(t) {
    				var d2 = interpolate(t);
    				var pos = outerArc.centroid(d2);
    				pos[0] = radius * 0.95 * (midAngle(d2) < Math.PI ? 1 : -1);
    				return [arc.centroid(d2), outerArc.centroid(d2), pos];
    			};
    		});

    	polyline.exit().remove();

        return self;
    };

    this.on = function(handlers) {
        self.handlers = handlers;
        return self;
    }

}
