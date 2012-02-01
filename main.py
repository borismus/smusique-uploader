from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import conversion
from google.appengine.api import urlfetch

import os
import S3
import simplejson


AWS_ACCESS_KEY_ID = 'AKIAJAA44SMSVX4D34NQ'
AWS_SECRET_ACCESS_KEY = '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'
URL_FORMAT = 'https://s3.amazonaws.com/%(bucket)s/%(path)s'
DEFAULT_BUCKET = 'uploader'


# From http://goo.gl/8Lqdi:
import urlparse, urllib
def fixurl(url):
    # turn string into unicode
    if not isinstance(url,unicode):
        url = url.decode('utf8')

    # parse it
    parsed = urlparse.urlsplit(url)

    # divide the netloc further
    userpass,at,hostport = parsed.netloc.partition('@')
    user,colon1,pass_ = userpass.partition(':')
    host,colon2,port = hostport.partition(':')

    # encode each component
    scheme = parsed.scheme.encode('utf8')
    user = urllib.quote(user.encode('utf8'))
    colon1 = colon1.encode('utf8')
    pass_ = urllib.quote(pass_.encode('utf8'))
    at = at.encode('utf8')
    host = host.encode('idna')
    colon2 = colon2.encode('utf8')
    port = port.encode('utf8')
    path = '/'.join(  # could be encoded slashes!
        urllib.quote(urllib.unquote(pce).encode('utf8'),'')
        for pce in parsed.path.split('/')
    )
    query = urllib.quote(urllib.unquote(parsed.query).encode('utf8'),'=&?/')
    fragment = urllib.quote(urllib.unquote(parsed.fragment).encode('utf8'))

    # put it back together
    netloc = ''.join((user,colon1,pass_,at,host,colon2,port))
    return urlparse.urlunsplit((scheme,netloc,path,query,fragment))



class UploadHandler(webapp.RequestHandler):

    def get(self):
        self.response.out.write('Upload!')


    def post(self):
        request = simplejson.loads(self.request.body)
        path = request["path"]
        content = request["content"]
        # Make an upload request to S3.
        url = createTextFile(path, content)
        output = {
          'url': url
        }
        self.response.out.write(simplejson.dumps(output))

class PdfUrlHandler(webapp.RequestHandler):

    def get(self):
        self.response.out.write('Upload PDF!')


    def error(self, error):
        out = {'error': error}
        self.response.out.write(simplejson.dumps(output))
        return


    def post(self):
        request = simplejson.loads(self.request.body)
        path = request["path"]
        url = request["url"]
        # Fetch the PDF at URL.
        result = urlfetch.fetch(url)
        if result.status_code != 200:
            return self.error('error %s fetching pdf at URL %s' %
                    (result.status_code, url))
        # Convert PDF to images, one per page.
        input_data = result.content
        input_type = 'application/pdf'
        input_name = 'sheet'
        output_type = 'image/png'
        conversion_request = conversion.ConversionRequest(
            conversion.Asset(input_type, input_data, input_name), output_type)
        result = conversion.convert(conversion_request)
        if not (result and result.assets):
            return self.error('problem converting PDF to PNGs')

        urls = []
        # Upload images to S3.
        for i, r in enumerate(result.assets):
            # Get the path to upload to.
            upload_path = (path + '/' + str(i)).encode('UTF-8')
            # Upload each image to S3 and record its URL.
            url = fixurl(createImageFile(upload_path, r.data))
            urls.append(url)
        # Return with an array of URLs:
        output = {
          'urls': urls,
        }
        self.response.out.write(simplejson.dumps(output))
        #self.response.out.write(result.assets[0].data)


class UploadInfo:

    def __init__(self, request):
        """Reads all known fields from the request."""
        self.composer = request.get('composer')
        self.title = request.get('title')
        self.label = request.get('label')
        self.notation = request.get('notation')
        # XOR fields
        self.text = request.get('text')
        self.pdf = request.get('pdf')
        self.pdfurl = request.get('pdfurl')
        # Optional fields
        self.rating = request.get('rating')

    def validate(self):
        """Validates the request to make sure all of the required fields exist,
        and only one XOR field is specified. Returns True iff valid."""
        message = ''
        required = self.composer and self.title and self.label \
            and self.notation

        if not required:
            message = 'Some required variables are not specified.'

        xor = (self.text and not self.pdf and not self.pdfurl) or \
            (not self.text and self.pdf and not self.pdfurl) or \
            (not self.text and not self.pdf and self.pdfurl)

        if not xor:
            message = 'Error with exclusive variables.' + self.text

        return (required and xor, message)

    def get_path(self):
        """Returns the path for uploading to S3."""
        return self.composer + '/' + self.title + '/' + self.label

    def is_pdf_url(self):
        """Return True iff it's a PDF URL."""
        return bool(self.pdfurl)

    def is_pdf_binary(self):
        """Return True iff it's a PDF URL."""
        return bool(self.pdf)

    def is_text(self):
        """Return True iff it's a text."""
        return bool(self.text)


class MainHandler(webapp.RequestHandler):

    def get(self):
        """Renders an upload form."""
        self.redirect('/upload/')

    def post(self):
        """Handles a request to upload stuff. This can come from the form or
        from an external source."""
        info = UploadInfo(self.request)
        # Validate all of the required fields.
        (is_valid, error) = info.validate()
        if not is_valid:
            # If invalid, return an error.
            return self.create_error(500, error);

        urls = []
        # Check which case we're dealing with (plaintext, pdf or pdf_url):
        if info.is_text():
            # Upload the content to S3.
            url = self.upload_text(info.get_path(), info.text)
            # Get the URL of the uploaded content.
            urls = [url]

        if info.is_pdf_binary():
            # Get the binary PDF from the request.
            pdf = self.request.get('pdf')
            # Convert PDF to images.
            images = self.convert_pdf(pdf)
            # Upload each image to the appropriate place in S3.
            for image in images:
                url = self.upload_image(info.get_path(), image)
                urls.append(url)

        if info.is_pdf_url():
            # Make a request to get the PDF by URL.
            # (same as above)
            pass

        # Create database entry in smusique.
        result = self.create_db_entry(info, urls)
        if result:
            self.response.out.write('Upload successful')
        else:
            self.create_error(500, 'database creation failed')

    def create_error(self, code, message):
        self.error(code);
        self.response.out.write(message)

    def upload_image(self, path, image_data):
        """Uploads image data to S3 on the given path. Returns URL of the
        uploaded image."""
        self.upload_helper(path, image_data, 'image/pdf')

    def upload_text(self, path, text):
        """Uploads text data to S3 on the given path. Returns URL of the
        uploaded text."""
        self.upload_helper(path, text, 'text/plain')

    def upload_helper(self, path, data, contentType):
        conn = S3.AWSAuthConnection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        options = {'x-amz-acl': 'public-read', 'Content-Type': contentType}
        response = conn.put(DEFAULT_BUCKET, path, S3.S3Object(data), options)
        return URL_FORMAT % {'bucket': DEFAULT_BUCKET, 'path': path}

    def convert_pdf(self, pdf_data):
        """Converts PDF to PNG images. Returns an array of PNG data."""
        return []

    def create_db_entry(self, info, urls):
        """Creates a smusique.com database entry for the info and the
        associated URLs. Returns True iff successful."""
        return False
#function addToDB(info, urls, callback) {
#  // Create an entry in the database.
#  // -d '{"title": "Karma Police", "composer": "RRadiohead", "label": "tab2", "notation": "tab", "urls": ["/foo/aaaee.txeeet"], "rating": 34}'
#  var xhr = new XMLHttpRequest();
#  xhr.open('POST', 'http://smusiclib.appspot.com/version/');
#  xhr.addEventListener('load', function() {
#    if (this.status == 200) {
#      var result = JSON.parse(this.response);
#      callback(result);
#    }
#  });
#  var data = JSON.stringify({
#    title: info.title,
#    composer: info.composer,
#    notation: info.type,
#    rating: info.rating,
#    label: info.label,
#    urls: urls
#  });
#  xhr.send(data);
#}


def main():
    application = webapp.WSGIApplication([('/', MainHandler)], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
