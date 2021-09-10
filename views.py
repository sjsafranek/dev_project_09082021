
import json
import os.path


class ModelsView(object):

    def __init__(self, model):
        self.model = model

    def render(self):
        # I am tired of writing Python so lets switch over to JavaScript...
        data = self.model.toDict()
        fpath = os.path.join('tmpl', 'page.html')
        with open(fpath) as fh:
            tmpl = fh.read()
            return tmpl.replace('{{models}}', json.dumps(data))
