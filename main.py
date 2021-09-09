#!/usr/bin/python3

import argparse

import server


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='OCCU Project')
    parser.add_argument('-host', type=str, default='localhost', help='server host')
    parser.add_argument('-port', type=int, default=8080, help='server port')
    args, unknown = parser.parse_known_args()

    # Start server
    server.start(args.host, args.port)
