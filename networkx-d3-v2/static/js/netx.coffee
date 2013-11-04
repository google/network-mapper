###
Single-Page UI for network visualizer.
keroserene@google.com  (Serene Han)
###
define ['domReady', 'jquery', 'underscore'], (domReady, $, _) ->

  gButter = null

  class Vis
    ID_PREFIX = '#v-'
    constructor: (@id, @name, @url, @isPublic) ->
      @entry = $(ID_PREFIX + @id)

  fadeHide = (element) ->
    element.addClass 'hidden'
    element.hideTimer = setTimeout (=> element.hide()), 300

  fadeShow = (element) ->
    element.show()
    setTimeout (=>element.removeClass 'hidden'), 10
    if element.hideTimer
      clearTimeout element.hideTimer
      element.hideTimer = null


  ###
  Maintains State about all of the user's visualizations.
  ###
  class VisIndex
    JSON_DATA_URL = '/data.json'

    constructor: ->
      @newEntryIsPending = false
      @$index = $ '#vis-index'
      @visualizations = []
      @visByID = {}
      @data = null

    show: -> fadeShow @$index
    hide: -> fadeHide @$index
    updateData: (data) ->
      console.log @visByID
      _.each data, (datum) =>
        [id, name, spreadsheet, isPublic] = datum
        if not @visByID.hasOwnProperty id
          vis = new Vis(id, name, spreadsheet, isPublic)
          @visualizations.push vis
          @visByID[id] = vis
        else
          console.log 'vis ' + id + ' already exists.'
      @data = data

    # Fetch JSON summary info for all existing visualizations, and update the
    # DOM if new visualizations must be listed.
    refresh: () ->
      console.log 'refreshing index.'
      # pending = $('#pending')
      # $.getJSON @JSON_DATA_URL, (data) ->
        # _.each data, (entry) =>
          # return if not pending
          # TODO(keroserene): Use sexy coffeescript stuff here
          # id = entry[0]
          # name = entry[1]
          # spreadsheet = entry[2]
          # @visByID[id] = new Vis(id, name, spreadsheet, null)
          # if not id in gGraphs
            # gGraphs[id] = name
            # entryDOM = pending[0]
            # pending = null
            # entryDOM.id = ENTRY_ID_PREFIX + id
            # entryDOM.innerHTML = name
            # hookGraphEntry(entryDOM)
        # if pending  # Try a refresh again
          # setTimeout(refreshEntries, 500);

  ###
  Holds state for the actions panel.
  ###
  class VisActions
    constructor: ->
      @$actions = $ '#vis-actions'
      @$viewMode = $ '#vis-view-mode'
    show: (viewMode=true) ->
      if viewMode
        fadeShow @$viewMode
      else
        fadeHide @$viewMode
      fadeShow @$actions
    hide: -> fadeHide @$actions


  # Holds state about the edit/create visualization form.
  class VisForm
    constructor: (@view)->
      @$form = $ '#vis-form-panel'
      @$formData = $ '#vis-form'
      @$index = $ '#vis-index'
      @$create = $ '#btn-create'
      @$nameInput = $ '#input_name'
      @$spreadsheetInput = $ '#input_url'
      @$publicInput = $ '#input_public'
      @$IDinput = $ '#input_id'
      @$save = $ '#btn-save'
    show: () ->
      fadeShow @$form
      @$nameInput.focus()
    hide: () -> fadeHide @$form
    # When currently viewing a particular visualization, prefill the form with
    # its info so that edits occur correctly.
    prefill: (vis) ->
      @$nameInput.val vis.name
      @$spreadsheetInput.val(
          'https://docs.google.com/a/google.com/spreadsheet/ccc?key=' +
          vis.url)
      @$publicInput[0].checked = vis.isPublic
      @$IDinput.val vis.id    # ID must be set for delete requests.
    clearForm: ->
      @$nameInput.val ''
      @$spreadsheetInput.val ''
      @$publicInput.checked = false
      @$IDinput.val ''

    saveOrCreate: () ->
      # TODO(keroserene): Pre-validate spreadsheet url/format?
      return if not validEntry('id_name', 'Please name your visualization.') or
         not validEntry('id_spreadsheet_link',
                        'Please provide a valid spreadsheet link.')
      success = false
      if (gEditMode)
        success = updateVis()
      else  # CREATE_MODE
        success = createVis()
        awaitUpdate()
      if success
        resetSidebar()

    ###
    Send AJAX POST to create new visualization.
    Updates local DOM to indicate the new graph.
    ###
    createVis: () ->
      data = @$formData.serialize()
      # The trailing slash in /graph/create/ is important.
      $.post '/graph/create/', data, () ->
        # gButter.show('Finished creation.')
        console.log 'created!'
        # setTimeout(refreshEntries, 100)
        true
      name = $('#input_name').val()
      # gButter.show('Creating new visualization "' + name  + '"...', false)
      console.log 'making a new thingy...' + name
      true

    ###
    Update visualization's meta-data.
    ###
    updateVis: (vis) ->
      # oldSpreadsheet = gSpreadsheets[gCurrentGraphID];
      sMatch = @$spreadsheetInput.val().match(/ccc\?key=(.*)/)
      if null == sMatch
        # gButter.showError('Invalid spreadsheet URL.')
        console.log 'invalid'
        return false
      newSpreadsheet = sMatch[1]
      oldSpreadsheet = vis.url
      oldID = vis.id
      # Trailing slash is vital.
      data = @$formData.serialize()
      $.post '/graph/' + vis.id + '/update/', data, =>
        gButter.show('Update complete.')
        console.log 'updated'
        # Refresh if spreadsheet changed and still viewing current graph.
        if (newSpreadsheet != oldSpreadsheet)# && gCurrentGraphID == cachedGraphID)
          setTimeout refreshGraph, 100
        newName = @$nameInput.val()
        vis.name = newName
        # Update local data model and DOM.
        vis.name = newName
        vis.entry.find('.vis-entry-name').html newName
        vis.url = newSpreadsheet
        vis.isPublic = @$publicInput.checked
        @view.$name.html newName
      gButter.show('Updating details...', false)
      true


  # State-holding class for NetworkX primary viewport.
  class View
    INDEX = 0
    VIEWING = 1
    EDITING = 2

    constructor: (@visIndex) ->
      @$view = $ '#view'
      @$loading = $ '#view-loading'
      # @$frame = $('#ajax-view').find('.vis-frame')
      @currentID = null
      @editMode = false
      @$name = $ '#view-name'
      @state = @INDEX
      # The script for running the d3 visualization code may be dynamically
      # loaded, once, when necessary.
      @_visCodeLoaded = false

    edit: -> @editMode = true

    # Entry point of showing a new visualization.
    show: (id) ->
      fadeShow @$loading
      window.VIS_ID=id  # Hack so that graph.coffee knows what to load.
      @_loadURL('/view/' + id + '/standalone')
      @currentID = id
      @$name.html @visIndex.visByID[id].name

    # Load a url into the AJAX viewport.
    # Requires the target URL to have a div #ajax-view.
    _loadURL: (url) ->
      console.log 'Loading AJAX: ' + url
      @$view.load url + ' #ajax-view', =>
        # gButter.hide()
        # @$frame = $('#ajax-view').find('.vis-frame')
        @$loading.hide()
        if not @_visCodeLoaded
          @_visCodeLoaded = true
          console.log 'Loading graph js for the first time...'
          require ['cs!graph']
        else
          window.initVisualization VIS_ID
      @$view.removeClass('hidden')
      @$view.show()

    # Refresh the currently viewed graph
    refresh: () ->
      return if not @currentID
      console.log 'refreshing'
      cachedGraphID = @currentID  # In case user loads another graph.
      $.get '/graph/' + @currentID + '/reload/', [], () =>
        # Success callback which updates butterbar and DOM.
        $('#btn-refresh').removeClass('disabled')
        gButter.show('Visualization data refreshed!')
        if cachedGraphID is @currentID
          @show @currentID
      # $('#btn-refresh').addClass('disabled')
      # hideToolTip($('#tooltip-refresh'))
      gButter.show('Refreshing data from spreadsheet...', false)

    # Clears everything from the AJAX viewport. Used prior to loading any new
    # view, or when opening the create visualization pane.
    clear: () ->
      @$view.empty()
      fadeHide @$loading
      fadeHide @$view
      window.history.pushState({}, null, '/')
      window.addEventListener 'popstate', (e) => @show @currentID
      @currentID = null
      @$name.html ''
      # $('.vis-entry').filter('.selected').removeClass('selected')
      # Conceal any open dialogues.
      # if $('#btn-embed').hasClass('active')
        # toggleEmbedLink()


  ###
  Class describing the butterbar for temporary feedback messages.
  ###
  class ButterBar
    TIMEOUT_MS: 1800
    constructor: ->
      @bar = $ '#butterbar'
      @text = $ '#butterbar-text'
      @dismissButton = $ '#butterbar-dismiss'
      @dismissButton.click( => @hide())

    show: (message, autohide=true) ->
      return if not message
      @reset()
      this.text.html message
      this.bar.removeClass 'hidden'
      if autohide
        timeout = setTimeout =>
          @bar.addClass 'hidden'
        , @TIMEOUT_MS

    showError: (message) ->
      @reset()
      @show('ERROR: ' + message, false)
      @bar.addClass 'error'
      @dismissButton.removeClass 'hidden'
      @dismissButton.show()

    hide: -> @bar.addClass 'hidden'

    reset: ->
      if @timeout
        window.clearTimeout @timeout
        @timeout = null
      @bar.removeClass 'error'
      @dismissButton.addClass 'hidden'
      @dismissButton.hide()
      @text.html ''


  # Prepare all AJAX / DOM / event handlers.
  domReady ->
    # Prepare required state-holders.
    gButter = new ButterBar()
    gActions = new VisActions()
    gIndex = new VisIndex()
    gView = new View(gIndex)
    gForm = new VisForm(gView)

    returnToIndex = ->
      currentVis = gIndex.visByID[gView.currentID]
      currentVis.entry.removeClass 'selected' if currentVis
      gIndex.show()
      gView.clear()
      gActions.hide()
      gForm.hide()

    # Fetch potential django template variables.
    gIndex.updateData INDEX_DATA
    gView.currentID = VIS_ID if VIS_ID

    # Prepare view handler for each graph entry.
    $visEntries = $ '.vis-entry'
    _.each gIndex.visualizations, (vis) ->
      console.log vis
      vis.entry.click =>
        # gIndex.hide()
        vis.entry.addClass 'selected'
        gActions.show()
        console.log('showing', vis)
        # Slightly delay the actual loading of the visualization.
        window.setTimeout (=> gView.show(vis.id)), 300
        # hideHelp()
        # To be closed upon successful loading, or an error message appears.
        # if id isnt gCurrentGraphID
          # gButter.show('Loading...', false)
        # $visEntries.removeClass 'selected'
        # $(this).addClass 'selected'
        # $('#view-name').html(vis.name)

        # Use pushState to update the browser's URL.
        window.history.pushState({}, null, 'view/' + vis.id)
        window.addEventListener 'popstate', (e) =>
          # Allow the back-button to restore previous state.
          e.preventDefault()
          returnToIndex()

    $back = $ '#btn-back'
    $back.click (e) ->
      e.preventDefault()
      if gView.editMode
        # Return to view mode.
        gView.editMode = false
        console.log 'returning from edit mode! ' + gView.currentID
        gForm.hide()
        fadeShow gActions.$viewMode
      else
        # Return to index.
        returnToIndex()

    # Clicking 'Create Visualization' opens up a fresh visualization view.
    gForm.$create.click () ->
      gIndex.hide()
      gForm.clearForm()
      gForm.show()
      gActions.show(viewMode=false)

    # Clicking 'Save' either creates or updates a visualization.
    gForm.$save.click (e) ->
      e.preventDefault()  # Prevent unnecessary postback.
      if gView.currentID
        vis = gIndex.visByID[gView.currentID]
        gForm.updateVis(vis)
        $back.click()
      else
        gForm.createVis()
        gForm.hide()
      true

    $(document).ajaxError (request, text, error) ->
      console.log 'ajax error.'
      gButter.showError(
          'Something went wrong (' + request.responseText + ') ' +
          'OAuth probably needs to reauthorize.')
      $('#pending').remove()
      $('#btn-refresh').removeClass('disabled')

    ###
    Handler for clicking on "EDIT".
    Needs to update the form entries to match the parameters for the currently
    selected visualization
    ###
    $edit = $ '#btn-edit'
    $edit.click (e) ->
      e.preventDefault()
      gView.editMode = true
      gForm.prefill gIndex.visByID[gView.currentID]
      gForm.show()
      fadeHide gActions.$viewMode
      # gDOM.saveBtn.text('Save')

    $tt = $('#tooltip')
    showTooltip = (tool, tip) ->
      ofs = tool.offset()
      # $tt.removeClass 'hidden'
      fadeShow $tt
      $tt.html tip
      $tt.css ofs
    hideTooltip = -> fadeHide $tt
    hookTooltip = (tool, tip) ->
      show = -> showTooltip tool, tip
      tool.hover show, hideTooltip
      tool.focus show
      tool.blur hideTooltip

    $refresh = $ '#btn-refresh'
    $refresh.click (e) ->
      e.preventDefault()
      gView.refresh()

    $embed = $ '#btn-embed'
    $embed.click (e) ->
      e.preventDefault()
      console.log 'share link'

    $saveNodes = $ '#btn-save-positions'
    $saveNodes.click (e) ->
      e.preventDefault()
      # This function lives inside graph.coffee.
      queryString = gView.$frame[0].contentWindow.getPositionQuery()
      updateUrl = '?' + queryString
      window.history.pushState({}, 'unused', updateUrl)
      # TODO(keroserene): Push changes to the underlying document.


    hookTooltip $back, 'back'
    hookTooltip $edit, 'edit'
    hookTooltip $refresh, 'refresh visualization'
    hookTooltip $embed, 'share'
    hookTooltip $saveNodes, 'save node positions'

    $(document).keydown (e) ->
      # Catch 'escape' as equivalent to clicking the back button.
      if e.keyCode is 27
        $back.click()

    # If a specific VIS_ID was specified, automatically open up the
    # visualization.
    if VIS_ID
      gView.show VIS_ID

    ###
    # Primary button handlers.
    # The "save" button switches innerHTML between "Save" and "Create"
    # depending on if the opened dialogue is an edit or a new visualization.
    $('#btn-delete').click(deleteGraph);
    $('#btn-embed').click(toggleEmbedLink);
    # Tooltips.
    $('#btn-refresh').hover(
      function() { showToolTip($('#tooltip-refresh')); },
      function() { hideToolTip($('#tooltip-refresh')); });

    # Help
    $('#link-help').click(function(ev) {
      ev.preventDefault();
      window.history.pushState({}, 'unused', '/help/');
      showHelp();
    });

    #Dark mode
    $('#darkmode').click(function() {
      var vis = gDOM.graphFrame.contents();
      // $('#visualization')
      var graph = $('.graph', vis);
      graph.addClass('dark');
      $('.node-circle', graph).attr('class', function(i, o) {
        return o.replace('node-circle', 'node-circle-dark');
      });
      $('.label-text', graph).attr('class', 'label-text-dark');
    ###
