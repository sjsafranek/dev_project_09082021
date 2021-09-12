#!/usr/bin/python3

'''
The main thing I wanted to demonstrate here is to add some logic
controlled in the database via a 'TRIGGER'.

I typically use PostGreSQL for database backends and feel much more
confortable with it than SQLite. I am choosing SQLite because it is
included in standard library for Python.

I have included a more advanced PostGreSQL/PostGIS script template
demonstrating some more advanced SQL.

    - ./examples/osm_road_snapper.tmpl.sql

Here are some other SQL examples on my github:

    - https://github.com/sjsafranek/find5/blob/c8d5bbbcfb4b33f420a83f07025bad9727474ce3/findapi/lib/database/user.go#L360
    - https://github.com/sjsafranek/find5/blob/c8d5bbbcfb4b33f420a83f07025bad9727474ce3/finddb_schema/base_schema/create_users_table.sql#L2
'''

# import uuid
import random
import os.path
import sqlite3

from conf import DB_FILE


# Check for database file
# Doing this before the running sqlite3.connect
# to avoid any changes on the file system.
_dbExists = os.path.exists(DB_FILE)


# Open new database connection
def connect():
    # This is technically dangerous because with multiple writers SQLite3
    # could lock. I am going to ignore this consern because the likelyhood
    # of this happening is low.
    conn = sqlite3.connect(DB_FILE)

    # Enable dict factory for sqlite3.
    # I would typically use the PostGreSQL JSON functionality.
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    conn.row_factory = dict_factory

    # Set journal mode to WAL.
    # source: https://charlesleifer.com/blog/going-fast-with-sqlite-and-python/
    # https://sqlite.org/wal.html
    # This isn't really needed for this project, but it is
    # helpful for high concurrency applications.
    conn.execute('pragma journal_mode=wal')

    # Return database connection
    return conn


# Initialize database if it does not yet exist
if not _dbExists:

    # The 'with' clause will automatically call the close
    # method on the database connection.
    with connect() as conn:

        # Create basic tables and triggers
        cursor = conn.cursor()

        # I am using a UUID for a primary key. This is over kill for a small
        # project. I have gotten in the habit of doing this when working with
        # horizontally scaling systems.
        # SQLite3 doesn't have a UUID function so we will use a custom one.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS models (
                id              DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
                name            TEXT UNIQUE,
                make            TEXT,
                color           TEXT,
                status          TEXT,
                create_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY ("id")
            );
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS on_models_update
               AFTER UPDATE OF make, color, status ON models
            BEGIN
                UPDATE models SET update_at = CURRENT_TIMESTAMP WHERE name = NEW.name;
            END;
        ''')

        conn.commit()

        # Generate an example dataset
        cursor = conn.cursor()
        make_options = ['ford', 'subaru', 'honda', 'toyota', 'gm', 'mazda']
        color_options = ['blue', 'red', 'silver', 'white', 'black']
        status_options = ['fail'] * 10 + ['warn'] * 20 + ['pass'] * 70

        for i in range(37):
            name = 'thing_{0}'.format(i)
            make = random.choice(make_options)
            color = random.choice(color_options)
            status = random.choice(status_options)
            cursor.execute(
                '''INSERT INTO models (name, make, color, status) VALUES (?, ?, ?, ?)''', (name, make, color, status, ))

        conn.commit()
