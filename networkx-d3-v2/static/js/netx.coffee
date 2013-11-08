###
Single-Page UI for network visualizer.
keroserene@google.com  (Serene Han)
###
define ['domReady', 'jquery', 'underscore'], (domReady, $, _) ->
  gButter = null
  gActions = null
  gIndex = null
  gView = null
  gForm = null

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
    @JSON_DATA_URL = '/data.json'

    constructor: ->
      @$index = $ '#vis-index'
      @visByID = {}   # ID -> visualization.
      @data = null
      @newEntryIsPending = false

    show: -> fadeShow @$index
    hide: -> fadeHide @$index

    # Given JSON |data|, update internal index of all visualizations.
    updateData: (data) ->
      _.each data, (datum) =>
        [id, name, spreadsheet, isPublic] = datum
        if not @visByID.hasOwnProperty id
          vis = new Vis(id, name, spreadsheet, isPublic)
          @visByID[id] = vis
        else
          console.log 'vis ' + id + ' already exists.'
      @data = data

    # Fetch JSON summary info for all existing visualizations, and update the
    # DOM if new visualizations must be listed.
    refresh: ->
      console.log 'refreshing index.'
      $.getJSON VisIndex.JSON_DATA_URL, (data) =>
        # Update index of visualizations and determine newest ID.
        oldIDs = _.keys(@visByID)
        @updateData data
        # Isolate new visualization ID (only 1 is expected) and add to DOM.
        newIDs = _.difference(_.keys(@visByID), oldIDs)
        if 0 is newIDs.length
          console.warn 'No new visualization ID discovered after creation...'
          return false
        if newIDs.length > 1
          console.warn 'More than 1 new visualization ID discovered...'
        id = newIDs[0]
        vis = @visByID[id]
        $pending = $ '#pending'
        if not $pending
          console.warn 'No pending DOM entry provided...'
          return false
        $pending.attr('id', 'v-' + id)
        $pending.append '<div class="vis-entry-name">' + vis.name + '</div>'
        vis.entry = $pending
        hookVisEntry vis

    # Actually remove |vis| from the index.
    remove: (vis) ->
      if not @visByID[vis.id]
        console.warn 'Attempted to remove non-existent visualization: ', vis
        return false
      @visByID[vis.id] = undefined


  ###
  Holds state for the actions panel.
  ###
  class VisActions
    constructor: ->
      @$actions = $ '#vis-actions'
      @$viewMode = $ '#vis-view-mode'
      @$edit = $ '#btn-edit'
      @$docs = $ '#btn-docs'
      # For the sharing box.
      @shareBoxVisible = false
      @$shareBox = $ '#share-content'
      @$snippet = $ '#snippet'
      @$standaloneLink = $ '#standalone-link'

    show: (viewMode=true) ->
      if viewMode
        fadeShow @$viewMode
      else
        fadeHide @$viewMode
      fadeShow @$actions
    hide: -> fadeHide @$actions

    toggleShareBox: ->
      @shareBoxVisible = not @shareBoxVisible
      @$shareBox.toggleClass 'hidden', not @shareBoxVisible
      if @shareBoxVisible
        standaloneUrl = '/view/' + getCurrentVisualization().id + '/standalone'
        embedCode = '<iframe src="' + HOSTNAME + standaloneUrl +
                    '" width="1000" height="600"></iframe>'
        @$snippet.text embedCode
        @$snippet.select()  # Auto-hilight the embed code.
        @$standaloneLink.attr('href', standaloneUrl)


  # Holds state about the edit/create visualization form.
  class VisForm
    @CREATE_URL: '/create/'  # The trailing slash is important.
    @VALID_NAME = /^[\d\w\s]+$/i
    @VALID_URL = /^https:\/\/docs.google.com\/[\d\.\w\/]+\?key=.+$/i

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
      @$delete = $ '#btn-delete'
      @_spreadsheetId = ''
      # Attach dynamic validation handlers.
      @$nameInput.keyup =>
        name = @$nameInput.val()
        @$nameInput.toggleClass(
            'invalid', name.length > 0 and not VisForm.VALID_NAME.test name)
      @$spreadsheetInput.keyup =>
        url = @$spreadsheetInput.val()
        @$spreadsheetInput.toggleClass(
            'invalid', url.length > 0 and not VisForm.VALID_URL.test url)

    show: () ->
      fadeShow @$form
      @$nameInput.focus()
    hide: () ->
      # fadeHide @$form
      @$form.addClass 'hidden'

    # When currently viewing a particular visualization, prefill the form with
    # its info so that edits occur correctly.
    prefill: (vis) ->
      @$nameInput.val vis.name
      @$spreadsheetInput.val(
          'https://docs.google.com/a/google.com/spreadsheet/ccc?key=' +
          vis.url)
      @$publicInput[0].checked = vis.isPublic
      @$IDinput.val vis.id    # ID must be set for delete requests.
      @$delete.show()
    clearForm: ->
      @$nameInput.val ''
      @$spreadsheetInput.val ''
      @$publicInput.checked = false
      @$IDinput.val ''
      @$delete.hide()

    # Ensure the fields in the form are correct. Assumed to be called prior to
    # createVis() or updateVis()
    validate: ->
      name = @$nameInput.val()
      if not VisForm.VALID_NAME.test name
        gButter.show 'Please provide a valid name.'
        return false
      url = @$spreadsheetInput.val()
      if not VisForm.VALID_URL.test url
        gButter.show 'Please provide a valid spreadsheet url.'
        return false
      query = url.split('?key=')[1]
      @_spreadsheetId = query.split('&')[0]
      true

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
      $.post VisForm.CREATE_URL, data, =>
        gButter.show('Finished creation.')
        console.log 'created.'
        @view.visIndex.refresh()
        true
      name = $('#input_name').val()
      gButter.showPersist('Creating new visualization "' + name  + '"...')
      console.log 'New Visualization [' + name + ']  ......'
      # Create placeholder DOM element.
      @$create.before '<div id="pending" class="vis-entry"></div>'
      @view.visIndex.show()
      gActions.hide()
      true

    ###
    Update visualization's meta-data. Assumes form is validated alreday.
    ###
    updateVis: (vis) ->
      # sMatch = @$spreadsheetInput.val().match(/\?key=(.*)/)
      newSpreadsheet = @_spreadsheetId  #@$spreadsheetInput.val().split('?key=')[1].split('&')[0]
      if null == newSpreadsheet
        gButter.showError('Invalid spreadsheet URL.')
        console.log 'invalid'
        return false
      # newSpreadsheet = sMatch[1]
      oldSpreadsheet = vis.url
      oldID = vis.id
      data = @$formData.serialize()     # Trailing slash is vital.
      $.post '/update/' + vis.id + '/', data, =>
        gButter.show('Updated.')
        # Refresh if spreadsheet changed and still viewing current graph.
        if (newSpreadsheet != oldSpreadsheet) # && gCurrentGraphID == cachedGraphID)
          setTimeout (=> gView.refresh()), 100
        newName = @$nameInput.val()
        # Update local data model and DOM.
        vis.name = newName
        vis.entry.find('.vis-entry-name').html newName
        vis.url = newSpreadsheet
        vis.isPublic = @$publicInput.checked
        @view.$name.html newName
      gButter.showPersist('Updating visualization details...')
      true

    # Delete a visualization from the index.
    deleteVis: (vis) ->
      data = @$formData.serialize()
      id = vis.id
      name = vis.name
      console.log 'Deleting ' + vis.id
      $.post '/delete/' + vis.id + '/', data, =>
        console.log 'deleted ' + id
        vis.entry.remove()
        gIndex.remove vis
        gButter.show 'Deleted "' + name + '".'
      .fail =>
        console.error 'failed to delete!'
        gButter.showError 'Failed to delete.'
        vis.entry.removeClass('deleting')
      # Remove from the DOM prematurely.
      gButter.showPersist 'Deleting "' + vis.name + '"...'
      vis.entry.addClass('deleting')


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
      return false if not id

      @_loadURL('/view/' + id + '/standalone')
      @currentID = id
      vis = @visIndex.visByID[id]
      @$name.html vis.name if vis

    # Load a url into the AJAX viewport.
    # Requires the target URL to have a div #ajax-view.
    _loadURL: (url) ->
      console.log 'Loading AJAX: ' + url
      @$view.load url + ' #ajax-view', =>
        @$loading.hide()
        if not @_visCodeLoaded
          @_visCodeLoaded = true
          console.log 'Loading vis scripts...'
          require ['cs!vis']
        else
          window.initVisualization VIS_ID
      @$view.removeClass('hidden')
      @$view.show()

    # Refresh the currently viewed graph.
    refresh: () ->
      return if not @currentID

      cachedGraphID = @currentID  # In case user loads another graph.
      $.get '/refresh/' + @currentID + '/', [], () =>
        # Success callback which updates butterbar and DOM.
        $('#btn-refresh').removeClass('disabled')
        gButter.show('Visualization data refreshed!')
        if cachedGraphID is @currentID
          @show @currentID
      # $('#btn-refresh').addClass('disabled')
      # hideToolTip($('#tooltip-refresh'))
      gButter.showPersist('Refreshing data from spreadsheet...')

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
      @_timer = undefined

    # Shows a butterbar message. Defaults to auto-hiding after a short while.
    show: (message, autohide=true) ->
      return if not message
      @reset()
      this.text.html message
      this.bar.removeClass 'hidden'
      # Anytime a new message is shown, override any previous autohide timers since
      # they're no longer relevant.
      if @_timer
        clearTimeout @_timer
        @_timer = undefined
      if autohide
        @_timer = setTimeout =>
          @bar.addClass 'hidden'
          @_timer = undefined
        , @TIMEOUT_MS

    showPersist: (message) -> @show(message, autohide=false)

    showError: (message) ->
      @reset()
      @showPersist('ERROR: ' + message)
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

  returnToIndex = null

  # Opens up a visualization and prepares all state.
  viewVisualization = (vis) ->
    vis.entry.addClass 'selected'
    gActions.show()
    console.log('showing', vis)
    # Slightly delay the actual loading of the visualization.
    # window.setTimeout (=> gView.show(vis.id)), 300
    gView.show(vis.id)
    # Change spreadsheet target.
    console.log vis
    gActions.$docs.attr(
        'href',
        'https://docs.google.com/spreadsheet/ccc?key=' + vis.url)

    # hideHelp()
    # To be closed upon successful loading, or an error message appears.
    # if id isnt gCurrentGraphID
      # gButter.show('Loading...', false)
    # Use pushState to update the browser's URL.
    window.history.pushState({}, null, '/view/' + vis.id)
    window.addEventListener 'popstate', (e) =>
      # Allow the back-button to restore previous state.
      e.preventDefault()
      returnToIndex()

  # Installs the click handler on a visualization entry in the index.
  hookVisEntry = (vis) -> vis.entry.click => viewVisualization vis

  getCurrentVisualization = -> gIndex.visByID[gView.currentID]

  # Prepare all AJAX / DOM / event handlers.
  domReady ->
    # Prepare required state-holders.
    gButter = new ButterBar()
    gActions = new VisActions()
    gIndex = new VisIndex()
    gView = new View(gIndex)
    gForm = new VisForm(gView)

    # This function should be called anytime when the original visualization
    # index view wants to be restored.
    returnToIndex = ->
      currentVis = getCurrentVisualization()
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
    _.each _.values(gIndex.visByID), (vis) -> hookVisEntry vis

    $back = $ '#btn-back'
    $back.click (e) ->
      e.preventDefault()
      if gView.editMode
        # Return to view mode.
        gView.editMode = false
        gForm.hide()
        fadeShow gActions.$viewMode
        gActions.$edit.focus()
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
      valid = gForm.validate()
      return false if not valid

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

    $refresh = $ '#btn-refresh'
    $refresh.click (e) ->
      e.preventDefault()
      gView.refresh()

    $embed = $ '#btn-embed'
    $embed.click (e) ->
      e.preventDefault()
      gActions.toggleShareBox()

    $saveNodes = $ '#btn-save-positions'
    $saveNodes.click (e) ->
      e.preventDefault()
      # This function lives inside graph.coffee.
      # queryString = gView.$frame[0].contentWindow.getPositionQuery()
      queryString = window.getPositionQuery()
      updateUrl = '?' + queryString
      window.history.pushState({}, 'unused', updateUrl)
      # TODO(keroserene): Push changes to the underlying document.

    $docs = $ '#btn-docs'

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
    hookTooltip $back, 'back'
    hookTooltip $edit, 'edit'
    hookTooltip $refresh, 'refresh visualization'
    hookTooltip $embed, 'share'
    hookTooltip $docs, 'open underlying spreadsheet'
    hookTooltip $saveNodes, 'save node positions'

    # Catch 'escape' events as 'going backwards'
    $(document).keydown (e) ->
      if e.keyCode is 27
        if gActions.shareBoxVisible
          gActions.toggleShareBox()
        else
          $back.click()

    # Primary button handlers.
    # The "save" button switches innerHTML between "Save" and "Create"
    # depending on if the opened dialogue is an edit or a new visualization.
    gForm.$delete.click (e) ->
      e.preventDefault()
      vis = gIndex.visByID[gView.currentID]
      gForm.deleteVis(vis)
      returnToIndex()

    ###
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

    # Auto-view visualization if specified in URL.
    if VIS_ID
      viewVisualization gIndex.visByID[VIS_ID]
      gActions.show()
    else
      gIndex.show()
