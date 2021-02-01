#!/usr/bin/env python3
import argparse
import logging as log
import sched
import sqlite3
import time
from typing import Optional, Tuple

from mcstatus import MinecraftServer
from requests import get


def fetch_data(address: str) -> Tuple[Optional[int], Optional[int]]:
    log.debug('fetching data for: ' + address)
    try:
        status = MinecraftServer.lookup(address).status()
    except (IOError, ValueError):
        log.warning('error while fetching data for: ' + address)
        return None, None
    return status.players.online, round(status.latency)


def work(address: str, cur: sqlite3.Cursor, max_entries: int):
    player, ping = fetch_data(address)
    cur.execute('INSERT OR IGNORE INTO servers VALUES (?)', [address])
    cur.execute('INSERT INTO data VALUES (?,?,?,?)', (address, int(time.time()), player, ping))


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


def parse_args():
    parser = argparse.ArgumentParser()
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
        '--max-entries',
        action='store',
        type=int,
        required=False,
        default=10000,
        metavar='MAX',
        help='max amount of entries per server, defaults to 10000'
    )
    parser.add_argument(
        '--check-delay',
        action='store',
        type=int,
        required=False,
        default=10,
        metavar='SEC',
        help='delay between checks in seconds, defaults to 10'
    )
    parser.add_argument(
        '--servers',
        action='extend',
        type=str,
        nargs='+',
        required=False,
        default=list(),
        metavar='ADDRESS',
        help='servers to be monitored, supplied as list'
    )
    parser.add_argument(
        '--servers-url',
        action='store',
        type=str,
        required=False,
        metavar='URL',
        help='servers to be monitored, supplied as url'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    log.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=log.DEBUG)
    log.debug('starting gobbler with args: ' + str(args))
    servers = args.servers
    if args.servers_url is not None:
        log.debug('downloading servers file from: ' + args.servers_url)
        servers = servers + get(args.servers_url).text.splitlines()
    servers.sort()
    log.info('monitored servers: ' + str(servers))
    timer = sched.scheduler(time.time, time.sleep)
    db_con = db_init(args.db_file)
    while True:
        db_cur = db_con.cursor()
        for srv in servers:
            timer.enter(delay=0, priority=0, action=work, argument=[srv, db_cur, args.max_entries])
        timer.run(blocking=True)
        db_con.commit()
        db_cur.close()
        time.sleep(args.check_delay)
