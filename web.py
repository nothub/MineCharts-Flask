#!/usr/bin/env python3
import argparse
import logging as log
import sqlite3

from flask import Flask, jsonify

from lib import positive_int_type, non_empty_string, init_logger

app = Flask(__name__)


@app.route('/')
def index():
    return 'index'


@app.route('/servers')
def api_servers():
    cur = sqlite3.connect(args.db_file).cursor()
    cur.execute('SELECT address FROM servers order by address')
    return jsonify(cur.fetchall())


@app.route('/servers/<address>')
def api_servers_data(address):
    # a = request.args.get('a', default = 1, type = int)
    # b = request.args.get('b', default = 'b', type = str)
    cur = sqlite3.connect(args.db_file).cursor()
    cur.execute('SELECT time, players, ping FROM data WHERE address = (?) ORDER BY time DESC', [address])
    return jsonify(cur.fetchall())


@app.errorhandler(404)
def page_not_found(error):
    'error: ' + str(error), 404


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-db', '--db-file',
        action='store',
        type=non_empty_string,
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
