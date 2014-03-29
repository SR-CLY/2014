from time import sleep
from traceback import print_exc
import math
from sr import Robot

from movements import Tracker, turn
from strategy import get_token_from_corner, token_to_slot


def main():
    robot = Robot()
    robot.position = Tracker(robot.zone)
    reset_log(robot)
    while 1:
        try:
            get_token_from_corner(robot, robot.zone)
            token_to_slot(robot, robot.zone)
        except:
            print_exc()
            reset_log(robot)
            print '\nRestarting in 2s...\n'
            sleep(2)


main()
