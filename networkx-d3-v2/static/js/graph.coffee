# Graph visualizer.
define ['domReady', 'd3', 'jQuery', 'modernizr', 'backbone', 'underscore'], (
    domReady, d3, $, Modernizr, Backbone, _) ->

  Params = {
    NODE_INIT_RANGE: 0.5
    # To help the graph "settle down" faster; lower number = faster.
    # TODO(ldixon): rethink this; this is tick-local, not user-experience local.
    FORCE_LAYOUT_DECAY: 0.95
  }

  class NetX
    @LABEL_TICK_MS: 1000

    # Obtain manual coordinate for fixed nodes.
    @getQueryString: () ->
      queries = window.parent.location.search.replace('?', '').split('&')
      keyValues = {}
      $.each queries, (i, kv) =>
        s = kv.split('=')
        keyValues[s[0]] = s[1] if 2 == s.length
      keyValues

    # Bound |val| between |min| and |max|.
    @bound: (val, min, max) -> Math.max(min, Math.min(max, val))

    # Check if two boxes overlap.
    @boxCollision: (b1, b2) ->
      not (b1.left >= b2.right or b1.top >= b2.bottom or
           b1.right < b2.left  or b1.bottom < b2.top)

  ###
  Description and state-holder for a single Graph visualization.
  This is mostly a wrapper around a d3 force layout.
  ###
  class Graph
    constructor: (options) ->
      [@width, @height] = [options.width, options.height]
      # @height = options.height
      @minScale = 0.5
      @maxScale = 8
      @detailInterval_ = null  # Hover-activated single-node detail pane.
      @setupSize(@width, @height)

      _.bindAll @, 'tickUpdate', 'getRadiusForNode'
      @setupSize @width, @height

      # Construct scaling functions.
      @xScale = d3.scale.linear().domain([0,@width]).range([0,0])
      @yScale = d3.scale.linear().domain([0,@height]).range([0,0])

      @zoomRange = d3.scale.linear()
          .domain([@minScale, @maxScale])
          .rangeRound([@minScale, @maxScale])
          .clamp(true)
          .nice()
      @zoom = d3.behavior.zoom()
          .x(@xScale)
          .y(@yScale)
          .scaleExtent([@minScale, @maxScale])
          .on('zoom', (e) => @tickUpdate(e))
      @svgContext = d3.select('.graph')
          .append('svg')
          .attr('id', 'visualization')
          .attr('class', 'light')
          .attr('width', @width)
          .attr('height', @height)
          .call(@zoom)
      @svg = @svgContext
          .append('g')
          .attr('id', 'elements')
          .attr('width', @width)
          .attr('height', @height)
      @$svg = @svg[0][0]
      @url = options.url
      @links = undefined
      @nodes = undefined
      @labels = undefined
      @circles = undefined
      @json = undefined
      @pointsQuadTree_ = undefined

      @nodeInfos = [];     # Array of all node details.
      @activeNode = null;  # Currently hovered / dragged node.

      # Smoothing parameters.
      @targetScale = 1.0
      @actualTranslate = [0,0]
      @actualScale = @targetScale
      @isZooming = false

      # Initialize this d3 Force Layout.
      @force = d3.layout.force()
        .charge(-300)
        .size([@width, @height])
        .friction(0.6)
        .gravity(0)
        .theta(0.95)   # Higher theta => more approximate but faster.
        .linkStrength(0.9)
        .linkDistance((o,i) -> 20 + (o.source.importance * o.target.importance))

      # Check for custom positions for fixed nodes.
      # The format for each query string is node_id=x+y
      queries = NetX.getQueryString()

      @startPositions = @setupStartPositions queries

      d3.json @url, (json) =>
        @json = json
        $('#graph-loading').html('')  # TODO(keroserene): Improve loader gfx.
        @setupLinks()
          .setupNodes()
          .setuptickUpdate()
          .setupClick()
          .setupHover()
          .setupDrag()
        @force
          .nodes(@json.nodes)
          .links(@json.links)
        @labels = new LabelSet @svg   # Prepare label interactions.

        # Initialize positions of all nodes within the screen.
        @force.nodes().forEach (d, i) =>
          node_style = d.node_style.split ' '
          if i of @startPositions
            fP = @startPositions[i]
            d.x = fP.x
            d.y = fP.y
          else
            r = Params.NODE_INIT_RANGE
            d.x = @width * ((1.0-r)*0.5 + Math.random() * r)
            d.y = @height * ((1.0-r)*0.5 + Math.random() * r)
          # If it is specified as 'fixed', prevent it from moving
          # around. Then, check if user specified an initial position.
          if $.inArray('fixed', node_style) > -1
            d.fixed = true
            @nodeInfos[i].isFixed = true


        @force.start()
        # End of json success callback.

    _.extend(Graph.prototype, Backbone.Events)

    getRadiusForNode: (d) ->
      importance = d.importance or 1
      Math.max(5, importance * 2)

    # Track window size internally for force layout.
    setupSize: (width, height) ->
      @width = width
      @height = height

    setupStartPositions: (queries) ->
      startPositions = {}    # Dict of node_id -> (x, y) tuple
      for key, value of queries
        # Validate the key-value pair as a position.
        nodeID = parseInt key
        coordinates = value.split '+'
        if isNaN nodeID or 2 != coordinates.length
          continue
        startPositions[nodeID] = {
          'x': parseInt(coordinates[0])
          'y': parseInt(coordinates[1])
        }
      startPositions

    # Construct a link based on all the link data.
    setupLinks: () ->
      @links = @svg.selectAll('.link')
          .data(@json.links)
          .enter()
          .append('line')
          .attr('class', 'link')
      @$links = @links[0]
      @

    # Prepares DOM elements and handlers for all nodes.
    setupNodes: () ->
      # Join the nodes with data.
      @nodes = @svg.selectAll('g.node')
        .data(@json.nodes)
        .enter()
        .append('g')
        .attr('id',  (d, i) -> 'n' + i)
        .attr('class', 'node')
        .call(@force.drag)
      # Add circles.
      @nodes
        .append('circle')
        .attr('r', @getRadiusForNode)
        .attr('class', (d) => 'node-circle ' + d.node_style || '')
      # Add label holders.
      @nodes
        .append('g')
        .attr('id', (d,i) -> 'l' + i)
        .attr('class', (d) -> 'label ' + d.label_style || '')
      @circles = @svg.selectAll 'g.node circle'
      # Prepare all NodeInfo objects.
      @nodes.each (d, i) => @nodeInfos.push new NodeInfo(d, i)
      @

    setuptickUpdate: () ->
      @force.on('tick', (e) => @tickUpdate e)
      @

    setupClick: () ->
      @svg.selectAll('g.node').on('click', (d) =>
        @trigger('click:node', d3.event, d))
      @svg.selectAll('g.label').on('click',
        (d) => @trigger('click:node', d3.event, d))
      @

    # Prepare the hover handlers. When a node is hovered, adjacent links will
    # also be hilighted. Hovering and dragging are interrelated - for example,
    # new hover effects do not begin when one is already dragging another node.
    setupHover: () ->
      # Construct mappings from nodes to each of their links.
      @json.links.forEach (edge, index) =>
        @nodeInfos[edge.source].addLinkMapping @$links[index]
        @nodeInfos[edge.target].addLinkMapping @$links[index]
      # Remember DOM references.
      @nodeInfos.forEach (n) -> n.cacheLinks()
      @svg.selectAll('g.node')
        .on('mouseover', (d,i) => @hover(d,i,true))
        .on('mouseout', (d,i) => @hover(d,i,false))
      @

    # Add some special styling for dragged nodes and their labels.
    setupDrag: () ->
      drag = @force.drag()
      listenerFactory = (beingDragged) =>
        (d, i) =>
          label = d3.select('#l' + i)
          label.classed('drag-label', beingDragged)
          node = d3.select('#n' + i)
          label.classed('drag-node', beingDragged)
          # Guard the dragging state with hover modifications.
          @hover(d,i,true) if beingDragged
          @dragging = beingDragged
          @hover(d,i,false) if not beingDragged
      drag.on('dragstart.label-highlight', listenerFactory(true))
      drag.on('dragend.label-highlight', listenerFactory(false))
      @

    getPositionQuery: () ->
      @nodeInfos.filter((n) -> n.isFixed)
        .map((n) -> n.getPositionQuery())
        .join('&')

    # Event handler for hover updates. Hover only activates if one is not
    # actively dragging another node.
    hover: (d,i,hover) ->
      return false if (@dragging)
      # Disable hovering if necessary.
      if hover
        @activeNode = @nodeInfos[i]
        @activeNode.activate()
      else if null isnt @activeNode
        @activeNode.deactivate()
        @activeNode = null


  ###
  Keep track of details for a single Node, for activeNode and dragging
  interacitons.
  ###
  class NodeInfo
    @ROUNDING_POINT: 4
    constructor: (@data, @id) ->
      @label = d3.select '#l' + @id
      @node = d3.select '#n' + @id
      @links = []  # Only those links adjacent to this node.
      @sLinks = null
      @isFixed = false

    addLinkMapping: ($link) -> @links.push $link
    cacheLinks: () -> @sLinks = d3.selectAll(@links)

    # Make this node appear "active" (typically for hovering)
    activate: () ->
      @label.classed('hidden', false)
      @label.classed('hovered-label', true)
      @node.classed('hovered-node', true)
      # Also hilight all links associated with this node.
      # $.each @json.nodes[i].links, (i, d) =>
        # d3.select(d).classed 'hover', true
      @sLinks.classed('hover', true)

    deactivate: () ->
      @label.classed('hovered-label', false)
      @node.classed('hovered-node', false)
      # Also unhilight all links associated with this node.
      @sLinks.classed('hover', false)

    getInfoHtml: () -> 'Node #' + @id +
        '<br>Fixed:' + @isFixed +
        '<br>X: ' + @data.x.toFixed(@ROUNDING_POINT) +
        '<br>Y: ' + @data.y.toFixed(@ROUNDING_POINT)

    getPositionQuery: () -> @id + '=' + @data.x.toFixed(@ROUNDING_POINT) +
                                  '+' + @data.y.toFixed(@ROUNDING_POINT)


  # Zoom/Drag smoothing.
  SMOOTHING = {
    ENABLED: false
    MAX_INVERT: 1.25
  }


  ###
  Description of a set of labels on nodes, primarily in order to determine
  visibility and bounds checking.
  ###
  class LabelSet
    constructor: (svg) ->
      @labels = svg.selectAll('g.label')
        .append('text')
        .attr('class', (d) -> 'label-text ' + (d.label_style or ''))
        .attr('text-anchor', 'middle')
        .text((d) -> d.name)
      @total = @labels[0].length
      @selections = []    # Cache d3 selections for each individual label.
      @$labels = []
      @labels.each (d,i) =>
        @$labels.push(@labels[0][i])
        @selections.push(d3.select @$labels[i])
      @labelClashTimerID_ = null

    checkVisibility: (el) ->
      has = (s) -> el.classed s
      return true if (has 'always-shown-label') or (has 'hovered-label') or
                     (has 'drag-label')
      return false if has 'always-hidden-label'
      null   # Visibility was not determined by a css class.

    # Returns true if the current label is obscured by any other label.
    isObscured: (d, i) ->
      for s, j in @selections
        d2 = s.datum()
        if (j isnt i) and (true is d2.isVisible) and
           NetX.boxCollision(d.label_bounds, d2.label_bounds)
          return true
      false

    tickUpdate: (e) ->
      ticks = 5
      if null == @labelClashTimerID_
        @labelClashTimerID_ = window.setInterval () =>
          sLabel = null
          # Refresh bounding boxes and vis classes.
          @labels.each (d, i) =>
            d.label_bounds = @$labels[i].getBoundingClientRect()
            d.isVisible = @checkVisibility @selections[i]
          # Decide visibility for every label.
          @labels.each (d, i) =>
            sLabel = @selections[i]
            d.isVisible = not @isObscured(d, i) if null is d.isVisible
            sLabel.classed('hidden', not d.isVisible)
          if ticks-- <= 0
            clearInterval @labelClashTimerID_
            @labelClashTimerID_ = null
        , NetX.LABEL_TICK_MS

    transform: (invertScale) ->
      @labels.transition()
        .call(GeometricZoomGraph.smooth, @isZooming)
        .attr 'transform', (d) =>
          return if undefined is d or undefined is d.label_bounds
          voffset = 0
          if (undefined is d.short_description or '' is d.short_description)
            voffset = (d.label_bounds.bottom - d.label_bounds.top) *
                      0.3 * invertScale
          else
            voffset = Graph.prototype.getRadiusForNode(d) +
                      (d.label_bounds.bottom - d.label_bounds.top) * 0.9
          'translate(0, ' + voffset * invertScale + ')' +
          'scale(' + invertScale + ')'


  ###
  Zoomable graph.
  ###
  class GeometricZoomGraph extends Graph

    # Transition modifier.
    @smooth: (transition, isZooming) ->
      trans_ms = if isZooming then 231 else 33
      algorithm = if isZooming then 'easeInOutQuad' else 'easeInOutSine'
      transition
          .duration(trans_ms)
          .ease(algorithm)
      transition

    tick: 1

    # Primary tick function which occurs whenever the force layout updates
    # the position of nodes. Handles smoothing and other effects.
    tickUpdate: (e) ->
      @labels.tickUpdate(e) if @labels
      # Restrict scrolling/panning to the screen.
      translate = @zoom.translate()
      scale = @zoom.scale()
      box = @$svg.getBBox()
      rawCenterX = box.x + box.width / 2
      rawCenterY = box.y + box.height / 2
      # getBBox doesn't include attr translation/scaling, so recalculate.
      tXmin = -(rawCenterX * scale)
      tYmin = -(rawCenterY * scale)
      # Bound the translation coordinate between a minimum and a maximum.
      tX = NetX.bound(translate[0], tXmin, @width + tXmin)
      tY = NetX.bound(translate[1], tYmin, @height + tYmin)
      translate = [tX, tY]
      @zoom.translate(translate)

      if SMOOTHING.ENABLED
        @targetScale = scale
        if not @isZooming
          @isZooming = scale isnt @actualScale
        @svg.transition()
            .call(GeometricZoomGraph.smooth, @isZooming)
            .attr('transform',
                'translate(' + translate + ')' +
                'scale(' + scale + ')')
            .each('end', () -> @isZooming = false )  # Finish the zooming.
        if @isZooming
          if @circles
            invertFactor = 0.8
            invertScale = (invertFactor / @targetScale) + (1 - invertFactor)
            invertScale = Math.min(SMOOTHING.MAX_INVERT, invertScale)
            transformVal = 'scale(' + invertScale + ')'
            @circles.transition()
                .call(GeometricZoomGraph.smooth, @isZooming)
                .attr('transform', transformVal)
          # Maintain the size of all the link stroke widths.
          @links.transition().call(GeometricZoomGraph.smooth, @isZooming)
              .style('stroke-width', 1 / @targetScale)
      else
        @svg.attr 'transform',
            'translate(' + translate + ')' +
            'scale(' + scale + ')'
      @labels.transform 1.0 / @targetScale if @labels

      # Keep track of the current scale and translate for future deltas.
      @actualScale = scale
      @actualTranslate = translate
      @nodes.attr 'transform',
        (d) -> 'translate(' + d.x + ',' + d.y + ')'
      @links
        .attr('x1', (d) -> d.source.x)
        .attr('y1', (d) -> d.source.y)
        .attr('x2', (d) -> d.target.x)
        .attr('y2', (d) -> d.target.y)

      # Speed-up the last bit of smoothing so that it settles fast.
      alpha = @force.alpha()
      if alpha < 0.09
        @force.alpha(alpha * Params.FORCE_LAYOUT_DECAY)


  ###
  Description of the popup details for every node.
  ###
  class Popup
    constructor: (options) ->
      _.bindAll(@, 'open', 'close')

      @$el = $('.info-panel')
      @$heading = @$el.find('.info-heading')
      @$shortDescription = @$el.find('.info-short-description')
      @$longDescription = @$el.find('.info-long-description')
      @$youtube = @$el.find('.info-youtube')
      @$link = @$el.find('.more-information-link')
      @$credit = @$el.find('.info-credit')
      @currentCoords = {
        x: undefined
        y: undefined
      }
      @data = {
        heading: ''
        shortDescription: ''
        longDescription: ''
        youtube: ''
        contextUrl: ''
        credit: ''
      }
      @panelOpen = false
      @transitionPrefixedName = @hyphenisor(Modernizr
        .prefixed('transition'))
      @transformPrefixedName = @hyphenisor(Modernizr
        .prefixed('transform'))
      @setupCloseEvent()

    _.extend(Popup.prototype, Backbone.Events)

    hyphenisor: (str) ->
      str.replace /([A-Z])/g, (str, letter) ->
        '-' + letter.toLowerCase()
      .replace(/^ms-/, '-ms-')

    open: (coords) ->
      if not @panelOpen
        css = {
          top: coords.y + 'px'
          left: coords.x + 'px'
        }
        css[@transitionPrefixedName] = 'none'
        @$el.css css
        window.setTimeout () =>
          css = { opacity: 1, top: '', left: '50%' }
          css[@transformPrefixedName] = 'scale(1)'
          css[@transitionPrefixedName] = 'all 0.2s'
          @$el.css css
        ,0
        @panelOpen = true
      @currentCoords = coords

    close: () ->
      css = {
        opacity: 0
        top: @currentCoords.y + 'px'
        left: @currentCoords.x + 'px'
      }
      css[@transformPrefixedName] = 'scale(0)'
      @$el.css css
      @panelOpen = false

    setupCloseEvent: () -> @$el.on 'click', '.close-button', @close
    setData: (data) -> @data = data
    renderContent: () ->
      @$heading         .text @data.heading
      @$shortDescription.text @data.shortDescription
      @$longDescription .text @data.longDescription
      @$youtube.html    @data.youtube
      @$credit.html     @data.credit
      if @data.contextUrl
        @$link.toggle true
        @$link.attr('href', @data.contextUrl)
      else
        @$link.toggle false
        @$link.attr('href', '')


  getPositionQuery = () ->
    console.log 'wtf'

  ##############################################################################
  # Entry point.
  $ ->
    graph = new GeometricZoomGraph {
        width: window.innerWidth
        height: window.innerHeight
        url: $('body').data 'graph-url'
        # query: window.location.search
      }
    window.getPositionQuery = () -> graph.getPositionQuery()
    popup = new Popup()
    ESCAPE_KEY_CODE = 27
    # Prepare popup handlers.
    popup.listenTo graph, 'click:node', (evt, obj) =>
      return if undefined is obj.short_description

      credit = obj.credit
      youtube_id = obj.youtube_id
      context_url = obj.context_url

      popup.open {
        x: evt.offsetX
        y: evt.offsetY - 175
      }
      if 0 is credit.indexOf('http://')
        credit = '<a href="' + credit + 'target="_blank">' + credit + '</a>'
      credit = "This data entry was provided by " + credit if credit
      if youtube_id
        youtube_id =
          '<iframe title="YouTube video player" ' +
          'src="http://www.youtube.com/embed/' +
          youtube_id + '" width="480" height="390" frameborder="0"></iframe>'
        context_url = ''
      popup.setData {
        heading: obj.name
        shortDescription: obj.short_description
        longDescription: obj.long_description
        contextUrl: context_url
        credit: credit
        youtube: youtube_id
      }
      popup.renderContent()

    $('body').on 'click', (evt) =>
      if (0 is $(evt.target).closest('.info-panel').length) and
         (not $(evt.target).is '.circle')
        popup.close()
    $('body').on 'keydown', (evt) ->
      popup.close() if ESCAPE_KEY_CODE is evt.keyCode

    # Update the size of graph's context whenever window changes.
    window.onresize = (e) ->
      graph.setupSize window.innerWidth, window.innerHeight

    $nodeInfo = $ '#node-info'
    $coord    = $ '#graph-coordinates'

    # Update graph details on mouse move if there is an active node.
    $(document).mousemove (e) ->
      if graph.activeNode
        $nodeInfo.show()
        $nodeInfo.removeClass 'hidden'
        $coord.html graph.activeNode.getInfoHtml()
        $nodeInfo.css {
          left: e.clientX
          top: e.clientY
        }
      else
        $nodeInfo.addClass 'hidden'
        window.setTimeout (() -> $nodeInfo.hide())
        , 100
