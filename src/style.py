import re


BOLD = '\x02'
COLOR = '\x03'
NORMAL = '\x0F'
REVERSED = '\x16'
UNDERLINE = '\x1F'

BLACK = '1'
NAVY_BLUE = '2'
GREEN = '3'
RED = '4'
BROWN = '5'
PURPLE = '6'
OLIVE = '7'
YELLOW = '8'
LIME_GREEN = '9'
TEAL = '10'
AQUA = '11'
BLUE = '12'
PINK = '13'
DARK_GRAY = '14'
LIGHT_GRAY = '15'
WHITE = '16'


def remove(text):

    return re.sub('(\x02|\x1F|\x16|\x0F|(\x03(\d+(,\d+)?)?)?)', '', text)


def bold(text):

    return BOLD + text + BOLD


def color(text, foreground, background=None):

    color_code = COLOR

    if foreground: color_code += foreground

    if background: color_code += ',%s' % background

    return color_code + text + (COLOR * 3)


def normal(text):

    return NORMAL + text + NORMAL


def reversed(text):

    return REVERSED + text + REVERSED


def underline(text):

    return UNDERLINE + text + UNDERLINE
