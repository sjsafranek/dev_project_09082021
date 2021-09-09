import json
import time
import uuid
import random
import os.path
import sqlite3
import argparse
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer



# CONFIG
DB_FILE = 'db.sqlite3'


VERSION = '0.0.1'
START_TIME = time.time()



# Check for database file
# Doing this before the running sqlite3.connect
# to avoid any possible file system changes.
_dbExists = os.path.exists(DB_FILE)

# Open database connection
conn = sqlite3.connect(DB_FILE)

# Enable dict factory for sqlite3
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn.row_factory = dict_factory

# Set journal mode to WAL.
# source: https://charlesleifer.com/blog/going-fast-with-sqlite-and-python/
conn.execute('pragma journal_mode=wal')


# Initialize database if it does not yet exist
if not _dbExists:

    # Get cursor
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS models (
            name            TEXT PRIMARY KEY,
            make            TEXT,
            color           TEXT,
            status          TEXT,
            create_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_at       DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS on_models_update
           AFTER UPDATE OF make, color, status ON models
         --  FOR EACH ROW
        BEGIN
            UPDATE models SET update_at = CURRENT_TIMESTAMP WHERE name = NEW.name;
        END;
    ''')

    # Make default records
    make_options = ['ford', 'subaru', 'toyota']
    color_options = ['blue', 'red', 'silver', 'green', 'white', 'black']
    status_options = ['driving', 'crashed', 'parked']

    for i in range(37):
        make = random.choice(make_options)
        color = random.choice(color_options)
        status = random.choice(status_options)
        cursor.execute('''INSERT INTO models (name, make, color, status) VALUES (?, ?, ?, ?)''', ( str(uuid.uuid4()), make, color, status, ) )

    # Commit database changes
    conn.commit()



#############
#   Model   #
#############

class Model(object):

    fields = ['make', 'color', 'status', 'create_at', 'update_at']

    def __init__(self, name, **kwargs):
        self.name = name
        self.data = kwargs

    def get(self, key):
        if key in self.fields:
            if key not in self.data:
                for row in self._fetch(name = self.name):
                    self.data = row
            return self.data.get(key)

    @property
    def make(self):
        return self.get('make')

    @make.setter
    def make(self, value):
        self.data['make'] = value

    @property
    def color(self):
        return self.get('color')

    @color.setter
    def color(self, value):
        self.data['color'] = value

    @property
    def status(self):
        return self.get('status')

    @status.setter
    def status(self, value):
        self.data['status'] = value

    @property
    def create_at(self):
        return self.get('create_at')

    @property
    def update_at(self):
        return self.get('update_at')

    def save(self):
        # Collect args
        args = (self.get('make'), self.get('color'), self.get('status'), self.name, )

        # Get cursor
        cursor = conn.cursor()

        # Determine if this is an INSERT or UPDATE
        if len(self.fetch(name=self.name)):
            cursor.execute('''UPDATE models SET make = ?, color = ?, status = ? WHERE name = ?;''', args)
        else:
            # https://www.sqlite.org/lang_returning.html
            # The RETURNING syntax has been supported by SQLite since version 3.35.0 (2021-03-12).
            # rows = cursor.execute('''INSERT INTO models (name, make, color, status) VALUES (?, ?, ?, ?) RETURNING *;''', args)
            cursor.execute('''INSERT INTO models (make, color, status, name) VALUES (?, ?, ?, ?);''', args)

        # Commit changes
        conn.commit()

    @classmethod
    def _fetch(cls, **kwargs):
        # Build query and collect filter params
        query = '''SELECT * FROM models'''
        params = tuple()
        if len(kwargs.keys()):
            filters = ['{0} = ?'.format(key) for key in kwargs.keys()]
            params = tuple(kwargs.values())
            query += ' WHERE ' + ' AND '.join(filters)

        # Run query and return results
        cursor = conn.cursor()
        rows = cursor.execute(query, params)
        return rows.fetchall()

    @classmethod
    def fetch(cls, **kwargs):
        return [
            Model(**row) for row in cls._fetch(**kwargs)
        ]

    def toDict(self):
        return self.data



##################
#   Controller   #
##################

# Handler for api requests
def do(request):

    # Lets handle the api calls via "RPC"
    method = request.get('method', 'ping')
    params = request.get('params', {})

    if 'ping' == method:
        return {
            "status": "ok",
            "data": {
                "version": VERSION,
                "start_time": START_TIME,
                "up_time": time.time() - START_TIME
            }
        }, 'application/json', 200

    elif 'get_models' == method:
        return {
            "status": "ok",
            "data": {
                "models": [
                    model.toDict() for model in Model.fetch(**params)
                ]
            }
        }, 'application/json', 200

    elif 'update_model' == method:
        return {
            "status": "TODO"
        }, 'application/json', 200


# Basic server for handling requests
class Server(BaseHTTPRequestHandler):

    def do_HEAD(self):
        return

    def do_GET(self):
        self.respond()

    def do_POST(self):
        self.respond()

    @property
    def body(self):
        content_len = int(self.headers.get('content-length', 0))
        return self.rfile.read(content_len)

    def json(self):
        if self.body:
            return json.loads(self.body)
        return {"method": "ping"}

    def handle_http(self):
        statusCode = 404
        contentType = 'text/plain'
        content = json.dumps({"status":"error", "error": {"message": "Not Found"}})

        if '/v1/api' == self.path:
            request = self.json()
            response, contentType, statusCode = do(request)
            content = json.dumps(response)

        elif '/models' == self.path:
            response, contentType, statusCode = do({"method": "get_models", "params": {}})
            content = json.dumps(response)

        # content = routes[self.path]

        self.send_response(statusCode)
        self.send_header("Content-type", contentType)
        self.end_headers()

        return bytes(content, "UTF-8")

    def respond(self):
        content = self.handle_http()
        self.wfile.write(content)




############
#   Main   #
############

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='OCCU Project')
    parser.add_argument('-host', type=str, default='localhost', help='server host')
    parser.add_argument('-port', type=int, default=8080, help='server port')
    args, unknown = parser.parse_known_args()

    webServer = HTTPServer((args.host, args.port), Server)
    print("Server started http://%s:%s" % (args.host, args.port))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
