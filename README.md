# dev_project_09082021

occu dev project


## Description

I chose Python3 for this project because SQLite is included in the standard library.
My second option was GoLang because I work with that language most of the time.

Typically I use the type annotations for Python. I didn't want this to break given
differing versions (https://docs.python.org/3.5/library/typing.html). I have tested
it out using the following operating systems and versions:

| Program  | Debian 10 | Windows 10 |
| -------- | --------- | ---------- |
| SQLite3  | 3.27.2    | 3.35.5     |
| pysqlite | 2.6.0     | 2.6.0      |
| Python   | 3.7.3     | 3.9.7      |

Instead of doing a "simple" website I opted for a more dynamic UI using with Vue and D3.

I included comments throughout the code detailing some of my though process as I went
through the exercise. I tried to identify as many bugs as I could (all software has them).
I apologize in advance for any spell mistakes and I thank you for your consideration.


## Usage

1. Startup the server

```bash
$ python3 main.py
Server started http://localhost:8080
```

2. In your preferred browser go to http://localhost:8080

The script also accepts arguments from the command line:

 - host (default localhost)
 - port (default 8080)

```bash
$ python3 main.py -host 0.0.0.0 -port 8888
Server started http://0.0.0.0:8888
```
