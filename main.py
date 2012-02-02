from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import conversion
from google.appengine.api import urlfetch


import os
import S3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


AWS_ACCESS_KEY_ID = 'AKIAJAA44SMSVX4D34NQ'
AWS_SECRET_ACCESS_KEY = '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'
URL_FORMAT = 'https://s3.amazonaws.com/%(bucket)s/%(path)s'
DEFAULT_BUCKET = 'smusique'
SMUSIQUE_UPLOAD_URL = 'http://smusiclib.appspot.com/version/'


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
        self.rating = request.get('rating') or 0

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

    def serialize(self):
        """Serializes the required info into a dictionary."""
        return {
          "composer": self.composer,
          "title": self.title,
          "label": self.label,
          "notation": self.notation,
          "rating": self.rating
        }

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
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, {}))

    def post(self):
        """Handles a request to upload stuff. This can come from the form or
        from an external source."""
        info = UploadInfo(self.request)
        # Validate all of the required fields.
        (is_valid, error) = info.validate()
        if not is_valid:
            # If invalid, return an error.
            return self.create_error(500, error);

        try:
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
                logger.info('type is %s, len is %d' %(type(pdf), len(pdf)))
                urls = self.convert_upload_helper(pdf, info.get_path())

            if info.is_pdf_url():
                # Make a request to get the PDF by URL.
                pdf = self.fetch_pdf(info.pdfurl)
                urls = self.convert_upload_helper(pdf, info.get_path())

            # Create database entry in smusique.
            self.create_db_entry(info, urls)

        except Exception as e:
            return self.create_error(500, e)

        self.response.out.write('Upload successful')

    def convert_upload_helper(self, pdf, root):
        """Converts the PDF to images, uploads the images and returns URLs of
        the images."""
        urls = []
        index = 0
        # Convert PDF to images.
        images = self.convert_pdf(pdf)
        logger.info('there are %d images' % len(images))
        # Upload each image to the appropriate place in S3.
        for image in images:
            path = root + '/' +  str(index)
            url = self.upload_image(path, image)
            urls.append(url)
            index += 1

        return urls

    def create_error(self, code, message):
        self.error(code);
        self.response.out.write(message)

    def upload_image(self, path, image_data):
        """Uploads image data to S3 on the given path. Returns URL of the
        uploaded image."""
        return self.upload_helper(path, image_data, 'image/png')

    def upload_text(self, path, text):
        """Uploads text data to S3 on the given path. Returns URL of the
        uploaded text."""
        return self.upload_helper(path, text, 'text/plain')

    def upload_helper(self, path, data, contentType):
        conn = S3.AWSAuthConnection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        options = {'x-amz-acl': 'public-read', 'Content-Type': contentType}
        response = conn.put(DEFAULT_BUCKET, path, S3.S3Object(data), options)
        return URL_FORMAT % {'bucket': DEFAULT_BUCKET, 'path': path}

    def convert_pdf(self, pdf_data):
        """Converts PDF to PNG images. Returns an array of PNG data."""
        asset = conversion.Asset('application/pdf', pdf_data, 'sheet.pdf')
        conversion_request = conversion.Conversion(asset, 'image/png')
        result = conversion.convert(conversion_request)
        if result.assets:
            return [asset.data for asset in result.assets]
        else:
            raise Exception('Conversion failed: %d %s'
                    % (result.error_code, result.error_text))

    def create_db_entry(self, info, urls):
        """Creates a smusique.com database entry for the info and the
        associated URLs. Returns True iff successful."""
        d = info.serialize()
        d['urls'] = urls
        logger.info('payload ' + json.dumps(d))
        result = urlfetch.fetch(
                url=SMUSIQUE_UPLOAD_URL,
                payload=json.dumps(d),
                method=urlfetch.POST)

        logger.info('result info %d' % result.status_code)
        if result.status_code is not 200:
            raise Exception('Failed to upload')

    def fetch_pdf(self, url):
        """Returns the binary data of the PDF at a given URL."""
        result = urlfetch.fetch(url)
        return result.content


def main():
    application = webapp.WSGIApplication([('/', MainHandler)], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
