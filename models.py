#!/usr/bin/python3

'''
Interfaces with the sqlite3 database.

This is our "model".
'''

import uuid

from database import conn


class Model(object):

    fields = ['name', 'make', 'color', 'status', 'create_at', 'update_at']
    filterable = ['name', 'make', 'color', 'status', 'create_at', 'update_at']
    editable = ['make', 'color', 'status']

    def __init__(self, **kwargs):
        self._data = kwargs

    def get(self, key):
        if key in self.fields:
            if key not in self._data:
                for row in self._fetch(name = self.name):
                    self._data = row
            return self._data.get(key)

    @property
    def name(self):
        return self.get('name')

    @property
    def make(self):
        return self.get('make')

    @make.setter
    def make(self, value):
        self._data['make'] = value

    @property
    def color(self):
        return self.get('color')

    @color.setter
    def color(self, value):
        self._data['color'] = value

    @property
    def status(self):
        return self.get('status')

    @status.setter
    def status(self, value):
        self._data['status'] = value

    @property
    def create_at(self):
        return self.get('create_at')

    @property
    def update_at(self):
        return self.get('update_at')

    def save(self):
        '''
        I personally like having the database control the generation of things such as PRIMARY KEYS or UUIDS.

        In larger projects I tend to use a 'RETURNING' clause to send back the newly created record, having
        the database maintain control over DEFAULT values. According to the SQLite documentation 'RETURNING'
        is availble since version 3.35.0 (2021-03-12): https://www.sqlite.org/lang_returning.html

            - https://github.com/sjsafranek/find5/blob/c8d5bbbcfb4b33f420a83f07025bad9727474ce3/findapi/lib/database/database.go#L113
            - https://github.com/sjsafranek/find5/blob/c8d5bbbcfb4b33f420a83f07025bad9727474ce3/finddb_schema/base_schema/create_users_table.sql#L6

        '''
        # If 'name' is not supplied generate a random one
        if 'name' not in self._data or not self._data['name']:
            self._data['name'] = str(uuid.uuid4())

        # Get cursor
        cursor = conn.cursor()

        # Determine if this is an INSERT or UPDATE
        args = (self.make, self.color, self.status, self.name, )
        if len(self._fetch(name=self.name)):
            cursor.execute('''UPDATE models SET make = ?, color = ?, status = ? WHERE name = ?;''', args)
        else:
            cursor.execute('''INSERT INTO models (make, color, status, name) VALUES (?, ?, ?, ?);''', args)

        # Commit changes
        conn.commit()

    def delete(self):
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM models WHERE name = ?;''', (self.name,))
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

    @classmethod
    def exists(cls, name):
        return 0 != len(cls._fetch(name=name))

    def toDict(self):
        data = self._fetch(name=self.name)
        if len(data):
            return data[0]
        return self._data




class ModelCollection(object):
    '''
        Helper class for doing bulk operations
    '''
    def __init__(self, models):
        self.collection = models

    def toDict(self):
        return [item.toDict() for item in self.collection]

#
