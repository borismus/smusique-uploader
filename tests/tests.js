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
      ok(false, 'error ' + e.status + ' ' + e.responseText);
    }
  });
});

test('simple PDF url upload works', function() {
  var requestData = {
    composer: 'Bach, Johann Sebastian',
    title: 'Prelude Test Upload',
    label: 'tab1',
    notation: 'piano',
    pdfurl: 'http://imslp.info/files/imglnks/usimg/e/e7/IMSLP94668-PMLP05948-Bach_Praeludium_No_1_in_C-Mjaor__RSB_.pdf'
  };
  stop(5000);
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
      ok(false, 'error ' + e.status + ' ' + e.responseText);
    }
  });
});

test('simple PDF binary upload works', function() {
});


module('validation tests');

test('upload fails with missing field', function() {
  var requestData = {
    composer: 'Bach, Johann Sebastian',
    title: 'Prelude 1',
    notation: 'piano',
    pdfurl: 'http://imslp.info/files/imglnks/usimg/e/e7/IMSLP94668-PMLP05948-Bach_Praeludium_No_1_in_C-Mjaor__RSB_.pdf'
  };
  stop(2000);
  $.ajax({
    type: 'POST',
    url: URL,
    data: requestData,
    success: function(responseData, textStatus, jqXHR) {
      start();
      ok(false, 'error did not fire!');
    },
    error: function(e) {
      start();
      ok(true, 'expect an error since label field was missing');
    }
  });
});

test('upload fails when no XOR fields are specified', function() {
  var requestData = {
    composer: 'Bach, Johann Sebastian',
    title: 'Prelude 1',
    notation: 'piano',
    label: 'foo',
  };
  stop(2000);
  $.ajax({
    type: 'POST',
    url: URL,
    data: requestData,
    success: function(responseData, textStatus, jqXHR) {
      start();
      ok(false, 'error did not fire!');
    },
    error: function(e) {
      start();
      ok(true, 'expected error since no XOR fields specified');
    }
  });
});

test('upload fails when multiple XOR fields are specified', function() {
  var requestData = {
    composer: 'Bach, Johann Sebastian',
    title: 'Prelude 1',
    notation: 'piano',
    label: 'foo',
    text: 'foo',
    pdfurl: 'ble'
  };
  stop(2000);
  $.ajax({
    type: 'POST',
    url: URL,
    data: requestData,
    success: function(responseData, textStatus, jqXHR) {
      start();
      ok(false, 'error did not fire!');
    },
    error: function(e) {
      start();
      ok(true, 'expected error since multiple XOR fields specified');
    }
  });
});

test('upload fails when invalid file specified', function() {
});

test('upload fails when an invalid URL is specified', function() {
  var requestData = {
    composer: 'Bach, Johann Sebastian',
    title: 'Prelude 1',
    notation: 'piano',
    label: 'foo',
    pdfurl: 'htp:/www.google.com'
  };
  stop(2000);
  $.ajax({
    type: 'POST',
    url: URL,
    data: requestData,
    success: function(responseData, textStatus, jqXHR) {
      start();
      ok(false, 'error did not fire!');
    },
    error: function(e) {
      start();
      ok(true, 'expect an error since invalid URL specified');
    }
  });
});
