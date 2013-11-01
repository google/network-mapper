// Description: Single-Page UI for network visualizer.
// Author: keroserene@google.com  (Serene Han)

define(['domReady', 'jQuery'], function (domReady, $) {
  var ENTRY_ID_PREFIX = 'v-';
  var NOHOVER_TIMEOUT = 100;

  var gDOM = null;
  var gView = null;
  var gButter = null;

  var gGraphs = {};        // Dict of ID -> Name
  var gSpreadsheets = {};  // Dict of ID -> Spreadsheet Key
  var gIsPublic = {};      // Dict of ID -> Is Public

  var gCurrentGraphID = 0;
  var gEditMode = false;

  /**
   * Class which maintains specific DOM operations and state.
   */
  var DOM = function(options) {};
  DOM.prototype.rememberDOM = function() {
    // Remember DOM references.
    this.btnbar = $('#btnbar');
    this.help = $('#help');
    this.editPane = $('#edit-pane');
    this.saveBtn = $('#btn-save');
    this.graphFrame = $('.vis-frame');
  };

  /**
   * State-holding class for NetworkX primary viewport.
   */
  var View = function(options) {
    this.$view = $('#view');
    this.$frame = $('#ajax-view').find('.vis-frame');
  };

  /**
   * Load a url into the AJAX viewport.
   * Requires the target URL to have a div #ajax-view.
   */
  View.prototype.loadURL = function(url) {
    var _this = this;
    this.$view.load(url + ' #ajax-view', function() {
      gButter.hide();
      _this.$frame = $('#ajax-view').find('.vis-frame');
    });
    this.$view.removeClass('hidden');
    this.$view.show();
  };

  /**
   * Clears everything from the AJAX viewport. Used prior to loading any new
   * view, or when opening the create visualization pane.
   */
  View.prototype.clear = function() {
    $('.vis-entry').filter('.selected').removeClass('selected');
    this.$view.empty();
    this.$view.hide();
    // Conceal any open dialogues.
    if ($('#btn-embed').hasClass('active')) {
      toggleEmbedLink();
    }
  };


  /**
   * Class describing the butterbar for temporary feedback messages.
   */
  var ButterBar = function() {
    var self = this;
    self.TIMEOUT_MS = 1800;
    self.bar = $('#butterbar');
    self.text = $('#butterbar-text');
    self.dismissButton = $('#butterbar-dismiss');
    self.dismissButton.click(function() { self.hide(); });
  }

  ButterBar.prototype.show = function(message, autohide) {
    if (!message) {
      return;
    }
    this.reset();
    if (undefined === autohide) {
      autohide = true;
    }
    // console.log(msg);
    this.text.html(message);
    this.bar.removeClass('hidden');
    if (autohide) {
      var self = this;
      this.timeout = setTimeout(function() {
        self.bar.addClass('hidden');
      }, this.TIMEOUT_MS);
    }
  }

  ButterBar.prototype.showError = function(message) {
    this.reset();
    this.show('ERROR: ' + message, false);
    this.bar.addClass('error');
    this.dismissButton.removeClass('hidden');
    this.dismissButton.show();
  }

  ButterBar.prototype.hide = function() {
    this.bar.addClass('hidden');
  }

  ButterBar.prototype.reset = function() {
    if (this.timeout) {
      window.clearTimeout(this.timeout);
    }
    this.bar.removeClass('error');
    this.dismissButton.addClass('hidden');
    this.dismissButton.hide();
    this.text.html('');
  }


  // Hook |entry| (DOM element) to open up a single visualization view.
  function hookGraphEntry(entry, id) {
    var id = entry.id.split('-')[1];  // IDs look like 'v-123456789'
    var name = entry.innerHTML;
    gGraphs[id] = name.trim();
    entry.onclick = function() {
      viewGraph(id);
      $('.vis-entry').removeClass('selected');
      $(this).addClass('selected');
    };
  }
  // Display specific visualization, loaded via AJAX. Also reveal the buttonbar.
  function viewGraph(id) {
    window.history.pushState({}, 'unused', '/view/' + id);
    gView.loadURL('/graph/' + id);
    gDOM.btnbar.show();
    gDOM.btnbar.removeClass('hidden');
    hideHelp();
    if (id != gCurrentGraphID) {
      // To be closed upon successful loading, or an error message appears.
      gButter.show('Loading...', false);
    }
    gCurrentGraphID = id;
  }

  // When a visualization is created, prepare a new element in the Entries list
  // to indicate a new entry is being created, while awaiting for the actual
  // visualization to be readied.
  function awaitUpdate() {
    $('#vis-list').prepend(
        '<div id="pending" class="vis-entry">...</div>');
  }

  // Fetch JSON data about all existing visualization entries, and update the
  // DOM list if a new one is found.
  function refreshEntries() {
    var pending = $('#pending');
    $.getJSON('/data.json', function(data) {
      $.each(data, function(i, entry) {
        if (!pending) {
          return;
        }
        var id = entry[0];
        var name = entry[1];
        var spreadsheet = entry[2];
        gSpreadsheets[id] = spreadsheet;
        if (!(id in gGraphs)) {
          gGraphs[id] = name;
          var entryDOM = pending[0];
          pending = null;
          entryDOM.id = ENTRY_ID_PREFIX + id;
          entryDOM.innerHTML = name;
          hookGraphEntry(entryDOM);
        }
      });
      if (pending) {  // Try again if no new entry was found.
        setTimeout(refreshEntries, 500);
      }
    });
  }

  function hideButtonBar() {
    gDOM.btnbar.addClass('hidden');
    setTimeout(function () { gDOM.btnbar.hide(); }, 300);
  }

  // Handler for clicking on "CREATE VISUALIZATION".
  function prepareCreateForm() {
    gEditMode = false;
    gDOM.saveBtn.text('Create');
    gView.clear();
    showHelp();  // Also hides the button bar.
    $('#btn-delete').hide();
    $('.vis-entry').filter('.selected').removeClass('selected');
    // Clear the form.
    $('#id_name').val('');
    $('#id_spreadsheet_link').val('');
    $('#id_is_public')[0].checked = true;
    shiftSidebar();
  }

  /**
   * Handler for clicking on "EDIT".
   * Needs to update the form entries to match the parameters for the currently
   * selected visualization.
   */
  function prepareEditForm() {
    gEditMode = true;
    gDOM.saveBtn.text('Save');
    $('#btn-edit').addClass('disabled');
    $('#btn-delete').show();
    $('#id_name').val(gGraphs[gCurrentGraphID]);
    $('#id_spreadsheet_link').val(
        'https://docs.google.com/a/google.com/spreadsheet/ccc?key=' +
        gSpreadsheets[gCurrentGraphID]);
    $('#id_is_public')[0].checked = gIsPublic[gCurrentGraphID];
    $('#id_graph_id').val(gCurrentGraphID);  // For delete requests.
    shiftSidebar();
  }

  // Open the help page via AJAX.
  function showHelp() {
    hideButtonBar();
    gDOM.help.removeClass('no-hover');
    gDOM.help.removeClass('hidden');
  }
  function hideHelp() {
    gDOM.help.addClass('hidden no-hover');
  }

  function saveOrCreate() {
    // TODO(keroserene): Pre-validate spreadsheet url/format?
    if (!validEntry('id_name', 'Please name your visualization.') ||
        !validEntry('id_spreadsheet_link',
                    'Please provide a valid spreadsheet link.')) {
      return;
    }
    var success = false;
    if (gEditMode) {
      success = updateGraph();
    } else {  // CREATE_MODE
      success = createGraph();
      awaitUpdate();
    }
    if (success) {
      resetSidebar();
    }
  }

  // Validates a form text entry. Returns true if valid, false otherwise.
  function validEntry(entry_id, error_msg) {
    var entry = $('#' + entry_id);
    if (!entry.val()) {
      gButter.show(error_msg);
      entry.focus();
      return false;
    }
    return true;
  }

  /**
   * Send AJAX POST to create new graph, update local DOM to indicate
   * loading and new graph.
   */
  function createGraph() {
    var data = $('#vis-form').serialize();
    // The trailing slash is /graph/create/ is important.
    $.post('/graph/create/', data, function() {
        gButter.show('Finished creation.');
        setTimeout(refreshEntries, 100);
    });
    var name = $('#id_name').val();
    gButter.show('Creating new visualization "' + name  + '"...', false);
    return true;
  }

  /**
   * Update the details of a visualization. If the spreadsheet is changed, also
   * reloads data and refreshes the page.
   *
   * @return True on success, False otherwise.
   */
  function updateGraph() {
    var data = $('#vis-form').serialize();
    var oldSpreadsheet = gSpreadsheets[gCurrentGraphID];
    var sMatch = $('#id_spreadsheet_link').val().match(/ccc\?key=(.*)/);
    if (null == sMatch) {
      gButter.showError('Invalid spreadsheet URL.');
      return false;
    }
    var newSpreadsheet = sMatch[1];
    var cachedGraphID = gCurrentGraphID;
    // Trailing slash is vital.
    $.post('/graph/' + gCurrentGraphID + '/update/', data, function() {
      gButter.show('Update complete.');
      if (newSpreadsheet != oldSpreadsheet && gCurrentGraphID == cachedGraphID)
        setTimeout(refreshGraph, 100);
    });
    gButter.show('Updating details...', false)
    var newName = $('#id_name').val();
    // Rename without bothering with JSON.
    $('#' + ENTRY_ID_PREFIX + gCurrentGraphID).text(newName);
    gGraphs[gCurrentGraphID] = newName;
    gSpreadsheets[gCurrentGraphID] = newSpreadsheet;
    gIsPublic[gCurrentGraphID] = $('#id_is_public').checked;
    return true;
  }

  function deleteGraph() {
    var data = $('#vis-form').serialize()
    var name = gGraphs[gCurrentGraphID];
    $.post('/graph/' + gCurrentGraphID + '/delete/', data, function() {
      gButter.show('Deleted graph "' + name + '".');
    });
    $('#' + ENTRY_ID_PREFIX + gCurrentGraphID).remove();
    gView.clear();
    hideButtonBar();
    gCurrentGraphID = null;
    window.history.pushState({}, 'unused', '/');
    resetSidebar();
    gButter.show('Deleting "' + name + '"...');
    return true;
  }

  /**
   * Send a refresh-data request for the current graph.
   */
  function refreshGraph() {
    var cachedGraphID = gCurrentGraphID;  // In case user loads another graph.
    $.get('/graph/' + gCurrentGraphID + '/reload/', [], function() {
      // Success callback which updates the butterbar and DOM.
      $('#btn-refresh').removeClass('disabled');
      gButter.show('Visualization data refreshed!');
      if (cachedGraphID == gCurrentGraphID) {
        viewGraph(gCurrentGraphID);
      }
    });
    $('#btn-refresh').addClass('disabled');
    hideToolTip($('#tooltip-refresh'));
    gButter.show('Refreshing data from spreadsheet...', false);
  }

  function shiftSidebar() {
    $('#sidebar').addClass('widened');
    $('#sidebar-content').addClass('shifted');
    gDOM.editPane.show();
  }
  function resetSidebar() {
    $('#sidebar').removeClass('widened');
    $('#sidebar-content').removeClass('shifted');
    gDOM.editPane.hide();
    $('#btn-edit').removeClass('disabled');
    hideHelp();
  }

  function showToolTip(element) {
    element.removeClass('no-hover');
    setTimeout(function() {
      element.removeClass('hidden');
    }, NOHOVER_TIMEOUT);
  }

  function hideToolTip(element) {
    element.addClass('hidden');
    setTimeout(function() {
      element.addClass('no-hover');
    }, NOHOVER_TIMEOUT);
  }

  // Toggles the embed link. Auto-updates and selects code if needed.
  function toggleEmbedLink() {
    $('#btn-embed').toggleClass('active');
    var embedCode = '<iframe src="' + HOSTNAME + '/graph/' +
                    gCurrentGraphID + '/embed/" ' +
                    'width="1000" height="600"></iframe>';
    var snippet = $('#snippet');
    snippet.text(embedCode);
    snippet.toggleClass('hidden');
    if (!snippet.hasClass('hidden')) {
      snippet.select();
    }
  }

  /**
   * Prepare all AJAX / DOM / event handlers.
   */
  domReady(function () {
    // Prepare required state-holders.
    gDOM = new DOM();
    gView = new View();
    gButter = new ButterBar();

    gDOM.rememberDOM();

    // Obtain data about all user visualizations in order to populate list.
    $.getJSON('/data.json', function(data) {
      $.each(data, function(i, entry) {
        var id = entry[0];
        gGraphs[id] = entry[1];   // The graph's name.
        gSpreadsheets[id] = entry[2];
        gIsPublic[id] = entry[3];
      });
    });


    // Install a view handler for each graph entry.
    $.each($('.vis-entry'), function(i, entry) {
      hookGraphEntry(entry);
    });
    if (GRAPH_ID) {  // If initially loaded from django template.
      gCurrentGraphID = GRAPH_ID;
    }

    // Primary button handlers.
    $('#btn-create').click(prepareCreateForm);
    $('.btn-cancel').click(resetSidebar);
    // The "save" button switches innerHTML between "Save" and "Create"
    // depending on if the opened dialogue is an edit or a new visualization.
    $('#btn-save').click(saveOrCreate);
    $('#btn-edit').click(prepareEditForm);
    $('#btn-delete').click(deleteGraph);
    $('#btn-refresh').click(refreshGraph);
    $('#btn-embed').click(toggleEmbedLink);

    $('#btn-save-positions').click(function () {
      var queryString = gView.$frame[0].contentWindow.getPositionQuery();
      var updateUrl = '?' + queryString;
      window.history.pushState({}, 'unused', updateUrl);
      // TODO(keroserene): Push changes to the underlying document.
    });

    // Tooltips.
    $('#btn-refresh').hover(
      function() { showToolTip($('#tooltip-refresh')); },
      function() { hideToolTip($('#tooltip-refresh')); });

    // Help
    $('#link-help').click(function(ev) {
      ev.preventDefault();
      window.history.pushState({}, 'unused', '/help/');
      showHelp();
    });

    $(document).ajaxError(function(request, text, error) {
      gButter.showError(
          'Something went wrong (' + request.responseText + ') ' +
          'OAuth probably needs to reauthorize.');
      $('#pending').remove();
      $('#btn-refresh').removeClass('disabled');
    });

    // Dark mode
    $('#darkmode').click(function() {
      var vis = gDOM.graphFrame.contents();
      // $('#visualization')
      var graph = $('.graph', vis);
      graph.addClass('dark');
      $('.node-circle', graph).attr('class', function(i, o) {
        return o.replace('node-circle', 'node-circle-dark');
      });
      $('.label-text', graph).attr('class', 'label-text-dark');
    });
  });

});
