import logging as log
import sqlite3
import time
from sqlite3 import Connection
from typing import Optional, List, Tuple


def cursor_server(con):
    cur = con.cursor()
    cur.execute('SELECT address FROM servers order by address')
    return cur


def cursor_data(address: str, con: Connection, entries: int):
    cur = con.cursor()
    cur.execute('SELECT time, players, ping FROM data WHERE address = (?) ORDER BY time DESC LIMIT (?)', [address, entries])
    return cur


class DB:
    __db_file: str
    __max_entries: int
    __auto_clean: bool

    def __init__(self, db_file: str = 'db.sqlite', max_entries: int = 10000, auto_clean: bool = True):
        self.__db_file = db_file
        self.__max_entries = max_entries
        self.__auto_clean = auto_clean
        with sqlite3.connect(self.__db_file) as con:
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

    def get_servers(self) -> List[str]:
        with sqlite3.connect(self.__db_file) as con:
            return [i[0] for i in cursor_server(con).fetchall()]

    def get_data(self, address: str, entries: int = 240) -> List[Tuple[int, Optional[int], Optional[int]]]:
        with sqlite3.connect(self.__db_file) as con:
            return cursor_data(address, con, entries).fetchall()

    def write_data(self, address: str, players: Optional[int], ping: Optional[int]):
        with sqlite3.connect(self.__db_file) as con:
            cur = con.cursor()
            cur.execute('INSERT OR IGNORE INTO servers VALUES (?)', [address])
            cur.execute('INSERT INTO data VALUES (?,?,?,?)', (address, int(time.time()), players, ping))
            cur.execute('SELECT COUNT(*) FROM data WHERE address = (?)', [address])
            if self.__auto_clean and int(cur.fetchone()[0]) > self.__max_entries:
                log.debug('removing oldest 100 entries for ' + address)
                cur.execute('''DELETE FROM data WHERE address = (?) ORDER BY time ASC LIMIT 100''', [address])
            con.commit()
