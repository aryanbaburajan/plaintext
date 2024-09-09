import os

width = os.get_terminal_size().columns


def separator():
    print("_" * width)
