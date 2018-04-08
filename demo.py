from tasktimer import *
import time

timer = TaskTimer()

timer.task('Assembling stiffness matrix (A)')
time.sleep(5) # Dummy

for n in timer.range(40):

    timer.task('Assembling load vector (b)')
    time.sleep(1) # Dummy

    timer.task('Solving linear system Au=b')
    time.sleep(5) # Dummy

print(timer)
