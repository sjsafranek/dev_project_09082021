#!/usr/bin/python3

from mimetypes import MimeTypes
mime = MimeTypes()

def getMimeTypeFromFile(fpath):
    return mime.guess_type(fpath)
