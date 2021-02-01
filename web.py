#!/usr/bin/env python3
import argparse
import sqlite3

from flask import Flask, jsonify

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
    cur.execute('SELECT time, players, ping FROM data WHERE address = (?) order by time limit (?)', [address, args.max_response_entries])
    return jsonify(cur.fetchall())


@app.errorhandler(404)
def page_not_found(error):
    'error: ' + str(error), 404


def parse_args():
    parser = argparse.ArgumentParser(prog='focal-standalone-init')
    parser.add_argument(
        '-db', '--db-file',
        action='store',
        type=str,
        required=False,
        default=':memory:',
        metavar='FILE',
        help='name of database file, defaults to ":memory:"'
    )
    parser.add_argument(
        '--max-response-entries',
        action='store',
        type=int,
        required=False,
        default=100,
        metavar='MAX',
        help='max amount of entries per response, defaults to 100'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    app.run(debug=True)
