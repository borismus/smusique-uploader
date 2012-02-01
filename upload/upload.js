var form = document.querySelector('form');
form.addEventListener('submit', onSubmit);

function onSubmit(e) {
  e.preventDefault();
  console.log('submitting...');
  var file = form.upload.files[0];
  var formData = new FormData();
  var url = form.title.value.trim() + '/' + form.composer.value.trim() + '/' +
      form.label.value.trim();
  formData.append("pdf", file);
  formData.append("url", url);

  var xhr = new XMLHttpRequest();
  xhr.open('POST', 'http://file-upload-proxy.appspot.com/pdfdata/');
  xhr.send(formData);
}
