import logging as log
import sqlite3
import time
from sqlite3 import Connection
from typing import Optional, List, Tuple


def cursor_servers(con):
    cur = con.cursor()
    cur.execute('SELECT address FROM servers order by address')
    return cur


def cursor_server_data(address: str, con: Connection, entries: int):
    cur = con.cursor()
    cur.execute('SELECT time, players FROM players WHERE address = (?) ORDER BY time DESC LIMIT (?)', [address, entries])
    return cur


def cursor_latest_players(con: Connection):
    cur = con.cursor()
    cur.execute('SELECT players FROM (SELECT * FROM players ORDER BY time DESC) GROUP BY address')
    return cur


def cursor_ping(con: Connection):
    cur = con.cursor()
    cur.execute('SELECT ping FROM servers ORDER BY address')
    return cur


class DB:
    __db_file: str
    __max_entries: int

    def __init__(self, db_file: str = 'db.sqlite', max_entries: int = 2419200):
        self.__db_file = db_file
        self.__max_entries = max_entries
        with sqlite3.connect(self.__db_file) as con:
            cur = con.cursor()
            cur.execute(
                ''' CREATE TABLE IF NOT EXISTS servers
                (address TEXT NOT NULL UNIQUE PRIMARY KEY,
                ping INTEGER,
                logo TEXT)'''
            )
            cur.execute(
                ''' CREATE TABLE IF NOT EXISTS players
                (address TEXT NOT NULL REFERENCES servers(address),
                time INTEGER NOT NULL,
                players INTEGER)'''
            )
            cur.execute(
                ''' CREATE TABLE IF NOT EXISTS top
                (address TEXT NOT NULL UNIQUE REFERENCES servers(address),
                time INTEGER NOT NULL,
                players INTEGER)'''
            )
            con.commit()

    def get_servers(self) -> List[str]:
        with sqlite3.connect(self.__db_file) as con:
            return [i[0] for i in cursor_servers(con).fetchall()]

    def get_data(self, address: str, entries: int = 240) -> List[Tuple[int, Optional[int], Optional[int]]]:
        with sqlite3.connect(self.__db_file) as con:
            return cursor_server_data(address, con, entries).fetchall()

    def get_latest_players(self) -> List[Optional[int]]:
        with sqlite3.connect(self.__db_file) as con:
            return [i[0] for i in cursor_latest_players(con).fetchall()]

    def get_latest_ping(self) -> List[Optional[int]]:
        with sqlite3.connect(self.__db_file) as con:
            return [i[0] for i in cursor_ping(con).fetchall()]

    def write_data(self, address: str, players: Optional[int], ping: Optional[int], logo: Optional[str]):
        with sqlite3.connect(self.__db_file) as con:
            cur = con.cursor()
            cur.execute('REPLACE INTO servers VALUES (?,?,?)', (address, ping, logo))
            cur.execute('INSERT INTO players VALUES (?,?,?)', (address, int(time.time()), players))
            cur.execute('SELECT COUNT(*) FROM players WHERE address = (?)', [address])
            if int(cur.fetchone()[0]) > self.__max_entries:
                log.debug('removing oldest 100 entries for ' + address)
                cur.execute('''DELETE FROM players WHERE address = (?) ORDER BY time ASC LIMIT 100''', [address])
            con.commit()
