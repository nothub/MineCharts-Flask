import argparse


def non_empty_string_type(s):
    s = str(s)
    if not s or not s.isprintable():
        raise argparse.ArgumentTypeError("invalid argument! value should be non empty")
    return s


def positive_int_type(n):
    n = int(n)
    if n <= 0:
        raise argparse.ArgumentTypeError("invalid argument! value should be positive")
    return n


def min_1000_int(n):
    n = int(n)
    if n < 1000:
        raise argparse.ArgumentTypeError("invalid argument! value should be >= 1000")
    return n
