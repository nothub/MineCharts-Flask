#!/usr/bin/env python3
import argparse
import logging as log
import os
import random
import sqlite3
from threading import *

from flask import Flask, jsonify, make_response, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import gobbler
from lib import non_empty_string_type, positive_int_type, min_1000_int

FRESH_PRINCE = [
    "Now, this is a story all about how",
    "My life got flipped-turned upside down",
    "And I'd like to take a minute",
    "Just sit right there",
    "I'll tell you how I became the prince of a town called Bel Air",

    "In west Philadelphia born and raised",
    "On the playground was where I spent most of my days",
    "Chillin' out maxin' relaxin' all cool",
    "And all shootin some b-ball outside of the school",
    "When a couple of guys who were up to no good",
    "Started making trouble in my neighborhood",
    "I got in one little fight and my mom got scared",
    "She said 'You're movin' with your auntie and uncle in Bel Air'",

    "I begged and pleaded with her day after day",
    "But she packed my suit case and sent me on my way",
    "She gave me a kiss and then she gave me my ticket.",
    "I put my Walkman on and said, 'I might as well kick it'.",

    "First class, yo this is bad",
    "Drinking orange juice out of a champagne glass.",
    "Is this what the people of Bel-Air living like?",
    "Hmmmmm this might be alright.",

    "But wait I hear they're prissy, bourgeois, all that",
    "Is this the type of place that they just send this cool cat?",
    "I don't think so",
    "I'll see when I get there",
    "I hope they're prepared for the prince of Bel-Air",

    "Well, the plane landed and when I came out",
    "There was a dude who looked like a cop standing there with my name out",
    "I ain't trying to get arrested yet",
    "I just got here",
    "I sprang with the quickness like lightning, disappeared",

    "I whistled for a cab and when it came near",
    "The license plate said fresh and it had dice in the mirror",
    "If anything I could say that this cab was rare",
    "But I thought 'Nah, forget it' - 'Yo, homes to Bel Air'",

    "I pulled up to the house about 7 or 8",
    "And I yelled to the cabbie 'Yo homes smell ya later'",
    "I looked at my kingdom",
    "I was finally there",
    "To sit on my throne as the Prince of Bel Air"]

app = Flask(__name__)

# noinspection PyTypeChecker
api_limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=['4/second,60/minute']
)


# handler args:
# a = request.args.get('a', default = 1, type = int)
# b = request.args.get('b', default = 'b', type = str)

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
    return make_response(random.choice(FRESH_PRINCE), 418)


@app.errorhandler(429)
def err_handler_429(error):
    log.warning(str(error))
    return make_response(random.choice(FRESH_PRINCE), 418)


@app.route('/servers')
def api_servers():
    cur = sqlite3.connect(args.db_file).cursor()
    cur.execute('SELECT address FROM servers order by address')
    return jsonify(cur.fetchall())


@app.route('/servers/<address>')
@api_limiter.limit('1/second,20/minute')
def api_servers_data(address):
    cur = sqlite3.connect(args.db_file).cursor()
    cur.execute('SELECT time, players, ping FROM data WHERE address = (?) ORDER BY time DESC', [address])
    return jsonify(cur.fetchall())


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
        '-db', '--db-file',
        action='store',
        type=non_empty_string_type,
        required=False,
        default='data.db',
        metavar='FILE',
        help='name of database file, defaults to data.db'
    )
    parser.add_argument(
        '--check-delay',
        action='store',
        type=positive_int_type,
        required=False,
        default=10,
        metavar='SEC',
        help='min delay between checks in seconds, defaults to 10'
    )
    parser.add_argument(
        '--max-entries',
        action='store',
        type=min_1000_int,
        required=False,
        default=10000,
        metavar='MAX',
        help='max amount of db entries per server, defaults to 10000'
    )
    parser.add_argument(
        '--disable-autoclean',
        action='store_true',
        required=False,
        help='disables the automatic db cleanup'
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
    log.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=log.DEBUG)
    log.info('hello world!')
    gobbler_thread = Thread(target=gobbler.init, args=[args])
    gobbler_thread.setDaemon(True)
    gobbler_thread.start()
    log.info('starting web with args: ' + str(args))
    app.run(debug=True, host='0.0.0.0')
