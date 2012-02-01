var URL = '/';

module('basic tests');

test('simple text upload works', function() {
  var requestData = {
    composer: 'Radiohead',
    title: 'Karma Police',
    label: 'tab1',
    notation: 'tab',
    text: 'hello world'
  };
  stop(2000);
  $.ajax({
    type: 'POST',
    url: URL,
    data: requestData,
    success: function(responseData, textStatus, jqXHR) {
      start();
      ok(true, 'good response');
    },
    error: function(e) {
      start();
      ok(false, 'error ' + e.status);
    }
  });
});

test('simple PDF upload works', function() {
});

test('simple PDF URL upload works', function() {
});


module('validation tests');

test('upload fails with missing field', function() {
});

test('upload fails when no XOR fields are specified', function() {
});

test('upload fails when multiple XOR fields are specified', function() {
});

test('upload fails when invalid file specified', function() {
});

test('upload fails when an invalid URL is specified', function() {
});
