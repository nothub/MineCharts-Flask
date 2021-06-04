import concurrent.futures
import logging as log
import time
from typing import Optional, Tuple, List

from mcstatus import MinecraftServer

import db


def poll_server(address: str) -> Tuple[str, Optional[int], Optional[int], Optional[str]]:
    """
    Poll server and return a Tuple:
    address, players, ping, logo
    """
    log.debug('fetching data for: ' + address)
    try:
        # TODO: allow non standard ports
        status = MinecraftServer.lookup(address).status()
    except (IOError, ValueError):
        log.debug('error while fetching data for: ' + address)
        return address, None, None, None
    return address, status.players.online, round(status.latency), status.favicon if status.favicon else None


class Gobbler:
    __servers: List[str]
    __db: db.DB
    __active: bool = True

    def __init__(self, servers: List[str], db: db.DB):
        self.__servers = servers
        self.__db = db

    def shutdown(self):
        self.__active = False

    def init(self):
        while self.__active:
            time_start = time.time()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for result in executor.map(poll_server, self.__servers):
                    address, players, ping, logo = result
                    self.__db.write_data(address, players, ping, logo)
                executor.shutdown(wait=True)
            log.debug('saved to db')
            time_total = time.time() - time_start
            log.debug('polled servers in: ' + str(time_total) + '/15 seconds')
            if time_total > 15:
                log.warning('polling server data took very long: ' + str(time_total) + '/15 seconds')
                log.warning('consider increasing the polling delay!')
                time.sleep(1)
            else:
                time.sleep(15 - time_total)
