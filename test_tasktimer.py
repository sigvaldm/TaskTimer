"""
Copyright 2018 Sigvald Marholm <marholm@marebakken.com>

This file is part of TaskTimer.

TaskTimer is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

TaskTimer is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with TaskTimer.  If not, see <http://www.gnu.org/licenses/>.
"""

from tasktimer import *
import pytest
from pytest import approx
from math import sqrt, isnan

@pytest.fixture
def time():

    class Time(object):

        def __init__(self):
            self.t = 0

        def set(self, t):
            self.t = t

        def __call__(self):
            return self.t

    return Time()

def prefill(timer):
    timer.last = 2
    timer.total = 4.5
    timer.mean = 1.5
    timer.sum_sq_diff = 0.5
    timer.laps = 3
    return timer

def test_Timer(time):

    timer = Timer(time_function=time)

    assert timer.last == approx(0)
    assert timer.total == approx(0)
    assert timer.mean == approx(0)
    assert timer.sum_sq_diff == approx(0)
    assert timer.laps == approx(0)
    assert isnan(timer.population_variance())
    assert isnan(timer.population_stdev())
    assert isnan(timer.sample_variance())
    assert isnan(timer.sample_stdev())

    time.set(4)
    timer.start()
    time.set(5.5)
    timer.stop()    # 1.5

    assert timer.last == approx(1.5)
    assert timer.total == approx(1.5)
    assert timer.mean == approx(1.5)
    assert timer.sum_sq_diff == approx(0)
    assert timer.laps == approx(1)
    assert timer.population_variance() == approx(0)
    assert timer.population_stdev() == approx(0)
    assert isnan(timer.sample_variance())
    assert isnan(timer.sample_stdev())

    time.set(7)
    timer.start()
    time.set(8)
    timer.stop()    # 1

    assert timer.last == approx(1)
    assert timer.total == approx(2.5)
    assert timer.mean == approx(1.25)
    assert timer.sum_sq_diff == approx(0.125)
    assert timer.laps == approx(2)
    assert timer.population_variance() == approx(0.0625)
    assert timer.population_stdev() == approx(sqrt(0.0625))
    assert timer.sample_variance() == approx(0.125)
    assert timer.sample_stdev() == approx(sqrt(0.125))

    time.set(11)
    timer.start()
    time.set(13)

    assert timer.laps == approx(2)

    timer.stop()    # 2

    assert timer.last == approx(2)
    assert timer.total == approx(4.5)
    assert timer.mean == approx(1.5)
    assert timer.sum_sq_diff == approx(0.5)
    assert timer.laps == approx(3)
    assert timer.population_variance() == approx(0.5/3)
    assert timer.sample_variance() == approx(0.5/2)
    assert timer.population_stdev() == approx(sqrt(0.5/3))
    assert timer.sample_stdev() == approx(sqrt(0.5/2))

    timer.reset()

    assert timer.last == approx(0)
    assert timer.total == approx(0)
    assert timer.mean == approx(0)
    assert timer.sum_sq_diff == approx(0)
    assert timer.laps == approx(0)
    assert isnan(timer.population_variance())
    assert isnan(timer.population_stdev())
    assert isnan(timer.sample_variance())
    assert isnan(timer.sample_stdev())

def test_Timer_statistics(caplog):

    timer = Timer(statistics='population')
    prefill(timer)
    assert timer.variance() == timer.population_variance()
    assert timer.stdev() == timer.population_stdev()

    timer = Timer(statistics='sample')
    prefill(timer)
    assert timer.variance() == timer.sample_variance()
    assert timer.stdev() == timer.sample_stdev()

    with pytest.raises(TypeError):
        timer = Timer(statistics='bullshit')
