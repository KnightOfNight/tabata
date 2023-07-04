"""tabata.py - run a Tabata style workout"""

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
_COLOR_PROMPT_MSG_ERROR = 41

_TITLE = 'TABATA TIMER'
_VERSION = 'V3.1.0'
_PROMPT = 'COMMAND'

LAST_MSG = ""

def run(cmd, background=False):
    """Run a command, optionally in the background."""
    debug('run(cmd="%s", background=%s)' % (cmd, background))

    if background:
        subprocess.Popen(cmd.split(' ')) #pylint: disable=consider-using-with
    else:
        subprocess.run(cmd.split(' '), check=True)

def say(msg, background=False):
    """Use the Mac program 'say' to verbalize a message."""
    debug('say(msg="%s", background=%s)' % (msg, background))

    start_time = time.time()
    cmd = 'say'+' '+msg
    run(cmd, background=background)
    end_time = time.time()

    return end_time - start_time

def debug(msg):
    """Print a debug message to stderr."""
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
    sys.stderr.write('%s DEBUG %s\n' % (timestamp, msg))

class Screen():
    """Class for the main screen."""
    # pylint: disable=too-many-instance-attributes
    def __init__(self, window):
        """Initialize the class."""
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

        curses.init_pair(_COLOR_PROMPT_MSG_ERROR, curses.COLOR_RED, curses.COLOR_BLACK)

        self.height = max_y
        self.width = max_x

        self.usable_last_y = self.height - 1
        self.usable_last_x = self.width - 2

        self.usable_start_x = 2
        self.usable_width = self.width - 2 - self.usable_start_x
        self.usable_offset = 1

        self.header()

    def header(self):
        """Add the screen header."""
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

    def status(self, set_idx, circuit_num, current_interval, next_interval):
        """Add the workout status to the screen."""
        debug('status(set_idx=%s, circuit_num=%s, current_interval=%s, next_interval=%s)'
              % (set_idx, circuit_num, current_interval, next_interval))

        if set_idx is not None:
            set_num_str = str(set_idx + 1)
        else:
            set_num_str = 'NONE'

        if circuit_num is not None:
            circuit_num_str = str(circuit_num)
        else:
            circuit_num_str = 'NONE'

        if not current_interval:
            current_interval = 'none'

        if not next_interval:
            next_interval = 'none'

        pos_y = 2
        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_HEADER))
        pos_x += self.usable_offset
        text = 'SET/CIRCUIT :'
        self.window.addstr(pos_y, pos_x, text, curses.color_pair(_COLOR_HEADER))
        self.window.addstr(pos_y, pos_x + len(text) + 1,
                           set_num_str + '/' + circuit_num_str, curses.color_pair(_COLOR_STATUS))

        pos_y += 1
        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_HEADER))
        pos_x += self.usable_offset
        text = 'CURRENT INTERVAL :'
        self.window.addstr(pos_y, pos_x, text, curses.color_pair(_COLOR_HEADER))
        self.window.addstr(pos_y, pos_x + len(text) + 1,
                           current_interval.upper(), curses.color_pair(_COLOR_STATUS))

        pos_y += 1
        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_HEADER))
        pos_x += self.usable_offset
        text = 'NEXT INTERVAL :'
        self.window.addstr(pos_y, pos_x, text, curses.color_pair(_COLOR_HEADER))
        self.window.addstr(pos_y, pos_x + len(text) + 1,
                           next_interval.upper(), curses.color_pair(_COLOR_STATUS))

    def prompt(self, help_msg=None, error_msg=None, error_msg_color=_COLOR_PROMPT):
        """Add a prompt line to the screen."""
        debug('prompt()')

        pos_y = self.usable_last_y - 1

        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_PROMPT))

        pos_x += self.usable_offset
        self.window.addstr(pos_y, pos_x, _PROMPT, curses.color_pair(_COLOR_PROMPT))
        pos_x += len(_PROMPT)

        if help_msg:
            next_str = ' [' + help_msg + '] : '
        else:
            next_str = ' : '

        self.window.addstr(pos_y, pos_x, next_str, curses.color_pair(_COLOR_PROMPT))
        pos_x += len(next_str)

        if error_msg:
            self.window.addstr(pos_y, pos_x, error_msg, curses.color_pair(error_msg_color))

        self.window.refresh()

    def key(self, timeout=-1, msg=None, allowed=None):
        """Get a key from the operator."""
        debug('key(timeout=%.3f, msg="%s", allowed="%s")' % (timeout, msg, allowed))

        if msg:
            (row, col) = self.window.getyx()
            self.window.addstr(row, col, msg)

        if allowed:
            prompt_help = ', '.join(allowed.values())
        else:
            prompt_help = None

        self.window.timeout(timeout)

        while True:
            self.prompt(help_msg=prompt_help)

            key_code = self.window.getch()

            if key_code == -1:
                return None

            key = chr(key_code)

            if allowed:
                if key in allowed:
                    return key

                self.prompt(help_msg=prompt_help, error_msg='invalid key',
                            error_msg_color=_COLOR_PROMPT_MSG_ERROR)

                time.sleep(3)

            else:
                return key

    def footer(self):
        """Add a footer to the screen."""
        debug('footer()')

        pos_y = self.usable_last_y

        pos_x = self.usable_start_x
        self.window.addstr(pos_y, pos_x, ' ' * self.usable_width, curses.color_pair(_COLOR_FOOTER))

        pos_x += self.usable_offset
        self.window.addstr(pos_y, pos_x, _TITLE, curses.color_pair(_COLOR_FOOTER))

        pos_x = self.usable_last_x - len(_VERSION) - self.usable_offset
        self.window.addstr(pos_y, pos_x, _VERSION, curses.color_pair(_COLOR_FOOTER))

        self.window.refresh()

    def timer(self, seconds, additional_messages=None):
        """Add a countdown timer to the screen."""
        debug('timer(seconds=%d)' % (seconds))

        assert seconds <= 5940

        remaining = seconds

        time_str_len = 5

        pos_y = int( (self.height / 2) - (characters.HEIGHT / 2) ) + 2
        pos_x = int( (self.width / 2) - (time_str_len * characters.SPACING / 2) )

        while remaining:
            time_str = "%.2d:%.2d" % (int(remaining / 60), remaining % 60)

            if remaining <= 10:
                color = curses.color_pair(_COLOR_CLOCK_RED)
            else:
                color = curses.color_pair(_COLOR_CLOCK_NORMAL)

            self._draw_time(time_str, color, pos_y, pos_x)

            key = self.key(timeout=0, allowed={'p':'(p)ause'})

            if key == 'p':
                key = self.key(allowed={'r':'(r)esume'})

            say_time = 0

            if remaining <= 5:
                say_time = say(str(remaining), background=True)

            elif additional_messages and remaining in additional_messages:
                msg = '%d seconds.' % (remaining)
                if additional_messages[remaining]:
                    msg += ' %s' % (additional_messages[remaining])
                say_time = say(msg, background=True)

            debug('say_time=%.3f' % say_time)

            sleep_time = max(0, 1 - say_time)
            debug('sleep_time=%.3f' % sleep_time)

            time.sleep(sleep_time)

            remaining -= 1

        self._draw_time('00:00', curses.color_pair(_COLOR_CLOCK_NORMAL), pos_y, pos_x)

    def _draw_time(self, time_str, color, row, col):
        """Draw a specific time string."""
        debug('_draw_time(time_str="%s", color="%s", row=%d, col=%d)' % (time_str, color, row, col))

        for character in time_str:
            self._draw_character(character, color, row, col)
            col += characters.SPACING

    def _draw_character(self, character, color, row, start_col):
        """Draw a specific character in a time string."""
        debug('_draw_character(c="%s", color="%s", row=%d, start_col=%d'
              % (character, color, row, start_col))

        config = characters.CHARACTERS[character]
        for line in config:
            col = start_col
            for column in line:
                if column == ' ':
                    pixel_color = curses.color_pair(_COLOR_CLOCK_BG)
                elif column == 'X':
                    pixel_color = color
                self.window.addstr(row, col, ' ', pixel_color)
                col += 1
            row += 1

class Workout():
    """Class for a workout."""
    # pylint: disable=too-many-instance-attributes
    def __init__(self, file):
        """Initialize the class."""
        debug('Workout.__init__')

        try:
            print('loading JSON')
            with open(file, 'r', encoding="utf-8") as workout_fp:
                workout = json.load(workout_fp)
        except FileNotFoundError:
            print('ERROR: file "%s" not found' % (file))
            sys.exit(1)

        self.start_time = workout['start_time']

        self.interval_exercise_time = workout['interval_exercise_time']
        self.interval_rest_time = workout['interval_rest_time']
        self.interval_switch_time = workout['interval_switch_time']

        self.circuits_per_set = workout['circuits_per_set']

        self.circuits = workout['circuits']

        self.sets_per_workout = len(self.circuits)
        self.set_last_idx = self.sets_per_workout - 1
        self.set_rest_time = workout['set_rest_time']

        self.first_interval = self.circuits[0][0]['name']

        self.rest_between_circuits = 'rest between circuits'
        self.rest_between_sets = 'rest between sets'

    def next_interval_in_circuit(self, set_idx, circuit_num, interval_idx):
        """Get the next interval in the specified set."""
        debug('next_interval_in_circuit(set_idx=%d, circuit_num=%d, interval_idx=%d)'
              % (set_idx, circuit_num, interval_idx))

        if interval_idx < self._last_interval_in_circuit(set_idx):
            next_interval = self.circuits[set_idx][interval_idx + 1]['name']

        elif circuit_num < self.circuits_per_set:
            next_interval = self.rest_between_circuits

        elif set_idx < self.set_last_idx:
            next_interval = self.rest_between_sets

        else:
            next_interval = 'none'

        return next_interval

    def _last_interval_in_circuit(self, set_idx):
        """Get the index of the last interval in the specified set."""
        debug('_last_interval_in_circuit(set_idx=%d)' % (set_idx))

        return len(self.circuits[set_idx]) - 1

    def next_interval_after_rest(self, set_idx, rest):
        """Get the next interval after a rest interval."""
        debug('next_interval_after_rest(set_idx=%d, rest="%s")' % (set_idx, rest))

        if rest == self.rest_between_circuits:
            next_interval = self.circuits[set_idx][0]['name']

        elif rest == self.rest_between_sets:
            next_interval = self.circuits[set_idx + 1][0]['name']

        return next_interval

def main(window):
    """Main program."""
    # pylint: disable=too-many-locals,too-many-statements
    workout = Workout('tabata.json')

    screen = Screen(window)
    screen.status(None, None, '', '')
    screen.timer(0)
    key = screen.key(allowed={'s':'(s)tart', 'q':'(q)uit'})
    if key == 'q':
        return

    msg = 'Starting in %d seconds. Get ready for %s!' % (workout.start_time, workout.first_interval)
    screen.status(None, None, 'get ready to start', workout.first_interval)
    say(msg, background=True)
    msgs = { 15 : '', }
    screen.timer(workout.start_time, additional_messages=msgs)

    for (set_idx, circuit) in enumerate(workout.circuits):

        for circuit_num in range(1, workout.circuits_per_set + 1):

            for (interval_idx, interval) in enumerate(circuit):
                interval_type = interval['type']
                interval_name = interval['name']
                next_interval = workout.next_interval_in_circuit(set_idx, circuit_num, interval_idx)

                msgs = None

                if interval_type == 'exercise':
                    interval_time = interval.get('time', workout.interval_exercise_time)
                    msg = '%s! START!' % (interval_name)
                    background = False

                elif interval_type == 'rest':
                    interval_time = interval.get('time', workout.interval_rest_time)
                    msg = 'Rest! Get ready for %s!' % (next_interval)
                    background = True
                    msgs = { 15 : '', }

                elif interval_type == 'switch':
                    interval_time = interval.get('time', workout.interval_switch_time)
                    msg = 'Switch sides!'
                    background = True

                else:
                    raise ValueError('invalid interval type "%s"' % interval_type)

                screen.status(set_idx, circuit_num, interval_name, next_interval)
                say(msg, background=background)
                screen.timer(interval_time, additional_messages=msgs)

            if circuit_num < workout.circuits_per_set:
                rest = workout.rest_between_circuits
                next_interval = workout.next_interval_after_rest(set_idx, rest)
                screen.status(set_idx, circuit_num, rest, next_interval)
                msg = 'Rest! Get ready for %s!' % (next_interval)
                say(msg, background=True)
                msgs = { 15 : '', }
                screen.timer(workout.interval_rest_time, additional_messages=msgs)

        if set_idx < workout.set_last_idx:
            rest = workout.rest_between_sets
            next_interval = workout.next_interval_after_rest(set_idx, rest)
            screen.status(set_idx, circuit_num, rest, next_interval)
            msg = 'Rest and hydrate!'
            say(msg, background=True)
            msgs = {
                15 : '',
                30 : 'Get ready for %s!' % (next_interval),
                60 : '',
            }
            screen.timer(workout.set_rest_time, additional_messages=msgs)

    screen.status(None, None, '', '')
    screen.timer(0)

    say('Great job! You did it!', background=False)

    screen.key(allowed={'q':'quit'})

curses.wrapper(main)

sys.exit(0)
