$(function() {
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
      var $highlightedText = markMatch(item.text, term);
      var $highlightedCode = markMatch(item.id, term);
      $highlightedCode = $highlightedCode.addClass('select2-rendered__code');

      return $highlightedText.append($highlightedCode);
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
      url: 'https://api.morph.io/andylolz/org-id-finder/data.json',
      dataType: 'jsonp',
      data: function (params) {
        var query = {
          key: 'wFTSIH61nwMjLBhphd4T',
          query: 'SELECT * FROM "organisations" WHERE `name` LIKE "%' + params.term + '%" OR `code` LIKE "%' + params.term +  '%" LIMIT 5'
        };
        return query;
      },
      processResults: function (data) {
        var results = $.map(data, function(d) {
          var text = d.name;
          if (d.name_en !== '') {
            text = text + ' (' + d.name_en + ')';
          }
          return {
            id: d.code,
            text: text,
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

  orgSelect.on('select2:select', function(e) {
    // hack to fix a bug with select2
    var $selected = $('#select2-org-select-container');
    $selected.attr('title', e.params.data.text);
    $selected.text(e.params.data.text);

    var identifier = e.params.data.id;
    var sourceUrl = e.params.data.source_url;
    var sourceDataset = e.params.data.source_dataset;

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
});
