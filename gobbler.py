import concurrent.futures
import logging as log
import sqlite3
import time
from argparse import Namespace
from typing import Optional, Tuple, List

from mcstatus import MinecraftServer
from requests import get

ARGS: Namespace


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
    out = ARGS.servers
    if ARGS.servers_url is not None:
        log.debug('downloading servers file from: ' + ARGS.servers_url)
        out = out + get(ARGS.servers_url).text.splitlines()
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


def write_data(cursor, status):
    address, players, ping = status
    cursor.execute('INSERT OR IGNORE INTO servers VALUES (?)', [address])
    cursor.execute('INSERT INTO data VALUES (?,?,?,?)', (address, int(time.time()), players, ping))
    cursor.execute('SELECT COUNT(*) FROM data WHERE address = (?)', [address])
    if not ARGS.disable_autoclean and int(cursor.fetchone()[0]) > ARGS.max_entries:
        log.debug('removing oldest 100 entries for ' + address)
        cursor.execute('''DELETE FROM data WHERE address = (?) ORDER BY time ASC LIMIT 100''', [address])


def init(args: Namespace):
    global ARGS
    ARGS = args
    servers = parse_servers()
    log.info('monitoring ' + str(len(servers)) + ' servers: ' + str(servers))
    db_con = db_init(ARGS.db_path)
    while True:
        db_cur = db_con.cursor()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for result in executor.map(fetch_data, servers):
                write_data(db_cur, result)
            executor.shutdown(wait=True)
        # is this a race condition?
        db_con.commit()
        db_cur.close()
        log.debug('saved to db')
        time.sleep(ARGS.check_delay)
