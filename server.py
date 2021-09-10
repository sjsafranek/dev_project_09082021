#!/usr/bin/python3

'''
Web server to accept incomming HTTP requests.

This will constitute as our "[C]ontroller" in the MVC architecture.
'''

import re
import json
import time
import os.path
from urllib.parse import urlparse
from urllib.parse import parse_qs
from urllib.parse import unquote
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
# from socketserver import ForkingMixIn     # This does not work on windows
# import asyncio        # I haven't used this enough. If I have time I
# might try to utilize it.
import threading

from models import Model


VERSION = '0.0.1'

START_TIME = time.time()


# Basic server for handling requests
class Controller(BaseHTTPRequestHandler):

    ''' I hand rolled this using the standard modules to avoid any dependency issues.
        It was nice learing more about the http.server module even though it is pretty
        low level (at least for Python). Since the BaseHTTPRequestHandler class is
        fairly low level, I have implemented several methods to mimic some basic
        functionaly that would be present in 'out-of-the-box' frameworks.

        I typically use frameworks such as Django, Tornado or Flask for Python
        webs development. I like using Gorilla for GoLang web development.

        TODO:
         - Add a custom log format. I don't like the default one.
    '''

    def redirect(self, path):
        ''' A simple helper method for implementing HTTP redirects '''
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send(self, content, content_type='text/plain', status=200):
        ''' A helper method for sending the HTTP response '''
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(bytes(content, "UTF-8"))
        self.wfile.flush()
        # print(dir(self))
        # self.finish()

    # The next few methods are just helpers to keep things clean
    # within our application logic.
    def sendJSON(self, payload, status=200):
        self.send(
            json.dumps(payload),
            content_type='application/json',
            status=status)

    def sendHTML(self, content, status=200):
        self.send(content, content_type='text/html', status=status)

    def errorNotFound(self, message='Not Found'):
        self.sendJSON({"status": "error", "error": {
                      "message": message}}, status=404)

    def errorMethodNotAllowed(self, message='Method Not Allowed'):
        self.sendJSON({"status": "error", "error": {
                      "message": message}}, status=405)

    def errorMethodBadRequest(self, message='Bad Request'):
        self.sendJSON({"status": "error", "error": {
                      "message": message}}, status=400)

    def sendAPIResponse(self, **kwargs):
        return self.sendJSON({
            "status": 'ok' if 200 == kwargs.get('status', 200) else 'error',
            "data": kwargs
        }, kwargs.get('status', 200))

    # This section contains methods to help get/collect parameters
    # sent in the HTTP request.
    @property
    def body(self):
        ''' According to the documentation the BaseHTTPRequestHandler.rfile attribute
            is an io.BufferedIOBase.

            I haven't explored this too far but I will go with the assumption that we
            can only read from it once. To avoid any possible issues with multiple reads,
            I will cache the results after the first read.
        '''
        if hasattr(self, '_body'):
            return self._body
        content_len = int(self.headers.get('content-length', 0))
        self._body = self.rfile.read(content_len)
        return self._body

    def json(self):
        ''' Parses JSON payloads contained in the request body '''
        if 'application/json' == self.headers.get('content-type'):
            if self.body:
                try:
                    return json.loads(self.body)
                except BaseException:
                    return {}
        return {}

    @property
    def form(self):
        ''' Parses forms contained in the request body '''
        if 'application/x-www-form-urlencoded' == self.headers.get(
                'content-type'):
            if self.body:
                params = parse_qs(self.body)
                return {
                    k.decode(): v[0].decode() for k,
                    v in params.items() if v is not None}
        return {}

    @property
    def args(self):
        ''' Parses url query string parameters '''
        params = parse_qs(urlparse(self.path).query)
        return {
            k: v[0] for k, v in params.items() if v is not None
        }

    @property
    def params(self):
        ''' This merges parameters sent via different methods (JSON, form and query string).
            We will prioritize data sent within the request body.
        '''
        return {
            **self.args,
            **self.form,
            **self.json().get('params', {})
        }

    # These two methods are just helper functions for the application logic.
    def _getModelNameFromUrl(self):
        ''' This extracts the 'name' parameter from the url.

            Pretty clunky and room for improvement.
        '''
        url = urlparse(self.path)
        if url.path.startswith('/api/v1/model/'):
            parts = url.path.replace('/api/v1/model/', '').split('/')
            return unquote(parts[0])
        elif url.path.startswith('/model/'):
            parts = url.path.replace('/model/', '').split('/')
            return unquote(parts[0])
        return None

    def getModel(self):
        ''' Fetches the Model object for the given 'name' supplied by the request. '''
        name = self._getModelNameFromUrl()
        if not name:
            name = self.params['name']
        models = Model.fetch(name=name)
        return models[0] if len(models) else None

    # Here are the HTTP request handlers.
    # This section contains the bulk for our application logic.
    def indexHandler(self):
        ''' HTTP handler for our index path.

            This technically our [V]iew in the MVC architecture.

            In a 'simple' MVC website we might construct different views for each action
            a user could do. I decided to take some liberties here and create a more dynamic
            website, were all the functional requirements are folded together into a single
            page.

            Instead of using Python to generate raw HTML, I decided to push this job
            to a front end framework called Vue (https://vuejs.org/v2/guide/index.html).
            I felt this would better demonstrate some modern web development approaches
            as well as my full stack development capabilities.
        '''
        fpath = os.path.join('tmpl', 'page.html')
        with open(fpath) as fh:
            tmpl = fh.read()
            data = [model.toDict() for model in Model.fetch(**self.params)]
            page = tmpl.replace('{{models}}', json.dumps(data))
            self.sendHTML(page)

    def do_HEAD(self):
        return

    def do_POST(self):
        ''' An HTTP handler for the [C]reate method in the CRUD application. '''
        url = urlparse(self.path)

        # Handle redirects
        if '/' == url.path:
            return self.indexHandler()

        elif url.path in ['/api/v1/model', '/create']:
            # Check to see if a Model with the supplied name exists.
            # If one doesn't, create a new Model object.
            name = self.params.get('name')
            if name:
                if Model.exists(name):
                    return self.errorMethodBadRequest(
                        'Model already exists: {0}'.format(name))
            model = Model(**self.params)
            model.save()

            # Depending on endpoint return api response or redirect.
            if '/api/v1/model' == url.path:
                return self.sendAPIResponse(model=model.toDict())
            else:
                return self.redirect('/')

        self.errorNotFound()

    def do_GET(self):
        ''' An HTTP handler for the [R]ead method in the CRUD application. '''
        url = urlparse(self.path)

        # Handle redirects
        if '/' == url.path:
            return self.indexHandler()

        # It's always nice to include a route for health checks.
        elif '/ping' == url.path:
            return self.sendAPIResponse(
                version=VERSION,
                start_time=START_TIME,
                up_time=time.time() - START_TIME
            )

        # Basic API endpoints for testing
        elif '/api/v1/models' == url.path:
            return self.sendAPIResponse(models=[
                model.toDict() for model in Model.fetch(**self.params)
            ])

        elif re.match(r'^/api/v1/model/[^/]+$', url.path):
            model = self.getModel()
            if model:
                return self.sendAPIResponse(model=model.toDict())

        self.errorNotFound()

    def do_PUT(self):
        ''' An HTTP handler for the [U]pdate method in the CRUD application. '''
        url = urlparse(self.path)

        _isApiRequest = re.match(r'^/api/v1/model/[^/]+$', url.path)

        # Handle redirects
        if '/' == url.path:
            return self.indexHandler()

        elif _isApiRequest or re.match(r'^/model/[^/]+$', url.path):
            model = self.getModel()
            if model:
                # Update model with new values. Default to existing value.
                params = self.params
                model.color = params.get('color', model.color)
                model.make = params.get('make', model.make)
                model.status = params.get('status', model.status)
                model.save()

                # Depending on endpoint return api response or redirect.
                if _isApiRequest:
                    return self.sendAPIResponse(model=model.toDict())
                else:
                    return self.redirect('/')

        self.errorNotFound()

    def do_DELETE(self):
        ''' An HTTP handler for the [D]elete method in the CRUD application. '''
        url = urlparse(self.path)

        # Handle redirects
        if '/' == url.path:
            return self.indexHandler()

        elif url.path.startswith('/api/v1/model/') or re.match(r'^/model/[^/]+$', url.path):
            model = self.getModel()
            if model:
                model.delete()
                if url.path.startswith('/api/v1/model/'):
                    return self.sendAPIResponse()
                else:
                    return self.redirect('/')

        self.errorNotFound()


class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    ''' SQLite did not like the ThreadingMixIn when we had a single persistent
        database connection. I was going to scrap this and just use the plain
        HTTPServer, but unfortunately I would get the occasional hang when using
        multiple browser tabs.

        Unfortunately, this will occasionally deadlocks when it is shutting down.
        I looked around but haven't found a good solution yet...
    '''
    pass


# This is not supported for windows... sad day :(
# class ForkingHTTPServer(ForkingMixIn, HTTPServer):
#     '''
#         I was seeing that the HTTPServer was hanging on multiple
#         requests due to them blocking eachother.
#         The ForkingMixIn seems to have fixed these issues.
#     '''
#     pass


# Listen and serve on specified host and port
def start(host='localhost', port=8080):
    # server = ForkingHTTPServer((host, port), Controller)
    server = ThreadingSimpleServer((host, port), Controller)
    print("Server started http://%s:%s" % (host, port))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        # server.server_close()
        # server.socket.close()

    print("Server stopped.")
