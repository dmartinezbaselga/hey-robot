# timer.py

import time
from .logging import print_divider, print_value

class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""

class TimerCollection:

    def __init__(self, name) -> None:
        self._name = name
        
        self._total_time = 0.
        self._total_runs = 0
        self._last = 0.

        self._timer = None

    def start(self):
        self._timer = Timer(self._name, verbose=False)

    def stop(self):
        if self._timer is None:
            return

        self._last = self._timer.get_elapsed_time()
        self._total_time += self._last
        self._total_runs += 1
        self._timer = None
    
    def get_last(self):
        return self._last

    def report(self):
        if self._total_runs == 0:
            return
        print_divider()
        print(f"Timing for {self._name}")
        print_value("Average", f"{(self._total_time / self._total_runs):.1f}s")

class Timer:
    def __init__(self, name="", verbose=True):
        self._start_time = None
        self.name = name
        self.verbose = verbose
        self.start()

    def __del__(self):
        self.stop()

    def start(self):
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()

    def stop(self):
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        if not self.verbose:
            return
        
        if self.name != "":
            print(f"{self.name} took: {elapsed_time:0.1f} seconds")
        else:
            print(f"Elapsed time: {elapsed_time:0.1f} seconds")
    
    def get_elapsed_time(self):
        return time.perf_counter() - self._start_time