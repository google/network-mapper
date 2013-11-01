
    Graph.prototype.getZoomTranslateInterpolator = function (scale, dimension, offset) {
        var currentScale = this.zoom.scale(),
            scaleTo = this.zoomRange(scale),
            currentTranslate = this.zoom.translate();

        offset = offset - ((dimension / -2) * (currentScale - 1));

        return d3.interpolate(
            ((dimension / -2) * (currentScale - 1)) + offset,
            ((dimension / -2) * (scaleTo - 1)) + offset
        );
    };

    Graph.prototype.zoomToScale = function (scale) {
        var currentScale = this.zoom.scale(),
            scaleTo = this.zoomRange(scale),
            scaleIplt = d3.interpolate(currentScale, scaleTo),
            currentTranslate = this.zoom.translate(),
            offsetX = currentTranslate[0],
            offsetY = currentTranslate[1],
            translateXIplt = this.getZoomTranslateInterpolator(scale, this.width, offsetX),
            translateYIplt = this.getZoomTranslateInterpolator(scale, this.height, offsetY),
            self = this;

        d3.transition()
            .duration(100)
            .tween('zoom', function () {
                return function (t) {
                    self.zoom.scale(scaleIplt(t));
                    self.zoom.translate(
                        [
                            translateXIplt(t),
                            translateYIplt(t)
                        ]
                    );
                };
            });

        return this;
    };

    Graph.prototype.zoomIn = function () {
        this.zoomToScale(this.zoom.scale() + 1);
        return this;
    };

    Graph.prototype.zoomOut = function () {
        this.zoomToScale(this.zoom.scale() - 1);
        return this;
    };


    var SemanticZoomGraph = function (options) {
        var self = this, drag;

        Graph.call(this, options);

        drag = this.force.drag();

        drag.on('drag.force', function (d) {
            d.px += (d3.event.dx / self.zoom.scale());
            d.py += (d3.event.dy / self.zoom.scale());
            self.force.resume();
        });
    };

    SemanticZoomGraph.prototype = Object.create(Graph.prototype);

    SemanticZoomGraph.prototype.draw = function () {
        var evt = d3.event,
            x = this.xScale,
            y = this.yScale;

        //Graph.prototype.draw.call(this);

        this.nodes.attr(
            'transform',
            function (d) {
                return 'translate(' + x(d.x) + ',' + y(d.y) + ')';
            }
        );
        this.labels.attr(
            'transform',
            function (d) {
                return 'translate(' + x(d.x) + ','
                    + y(d.y + Graph.prototype.getRadiusForNode(d)) + ')';
        });
        this.links
            .attr('x1', function (d) {
                return x(d.source.x);
            })
            .attr('y1', function (d) {
                return y(d.source.y);
            })
            .attr('x2', function (d) {
                return x(d.target.x);
            })
            .attr('y2', function (d) {
                return y(d.target.y);
            });

        return this;
    };





/*
    // TODO(ldixon): use fancy quadtree like structure to determine hidden/shown labels.
    Graph.prototype.makePointsQuadTree = function () {
        // Create points for each corner of a label for clashing
        // label-detection.
        //TODO(ldixon): remove points & quadtree, replace with special
        // overlapping boxes quad-tree.
        var points = [];
        this.svg.selectAll('g.label')
            .each(function (d, i) {
                var bounds = this.getBoundingClientRect();
                points.push({x: bounds.left, y: bounds.top, idx: i});
                points.push({x: bounds.right, y: bounds.top, idx: i});
                points.push({x: bounds.left, y: bounds.bottom, idx: i});
                points.push({x: bounds.right, y: bounds.bottom, idx: i});
            });
        // Create quadtree for quickly lookup up points within a bounding box.
        return d3.geom.quadtree(points);
    }

    Graph.prototype.resetPointsQuadTree = function () {
        this.pointsQuadTree_ = this.makePointsQuadTree();
    }
*/



