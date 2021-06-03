#!/usr/bin/env python3
import argparse
import logging as log
import random
import subprocess as sp
import sys
from threading import *

from flask import Flask, jsonify, request, render_template
from flask_limiter import Limiter
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


limiter = Limiter(
    app,
    key_func=get_ip_proxied,
    default_limits=['4 per second, 60 per minute']
)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', title='Index', servers=(db.get_servers()))


@app.route('/servers', methods=['GET'])
def api_servers():
    return jsonify(db.get_servers())


@app.route('/servers/<address>', methods=['GET'])
@limiter.limit('1/second,20/minute')
def api_servers_data(address):
    return jsonify(db.get_data(address))


@app.errorhandler(Exception)
def error_handler(exception: Exception):
    code = 418
    log.warning(str(exception))
    if isinstance(exception, HTTPException) and exception.code < 500:
        code = exception.code
    return render_template('error.html', title=str(code), text=str(code) + ' - ' + random.choice(GENERIC_ERRORS))


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

    gobbler_thread = Thread(target=gobbler.init, args=[args.servers, args.servers_url])
    gobbler_thread.setDaemon(True)
    gobbler_thread.start()

    proc = sp.run(['gunicorn', '-b', '127.0.0.1:' + str(args.port), '--workers', str(args.workers), 'main:app'])
    log.debug('stderr: ' + str(proc.stderr), file=sys.stderr)
