# dev_project_09082021

occu dev project


## Description

I chose [Python3](https://www.python.org/) for this project because [SQLite3](https://www.sqlite.org/index.html)
is included in the standard library. My second language option was [GoLang](https://go.dev/) due to
its built-in support for concurrent applications.

I have tested it out using the following operating systems and versions:

| Program  | Debian 10 | Windows 10 |
| -------- | --------- | ---------- |
| SQLite3  | 3.27.2    | 3.35.5     |
| pysqlite | 2.6.0     | 2.6.0      |
| Python   | 3.7.3     | 3.9.7      |

I included comments throughout the code detailing my thought process as I went through the exercise.
I tried to identify as many bugs as I could (all software has them). I apologize in advance for any
spell mistakes and I thank you for your consideration.


### Model

I started out by wanting a solution that utilized a full stack: `database`, `server` and `client`.
I felt this would help show off my full stack developer capabilities.

[SQLite3](https://www.sqlite.org/index.html) was used for the backing store. It is a pretty simple
database, as we only have a single table. The database is initialized on server startup from
`database.py`.

Instead of using an ORM framework such as [SQLAlchemy](https://www.sqlalchemy.org/), I decided to
hand roll my own. This can be found in `models.py`. There are some syntax sugar functions and some
very simple SQL queries to create, read, update and delete records.


### Controller

[Python3](https://www.python.org/) was used for the HTTP server. I used the standard library instead
of using a framework such as [Flask](https://flask.palletsprojects.com/en/2.0.x/) or
[Tornado](https://www.tornadoweb.org/en/stable/). This was perhaps the most challenging piece of the
architecture due to my limited development experience with Windows. While `pthread` and `fork` worked
great on Linux... these are not available on Windows systems.

The server-side "controller" code can be found in `server.py`. The first half consists of helper
functions that a web framework would already include.

I tried to support elements of JSON-RPC (this is my preferred protocol), HTML forms and REST to
demonstrate my familiarity with these formats. There is definitely more work that could be done
here to have everything in a more consistent format.


### View

Instead of doing a "simple" website I opted for a more dynamic UI using [Vue](https://vuejs.org/),
[D3](https://d3js.org/) and [Bootstrap](https://getbootstrap.com/) for the front end. As user actions
take place, the view will update depending on the response. The code for the front end (View) is
contained in the `static` and `tmpl` directories.

The instructions 'technically' didn't say I needed to create two separate pages. I did everything
in a single page and used [D3](https://d3js.org/) to generate and pie chart to show an the status
values "at a glance" described in Requirement-1. I felt this would be appropriate because of the
search/filter functionality for Requirement-2. By tying these features together, it allowed the UI
to provide feed back to the user as filters are applied.


## Usage

1. Startup the server

```bash
$ python3 main.py
Starting server at http://localhost:8080
```

2. In your preferred browser go to http://localhost:8080

The script also accepts arguments from the command line:

 - host (default localhost)
 - port (default 8080)

```bash
$ python3 main.py -host 0.0.0.0 -port 8888
Starting server at http://0.0.0.0:8888
```


## Issues

1. When running on Windows (within cmd.exe), the program will sometimes not respond to the first
'CONTROL-C'. I am not sure why this is the case...

2. Since it is using [SQLite3](https://www.sqlite.org/index.html) in a multi threaded environment
there would be a locking issue if two writes happen at the same time. Since this isn't a high
traffic environment I doubt this would occur.

3. I am not properly sanitizing user input values. I didn't consider this until later in the
development of this project. It has also been a while since I have been a QA tester.

4. The static files should be served up by something that controls a cache policy.

5. Typically I would use the type annotations for [Python3](https://www.python.org/). I didn't
want this to break given differing versions (https://docs.python.org/3.5/library/typing.html).

6. I should have used something like [Elm](https://elm-lang.org/) or [TypeScript](https://www.typescriptlang.org/)
to write the client side code. There are a few features from more recent `ECMA` standards that
I use. These will probably break the client side if used in `Internet Explorer`.

7. The server side request routing should be cleaned up so there are separate handlers for each URL
endpoint. This would make it much more readable.
