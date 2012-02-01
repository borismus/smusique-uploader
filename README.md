A standalone Google App Engine application that uploads files to
smusique.com.

## API Description

### GET /:

Provides an upload form supporting both PDF files and plaintext
tabs/chords at up.smusique.com

### POST /:

Takes form-encoded info about the work being uploaded:

Required fields:

* title (string)
* composer (string)
* label (string)
* notation (string)

XOR fields (exactly one must be specified):

* text (string)
* pdf (binary)
* pdfurl (string)

Optional fields:

* rating (int)

## Test cases

Tests first! Write unit tests in QUnit for these cases:

1. Not all required fields are specified.
3. None of the XOR fields are specified.
4. More than one of the XOR fields are specified.
5. Invalid file is uploaded.
6. Invalid URL is specified.
7. PDF with N pages is uploaded, ensure that N expected URLs are
   created.
8. Something is uploaded, ensure that a corresponding smusique database
   entry gets created.
