#!/usr/bin/env python3

import curses
import datetime
import json
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
_PROMPT = 'COMMAND : '

LAST_MSG = ""

def run(cmd, background=False):
    debug('run(cmd="%s",background=%s)' % (cmd, background))

    if background:
        subprocess.Popen(cmd.split(' '))
    else:
        subprocess.run(cmd.split(' '))

def say(msg, background=False):
    debug('say(msg="%s",background=%s)' % (msg, background))

    start_time = time.time()
    cmd = 'say'+' '+msg
    run(cmd, background=background)
    end_time = time.time()

    return end_time - start_time

def debug(msg):
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
    sys.stderr.write('%s DEBUG %s\n' % (timestamp, msg))

class Screen():
    def __init__(self, window):
        debug('Screen.__init__')

        self.window = window

        (max_y, max_x) = self.window.getmaxyx()

        debug('max_y=%d' % (max_y))
        debug('max_x=%d' % (max_x))

        assert max_y == 22, 'window must be 22 rows high, currently %d rows' % max_y

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
        debug('header()')

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

    def status(self, group_num, round_num, current_item, next_item):
        debug('status()')

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
        text = 'GROUP/ROUND :'
        self.window.addstr(pos_y, pos_x, text, curses.color_pair(_COLOR_HEADER))
        self.window.addstr(pos_y, pos_x + len(text) + 1, str(group_num) + '/' + str(round_num), curses.color_pair(_COLOR_STATUS))

        pos_y += 1
        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_HEADER))
        pos_x += self.usable_offset
        text = 'CURRENT ACTIVITY :'
        self.window.addstr(pos_y, pos_x, text, curses.color_pair(_COLOR_HEADER))
        self.window.addstr(pos_y, pos_x + len(text) + 1, current_item.upper(), curses.color_pair(_COLOR_STATUS))

        pos_y += 1
        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_HEADER))
        pos_x += self.usable_offset
        text = 'NEXT UP :'
        self.window.addstr(pos_y, pos_x, text, curses.color_pair(_COLOR_HEADER))
        self.window.addstr(pos_y, pos_x + len(text) + 1, next_item.upper(), curses.color_pair(_COLOR_STATUS))

        self.prompt()

    def prompt(self):
        debug('prompt()')

        pos_y = self.usable_last_y - 1

        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_PROMPT))

        pos_x += self.usable_offset
        self.window.addstr(pos_y, pos_x, _PROMPT, curses.color_pair(_COLOR_PROMPT))

        self.window.refresh()

    def footer(self):
        debug('footer()')

        pos_y = self.usable_last_y

        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_FOOTER))

        pos_x += self.usable_offset
        self.window.addstr(pos_y, pos_x, _TITLE, curses.color_pair(_COLOR_FOOTER))

        pos_x = self.usable_last_x - len(_VERSION) - self.usable_offset
        self.window.addstr(pos_y, pos_x, _VERSION, curses.color_pair(_COLOR_FOOTER))

        self.window.refresh()

    def timer(self, seconds):
        debug('timer(seconds=%d)' % (seconds))

        assert seconds <= 5940

        remaining = seconds

        time_str_len = 5

        pos_y = int( (self.height / 2) - (characters.height / 2) ) + 2
        pos_x = int( (self.width / 2) - (time_str_len * characters.spacing / 2) )

        while remaining:
            time_str = "%.2d:%.2d" % (int(remaining / 60), remaining % 60)

            if remaining <= 10:
                color = curses.color_pair(_COLOR_CLOCK_RED)
            else:
                color = curses.color_pair(_COLOR_CLOCK_NORMAL)

            self._draw_time(time_str, color, pos_y, pos_x)

            say_time = 0
            if remaining <= 5:
                say_time = say(str(remaining), background=True)
            elif remaining in [10, 15, 30, 60] and seconds >= 120:
                say_time = say(str(remaining) + ' seconds', background=True)
            debug('say_time=%.3f' % say_time)

            sleep_time = max(0, 1 - say_time)
            debug('sleep_time=%.3f' % sleep_time)

            time.sleep(sleep_time)

            remaining -= 1

        self._draw_time('00:00', curses.color_pair(_COLOR_CLOCK_NORMAL), pos_y, pos_x)

    def _draw_time(self, time_str, color, y, x):
        debug('_draw_time(time_str="%s",color="%s",y=%d,x=%d)' % (time_str, color, y, x))

        for c in time_str:
            self._draw_character(c, color, y, x)
            x += characters.spacing

        self.prompt()

    def _draw_character(self, c, color, y, start_x):
        debug('_draw_character(c="%s",color="%s",y=%d,start_x=%d' % (c, color, y, start_x))

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

    def key(self, timeout=-1, msg=None):
        debug('key(timeout=%.3f,msg="%s")' % (timeout, msg))

        self.window.timeout(timeout)
        if msg:
            (y, x) = self.window.getyx()
            self.window.addstr(y, x, msg)
        return(self.window.getch())

class Routine():
    def __init__(self, file):
        debug('Routine.__init__')

        try:
            print('loading JSON')
            with open(file, 'r') as f:
                routine = json.load(f)
        except FileNotFoundError:
            print('ERROR: file "%s" not found' % (file))
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
        debug('next_item_in_group(dogroup=%d,doround=%d,doitem=%d)' % (dogroup, doround, doitem))

        if doitem < self._last_item_in_group(dogroup):
            next_item = self.groups[dogroup][doitem + 1]['name']
        elif doround < self.last_round:
            next_item = self.rest_between_rounds
        elif dogroup < self.last_group:
            next_item = self.rest_between_groups
        else:
            next_item = 'none'
        return next_item

    def _last_item_in_group(self, dogroup):
        debug('_last_item_in_group(dogroup=%d)' % (dogroup))

        return len(self.groups[dogroup]) - 1

    def next_item_after_rest(self, dogroup, rest):
        debug('next_item_after_rest(dogroup=%d,rest="%s")' % (dogroup, rest))

        if rest == self.rest_between_rounds:
            next_item = self.groups[dogroup][0]['name']
        elif rest == self.rest_between_groups:
            next_item = self.groups[dogroup + 1][0]['name']
        return next_item

def main(window):
    routine = Routine('tabata.json')

    screen = Screen(window)
    screen.status(0, 0, '', '')
    screen.timer(0)
    msg = 'hit any key to start'
    say(msg, background=True)
    screen.key(msg='(%s) ' % (msg))

    msg = 'Starting in %d seconds. Get ready for %s!' % (routine.start_time, routine.first_exercise)
    screen.status(1, 1, 'get ready to start', routine.first_exercise)
    say(msg, background=True)
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
                    background = False

                elif item_type == 'rest':
                    item_time = item.get('time', routine.default_rest_time)
                    msg = 'Rest! Get ready for %s!' % (next_item)
                    background = True

                elif item_type == 'switch':
                    item_time = item.get('time', routine.default_switch_time)
                    msg = 'Switch sides! Get ready for %s!' % (next_item)
                    background = True

                else:
                    raise ValueError('invalid item type "%s"' % item_type)
    
                screen.status(dogroup + 1, doround + 1, item_name, next_item)
                say(msg, background=background)
                screen.timer(item_time)

            if doround < routine.last_round:
                rest = routine.rest_between_rounds
                next_item = routine.next_item_after_rest(dogroup, rest)
                screen.status(dogroup + 1, doround + 1, rest, next_item)
                msg = 'Rest! Get ready for %s!' % (next_item)
                say(msg, background=True)
                screen.timer(routine.round_rest_time)

        if dogroup < routine.last_group:
            rest = routine.rest_between_groups
            next_item = routine.next_item_after_rest(dogroup, rest)
            screen.status(dogroup + 1, doround + 1, rest, next_item)
            msg = 'Rest! Hydrate! Get ready for %s!' % (next_item)
            say(msg, background=True)
            screen.timer(routine.group_rest_time)

    screen.status(0, 0, '', '')
    screen.timer(0)

    say('Great job! You did it!', background=False)

    msg = 'hit any key to exit'
    say(msg, background=True)
    screen.key(msg='(%s) ' % (msg))

curses.wrapper(main)

sys.exit(0)
