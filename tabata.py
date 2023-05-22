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

_COLOR_HEADER = 10

_COLOR_FOOTER = 15

_COLOR_STATUS = 20

_COLOR_CLOCK_BG = 30
_COLOR_CLOCK_NORMAL = 31
_COLOR_CLOCK_RED = 32

_COLOR_PROMPT = 40

_TITLE = 'TABATA TIMER'
_VERSION = 'V2.0.0'
_PROMPT = 'COMMAND: '

LAST_MSG = ""

def run(cmd):
    subprocess.run(cmd.split(' '))

def say(msg):
    start_time = time.time()
    cmd = 'say'+' '+msg
    run(cmd)
    end_time = time.time()
    return end_time - start_time

class Screen():
    def __init__(self, window):
        self.window = window

        (max_y, max_x) = self.window.getmaxyx()

        assert max_y == 22, 'window must be between 22 rows high, currently %d rows' % max_y

        curses.init_pair(_COLOR_HEADER, curses.COLOR_BLACK, curses.COLOR_WHITE)

        curses.init_pair(_COLOR_FOOTER, curses.COLOR_BLACK, curses.COLOR_WHITE)

        curses.init_pair(_COLOR_STATUS, curses.COLOR_BLUE, curses.COLOR_WHITE)

        curses.init_pair(_COLOR_CLOCK_BG, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(_COLOR_CLOCK_NORMAL, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(_COLOR_CLOCK_RED, curses.COLOR_BLACK, curses.COLOR_RED)

        curses.init_pair(_COLOR_PROMPT, curses.COLOR_WHITE, curses.COLOR_BLACK)

        self.height = max_y
        self.width = max_x

        self.usable_last_y = self.height - 1
        self.usable_last_x = self.width - 2

        self.usable_start_x = 2
        self.usable_width = self.width - 2 - self.usable_start_x
        self.usable_offset = 1

        self.header()

    def header(self):
        pos_y = 0
        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_HEADER))
        pos_x += self.usable_offset
        self.window.addstr(pos_y, pos_x, _TITLE, curses.color_pair(_COLOR_HEADER))
        pos_x = self.usable_last_x - len(_VERSION) - self.usable_offset
        self.window.addstr(pos_y, pos_x, _VERSION, curses.color_pair(_COLOR_HEADER))

        pos_y += 1
        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, '-' * self.usable_width, curses.color_pair(_COLOR_HEADER))

        self.window.refresh()

    def footer(self):
        pos_y = self.usable_last_y

        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_FOOTER))

        pos_x += self.usable_offset
        self.window.addstr(pos_y, pos_x, _TITLE, curses.color_pair(_COLOR_FOOTER))

        pos_x = self.usable_last_x - len(_VERSION) - self.usable_offset
        self.window.addstr(pos_y, pos_x, _VERSION, curses.color_pair(_COLOR_FOOTER))

        self.window.refresh()

    def status(self, group_num, round_num, current_item, next_item):
        if not group_num:
            group_num = 'NONE'

        if not round_num:
            round_num = 'NONE'

        if not current_item:
            current_item = 'none'

        if not next_item:
            next_item = 'none'

        pos_y = 2
        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_HEADER))
        pos_x += self.usable_offset
        key = 'GROUP/ROUND :'
        self.window.addstr(pos_y, pos_x, key, curses.color_pair(_COLOR_HEADER))
        self.window.addstr(pos_y, pos_x + len(key) + 1, str(group_num) + '/' + str(round_num), curses.color_pair(_COLOR_STATUS))

        pos_y += 1
        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_HEADER))
        pos_x += self.usable_offset
        key = 'CURRENT ACTIVITY :'
        self.window.addstr(pos_y, pos_x, key, curses.color_pair(_COLOR_HEADER))
        self.window.addstr(pos_y, pos_x + len(key) + 1, current_item.upper(), curses.color_pair(_COLOR_STATUS))

        pos_y += 1
        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_HEADER))
        pos_x += self.usable_offset
        key = 'NEXT UP :'
        self.window.addstr(pos_y, pos_x, key, curses.color_pair(_COLOR_HEADER))
        self.window.addstr(pos_y, pos_x + len(key) + 1, next_item.upper(), curses.color_pair(_COLOR_STATUS))

        self.prompt()

    def prompt(self):
        pos_y = self.usable_last_y

        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_PROMPT))

        pos_x += self.usable_offset
        self.window.addstr(pos_y, pos_x, _PROMPT, curses.color_pair(_COLOR_PROMPT))

        self.window.refresh()

    def timer(self, seconds):
        assert seconds <= 3600

        remaining = seconds

        time_str = "%.2d:%.2d" % (int(remaining / 60), remaining % 60)

        pos_y = int( (self.height / 2) - (characters.height / 2) ) + 2
        pos_x = int( (self.width / 2) - (len(time_str) * characters.spacing / 2) )

        while remaining:
            if remaining <= 10:
                color = curses.color_pair(_COLOR_CLOCK_RED)
            else:
                color = curses.color_pair(_COLOR_CLOCK_NORMAL)

            self._draw_time(time_str, color, pos_y, pos_x)

            cmd_time = 0

            if remaining <= 5:
                cmd_time = say(str(remaining))
            elif remaining in [10, 15, 30, 60] and seconds >= 120:
                cmd_time = say(str(remaining) + ' seconds')

            sleep_time = max(0, 1 - cmd_time)

            sys.stderr.write('DEBUG: say_time=%.3f\n' % cmd_time)
            sys.stderr.write('DEBUG: sleep_time=%.3f\n' % sleep_time)

            time.sleep(sleep_time)

            remaining -= 1

            time_str = "%.2d:%.2d" % (int(remaining / 60), remaining % 60)

        self._draw_time('     ', curses.color_pair(_COLOR_CLOCK_NORMAL), pos_y, pos_x)

    def _draw_time(self, time_str, color, y, x):
        for c in time_str:
            self._draw_character(c, color, y, x)
            x += characters.spacing

        self.prompt()

    def _draw_character(self, c, color, y, start_x):
        config = characters.characters(c)
        for row in config:
            x = start_x
            for column in row:
                if column == ' ':
                    pixel_color = curses.color_pair(_COLOR_CLOCK_BG)
                elif column == 'X':
                    pixel_color = color
                self.window.addstr(y, x, ' ', pixel_color)
                x += 1
            y += 1

    def key(self, timeout=-1):
        self.window.timeout(timeout)
        return(self.window.getch())

class Routine():
    def __init__(self):
        try:
            print('loading JSON')
            with open('tabata.json', 'r') as f:
                routine = json.load(f)
        except FileNotFoundError:
            print('ERROR: file "tabata.json" not found')
            sys.exit(1)

        self.start_time = routine['start_time']

        self.default_item_time = routine['item_time']
        self.default_rest_time = routine['item_rest_time']
        self.default_switch_time = routine['item_switch_time']

        self.num_rounds = routine['rounds']
        self.last_round = routine['rounds'] - 1
        self.round_rest_time = routine['round_rest_time']

        self.groups = routine['groups']
        self.num_groups = len(self.groups)
        self.last_group = len(self.groups) - 1
        self.group_rest_time = routine['group_rest_time']

        self.first_exercise = self.groups[0][0]['name']

        self.rest_between_rounds = 'rest between rounds'
        self.rest_between_groups = 'rest between groups'

    def next_item_in_group(self, dogroup, doround, doitem):
        if doitem < self.last_item(dogroup):
            next_item = self.groups[dogroup][doitem + 1]['name']
        elif doround < self.last_round:
            next_item = self.rest_between_rounds
        elif dogroup < self.last_group:
            next_item = self.rest_between_groups
        else:
            next_item = 'none'
        return next_item

    def next_item_after_rest(self, dogroup, rest):
        if rest == self.rest_between_rounds:
            next_item = self.groups[dogroup][0]['name']
        elif rest == self.rest_between_groups:
            next_item = self.groups[dogroup + 1][0]['name']
        return next_item

    def last_item(self, dogroup):
        return len(self.groups[dogroup]) - 1

def main(window):
    routine = Routine()

    screen = Screen(window)
    screen.status(0, 0, '', '')
    screen.key()

    # opening screen needed with "hit any key to begin"

    msg = 'Starting in %d seconds. Get ready for %s!' % (routine.start_time, routine.first_exercise)
    screen.status(1, 1, 'get ready to start', routine.first_exercise)
    say(msg)
    screen.timer(routine.start_time)

    for dogroup in range(0, routine.num_groups):
        group = routine.groups[dogroup]

        for doround in range(0, routine.num_rounds):

            for doitem in range(0, len(group)):
                item = group[doitem]
                item_type = item['type']
                item_name = item['name']
                next_item = routine.next_item_in_group(dogroup, doround, doitem)

                if item_type == 'exercise':
                    item_time = item.get('time', routine.default_item_time)
                    msg = '%s for %d seconds. START!' % (item_name, item_time)

                elif item_type == 'rest':
                    item_time = item.get('time', routine.default_rest_time)
                    msg = '%s for %d seconds. Get ready for %s!' % (item_name.capitalize(), item_time, next_item)

                elif item_type == 'switch':
                    item_time = item.get('time', routine.default_switch_time)
                    msg = '%s for %d seconds. Get ready for %s!' % (item_name.capitalize(), item_time, next_item)

                else:
                    raise ValueError('invalid item type "%s"' % item_type)
    
                screen.status(dogroup + 1, doround + 1, item_name, next_item)
                say(msg)
                screen.timer(item_time)

            if doround < routine.last_round:
                rest = routine.rest_between_rounds
                next_item = routine.next_item_after_rest(dogroup, rest)
                screen.status(dogroup + 1, doround + 1, rest, next_item)
                msg = '%s for %d seconds. Get ready for %s!' % (rest.capitalize(), routine.round_rest_time, next_item)
                say(msg)
                screen.timer(routine.round_rest_time)

        if dogroup < routine.last_group:
            rest = routine.rest_between_groups
            next_item = routine.next_item_after_rest(dogroup, rest)
            screen.status(dogroup + 1, doround + 1, rest, next_item)
            msg = '%s for %d seconds. Hydrate! Get ready for %s!' % (rest.capitalize(), routine.group_rest_time, next_item)
            say(msg)
            screen.timer(routine.group_rest_time)

    screen.status(0, 0, '', '')
    screen.key()

# oldmain()

curses.wrapper(main)

sys.exit(0)
