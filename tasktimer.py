# BUGS:
#
# - Header row is sometimes offset
# - Doesn't work when loop doesn't start on 0 (e.g. after reset)
# - 'compact' mode breaks when lines are too long
#

from __future__ import print_function, division
import sys
if sys.version_info.major == 2:
    from itertools import izip as zip
    range = xrange

import time as t
import numpy as np
from collections import OrderedDict

def format_time(seconds):
    """
    Formats a string from time given in seconds. For large times (seconds >= 60)
    the format is:

        dd:hh:mm:ss

    where dd, hh, mm and ss refers to days, hours, minutes and seconds,
    respectively. If the time is less than one day, the first block (dd:) is
    omitted, and so forth. Examples:

        format_time(24*60*60)   returns     "1:00:00:00"
        format_time(60*60)      returns     "1:00:00"
        format_time(60)         returns     "1:00"

    For small times (seconds < 60), the result is given in 3 significant
    figures, with units given in seconds and a suitable SI-prefix. Examples:

        format_time(10)         returns     "10.0s"
        format_time(1)          returns     "1.00s"
        format_time(0.01255)    returns     "12.6ms"
        format_time(1.255e-6)   returns     "1.26us"  rounds correctly

    """

    # Small times
    if seconds<1:
        milliseconds = 1000*seconds
        if milliseconds<1:
            microseconds = 1000*milliseconds
            if microseconds<1:
                nanoseconds = 1000*microseconds
                return "{:.0f}ns".format(nanoseconds)
            elif microseconds<10:
                return "{:.2f}us".format(microseconds)
            elif microseconds<100:
                return "{:.1f}us".format(microseconds)
            else:
                return "{:.0f}us".format(microseconds)
        elif milliseconds<10:
            return "{:.2f}ms".format(milliseconds)
        elif milliseconds<100:
            return "{:.1f}ms".format(milliseconds)
        else:
            return "{:.0f}ms".format(milliseconds)
    elif seconds<10:
            return "{:.2f}s".format(seconds)
    elif seconds<60:
            return "{:.1f}s".format(seconds)

    # Large times
    else:
        seconds = int(seconds)
        minutes = int(seconds/60)
        seconds %= 60
        if minutes<60:
            return "{:d}:{:02d}".format(minutes,seconds)
        else:
            hours = int(minutes/60)
            minutes %= 60
            if hours<24:
                return "{:d}:{:02d}:{:02d}".format(hours,minutes,seconds)
            else:
                days = int(hours/24)
                hours %= 24
                return "{:d}:{:02d}:{:02d}:{:02d}".format(
                    days,hours,minutes,seconds)

class Timer(object):
    """
    Timer acts like a stop watch. Start with start() and stop with stop().
    stop() also acts like a lap key when called several times. Example:

        timer = Timer(True)

        timer.start()
        # lap 1
        timer.stop()
        # lap 2
        timer.stop()

        # not counted

        timer.start()
        # lap 3
        timer.stop()

    If verbose is True, Timer will output statistics after every lap.
    One can also run

        print(timer)

    to print statistics, or fetch the variables directly from Timer for manual
    processing. They are:

        timer.last           Last lap time          t_N
        timer.total          Total elapsed time     sum_i(t_i)
        timer.mean_squared   Mean squared lap time  sum_i(t_i^2)/N
        timer.laps           Number of laps         N

    Timer will not grow slow and big as the number of laps increase, since these
    variables are computed in a running fashion. The downside, of course, is
    that only the last lap is available for inspection. One lap typically has an
    overhead of 2-300 ns (no guarantees).
    """

    def __init__(self, verbose=False, format_time=format_time):
        self.reset()
        self.verbose = verbose

    def reset(self):
        self.last         = 0
        self.total        = 0
        self.mean         = 0
        self.S            = 0
        self.mean_squared = 0
        self.sum_squared  = 0
        self.laps         = 0

    def start(self):
        self._start = t.time()

    def stop(self):
        new_time = t.time()
        elapsed = new_time - self._start
        self._start = new_time

        self.laps += 1
        self.last = elapsed
        self.total += elapsed

        self.mean_squared += (elapsed**2 - self.mean_squared)/self.laps
        self.sum_squared  += elapsed**2

        delta = elapsed - self.mean
        self.mean += delta/self.laps
        delta2 = elapsed - self.mean
        self.S += delta*delta2

        if self.verbose: print(self)

    def population_variance(self):
        self.mean = self.total/self.laps
        return self.mean_squared-self.mean**2

    def variance(self):
        return self.laps/max((self.laps-1),1) * self.population_variance()

    def population_stdev(self):
        return np.sqrt(self.population_variance())

    def stdev(self):
        return np.sqrt(self.variance())

    def mean(self):
        return self.total/self.laps

    def __str__(self):
        s = "Last lap: {}, Total: {}, Mean: {}, StDev: {}, Laps: {}".format(
            format_time(self.last),
            format_time(self.total),
            format_time(self.mean),
            format_time(self.stdev()),
            self.laps
        )
        return s

GLOBALTIMER = Timer()

def tic():
    GLOBALTIMER.start()

def toc():
    GLOBALTIMER.stop(True)

class TaskTimer(object):
    """
    Tracks timing of several tasks in a loop and maintains progress status and
    statistics. Example:
    """

    def __init__(self, mode='compact'):
        assert mode in ['simple','compact','quiet']
        self.mode = mode

        self.master = Timer()
        self.timers = OrderedDict()
        self.current = None
        self.laps = 1

    def task(self, tag):

        if self.current == None:
            self.master.start()

        if self.current != None:
            self.timers[self.current].stop()

        if not tag in self.timers:
            self.timers[tag] = Timer()

        self.timers[tag].start()
        self.current = tag

        if(self.mode=='compact'):
            print("\r",self,end='',sep='')
            sys.stdout.flush()

    def wrap(self, iterable):

        self.laps = len(iterable)

        for i in iterable:
            yield i
            self.end()

    def range(self, start, stop=None, step=1):

        if stop==None:
            stop = start
            start = 0

        rangeobj = range(start, stop, step)
        self.laps = len(rangeobj)

        for i in rangeobj:
            yield i
            self.end()

    def end(self):

        if self.current != None:
            self.timers[self.current].stop()
            self.master.stop()
            self.current = None

        if(self.mode=='simple'):
            print(self)

        if(self.mode=='compact'):
            print("\r",self,end='',sep='')
            sys.stdout.flush()
            if(self.master.laps==self.laps): print("\n")

    def summary(self):

        row = ['','Mean','StDev','Total','%']
        table = [row]

        K = list(self.timers.keys())
        V = list(self.timers.values())
        K.append('Total')
        V.append(self.master)

        for k,v in zip(K,V):
            fraction = 100
            if self.master.total != 0:
                fraction = 100*v.total/self.master.total
            row = [k, format_time(v.mean),
                      format_time(v.stdev),
                      format_time(v.total),
                      '{:.0f}'.format(fraction)]
            table.append(row)

        self.table = table

        colwidth = np.max(np.array([[len(a) for a in b] for b in table]),0)
        colwidth[1:] += 2 # column spacing

        s = ''
        for row in table:
            s += '{:<{w}}'.format(row[0],w=colwidth[0])
            for col,w in zip(row[1:],colwidth[1:]):
                s += '{:>{w}}'.format(col,w=w)
            s += "\n"

        print(s)

    def __str__(self):

        lap = self.master.laps
        total_time = (self.laps/max(lap,1))*self.master.total
        eta = total_time-self.master.total
        progress = 100.0*lap/self.laps
        width = max(len(a) for a in self.timers.keys())
        current = '' if self.current==None else self.current

        s  = "Completed step %i/%i (%.0f%%). "%(lap,self.laps,progress)
        s += "ETA: {} (total: {}). ".format(format_time(eta),format_time(total_time))
        s += "{:<{w}}".format(current,w=width)
        return s

if __name__ == "__main__":

    timer = Timer(False)
    for n in range(10000000):
        timer.start()
        timer.stop()

    # timer = Timer(False)
    # for n in range(100):
    #     timer.start()
    #     t.sleep(0.1)
    #     timer.stop()

    print(timer)
    print(timer.total/timer.laps)
    # timer = TaskTimer('simple')
    # timer.task("pre")

    # for n in timer.wrap(["a","b","c","d"]):

    #     timer.task("Task A")
    #     t.sleep(0.1)
    #     print(n)

    #     timer.task("Task B")
    #     t.sleep(0.2)

    # timer.summary()
