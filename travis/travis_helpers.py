# coding: utf-8
"""
helpers shared by the various QA tools
"""


RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
YELLOW_LIGHT = "\033[33m"
CLEAR = "\033[0;m"


def colorized(string, color):
    return '\n'.join(
        map(lambda line: color + line + CLEAR, string.split('\n')))

def green(string):
    return colorized(string, GREEN)


def yellow(string):
    return colorized(string, YELLOW)


def red(string):
    return colorized(string, RED)


def yellow_light(string):
    return colorized(string, YELLOW_LIGHT)


fail_msg = red("FAIL")
success_msg = green("Success")
