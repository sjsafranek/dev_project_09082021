
import json
import os.path


class ModelCollectionView(object):

    def __init__(self, collection):
        self.collection = collection

    def render(self):
        # I am tired of writing Python so lets switch over to JavaScript...
        data = self.collection.toDict()
        fpath = os.path.join('tmpl', 'page.html')
        with open(fpath) as fh:
            tmpl = fh.read()
            return tmpl.replace('{{models}}', json.dumps(data))
