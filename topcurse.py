import curses
import re
import subprocess
import time

from collections import deque

TIME_STEP = 5.0 # seconds
OLD_PROCESS_LIMIT = 20

class ProcessHistory:
    def __init__(self, pid, command):
        self.history_times = []
        self.history_cpus = []
        self.pid = pid
        self.command = command
        self.len = -1

    def add_sample(self, time, cpu):
        self.history_times.append(time)
        self.history_cpus.append(cpu)
        self.len += 1

    def get_most_recent_time(self):
        return self.history_times[self.len]

    def get_most_recent_cpu(self):
        return self.history_cpus[self.len]

start_time = time.time()
compact_whitespace = re.compile(r'[ \t]+')
time_history = deque(maxlen=20)

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

    while True:
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

            sorted_list = sorted(cur_list, key=cur_list.get, reverse=True)
            y = 0
            x = 0
            scr.clear()
            for name in sorted_list:
                #print name, proc_set[name].history[current_time]
                scr.addstr(y, x, "%-16s %5.1f" % (proc_set[name].command, proc_set[name].get_most_recent_cpu()))
                y += 1

            # cull processes that haven't updated recently
            time_history.append(current_time)
            if len(time_history) > OLD_PROCESS_LIMIT:
                limit_time = time_history.popleft()
                for proc in proc_set:
                    if proc_set[proc].get_most_recent_time() <= limit_time:
                        del proc_set[proc]
                        scr.addstr(y, x, "culled %s for age" % proc)
                        y += 1

            scr.refresh()

            # wait till next iteration
            time.sleep(TIME_STEP - ((time.time() - start_time) % TIME_STEP))
except (Exception, KeyboardInterrupt) as e:
    quit_curses()
    print e