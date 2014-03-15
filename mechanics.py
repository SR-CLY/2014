from time import time, sleep
from math import copysign, floor, modf
from threading import Thread

from sr import INPUT_PULLUP


NOTCHES_ON_WHEEL = 4
ROBOT_RADIUS = 0.185
M_SWITCH_LEFT  = 13
M_SWITCH_RIGHT = 12
WHEEL_CIRCUMFERENCE = 0.31

# Notes on approximation:
#
# Average dt for right wheel notch at power = 50 is
#     30 ms.
# Same thing for left wheel is
#     70 ms.
# Right wheel usually turns a bit quicker, according to notches.

class Journey:
    """
    Handles straight or rotational movement using threading.
    """
    def __init__(self, robot, distance=0, angle=0):
        self.robot = robot
        rduino = self.robot.ruggeduinos[0]

        self.run = True
        if distance != 0:
            self.length = distance
        elif angle != 0:
            self.length = -angle * ROBOT_RADIUS
        else:
            self.run = False
            return

        turnsToDo = self.length / WHEEL_CIRCUMFERENCE
      
        self.m0 = Motor(robot.motors[0].m0, M_SWITCH_LEFT, rduino, turnsToDo)
        if angle != 0:
            turnsToDo *= -1
        self.m1 = Motor(robot.motors[0].m1, M_SWITCH_RIGHT, rduino, turnsToDo)

    def start(self):
        if self.run:
            self.m0.start()
            self.m1.start()
            self.m0.join()
            self.m1.join()
        else:
            print "Warning: cannot run zero-length journey."


class Motor(Thread):
    """
    Drives a motor a given number of turns using micro-switches or,
    for small distances, approximation. Runs concurrently.
    """
    def __init__(self, motor, switchID, rduino, turns):
        super(Motor, self).__init__()
        self.switchID = switchID
        self.motor = motor
        self.turns = turns
        self.ruggeduino = rduino
        self.ruggeduino.pin_mode(switchID, INPUT_PULLUP)

    def time_a_switch(self):
        """
        At exit point of this function switch is pressed.
        It returns time difference between 2 consecutive switch triggers
        """
        while self.ruggeduino_input() is False:
            pass
        start = time()
        while self.ruggeduino_input() is True:
            pass
        return time() - start

    def ruggeduino_input(self):
        return self.ruggeduino.digital_read(self.switchID)

    def run(self):
        triggers = abs(self.turns) * NOTCHES_ON_WHEEL
        if triggers < 2:
            # Probably need different powers for turning/moving forward of the robot
            self.motor.power = copysign(35, self.turns)
            sleep(5 * abs(self.turns) * WHEEL_CIRCUMFERENCE)
        else:
            self.motor.power = copysign(35, self.turns)
            total_t = 0
            i = 0

            start_dt = self.time_a_switch()
            for i in range(1, int(floor(triggers))):
                total_t += self.time_a_switch()

            if i != 0:
                average_dt = total_t / i

            if start_dt < average_dt:
                sleep(average_dt - start_dt)
            sleep(average_dt * modf(triggers)[0])
        self.stop()

    def stop(self):
        self.motor.power = -copysign(20, self.turns)
        sleep(0.1)
        self.motor.power = 0
