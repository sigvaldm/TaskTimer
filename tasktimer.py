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

    The finest resolution is 1ns.

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
    Alterantively, one can run

        print(timer)

    to print statistics, or fetch the variables directly from Timer for manual
    processing. They are:

        timer.last          Last lap time          t_N
        timer.total         Total elapsed time     sum_i(t_i)
        timer.mean          Mean lap time          sum_i(t_i)/N (= mu_N)
        timer.sum_sq_diff                          sum_i((t_i-mu_N)^2)
        timer.laps          Number of laps         N

    Timer will not grow slow and big as the number of laps increase, since these
    variables are computed in a running fashion using Welford's algorithm. The
    downside is that only the last lap is available for inspection.

    You can customize the formatting of time durations by providing your own
    format_time function. This should take the time in seconds (float) and
    return a string.

    Statistical quantities can be inferred from the member variables. Let's say
    you execute a program that runs a certain function func() that's being
    measured:

        timer = Timer()
        for i in range(N):
            timer.start()
            func()
            timer.stop()

    You can get the *actual* mean, standard deviation and variance from
    these laps as follows:

        timer.mean
        timer.stdev()
        timer.variance()

    This is what's called population statistics. You can also consider these
    laps to be only a sample of the whole population. For instance func() might
    be run an infinite amount of times and you just want to run it N times to
    get an *estimate* of its expected execution time and standard deviation in
    general, not just for these laps. Then you need to use estimators from the
    sample. The above three quantities are valid estimators, but the standard
    deviation and variance would be biased in this case (especially for few
    laps). Better estimators use Bessel's correction:

        timer.mean
        timer.sample_stdev()
        timer.sample_variance()

    The overhead in Timer is reasonably low (typically a few hundred ns per lap)
    but it's not compiled and no guarantees are given.
    """

    def __init__(self, verbose=False, format_time=format_time):
        self.reset()
        self.verbose = verbose

    def reset(self):
        "Reset timer."
        self.last         = 0
        self.total        = 0
        self.mean         = 0
        self.sum_sq_diff  = 0
        self.laps         = 0

    def start(self):
        "Start timer."
        self._start = t.time()

    def stop(self):
        "Stop timer (or initiate new lap)."
        new_time = t.time()
        elapsed = new_time - self._start
        self._start = new_time

        self.laps += 1
        self.last = elapsed
        self.total += elapsed

        delta1 = elapsed - self.mean
        self.mean += delta1/self.laps
        delta2 = elapsed - self.mean
        self.sum_sq_diff += delta1*delta2

        if self.verbose: print(self)

    def variance(self):
        "Computes population variance or biased estimate from sample"
        return self.sum_sq_diff/self.laps

    def stdev(self):
        "Computes population standard deviation or biased estimate from sample"
        return np.sqrt(self.variance())

    def sample_variance(self):
        "Computes unbiased variance estimate from sample"
        return self.sum_sq_diff/(max(self.laps-1),1)

    def sample_stdev(self):
        "Computes unbiased standard deviation estimate from sample"
        return np.sqrt(self.sample_variance())

    def __str__(self):
        s = "Last lap: {}, Total: {}, Mean: {}, StDev: {}, Laps: {}".format(
            format_time(self.last),
            format_time(self.total),
            format_time(self.mean),
            format_time(self.stdev()),
            self.laps
        )
        return s

GLOBALTIMER = Timer(True)

def tic():
    GLOBALTIMER.start()

def toc():
    GLOBALTIMER.stop()

class TaskTimer(object):

    def __init__(self, mode='compact', format_time=format_time):
        assert mode in ['simple','compact','quiet']
        self.mode = mode

        self.timers = OrderedDict()
        self.current = None

    def task(self, tag):

        if self.current != None:
            self.timers[self.current].stop()

        if not tag in self.timers:
            self.timers[tag] = Timer()

        self.timers[tag].start()
        self.current = tag

    def iterate(self, iterable, iterations=None):

        if iterations==None:
            self.laps = len(iterable)
        else:
            self.laps = iterations

        for i in iterable:
            yield i

class TaskTimerOld(object):
    """
    Tracks timing of several tasks in a loop and maintains progress status and
    statistics. Example:
    """

    def __init__(self, mode='compact', format_time=format_time):
        assert mode in ['simple','compact','quiet']
        self.mode = mode

        self.master = Timer()
        self.timers = OrderedDict()
        self.current = None
        self.laps = 0

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

    def iterate(self, iterable, iterations=None):

        if iterations==None:
            self.laps = len(iterable)
        else:
            self.laps = iterations

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
                      format_time(v.stdev()),
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

    timer = TaskTimer('simple')
    # timer.task("pre")

    for n in timer.iterate(["a","b","c","d"]):

        timer.task("Task A")
        t.sleep(0.1)
        # print(n)

        timer.task("Task B")
        t.sleep(0.2)

        timer.task("Task A")
        t.sleep(0.1)
    timer.summary()
