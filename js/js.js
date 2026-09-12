$(window).on('load', function() {
  function clearHash() {
    if ('pushState' in history) {
      history.pushState('', document.title, window.location.pathname);
    } else {
      window.location.hash = '';
    }
  }

  // from: https://stackoverflow.com/questions/28958620/using-select2-4-0-0-with-infinite-data-and-filter#29018243
  function markMatch(text, term) {
    // Find where the match is
    var match = text.toUpperCase().indexOf(term.toUpperCase());

    var $result = $('<span></span>');

    // If there is no match, move on
    if (match < 0) {
      return $result.text(text);
    }

    // Put in whatever text is before the match
    $result.text(text.substring(0, match));

    // Mark the match
    var $match = $('<span class="select2-rendered__match"></span>');
    $match.text(text.substring(match, match + term.length));

    // Append the matching text
    $result.append($match);

    // Put in whatever is after the match
    $result.append(text.substring(match + term.length));

    return $result;
  }

  var orgSelect = $('#org-select').select2({
    theme: 'bootstrap',
    templateResult: function(item) {
      if (item.loading) {
        return item.text;
      }

      var term = search_query.term || '';
      var $highlightedName = markMatch(item.text, term);
      $highlightedName = $highlightedName.addClass('select2-rendered__name');
      var $highlightedOrgID = markMatch(item.id, term);
      $highlightedOrgID = $highlightedOrgID.addClass('select2-rendered__org_id');

      return $('<span>').append($highlightedName, $highlightedOrgID);
    },
    language: {
      errorLoading: function() {
        return 'No results found';
      },
      searching: function(params) {
        search_query = params;
        return 'Searching...';
      }
    },
    placeholder: 'E.g. Publish What You Fund',
    minimumInputLength: 3,
    ajax: {
      delay: 100,
      url: function (params) {
        var lookup = params.term.substr(0, 3);
        return '/data/lookup/' + encodeURIComponent(lookup) + '.json';
      },
      processResults: function (data, params) {
        data = data.filter(function (d) {
          var lowerTerm = params.term.toLowerCase();
          return d[0].toLowerCase().indexOf(lowerTerm) !== -1 || d[1].toLowerCase().indexOf(lowerTerm) !== -1;
        });
        var results = $.map(data, function (d) {
          var text = d[0];
          var org_id = d[1];
          return {
            id: org_id,
            text: text
          };
        });
        return {
          results: results
        };
      }
    }
  });

  orgSelect.on('select2:select', function(e) {
    // hack to fix a bug with select2
    var $selected = $('#select2-org-select-container');
    $selected.attr('title', e.params.data.text);
    $selected.text(e.params.data.text);

    var encodedId = encodeURIComponent(e.params.data.id);
    $.get('/data/' + encodedId + '.json').done(function (data) {
      if ($selected.text() === '') {
        $selected.text(data.name[data.lang]);
      }
      var identifier = data.org_id;
      var org_type_code = data.org_type_code;
      var org_type = data.org_type;
      if (org_type) {
        org_type = org_type + ' (' + org_type_code + ')';
      }
      var sourceUrl = data.source_url;
      var sourceDataset = data.source_dataset;

      window.location.hash = encodedId;

      var previewUrl = 'http://preview.iatistandard.org/index.php?url=' + encodeURIComponent(sourceUrl);
      var registryUrl = 'https://iatiregistry.org/dataset/' + sourceDataset;

      $('#source-preview').attr('href', previewUrl);
      $('#source-raw').attr('href', sourceUrl);
      $('#source-registry').attr('href', registryUrl);

      $('#org-identifier').val(identifier);
      $('#org-type').val(org_type);
      $('#org-identifier-group').css('visibility', 'visible').hide().fadeIn('slow');
    }).fail(function () {
      $(this).val(null).trigger('change');
      clearHash();
    });
  });

  orgSelect.on('select2:open', function() {
    $(this).val(null).trigger('change');
    clearHash();
    $('#org-identifier-group').css('visibility', 'hidden');
  });

  var pageHash = window.location.hash.substr(1);
  if (pageHash !== '') {
    var id = decodeURIComponent(pageHash);
    $('#org-select').val(id);
    $('#org-select').trigger({
      type: 'select2:select',
      params: {
        data: {
          id: id,
          text: ''
        }
      }
    });
  } else {
    orgSelect.select2('open');
  }

  var clipboard = new ClipboardJS('#copy-button');
  clipboard.on('success', function(e) {
    $('#copy-button').tooltip('show');
    e.clearSelection();
    setTimeout(function () {
      $('#copy-button').tooltip('dispose');
    }, 1000);
  });

  $.get('/data/status.json').done(function (val) {
    var now = new Date();
    var last_updated = new Date(val.finished_at);
    var hours_ago = Math.round((now - last_updated) / 3.6e6);
    var updated_str = hours_ago + ' hour' + ((hours_ago === 1) ? '' : 's') + ' ago';
    $('#last-updated').text(' (last updated: ' + updated_str + ')');
  });
});
