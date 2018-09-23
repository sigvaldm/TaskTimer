TaskTimer
=========

.. image:: https://travis-ci.com/sigvaldm/TaskTimer.svg?branch=master
    :target: https://travis-ci.com/sigvaldm/TaskTimer

.. image:: https://coveralls.io/repos/github/sigvaldm/TaskTimer/badge.svg?branch=master
    :target: https://coveralls.io/github/sigvaldm/TaskTimer?branch=master

.. image:: https://img.shields.io/pypi/pyversions/TaskTimer.svg
    :target: https://pypi.org/project/TaskTimer

Indicates progress during runtime, while keeping track of time consumed by user-defined tasks. Not quite a progress bar, not quite a profiler, but something in between which I personally have found to be very handy, especially when working with computationally intensive programs.

Consider this simple dummy program::

    from tasktimer import TaskTimer
    from time import sleep

    timer = TaskTimer()

    for n in timer.range(40):

        timer.task('Assembling load vector (b)')
        sleep(0.1) # Dummy

        timer.task('Solving linear system Au=b')
        sleep(0.5) # Dummy

    print(timer)
    
The ``task()`` method is used to indicate that from now on the program is working on another task. ``TaskTimer`` will indicate progress, and display the current task, for instance::

    Step 11/40 (28%). 17.5s of 24.1s remaining. Assembling load vector (b)

When all tasks are completed, ``print(timer)`` can be used to print statistics of the tasks::

                                 #   Mean   StDev  Total    %
    Assembling load vector (b)  40  101ms  89.2us  4.02s   17
    Solving linear system Au=b  40  501ms   140us  20.0s   83
    Total                                          24.1s  100

Many more options than demonstrated here are available, and the functionality is extensively documented in the docstrings. For instance, customization of the progress string (see ``TaskTimer``), iterating over general iterables using the ``iterate()`` method, sorting the statistics (see the ``summary()`` method). The time tracking of the individual tasks are performed by the ``Timer`` class, which can also be used stand-alone.

Installation
------------
Install from PyPI using ``pip``::

    pip install TaskTimer

Or download the GitHub repository https://github.com/sigvaldm/TaskTimer.git and run::

    python setup.py install
