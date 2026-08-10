#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, InfraredSensor, GyroSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait
from pybricks.robotics import DriveBase
# from pybricks.tools import wait, StopWatch, DataLog
# from pybricks.media.ev3dev import SoundFile, ImageFile

import termios, tty, sys
from umqtt.simple import MQTTClient

# Create your objects here.
ev3 = EV3Brick()

# Initialize motors at port A and B
right_motor, left_motor, fire_motor = Motor(Port.A), Motor(Port.D), Motor(Port.B)
#№ir_sensor = InfraredSensor(Port.S1)
#g_sensor = GyroSensor(Port.S4)

# Initialize Node-RED command states
Node_RED_Command = {
    'move_forward': False,
    'move_backward': False,
    'turn_right': False,
    'turn_left': False,
    'fire': False,
    'value': 0,
}

# MQTT callback function
def get_commands(topic, msg):
    payload = msg.decode()
    if " " in payload:
        command, value = payload.split(" ")
    else:
        command = payload
        value = 0

    Node_RED_Command['move_forward'] = False
    Node_RED_Command['move_backward'] = False
    Node_RED_Command['turn_left'] = False
    Node_RED_Command['turn_right'] = False
    Node_RED_Command['fire'] = False
    Node_RED_Command['value'] = int(value)

    if command == "MOVE_FORWARD":
        Node_RED_Command['move_forward'] = True
    if command == "MOVE_BACKWARD":
        Node_RED_Command['move_backward'] = True
    if command == "TURN_LEFT":
        # ev3.screen.load_image(ImageFile.MIDDLE_RIGHT)
        Node_RED_Command['turn_left'] = True
    if command == "TURN_RIGHT":
        # ev3.screen.load_image(ImageFile.MIDDLE_LEFT)
        Node_RED_Command['turn_right'] = True
    if command == "FIRE":
        Node_RED_Command['fire'] = True

# MQTT connection setup
MQTT_ClientID = 'Segway'
BROKER = '192.168.1.166'
client = MQTTClient(MQTT_ClientID, BROKER)
client.connect()

Topic = 'nodered/commands'
client.set_callback(get_commands)
client.publish(Topic, 'Publishing test')
client.subscribe(Topic)

# Stops both motors
def stop_motors():
    left_motor.stop()
    right_motor.stop()

# Main loop
while True: 
    try:
        left_motor.reset_angle(0)
        right_motor.reset_angle(0)
        # Segway balancing loop
        while True:
            # left_motor_angle, right_motor_angle = left_motor.angle(), right_motor.angle()

            client.check_msg()

            # MQTT mode
            if Node_RED_Command['move_forward'] == True:
                left_motor.reset_angle(0)
                right_motor.reset_angle(0)
                right_motor.run_target(1500, Node_RED_Command['value'] * 30, wait=False)
                left_motor.run_target(1500, Node_RED_Command['value'] * 30, wait=True)
                Node_RED_Command['move_forward'] = False

            if Node_RED_Command['move_backward'] == True:
                left_motor.reset_angle(0)
                right_motor.reset_angle(0)
                right_motor.run_target(1500, -Node_RED_Command['value'] * 30, wait=False)
                left_motor.run_target(1500, -Node_RED_Command['value'] * 30, wait=True)
                Node_RED_Command['move_backward'] = False

            if Node_RED_Command['turn_left'] == True:
                left_motor.reset_angle(0)
                right_motor.reset_angle(0)
                right_motor.run_target(1500, -Node_RED_Command['value'] * 4.4, wait=False)
                left_motor.run_target(1500, Node_RED_Command['value'] * 4.4, wait=True)
                Node_RED_Command['turn_left'] = False

            if Node_RED_Command['turn_right'] == True:
                left_motor.reset_angle(0)
                right_motor.reset_angle(0)
                right_motor.run_target(1500, Node_RED_Command['value'] * 4.4, wait=False)
                left_motor.run_target(1500, -Node_RED_Command['value'] * 4.4, wait=True)
                Node_RED_Command['turn_right'] = False

            if Node_RED_Command['fire'] == True:
                fire_motor.reset_angle(0)
                fire_motor.run_target(1500, 1080, wait=True)
                Node_RED_Command['fire'] = False
            
            # distance = ir_sensor.distance()
            # angle = Node_RED_Command['value'] + g_sensor.angle()

        # Stop all motors
        stop_motors()

    except KeyboardInterrupt:
        break # break out from main loop
        stop_motors()
        client.disconnect()

# test_motor.run_target(500, -90)
# Play another beep sound.
# ev3.speaker.beep(1000, 500)