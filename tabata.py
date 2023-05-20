#!/usr/bin/env python3

import curses
import datetime
import json
import math
import signal
import subprocess
import sys
import time

import characters

_COLOR_NORMAL = 1
_COLOR_INVERSE = 2
_COLOR_RED = 3
_COLOR_GREEN = 4
_COLOR_BLUE = 5

_TITLE = 'TABATA TIMER'
_VERSION = 'Version 2.0.0'

LAST_MSG = ""

def handler(signum, frame):
    print()
    while True:
        try:
            key = input('Press "q" to exit, "r" to resume: ')
        except RuntimeError:
            print('Exiting.')
            sys.exit(0)
        if key == 'q':
            print('Exiting.')
            sys.exit(0)
        elif key == 'r':
            print(LAST_MSG)
            return
        else:
            print('Invalid key.')

# signal.signal(signal.SIGINT, handler)

def run(cmd):
    subprocess.run(cmd.split(' '))

def clearscr():
    run('clear')

def say(msg, newline=True):
    if newline:
        msg += '\n'
    start_time = time.time()
    sys.stdout.write(msg)
    sys.stdout.flush()
    cmd = 'say'+' '+msg
    run(cmd)
    end_time = time.time()
    return end_time - start_time

def countdown(timer, msg):
    assert timer >= 5

    diff_time = say(msg)

#    if timer > 10:
#        timer = math.ceil(timer - diff_time)

    if timer > 100:
        modulo = 30

    for remaining in range(timer, 0, -1):
        diff_time = 0

        if remaining > 100:
            modulo = 30
        else:
            modulo = 10

        if timer > 30 and remaining == 30:
            diff_time = say(str(remaining)+' seconds ', newline=False)
        elif remaining <= 5:
            diff_time = say(str(remaining)+' ', newline=False)
        elif not remaining % modulo:
            sys.stdout.write(str(remaining)+' ')
            sys.stdout.flush()

        wait = max(0, 1 - diff_time)

        time.sleep(wait)

    print()
    sys.stdout.flush()

def oldmain():
    global LAST_MSG

    try:
        with open('tabata.json', 'r') as f:
            routine = json.load(f)
    except FileNotFoundError:
        print('File "tabata.json" not found')
        sys.exit(1)

    start_time = routine['start_time']
    first_name = routine['groups'][0][0]['name']

    default_item_time = routine['item_time']
    default_rest_time = routine['item_rest_time']
    default_switch_time = routine['item_switch_time']

    num_rounds = routine['rounds']
    last_round = routine['rounds'] - 1
    round_rest_time = routine['round_rest_time']

    num_groups = len(routine['groups'])
    last_group = len(routine['groups']) - 1
    group_rest_time = routine['group_rest_time']

    clearscr()
    say('Hit return when ready to begin.', newline=False)
    input()

    clearscr()
    LAST_MSG = 'Starting in %d seconds.\n\nGet ready for %s.' % (start_time, first_name)
    countdown(start_time, LAST_MSG)

    for dogroup in range(0, num_groups):
        group = routine['groups'][dogroup]

        for doround in range(0, num_rounds):

            for doitem in range(0, len(group)):
                item = group[doitem]
                item_type = item['type']

                clearscr()
                print('Exercise group %d, round %d, %s' % (dogroup+1, doround+1, item_type))

                if item_type == 'exercise':
                    item_time = item.get('time', default_item_time)
                    text = item['name'].capitalize()
                    LAST_MSG = '%s for %d seconds. Start!' % (text, item_time)
                else:
                    if item_type == 'rest':
                        item_time = item.get('time', default_rest_time)
                        text = 'Rest'
                    elif item_type == 'switch':
                        item_time = item.get('time', default_switch_time)
                        text = 'Switch sides'
                    else:
                        print('Invalid item type "%s"' % item_type)
                        sys.exit(1)

                    next_item_name = group[doitem+1]['name']
                    LAST_MSG = '%s for %d seconds.\n\nGet ready for %s.' % (text, item_time, next_item_name)

                print()
                countdown(item_time, LAST_MSG)

            if doround < last_round:
                print()
                next_item_name = group[0]['name']
                LAST_MSG = 'Rest between rounds for %d seconds.\n\nGet ready for %s.' % (round_rest_time, next_item_name)
                countdown(round_rest_time, LAST_MSG)

        if dogroup < last_group:
            print()
            next_item_name = routine['groups'][dogroup+1][0]['name']
            LAST_MSG = 'Rest between groups for %d seconds.\n\nGet ready for %s.' % (group_rest_time, next_item_name)
            countdown(group_rest_time, LAST_MSG)
        else:
            clearscr()
            say('All done! You did it!')

class Screen():
    def __init__(self, window):
        self.window = window
        curses.init_pair(_COLOR_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(_COLOR_INVERSE, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(_COLOR_RED, curses.COLOR_BLACK, curses.COLOR_RED)
        curses.init_pair(_COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(_COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)

    def refresh(self):
        self.window.refresh()

    def header(self):
        (_, max_x) = self.window.getmaxyx()
        for row in range(0, 3):
            self.window.addstr(row, 0, ' ' * max_x, curses.color_pair(_COLOR_INVERSE))
        pos_x = int( (max_x / 2) - (len(_TITLE) / 2) )
        self.window.addstr(1, pos_x, _TITLE, curses.color_pair(_COLOR_INVERSE))

    def footer(self):
        (max_y, max_x) = self.window.getmaxyx()
        for row in range(max_y - 4, max_y - 1):
            self.window.addstr(row, 0, ' ' * max_x, curses.color_pair(_COLOR_INVERSE))
        pos_x = 2
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        self.window.addstr(max_y - 3, pos_x, date, curses.color_pair(_COLOR_INVERSE))
        pos_x = max_x - len(_VERSION) - 2
        self.window.addstr(max_y - 3, pos_x, _VERSION, curses.color_pair(_COLOR_INVERSE))

    def clear(self):
        (max_y, _) = self.window.getmaxyx()
        for row in range(3, max_y - 5):
            self.window.move(row, 0)
            self.window.clrtoeol()

    def number(self, number, start_y=5, start_x=5):
        config = characters.numbers(number)

        row_num = start_y

        for row in config:
            col_num = start_x

            for column in row:
                if column == ' ':
                    color = curses.color_pair(_COLOR_NORMAL)
                elif column == 'X':
                    color = curses.color_pair(_COLOR_RED)

                self.window.addstr(row_num, col_num, ' ', color)

                col_num += 1

            row_num += 1

    def key(self):
        return(self.window.getch())

def main(window):
    screen = Screen(window)
    screen.header()
    screen.footer()
    for number in range(0, 10):
        screen.number(number)
        screen.refresh()
        time.sleep(2)
    k = screen.key()

# oldmain()

for number in range(0, 10):
    config = characters.numbers(number)
    if len(config) != 9:
        print('error in number %d: invalid number of rows (%d)' % (number, len(config)))
    for row in config:
        if len(row) != 9:
            print('error in number %d: invalid number of columns (%d)' % (number, len(row)))

#sys.exit()

curses.wrapper(main)

sys.exit(0)
