import concurrent.futures
import logging as log
import time
from typing import Optional, Tuple, List

from mcstatus import MinecraftServer
from requests import get

import db

db = db.DB()


def poll_server(address: str) -> Tuple[str, Optional[int], Optional[int]]:
    log.debug('fetching data for: ' + address)
    try:
        # TODO: allow non standard ports
        status = MinecraftServer.lookup(address).status()
    except (IOError, ValueError):
        log.debug('error while fetching data for: ' + address)
        return address, None, None
    return address, status.players.online, round(status.latency)


def init(servers: List[str], servers_url: str):
    out = servers
    if servers_url is not None:
        log.debug('downloading servers file from: ' + servers_url)
        out = out + get(servers_url).text.splitlines()
    # TODO: validate URL
    out.sort()
    servers = out
    log.info('monitoring ' + str(len(servers)) + ' servers: ' + str(servers))

    while True:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for result in executor.map(poll_server, servers):
                address, players, ping = result
                db.write_data(address, players, ping)
            executor.shutdown(wait=True)
        # is this a race condition?
        log.debug('saved to db')
        time.sleep(10)
