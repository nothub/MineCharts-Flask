#!/usr/bin/env python3
import argparse
import concurrent.futures
import logging as log
import sqlite3
import time
from typing import Optional, Tuple, List

from mcstatus import MinecraftServer
from requests import get

from lib import non_empty_string_type, positive_int_type, init_logger, min_1000_int


def parse_args():
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
    return parser.parse_args()


def db_init(file: str) -> sqlite3.Connection:
    con = sqlite3.connect(file)
    cur = con.cursor()
    cur.execute(
        ''' CREATE TABLE IF NOT EXISTS servers
        (address TEXT NOT NULL UNIQUE PRIMARY KEY)'''
    )
    cur.execute(
        ''' CREATE TABLE IF NOT EXISTS data
        (address TEXT NOT NULL REFERENCES servers(address),
        time INTEGER NOT NULL,
        players INTEGER,
        ping INTEGER)'''
    )
    con.commit()
    return con


def parse_servers() -> List[str]:
    out = args.servers
    if args.servers_url is not None:
        log.info('downloading servers file from: ' + args.servers_url)
        out = out + get(args.servers_url).text.splitlines()
    out.sort()
    return out


def fetch_data(address: str) -> Tuple[str, Optional[int], Optional[int]]:
    log.debug('fetching data for: ' + address)
    try:
        # TODO: allow non standard ports
        status = MinecraftServer.lookup(address).status()
    except (IOError, ValueError):
        log.debug('error while fetching data for: ' + address)
        return address, None, None
    return address, status.players.online, round(status.latency)


def save_data(cursor, status):
    address, players, ping = status
    cursor.execute('INSERT OR IGNORE INTO servers VALUES (?)', [address])
    cursor.execute('INSERT INTO data VALUES (?,?,?,?)', (address, int(time.time()), players, ping))
    cursor.execute('SELECT COUNT(*) FROM data WHERE address = (?)', [address])
    if not args.disable_autoclean and int(cursor.fetchone()[0]) > args.max_entries:
        log.debug('removing oldest 100 entries for ' + address)
        cursor.execute('''DELETE FROM data WHERE address = (?) ORDER BY time ASC LIMIT 100''', [address])


if __name__ == '__main__':
    args = parse_args()
    init_logger(log, log.DEBUG)
    log.debug('starting gobbler with args: ' + str(args))
    servers = parse_servers()
    log.info('monitoring ' + str(len(servers)) + ' servers: ' + str(servers))
    db_con = db_init(args.db_file)
    while True:
        db_cur = db_con.cursor()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for result in executor.map(fetch_data, servers):
                save_data(db_cur, result)
        db_con.commit()
        db_cur.close()
        time.sleep(args.check_delay)
