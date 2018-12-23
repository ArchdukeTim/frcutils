from datetime import datetime
from os import mkdir, chdir
from os.path import join
from subprocess import Popen, PIPE

try:
    import pyfrc
except:
    raise ImportError("Cannot generate robot project without pyfrc")

robot = """#!/usr/bin/env python3

import wpilib
import magicbot

class MyRobot(magicbot.MagicRobot):

    def createObjects(self):
        pass
    
    def autonomousInit(self):
        pass
    
    def autonomousPeriodic(self):
        pass
    
    def teleopInit(self):
        pass
    
    def teleopPeriodic(self):
        pass
    
    def disabledInit(self):
        pass
    
    def disabledPeriodic(self):
        pass

if __name__ == '__main__':
    wpilib.run(MyRobot)
"""


def generate():
    year = datetime.now().year
    rootdir = "%d-robot" % year

    mkdir(rootdir)
    mkdir(join(rootdir, "robot"))
    mkdir(join(rootdir, "tests"))
    mkdir(join(rootdir, "robot", "sim"))
    mkdir(join(rootdir, "robot", "components"))
    mkdir(join(rootdir, "robot", "autonomous"))
    mkdir(join(rootdir, "robot", "automations"))

    with open(join(rootdir, "robot", "robot.py"), "w") as f:
        f.write(robot)

    chdir(rootdir + "/robot")

    process = Popen(["python", "robot.py", "add-tests"], stdout=PIPE, stderr=PIPE)
    process.communicate()
