#!/usr/bin/env python3

import json
import socketserver
import threading
import http.server
import asyncio
import time
from http.client import parse_headers

DEFAULT_HTTP_HOST = '127.0.0.1'
DEFAULT_HTTP_PORT = 8087


async def http_handler(reader, writer):
    data = await reader.read(100)
    message = data.decode()

    print(message)
    # print(parse_headers())
    print()

    writer.write(data)
    await writer.drain()
    writer.close()
    print('done')


async def main():

    HTTP_HOST = DEFAULT_HTTP_HOST
    HTTP_PORT = DEFAULT_HTTP_PORT

    # This needs a callback
    http_server = await asyncio.start_server(http_handler, HTTP_HOST, HTTP_PORT)

    # This needs a 'protocol_factory'
    # https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.create_server
    # loop = asyncio.get_running_loop()
    # http_server = await loop.create_server(HTTPProtocol, SERVER_ADDRESS, HTTP_PORT)

    print("Starting server at http://{0}:{1}".format(HTTP_HOST, HTTP_PORT))

    try:
        await http_server.serve_forever()
    except KeyboardInterrupt:
        print('Exit called')


if __name__ == '__main__':
    asyncio.run(main())
