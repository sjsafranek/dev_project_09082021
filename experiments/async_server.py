#!/usr/bin/env python

import json
import socketserver
import threading
import http.server
import asyncio
import time

SERVER_ADDRESS = '127.0.0.1'
HTTP_PORT = 8087
parsed_data = {}


async def handle_http(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    print(message)
    writer.write(data)
    await writer.drain()
    writer.close()


async def main():
    http_server = await asyncio.start_server(
        handle_http, SERVER_ADDRESS, HTTP_PORT
    )
    print(f'HTTP server listening on port {HTTP_PORT}')

    try:
        while True:
            if parsed_data:
                print(parsed_data.values())
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print('Exit called')


if __name__ == '__main__':
    asyncio.run(main())
