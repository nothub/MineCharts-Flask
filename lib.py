import argparse
import logging


def init_logger(logger, level: int = logging.INFO):
    logger.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=level)


def non_empty_string(s):
    s = str(s)
    if not s or not s.isprintable():
        raise argparse.ArgumentTypeError("invalid argument! value should be non empty")
    return s


def positive_int_type(n):
    n = int(n)
    if n <= 0:
        raise argparse.ArgumentTypeError("invalid argument! value should be positive")
    return n


def non_negative_int_type(n):
    n = int(n)
    if n < 0:
        raise argparse.ArgumentTypeError("invalid argument! value should be non negative")
    return n


def min_1000_int(n):
    n = int(n)
    if n < 1000:
        raise argparse.ArgumentTypeError("invalid argument! value should be >= 1000")
    return n
