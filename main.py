#!/usr/bin/env python3
import argparse
import logging as log
import random
import re
import subprocess as sp
import sys
from threading import *
from typing import List, Dict, Tuple, Optional

from flask import Flask, jsonify, request, render_template
from flask_limiter import Limiter
from requests import get
from werkzeug.exceptions import HTTPException

import db
import gobbler
from parser_types import non_empty_string_type, positive_int_type, network_port_type

GENERIC_ERRORS = [
    'Oops! Something went wrong.',
    'Google Chrome quit unexpectedly.',
    'Changing gamemode is not allowed!',
    'Donkeys have been disabled due to an exploit!',
    'Keyboard not found press F1 to resume.',
    'Task failed successfully.',
    ':(){ :|:& };:',
]

log.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=log.INFO)

app = Flask(__name__)

db = db.DB()


def get_ip_proxied():
    ip = str(request.remote_addr)
    if ip is None or ip == '127.0.0.1':
        ip = str(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    if ip is None or ip == '127.0.0.1':
        ip = str(request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr))
    return ip or '127.0.0.1'


def alphabetic(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", s)


app.add_template_filter(alphabetic)

limiter = Limiter(
    app,
    key_func=get_ip_proxied,
    default_limits=['4 per second, 60 per minute']
)


@app.route('/', methods=['GET'])
def index():
    return render_template(
        'index.html',
        title='Index',
        servers=(db.get_servers()),
        players=(db.get_latest_players()),
        data=data_snapshot(1),
    )


@app.route('/servers', methods=['GET'])
def api_servers():
    return jsonify(db.get_servers())


@app.route('/players', methods=['GET'])
@limiter.limit('1/second,20/minute')
def api_players():
    return jsonify(db.get_latest_players())


@app.route('/ping', methods=['GET'])
@limiter.limit('1/second,20/minute')
def api_ping():
    return jsonify(db.get_latest_ping())


@app.route('/servers/<address>', methods=['GET'])
@limiter.limit('100/second')
def api_servers_data(address):
    return jsonify(db.get_data(address))


@app.errorhandler(Exception)
def error_handler(exception: Exception):
    code = 418
    log.warning(str(exception))
    if isinstance(exception, HTTPException) and exception.code < 500:
        code = exception.code
    return render_template('error.html', code=str(code), text=random.choice(GENERIC_ERRORS))


def data_snapshot(entries: int) -> Dict[str, List[Tuple[int, Optional[int], Optional[int]]]]:
    snapshot = dict()
    for server in db.get_servers():
        snapshot[server] = db.get_data(server, entries)
    return snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--servers',
        action='extend',
        type=non_empty_string_type,
        nargs='+',
        required=False,
        default=list(),
        metavar='ADDRESS',
        help='servers to be monitored, supplied as list'
    )
    parser.add_argument(
        '--servers-url',
        action='store',
        type=non_empty_string_type,
        required=False,
        metavar='URL',
        help='servers to be monitored, supplied as url'
    )
    parser.add_argument(
        '-p', '--port',
        action='store',
        type=network_port_type,
        required=False,
        default=5000,
        help='port'
    )
    parser.add_argument(
        '-w', '--workers',
        action='store',
        type=positive_int_type,
        required=False,
        default=4,
        help='gunicorn workers'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    log.info('starting with args: ' + str(args))

    servers: List[str] = args.servers
    if args.servers_url is not None:
        # TODO: validate URL
        log.debug('downloading servers file from: ' + args.servers_url)
        servers = servers + get(args.servers_url).text.splitlines()
    servers.sort()
    log.info('monitoring ' + str(len(servers)) + ' servers: ' + str(servers))

    gobbler = gobbler.Gobbler(servers, db)
    gobbler_thread = Thread(target=gobbler.init)
    gobbler_thread.setDaemon(True)
    gobbler_thread.start()

    proc = sp.run(['gunicorn', '-b', '127.0.0.1:' + str(args.port), '--workers', str(args.workers), 'main:app'])
    log.debug('stderr: ' + str(proc.stderr), file=sys.stderr)
