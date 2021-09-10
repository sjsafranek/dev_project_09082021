#!/usr/bin/python3

'''
This will constitute as our "controller".

I hand rolled this using the standard modules to avoid any dependency issues.
It was nice learing more about the http.server module even though it is pretty
low level (at least for Python).

I typically use frameworks such as Django, Tornado or Flask for Python
webs development. I also use Gorilla for GoLang web development.
'''

import re
import json
import time
from urllib.parse import urlparse
from urllib.parse import parse_qs
from urllib.parse import unquote
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from socketserver import ForkingMixIn
import threading

from models import Model
from models import ModelCollection
from views import ModelsView


VERSION = '0.0.1'

START_TIME = time.time()



# Basic server for handling requests
class Controller(BaseHTTPRequestHandler):

    def redirect(self, path):
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    @property
    def body(self):
        '''
            We will read the request body once by caching the results for later.
        '''
        if hasattr(self, '_body'):
            return self._body
        content_len = int(self.headers.get('content-length', 0))
        self._body = self.rfile.read(content_len)
        return self._body

    def json(self):
        if 'application/json' == self.headers.get('content-type'):
            if self.body:
                try:
                    return json.loads(self.body)
                except:
                    return {}
        return {}

    @property
    def form(self):
        if 'application/x-www-form-urlencoded' == self.headers.get('content-type'):
            if self.body:
                params = parse_qs(self.body)
                return {
                    k.decode(): v[0].decode() for k, v in params.items() if v is not None
                }
        return {}

    @property
    def args(self):
        '''
            This parses the url query string and only selects the fields of our model.
            If we add new fields to our model they will automatically be added to this
            lookup.
        '''
        params = parse_qs(urlparse(self.path).query)
        return {
            k: v[0] for k, v in params.items() if v is not None
        }

    @property
    def params(self):
        '''
            This merges the query string arguments with the request body.
            We will prioritize data sent within the request body.
        '''
        return {
            **self.args,
            **self.form,
            **self.json().get('params', {})
        }

    def send(self, content, content_type='text/plain', status=200):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(bytes(content, "UTF-8"))

    def sendJSON(self, payload, status=200):
        self.send(json.dumps(payload), content_type='application/json', status=status)

    def sendHTML(self, content, status=200):
        self.send(content, content_type='text/html', status=status)

    def errorNotFound(self, message='Not Found'):
        self.sendJSON({"status":"error", "error": {"message": message}}, status=404)

    def errorMethodNotAllowed(self, message='Method Not Allowed'):
        self.sendJSON({"status":"error", "error": {"message": message}}, status=405)

    def errorMethodBadRequest(self, message='Bad Request'):
        self.sendJSON({"status":"error", "error": {"message": message}}, status=400)

    def sendAPIResponse(self, **kwargs):
        return self.sendJSON({
            "status": 'ok' if 200 == kwargs.get('status', 200) else 'error',
            "data": kwargs
        }, kwargs.get('status', 200))

    def _getModelNameFromUrl(self):
        url = urlparse(self.path)
        if url.path.startswith('/api/v1/model/'):
            parts = url.path.replace('/api/v1/model/', '').split('/')
            return unquote(parts[0])
        elif url.path.startswith('/model/'):
            parts = url.path.replace('/model/', '').split('/')
            return unquote(parts[0])
        return None

    def getModel(self):
        name = self._getModelNameFromUrl()
        if not name:
            name = self.params['name']
        models = Model.fetch(name=name)
        return models[0] if len(models) else None

    def do_HEAD(self):
        return

    def do_GET(self):
        url = urlparse(self.path)

        if '/ping' == url.path:
            return self.sendAPIResponse(
                            version=VERSION,
                            start_time=START_TIME,
                            up_time=time.time()-START_TIME
                        )

        elif '/api/v1/models' == url.path:
            return self.sendAPIResponse(models=[
                model.toDict() for model in Model.fetch(**self.params)
            ])

        elif re.match(r'^/api/v1/model/[^/]+$', url.path):
            model = self.getModel()
            if model:
                return self.sendAPIResponse(model=model.toDict())

        # The next two endpoints will interface with the "View" component
        elif url.path in ['/', '/models']:
            view = ModelsView(ModelCollection(Model.fetch(**self.params)))
            page = view.render()
            return self.sendHTML(page)

        elif re.match(r'^/model/[^/]+$', url.path):
            model = self.getModel()
            if model:
                view = ModelsView(ModelCollection([model]))
                page = view.render()
                return self.sendHTML(page)

        self.errorNotFound()

    def do_POST(self):
        '''
            I am a fan of the JSON-RPC type protocol but lets go with
            a REST protocol for this project.

            https://www.jsonrpc.org/specification
        '''

        url = urlparse(self.path)

        # Api endpoints
        if '/api/v1/model' == url.path:
            name = self.params.get('name')
            if name:
                if Model.exists(name):
                    return self.errorMethodBadRequest('Model already exists')
            model = Model(name=name)
            model.save()
            return self.sendAPIResponse(model=model.toDict())

        # Form endpoints
        elif '/create' == url.path:
            name = self.params.get('name')
            if name:
                if Model.exists(name):
                    return self.errorMethodBadRequest('Model already exists')
            model = Model(name=name)
            model.save()
            return self.redirect('/')

        self.errorNotFound()

    def do_PUT(self):
        url = urlparse(self.path)
        if re.match(r'^/api/v1/model/[^/]+$', url.path):
            model = self.getModel()
            if model:
                # Update model with new values. Default to existing value.
                params = self.params
                model.color = params.get('color', model.color)
                model.make = params.get('make', model.make)
                model.status = params.get('status', model.status)
                model.save()
                return self.sendAPIResponse(model=model.toDict())

        self.errorNotFound()

    def do_DELETE(self):
        url = urlparse(self.path)
        if url.path.startswith('/api/v1/model/'):
            model = self.getModel()
            if model:
                model.delete()
                return self.sendAPIResponse()
        self.errorNotFound()



class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    '''
        SQlite did not like the ThreadingMixIn because we only
        have one connection to the in memory database.
    '''
    pass



class ForkingHTTPServer(ForkingMixIn, HTTPServer):
    '''
        I was seeing that the HTTPServer was hanging on multiple
        requests due to them blocking eachother.
        The ForkingMixIn seems to have fixed these issues.
    '''
    pass



# Listen and serve on specified host and port
def start(host='localhost', port=8080):
    # server = HTTPServer((host, port), Server)
    server = ForkingHTTPServer((host, port), Controller)
    print("Server started http://%s:%s" % (host, port))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
    print("Server stopped.")


#
