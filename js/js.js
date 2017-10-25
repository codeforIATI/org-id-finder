$(function() {
  var orgSelect = $('#org-select').select2({
    theme: 'bootstrap',
    language: {
      errorLoading: function() {
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
          return {
            id: d.code,
            text: d.name,
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
