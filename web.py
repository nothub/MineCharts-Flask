#!/usr/bin/env python3
import argparse
import logging as log
import os
import sqlite3

from flask import Flask, jsonify, make_response, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from lib import positive_int_type, non_empty_string_type, init_logger, fresh_prince_random

app = Flask(__name__)

# noinspection PyTypeChecker
api_limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=['4/second,60/minute']
)


@app.route('/')
def index():
    return 'index'


@app.route('/favicon.ico')
@api_limiter.limit('1/second,60/minute')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'assets/images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


@app.errorhandler(404)
def err_handler_404(error):
    log.warning(str(error))
    return make_response(fresh_prince_random(), 418)


@app.errorhandler(429)
def err_handler_429(error):
    log.warning(str(error))
    return make_response(fresh_prince_random(), 418)


@app.route('/servers')
def api_servers():
    cur = sqlite3.connect(args.db_file).cursor()
    cur.execute('SELECT address FROM servers order by address')
    return jsonify(cur.fetchall())


@app.route('/servers/<address>')
@api_limiter.limit('1/second,20/minute')
def api_servers_data(address):
    # a = request.args.get('a', default = 1, type = int)
    # b = request.args.get('b', default = 'b', type = str)
    cur = sqlite3.connect(args.db_file).cursor()
    cur.execute('SELECT time, players, ping FROM data WHERE address = (?) ORDER BY time DESC', [address])
    return jsonify(cur.fetchall())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-db', '--db-file',
        action='store',
        type=non_empty_string_type,
        required=False,
        default='data.db',
        metavar='FILE',
        help='name of database file, defaults to data.db'
    )
    parser.add_argument(  # TODO: unused
        '--max-response-entries',
        action='store',
        type=positive_int_type,
        required=False,
        default=1000,
        metavar='MAX',
        help='max amount of entries per response, defaults to 1000'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    init_logger(log)
    log.info('starting web with args: ' + str(args))
    app.run(debug=True)
