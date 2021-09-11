#!/usr/bin/python3

'''
Interfaces with the sqlite3 database.

This is our "[M]odel" in the MVC architecture.
'''

import uuid

import database


class Model(object):

    ''' Hand rolling my own little ORM for the 'model' table.
        Lots of room for improvement here. Some of the functionaly
        is a little 'happy path' for my liking.

        I am taking some inspiration from the Django ORM.
    '''

    fields = ['id', 'name', 'make', 'color', 'status', 'create_at', 'update_at']
    filterable = ['id', 'name', 'make', 'color', 'status', 'create_at', 'update_at']
    editable = ['make', 'color', 'status']

    def __init__(self, **kwargs):
        self._data = kwargs

    def get(self, key):
        if self._data:
            return self._data.get(key)

    @property
    def id(self):
        return self.get('id')

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

        https://github.com/sjsafranek/find5/blob/c8d5bbbcfb4b33f420a83f07025bad9727474ce3/findapi/lib/database/database.go#L113
        https://github.com/sjsafranek/find5/blob/c8d5bbbcfb4b33f420a83f07025bad9727474ce3/finddb_schema/base_schema/create_users_table.sql#L6

        '''
        # If the 'name' parameter is not supplied generate a random one.
        if 'name' not in self._data or not self._data['name']:
            self._data['name'] = str(uuid.uuid4())

        # Get cursor
        with database.connect() as conn:
            cursor = conn.cursor()

            # Determine if this is an INSERT or UPDATE.
            # Always use parameter substitution to prevent SQL injection.
            if self.exists(id=self.id):
                args = (self.make, self.color, self.status, self.name, self.id)
                cursor.execute(
                    '''UPDATE models SET make = ?, color = ?, status = ?, name = ? WHERE id = ?;''', args)
                # Get any changes
                self._data = cursor.execute('''SELECT * FROM models WHERE id = ?;''', (self.id,)).fetchone()
            else:
                # I would prefer to use the new 'RETURNING' clause here
                args = (self.make, self.color, self.status, self.name, )
                cursor.execute(
                    '''INSERT INTO models (make, color, status, name) VALUES (?, ?, ?, ?);''',
                    args)
                # Get new record
                self._data = cursor.execute('''SELECT * FROM models WHERE rowid = ?;''', (cursor.lastrowid,)).fetchone()

            # Commit changes
            conn.commit()

    def delete(self):
        with database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''DELETE FROM models WHERE id = ?;''', (self.id,))
            conn.commit()

    @classmethod
    def _fetch(cls, **kwargs):

        # Build query and collect filter params
        query = '''SELECT * FROM models'''
        filters = []
        params = []
        for key, value in kwargs.items():
            # This check should guard against SQL vulnerabilities.
            if key in cls.filterable:
                filters.append('{0} = ?'.format(key))
                params.append(value)
        if len(filters):
            query += ' WHERE ' + ' AND '.join(filters)
        query += ';'

        if len([f for f in filters if f]) != len([p for p in params if p]):
            raise Value('WAT?!?!')

        # Run query and return results
        with database.connect() as conn:
            cursor = conn.cursor()
            return cursor.execute(
                query, tuple(params)
            ).fetchall()

    @classmethod
    def fetch(cls, **kwargs):
        return [
            Model(**row) for row in cls._fetch(**kwargs)
        ]

    @classmethod
    def exists(cls, id):
        with database.connect() as conn:
            cursor = conn.cursor()
            row = cursor.execute(
                '''SELECT EXISTS(SELECT 1 FROM models WHERE id = ?) AS 'exists';''',
                (id,
                 )).fetchone()
            return 0 != row['exists']

    def toDict(self):
        return self._data


class ModelCollection(object):
    ''' Helper class for doing bulk operations.
        This is mainly for future proofing.
    '''

    def __init__(self, models):
        self.collection = models

    def toDict(self):
        return [item.toDict() for item in self.collection]


#
