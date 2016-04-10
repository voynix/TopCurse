import curses
import re
import subprocess
import time

from collections import deque

TIME_STEP = 3.0 # seconds
HISTORY_LENGTH = 37

SECOND_LEVEL = 12
MISC_LEVEL = 17

UP_CHAR = '/'
DOWN_CHAR = '\\'
FLAT_CHAR = '-'

USER = 'user'
SYSTEM = 'system'
IDLE = 'idle'

class ProcessHistory:
    def __init__(self, pid, command):
        self.history_times = deque()
        self.history_cpus = deque()
        self.history_mems = deque()
        self.pid = pid
        self.command = command
        self.len = -1

    def add_sample(self, time, cpu, mem):
        self.history_times.append(time)
        self.history_cpus.append(cpu)
        self.history_mems.append(mem)
        self.len += 1
        if self.len > HISTORY_LENGTH:
            self.history_times.popleft()
            self.history_cpus.popleft()
            self.history_mems.popleft()
            self.len -= 1

    def get_most_recent_time(self):
        return self.history_times[self.len]

    def get_most_recent_cpu(self):
        return self.history_cpus[self.len]

    def get_most_recent_mem(self):
        return self.history_mems[self.len]

start_time = time.time()
compact_whitespace = re.compile(r'[ \t]+')
time_history = deque()
sorted_lists = deque()

proc_set = {}

pagein = 0
pagein_dif = 0
pageout = 0
pageout_dif = 0
swapin = 0
swapin_dif = 0
swapout = 0
swapout_dif = 0

usage_set = {}
usage_set[USER] = ProcessHistory(0, USER)
usage_set[SYSTEM] = ProcessHistory(1, SYSTEM)
usage_set[IDLE] = ProcessHistory(2, IDLE)

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
    curses.curs_set(0)
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
    curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_WHITE)
    FLAT_CHAR = curses.ACS_HLINE

    while True:
        # clear screen
        scr.clear()

        # gather and extract top data
        top_output = subprocess.check_output("top -n 10 -l 2 -o cpu -stats pid,cpu,command,mem".split(' '))
        lines = top_output.split('\n')[-11:-1]
        current_time = time.time()
        cur_list = {}
        for line in lines:
            parts = compact_whitespace.sub(' ', line).split(' ')
            pid, cpu, command, mem = parts[:4]
            name = "%s|%s" % (pid, command)
            cur_list[name] = float(cpu)
            if name not in proc_set:
                proc_set[name] = ProcessHistory(pid, command)
            proc_set[name].add_sample(current_time, float(cpu), mem)

        # gather and display vm_stat data
        vmstat_output = subprocess.check_output("vm_stat")
        lines = vmstat_output.split('\n')[-5:-1]
        for line in lines:
            parts = compact_whitespace.sub(' ', line[:-1]).split(' ')
            value = int(parts[1])
            if parts[0] == 'Pageins:':
                pagein_dif = value - pagein
                pagein = value
            elif parts[0] == 'Pageouts:':
                pageout_dif = value - pageout
                pageout = value
            elif parts[0] == 'Swapins:':
                swapin_dif = value - swapin
                swapin = value
            elif parts[0] == 'Swapouts:':
                swapout_dif = value - swapout
                swapout = value
        y = MISC_LEVEL
        x = 0
        scr.addstr(y, x, "MEMORY", curses.color_pair(11))
        scr.addstr(y+1, x, "Pageins/out: %i/%i (+%i/+%i)" % (pagein, pageout, pagein_dif, pageout_dif))
        scr.addstr(y+2, x, "Swapins/outs: %i/%i (+%i/+%i)" % (swapin, swapout, swapin_dif, swapout_dif))

        # sort and display processes
        sorted_list = sorted(cur_list, key=cur_list.get, reverse=True)
        y = 1
        x = 40
        #scr.addstr(y-1, x+2, "%3s %-20s %5s %6s" % ("PID", "PROCESS", "CPU", "MEMORY"), curses.color_pair(11))
        scr.addstr(y-1, x+2, "PID", curses.color_pair(11))
        scr.addstr(y-1, x+6, "PROCESS", curses.color_pair(11))
        scr.addstr(y-1, x+29, "CPU", curses.color_pair(11))
        scr.addstr(y-1, x+33, "MEMORY", curses.color_pair(11))
        for i in xrange(0, len(sorted_list)):
            name = sorted_list[i]
            scr.addstr(y, x, "%5s %-20s %5.1f %6s" % (proc_set[name].pid, proc_set[name].command,
                                                      proc_set[name].get_most_recent_cpu(),
                                                      proc_set[name].get_most_recent_mem()), curses.color_pair(i+1))
            y += 1

        sorted_lists.append(sorted_list)
        if len(sorted_lists) > HISTORY_LENGTH + 1:
            sorted_lists.popleft()

        x = 1
        most_recent = len(sorted_lists) - 1
        y = 1
        scr.addstr(y-1, x-1, "CPU (RELATIVE USAGE)", curses.color_pair(11))
        for i in xrange(0, len(sorted_lists)):
            if i == 0:
                if len(sorted_lists) >= HISTORY_LENGTH + 1:
                    continue
                else:
                    for l in xrange(0, len(sorted_lists[most_recent])):
                        if sorted_lists[most_recent][l] in sorted_lists[i]:
                            scr.addch(y + sorted_lists[i].index(sorted_lists[most_recent][l]), x,
                                      FLAT_CHAR, curses.color_pair(l+1))
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
                        scr.addch(y + sorted_lists[i].index(proc), x, char, curses.color_pair(l+1))
            x += 1

        y = MISC_LEVEL + 2
        x = 40
        scr.addstr(y-2, x, "DEBUG", curses.color_pair(11))
        # cull processes that haven't updated recently
        time_history.append(current_time)
        procs_to_kill = []
        if len(time_history) > HISTORY_LENGTH:
            limit_time = time_history.popleft()
            for proc in proc_set:
                if proc_set[proc].get_most_recent_time() <= limit_time:
                    #del proc_set[proc]
                    procs_to_kill.append(proc)
                    scr.addstr(y, x, "Culled %s for age" % proc)
                    y += 1
        for proc in procs_to_kill:
            del proc_set[proc]

        # wait till next iteration
        delta = TIME_STEP - ((time.time() - start_time) % TIME_STEP)
        scr.addstr(MISC_LEVEL+1, x, "Sleep Time: %f" % (delta / TIME_STEP))

        # render
        scr.refresh()

        time.sleep(delta)
except (Exception, KeyboardInterrupt) as e:
    quit_curses()
    print e