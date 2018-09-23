# Wishlist
#
# - Write "34:77 elapsed" and number of iterations
# - Allow changing "Step" with some loop name
#

from __future__ import print_function, division
import sys
if sys.version_info.major == 2:
    from itertools import izip as zip
    range = xrange

from itertools import count
import time as t
import math
import shutil
from collections import OrderedDict
from frmt import *

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

    You can customize the formatting of this output by providing your own Python
    format string using the 'format_string' argument. This string may contain
    the following positional arguments:

        0 - Last lap time
        1 - Total time
        2 - Mean lap time
        3 - Standard deviation
        4 - Number of laps

    For instance format_string="Elapsed time: {1}" may be used to show a simpler
    output only including the total time. The positional arguments 0-3 are
    formatted using the format_time function. To format time differently, you
    can supply your own 'format_time' argument. This must be a function taking
    the time in number of seconds (float) and returning a string. It should also
    be able to represent float('nan').

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
        timer.population_stdev()
        timer.population_variance()

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

    You can also use timer.stdev() or timer.variance() which are either
    population statistics or sample statistics depending on the argument
    'statistics'. These are the ones used for the output string.

    The overhead in Timer is reasonably low (typically a few hundred ns per lap)
    but it's not compiled and no guarantees are given. Printing results takes
    somewhat longer, naturally.
    """

    def __init__(self,
                 verbose=False,
                 format_string=None,
                 format_time=format_time,
                 statistics='population'):

        self.reset()
        self.verbose = verbose
        self.format_time = format_time
        self.format_string = format_string
        if self.format_string==None:
            self.format_string = "Last lap: {}, Total: {}, Mean: {}, "\
                                 "StDev: {}, Laps: {}"

        if statistics == 'population':
            self.stdev = self.population_stdev
            self.variance = self.population_variance
        elif statistics == 'sample':
            self.stdev = self.sample_stdev
            self.variance = self.sample_variance
        else:
            raise TypeError("statistics must be either 'population' or "\
                            "'sample'")

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

    def population_variance(self):
        "Computes population variance or biased estimate from sample."
        return self.sum_sq_diff/self.laps

    def population_stdev(self):
        "Computes population standard deviation or biased estimate from sample."
        return math.sqrt(self.variance())

    def sample_variance(self):
        "Computes unbiased variance estimate from sample."
        if self.laps==1:
            return float('nan')
        else:
            return self.sum_sq_diff/(self.laps-1)

    def sample_stdev(self):
        "Computes unbiased standard deviation estimate from sample."
        return math.sqrt(self.sample_variance())

    def __str__(self):
        s = self.format_string.format(
            self.format_time(self.last),
            self.format_time(self.total),
            self.format_time(self.mean),
            self.format_time(self.stdev()),
            self.laps
        )
        return s

# GLOBALTIMER = Timer(True, format_string="Elapsed time: {1}")
# def tic():
#     GLOBALTIMER.restart()
#     GLOBALTIMER.start()
# def toc():
#     GLOBALTIMER.stop()

class TaskTimer(object):
    """
    This object provides status information and time tracking of several tasks
    which may be run one or more times, and within a loop or not. This is useful
    to keep track of the progress in the code, while giving some simple feedback
    to the user (and possibly developer) about what takes time in the program.
    In the case of running a loop, progress information including estimated time
    left is displayed. Example:

        timer = TaskTimer()

        timer.task("Initialization")
        # Do something

        for n in timer.range(N):

            timer.task("Task A")
            # Do something

            timer.task("Task B")
            # Do something

            timer.task("Task A")
            # Do something

        print(timer)

    There are several modes of displaying the status. In 'compact' mode
    (default) the progress in a loop is displayed by updating the text on the
    same line.  This is the neatest, but breaks down if you try to print other
    data within the loop. Alternatively, there's 'simple' mode which prints the
    iteration number for each iteration on a separate line, and which therefore
    doesn't interfere with whatever you may want to print. It does not report
    the individual tasks within the loop. At last, there's 'quiet' in which
    nothing is printed but where you still gather statistics.

    You can customize the formatting of the status output displayed during a
    loop by providing your own 'format_string' argument. This string may contain
    the following positional arguments:

        0 - Iteration number
        1 - Total number of iterations
        2 - Progress in percent (as a float)
        3 - Estimated time remaining
        4 - Estimated total time

    For instance format_string="Estimated time remaining: {3}" may be used to
    show a simpler output only including the estimated time remaining. The
    positional arguments 3-4 are formatted using the format_time function. To
    format time differently, you can supply your own 'format_time' argument.
    This must be a function taking the time in number of seconds (float) and
    returning a string. It should also be able to represent float('nan').
    """

    def __init__(self,
                 mode='compact',
                 format_string=None,
                 format_time=format_time):
        assert mode in ['simple','compact','quiet']
        self.mode = mode

        self.master = Timer()
        self.timers = OrderedDict()
        self.current = None
        self.laps = 0
        self.in_progress = False
        self.format_time = format_time
        if format_string==None:
            self.format_string = "Step {}/{} ({:.0f}%). {} of {} remaining. {}"
        else:
            self.format_string = format_string

    def task(self, tag):
        """
        Define that here begins a new task. Each task is defined by a unique
        text string (tag) and may be repeated as many times as desirable.
        To mark the end of the previous task while not marking the transition to
        a new task call task(None).
        """

        if self.current != None:
            self.timers[self.current].stop()

        if tag != None:

            if not tag in self.timers:
                self.timers[tag] = Timer()

            self.timers[tag].start()

        self.current = tag

        if self.mode=='compact':
            self.status()

    def iterate(self, iterable, iterations=None, offset=0):
        """
        To get progress information when looping over a generic iterable, it can
        be wrapped in this function. Example:

            for letter in timer.iterate(["a","b","c","d"])
                # Do something with letter

        If the iterable does not have a __len__() function then number of
        iterations must be provided manually thourh the 'iterations' argument.

        It is also possible to offset the iteration count by an amount 'offset'.
        For instance in the above example the status text would by default
        progress through steps 0, 1, 2, 3 and finally 4 of 4. But let's say that
        you have previously already done 4 steps (perhaps you have restarted the
        program and it is able to continue where it left off). Then you are
        already half done from the outset, and you're actually starting at step
        4 of 8 eventhough your iterable only has 4 elements. Then you can set
        'offset' equal to 4.
        """

        if iterations==None:
            self.laps = len(iterable)
        else:
            self.laps = iterations

        self.offset = offset
        self.in_progress = True

        self.master.reset()
        self.master.start()
        for i in iterable:
            self.status()
            yield i
            self.task(None)
            self.master.stop()

        self.status(True)
        self.in_progress = False

    def range(self, start, stop=None):
        """
        In places where you would normally loop over range(), you can instead
        loop over timer.range() to get progress information. The difference
        between

            for n in timer.range(10,20):

        and

            for n in timer.iterate(range(10,20)):

        is that the former case will show progress information starting to count
        at 10 and ending in 20, whereas the latter will start at 0 and count to
        10. I.e. the 'offset' is set to 10 in the former case.
        """

        if stop==None:
            stop = start
            start = 0

        return self.iterate(range(start,stop), offset=start)

    def status(self,newline=False):

        if self.in_progress:
            lap = self.master.laps
            total_time = (self.laps/max(lap,1))*self.master.total
            eta = total_time-self.master.total
            progress = 100.0*(lap+self.offset)/(self.laps+self.offset)
            current = '' if self.current==None else self.current

            s = self.format_string.format(
                lap+self.offset,
                self.laps+self.offset,
                progress,
                format_time(eta),
                format_time(total_time),
                current
            )

            if self.mode=='compact':
                print("\r", format_fit(s), sep='', end='')
                if newline: print("")
            elif self.mode=='simple':
                print(s)

            sys.stdout.flush()

        else:
            print(self.current)

    def summary(self, sortcol=None, sortrev=False):
        """
        Formats a summary table of the tasks and their statistics. Example:

            print(timer.summary())

        or equivalently (if no arguments are given to summary()),

            print(timer)

        prints a table such as the following one:

                           #   Mean   StDev  Total    %
        Initialization     1  2.00s     0ns  2.00s   50
        Task A             8  101ms  85.7us  805ms   20
        Task B             4  301ms  85.2us  1.20s   30
        Total                                4.01s  100

        This table shows the number of executions of each task, the mean
        execution time, the standard deviation of the execution time, the total
        execution time, and the percentage of the total time usage of each task.

        If 'sortcol' equals a number the table will be sorted according to the
        column with that number (starting at zero). E.g. to sort by total
        execution time, 'sortcol' would be 4. To reverse the sorting order,
        'sortrev' should be True.
        """

        K = list(self.timers.keys())
        V = list(self.timers.values())

        table = []

        total_time = sum([v.total for v in V])
        for k,v in zip(K,V):
            fraction = 100*v.total/total_time
            row = [k, v.laps, v.mean, v.stdev(), v.total, fraction]
            table.append(row)

        if sortcol!=None:
            table.sort(key=lambda x: x[sortcol], reverse=sortrev)

        for i in range(len(table)):
            table[i][1] = "{:d}".format(table[i][1])
            table[i][2] = self.format_time(table[i][2])
            table[i][3] = self.format_time(table[i][3])
            table[i][4] = self.format_time(table[i][4])
            table[i][5] = "{:.0f}".format(table[i][5])

        header = ['', '#', 'Mean', 'StDev', 'Total', '%']
        footer = ['Total', '', '', '', self.format_time(total_time), '100']
        table.insert(0, header)
        table.append(footer)

        return format_table(table, '<>')

    def __str__(self):
        return self.summary()

if __name__ == "__main__":

    timer = TaskTimer('compact')

    timer.task("Initialization")
    t.sleep(2)

    for n in timer.iterate(["a","b","c","d"]):

        timer.task("Task A")
        t.sleep(0.1)

        timer.task("Task B"+20* " asdf")
        t.sleep(0.3)

        timer.task("Task A")
        t.sleep(0.1)

    print(timer.summary(sortcol=4,sortrev=True))
    print(timer)
