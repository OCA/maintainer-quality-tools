# coding: utf-8
"""
helpers shared by the various QA tools
"""


RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
YELLOW_LIGHT = "\033[33m"
CLEAR = "\033[0;m"


def colorized(text, color):
    return '\n'.join(
        map(lambda line: color + line + CLEAR, text.split('\n')))


def green(text):
    return colorized(text, GREEN)


def yellow(text):
    return colorized(text, YELLOW)


def red(text):
    return colorized(text, RED)


def yellow_light(text):
    return colorized(text, YELLOW_LIGHT)


fail_msg = red("FAIL")
success_msg = green("Success")
