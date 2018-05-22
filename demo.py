from tasktimer import TaskTimer
from time import sleep

timer = TaskTimer()

for n in timer.range(40):

    timer.task('Assembling load vector (b)')
    sleep(0.1) # Dummy

    timer.task('Solving linear system Au=b')
    sleep(0.5) # Dummy

print(timer)
