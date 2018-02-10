$(function() {
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

  var morphApiUrl = 'https://api.morph.io/andylolz/org-id-finder/data.json';
  var morphApiKey = 'wFTSIH61nwMjLBhphd4T';

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
        return 'Searching...';
      },
      searching: function(params) {
        search_query = params;
        return 'Searching...';
      }
    },
    placeholder: 'E.g. Publish What You Fund',
    minimumInputLength: 2,
    ajax: {
      url: morphApiUrl,
      dataType: 'jsonp',
      data: function (params) {
        var query = {
          key: morphApiKey,
          query: 'SELECT * FROM "organisations" WHERE (`name` LIKE "%' + params.term + '%" OR `org_id` LIKE "%' + params.term +  '%") AND `self_reported` = 1 LIMIT 5'
        };
        return query;
      },
      processResults: function (data) {
        var results = $.map(data, function(d) {
          var text = d.name;
          var hash = d.org_id;
          if (d.name_en !== '') {
            text = text + ' (' + d.name_en + ')';
            hash = hash + '%20' + d.lang;
          }
          return {
            id: d.org_id,
            text: text,
            hash: hash,
            source_url: d.source_url,
            source_dataset: d.source_dataset
          };
        });
        return {
          results: results
        };
      }
    }
  });

  var pageHash = window.location.hash.substr(1);
  if (pageHash !== '') {
    var pageHashArr = pageHash.split('%20');
    var org_id = pageHashArr[0];
    var lang = 'en';
    if (pageHashArr.length > 1) {
      lang = pageHashArr[1];
    }
    $.get({
        url: morphApiUrl,
        dataType: 'jsonp',
        data: {
          key: morphApiKey,
          query: 'SELECT * FROM "organisations" WHERE `org_id` = "' + org_id + '" AND lang = "' + lang + '" AND `self_reported` = 1'
        }
    }).then(function (d) {
      if (d.length === 0) {
        clearHash();
      } else {
        d = d[0];
        var text = d.name;
        var hash = d.org_id;
        if (d.name_en !== '') {
          text = text + ' (' + d.name_en + ')';
          hash = hash + '%20' + d.lang;
        }
        var data = {
          id: d.org_id,
          text: text,
          hash: hash,
          source_url: d.source_url,
          source_dataset: d.source_dataset
        };

        // create the option and append to Select2
        var option = new Option(d.name, d.id, true, true);
        orgSelect.append(option).trigger('change');

        // manually trigger the `select2:select` event
        orgSelect.trigger({
            type: 'select2:select',
            params: {
                data: data
            }
        });
      }
    });
  }

  orgSelect.on('select2:select', function(e) {
    // hack to fix a bug with select2
    var $selected = $('#select2-org-select-container');
    $selected.attr('title', e.params.data.text);
    $selected.text(e.params.data.text);

    var identifier = e.params.data.id;
    var sourceUrl = e.params.data.source_url;
    var sourceDataset = e.params.data.source_dataset;

    window.location.hash = e.params.data.hash;

    var previewUrl = 'http://preview.iatistandard.org/index.php?url=' + encodeURIComponent(sourceUrl);
    var registryUrl = 'https://iatiregistry.org/dataset/' + sourceDataset;

    $('#source-preview').attr('href', previewUrl);
    $('#source-raw').attr('href', sourceUrl);
    $('#source-registry').attr('href', registryUrl);

    $('#org-identifier').val(identifier);
    $('#org-identifier-group').css('visibility', 'visible').hide().fadeIn('slow');
    $('body').animate({
      backgroundColor: '#353'
    }, 200, function() {
      $(this).animate({
        backgroundColor: '#333'
      }, 200);
    });
  });

  orgSelect.on('select2:open', function() {
    if ($(this).val() !== null) {
      $(this).val(null).trigger('change');
      clearHash();
    }
    $('#org-identifier-group').css('visibility', 'hidden');
  });

  var clipboard = new Clipboard('#copy-button');
  clipboard.on('success', function() {
    $('#copy-button').tooltip('show');
    setTimeout(function () {
      $('#copy-button').tooltip('destroy');
    }, 500);
  });

  $.ajax({
      url: morphApiUrl,
      dataType: 'jsonp',
      data: {
        key: morphApiKey,
        query: 'SELECT `finished_at` FROM "status" WHERE `success` = 1 ORDER BY `finished_at` DESC LIMIT 1'
      }
  }).done(function(val) {
    var now = new Date();
    var last_updated = new Date(val[0].finished_at);
    var hours_ago = Math.round((now - last_updated) / 3.6e6);
    var updated_str = hours_ago + ' hour' + ((hours_ago === 1) ? '' : 's') + ' ago';
    $('#last-updated').text(' (last updated: ' + updated_str + ')');
  });
});
