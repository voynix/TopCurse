import curses
import re
import subprocess
import time

from Queue import Queue

TIME_STEP = 5.0 # seconds
OLD_PROCESS_LIMIT = 20

class ProcessHistory:
    def __init__(self, pid, command):
        self.history = {}
        self.pid = pid
        self.command = command

    def add_sample(self, time, cpu):
        self.history[time] = cpu

    def get_most_recent_sample(self):
        return max(self.history.keys)

start_time = time.time()
compact_whitespace = re.compile(r'[ \t]+')''
time_history = Queue(maxsize=20)
time_history.put(start_time)

proc_set = {}

while True:
    top_output = subprocess.check_output("top -n 10 -l 2 -o cpu -stats pid,cpu,command".split(' '))
    lines = top_output.split('\n')[-11:-1]
    # print len(lines)

    current_time = time.time()
    cur_list = {}
    for line in lines:
        parts = compact_whitespace.sub(' ', line).split(' ')
        pid, cpu, command = parts[:3]
        name = "%s|%s" % (pid, command)
        cur_list[name] = float(cpu)
        if name not in proc_set:
            proc_set[name] = ProcessHistory(pid, command)
        proc_set[name].add_sample(current_time, cpu)

    sorted_list = sorted(cur_list, key=cur_list.get, reverse=True)
    print current_time
    for name in sorted_list:
        print name, proc_set[name].history[current_time]

    # cull processes that haven't updated recently
    limit_time = time_history.get()
    time_history.put(current_time)
    if time_history.full():
        for proc in proc_set:
            if proc_set[proc].get_most_recent_sample() <= limit_time:
                del proc_set[proc]

    # wait till next iteration
    time.sleep(TIME_STEP - ((time.time() - start_time) % TIME_STEP))