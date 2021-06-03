import concurrent.futures
import logging as log
import time
from typing import Optional, Tuple, List

from mcstatus import MinecraftServer

import db


def poll_server(address: str) -> Tuple[str, Optional[int], Optional[int]]:
    log.debug('fetching data for: ' + address)
    try:
        # TODO: allow non standard ports
        status = MinecraftServer.lookup(address).status()
    except (IOError, ValueError):
        log.debug('error while fetching data for: ' + address)
        return address, None, None
    return address, status.players.online, round(status.latency)


class Gobbler:
    __servers: List[str]
    __db: db.DB

    def __init__(self, servers: List[str], db: db.DB):
        self.__servers = servers
        self.__db = db

    def init(self):
        while True:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for result in executor.map(poll_server, self.__servers):
                    address, players, ping = result
                    self.__db.write_data(address, players, ping)
                executor.shutdown(wait=True)
            # is this a race condition?
            log.debug('saved to db')
            time.sleep(10)
