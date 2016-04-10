import subprocess
# import curses
import time

TIME_STEP = 5.0 # seconds

class ProcessHistory:
    def __init__(self, pid, command):
        self.history = {}
        self.pid = pid
        self.command = command

    def add_sample(self, time, values):
        self.history[time] = values

    def get_most_recent_sample(self):
        return max(self.history.keys)

start_time = time.time()

while True:
    top_output = subprocess.check_output("top -n 10 -l 2 -o cpu -stats pid,cpu,command".split(' '))
    lines = top_output.split('\n')[-10:]
    print len(lines)
    time.sleep(TIME_STEP - ((time.time() - start_time) % TIME_STEP))