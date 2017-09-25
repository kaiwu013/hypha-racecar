#!/usr/bin/env python

# Copyright (c) 2011, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the Willow Garage, Inc. nor the names of its
#      contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import rospy
import serial
import sys, select, termios, tty
import time
from time import sleep
# device port
port = rospy.get_param('~port', '/dev/uno')

# baudrate
baudrate = rospy.get_param('~baudrate', 115200)

# Check your COM port and baud rate
print ("Opening %s...", port)
try:
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=5)
except serial.serialutil.SerialException:
    print("IMU not found at port "+port + ". Did you specify the correct port in the launch file?")
    #exit
    sys.exit(0)

millis = int(round(time.time() * 1000))
print millis


msg = """
Control Your racecar!
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

space key, k : force stop
w/x: shift the middle pos of throttle by +/- 5 pwm
a/d: shift the middle pos of steering by +/- 2 pwm
CTRL-C to quit
"""

moveBindings = {
        'i':(1,0),
        'o':(1,-1),
        'j':(0,1),
        'l':(0,-1),
        'u':(1,1),
       # ',':(-1,0),
       # '.':(-1,1),
       # 'm':(-1,-1),
           }
moveBackBindings = {
        ',':(-1,0),
        '.':(-1,1),
        'm':(-1,-1),
	    }

def getKey():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def vels(speed,turn):
    return "currently:\tspeed %s\tturn %s " % (speed,turn)

if __name__=="__main__":
    settings = termios.tcgetattr(sys.stdin)
    
    rospy.init_node('racecar_teleop')


    count=0
    speed_mid = 1500 #(1500:stop, 1480:0.5m/s, 1450:2.5m/s)
    speed_bias = 0
    turn_mid = 90    #(0~180)
    turn_bias = 0
    control_speed = speed_mid
    control_turn = turn_mid
    try:
        print msg
        print vels(control_speed,control_turn)
        while(1):
            key = getKey()
            if key in moveBindings.keys():
                control_speed = -moveBindings[key][0]*50 + speed_mid + speed_bias
                control_turn = moveBindings[key][1]*30 + turn_mid + turn_bias
		count=0
	    elif key in moveBackBindings.keys():
		control_speed = -moveBackBindings[key][0]*100 + speed_mid + speed_bias
                control_turn = moveBackBindings[key][1]*30 + turn_mid + turn_bias
	        count=0
            elif key == ' ' or key == 'k' :
                control_speed = speed_mid + speed_bias
                control_turn = turn_mid + turn_bias
		count=0
            elif key == 'w' :
                speed_bias = speed_bias - 5
                control_speed = control_speed - 5
                print vels(control_speed,control_turn)
            elif key == 'x' :
                speed_bias = speed_bias + 5
                control_speed = control_speed + 5
                print vels(control_speed,control_turn)
            elif key == 'a' :
                turn_bias = turn_bias + 2
                control_turn = control_turn + 2
                print vels(control_speed,control_turn)
            elif key == 'd' :
                turn_bias = turn_bias - 2
                control_turn = control_turn - 2
                print vels(control_speed,control_turn)
            else:
                count = count + 1
                if count > 4:
                    control_speed = speed_mid + speed_bias
                    control_turn = turn_mid + turn_bias
                if (key == '\x03'):
                    break
	    if ((time.time() * 1000)-millis)> 20 :
	    	values=[str(control_turn),str(control_speed)]
	    	cmd = ",".join(values).encode()
	    	#ser.flushInput() 
	    	#print cmd
	    	ser.write(cmd)
		millis=time.time() * 1000

    except:
        print "error"

    finally:
	values=[str(turn_mid + turn_bias),str(speed_mid + speed_bias)]
	cmd = ",".join(values).encode() 
	ser.write(cmd)
	ser.close
	#f.close
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

