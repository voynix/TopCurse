import curses
import re
import subprocess
import time

from collections import deque

TIME_STEP = 5.0 # seconds
HISTORY_LENGTH = 20

UP_CHAR = '/'
DOWN_CHAR = '\\'
FLAT_CHAR = '-'

class ProcessHistory:
    def __init__(self, pid, command):
        self.history_times = deque()
        self.history_cpus = deque()
        self.pid = pid
        self.command = command
        self.len = -1

    def add_sample(self, time, cpu):
        self.history_times.append(time)
        self.history_cpus.append(cpu)
        self.len += 1
        if self.len > HISTORY_LENGTH:
            self.history_times.popleft()
            self.history_cpus.popleft()
            self.len -= 1

    def get_most_recent_time(self):
        return self.history_times[self.len]

    def get_most_recent_cpu(self):
        return self.history_cpus[self.len]

start_time = time.time()
compact_whitespace = re.compile(r'[ \t]+')
time_history = deque()
sorted_lists = deque()

proc_set = {}

# cleanup curses if something goes horribly wrong
def quit_curses():
    scr.keypad(0)
    curses.curs_set(1)
    curses.nocbreak()
    curses.echo()
    curses.endwin()

try:
    scr = curses.initscr()
    curses.noecho()
    curses.nocbreak()
    scr.keypad(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(10, curses.COLOR_WHITE, curses.COLOR_BLACK)
    FLAT_CHAR = curses.ACS_HLINE

    while True:
        # gather and extract data
        top_output = subprocess.check_output("top -n 10 -l 2 -o cpu -stats pid,cpu,command".split(' '))
        lines = top_output.split('\n')[-11:-1]
        current_time = time.time()
        cur_list = {}
        for line in lines:
            parts = compact_whitespace.sub(' ', line).split(' ')
            pid, cpu, command = parts[:3]
            name = "%s|%s" % (pid, command)
            cur_list[name] = float(cpu)
            if name not in proc_set:
                proc_set[name] = ProcessHistory(pid, command)
            proc_set[name].add_sample(current_time, float(cpu))

        # sort and display processes
        sorted_list = sorted(cur_list, key=cur_list.get, reverse=True)
        y = 1
        x = 25
        scr.clear()
        scr.addstr(y-1, x, "%5s %-20s %5s" % ("PID", "Process", "CPU"))
        for i in xrange(0, len(sorted_list)):
            name = sorted_list[i]
            scr.addstr(y, x, "%5s %-20s %5.1f" % (proc_set[name].pid, proc_set[name].command, proc_set[name].get_most_recent_cpu(), ), curses.color_pair(i+1))
            y += 1

        sorted_lists.append(sorted_list)
        if len(sorted_lists) > HISTORY_LENGTH + 1:
            sorted_lists.popleft()

        x = 1
        most_recent = len(sorted_lists) - 1
        base_y = 1
        for i in xrange(0, len(sorted_lists)):
            if i == 0:
                if len(sorted_lists) >= HISTORY_LENGTH + 1:
                    continue
                else:
                    for l in xrange(0, len(sorted_lists[most_recent])):
                        if sorted_lists[most_recent][l] in sorted_lists[i]:
                            scr.addch(base_y + sorted_lists[i].index(sorted_lists[most_recent][l]), x, FLAT_CHAR, curses.color_pair(l+1))
            else:
                for l in xrange(0, len(sorted_lists[most_recent])):
                    proc = sorted_lists[most_recent][l]
                    char = FLAT_CHAR
                    if proc in sorted_lists[i]:
                        if proc not in sorted_lists[i-1]:
                            char = UP_CHAR
                        else:
                            diff = sorted_lists[i].index(proc) - sorted_lists[i-1].index(proc)
                            if diff > 0:
                                char = DOWN_CHAR
                            elif diff < 0:
                                char = UP_CHAR
                        scr.addch(base_y + sorted_lists[i].index(proc), x, char, curses.color_pair(l+1))
            x += 1

        y = base_y + 12
        x = 0
        # cull processes that haven't updated recently
        time_history.append(current_time)
        procs_to_kill = []
        if len(time_history) > HISTORY_LENGTH:
            limit_time = time_history.popleft()
            for proc in proc_set:
                if proc_set[proc].get_most_recent_time() <= limit_time:
                    #del proc_set[proc]
                    procs_to_kill.append(proc)
                    scr.addstr(y, x, "culled %s for age" % proc)
                    y += 1
        for proc in procs_to_kill:
            del proc_set[proc]

        scr.refresh()

        # wait till next iteration
        time.sleep(TIME_STEP - ((time.time() - start_time) % TIME_STEP))
except (Exception, KeyboardInterrupt) as e:
    quit_curses()
    print e