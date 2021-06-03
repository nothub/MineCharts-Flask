import argparse
from pathlib import Path


def non_empty_string_type(s):
    s = str(s)
    if not s or not s.isprintable():
        raise argparse.ArgumentTypeError("invalid argument! value should be non empty")
    return s


def positive_int_type(n: str) -> int:
    n = int(n)
    if n <= 0:
        raise argparse.ArgumentTypeError("invalid argument: value negative")
    return n


def network_port_type(n: str) -> int:
    n = int(n)
    if n < 1 or n > 65535:
        raise argparse.ArgumentTypeError("invalid argument: value out of range")
    return n


def str_to_file_path(s: str):
    path = Path(s)
    if path is None or (path.exists() and not path.is_file()):
        raise argparse.ArgumentTypeError("invalid argument! path is not a valid file path")
    return path
