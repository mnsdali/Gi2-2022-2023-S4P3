
#LCDLIB
import I2C_LCD_driver

#ServoMotor
import time
from adafruit_servokit import ServoKit
#RFID RC522
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

import threading
import CommandThread

keypadInput = ""
secretCode = "*122#"
registerCode = "*100#"
authIDs = [1034121356282]
kit = ServoKit(channels=8)
rfid = SimpleMFRC522()

str_pad = " " * 16


#### LCD
mylcd = I2C_LCD_driver.lcd()

# These are the GPIO pin numbers where the
# lines of the keypad matrix are connected
L1 = 5
L2 = 6
L3 = 13
L4 = 19

# These are the four columns of Keypaf
C1 = 12
C2 = 16
C3 = 20
C4 = 21

# Setup GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(L1, GPIO.OUT)
GPIO.setup(L2, GPIO.OUT)
GPIO.setup(L3, GPIO.OUT)
GPIO.setup(L4, GPIO.OUT)

# Use the internal pull-down resistors
GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# This callback registers the key that was pressed
# if no other key is currently pressed
def keypadCallback(channel):
    global keypadPressed
    if keypadPressed == -1:
        keypadPressed = channel

# Detect the rising edges on the column lines of the
# keypad. This way, we can detect if the user presses
# a button when we send a pulse.
GPIO.add_event_detect(C1, GPIO.RISING, callback=keypadCallback)
GPIO.add_event_detect(C2, GPIO.RISING, callback=keypadCallback)
GPIO.add_event_detect(C3, GPIO.RISING, callback=keypadCallback)
GPIO.add_event_detect(C4, GPIO.RISING, callback=keypadCallback)

# Sets all lines to a specific state. This is a helper
# for detecting when the user releases a button
def setAllLines(state):
    GPIO.output(L1, state)
    GPIO.output(L2, state)
    GPIO.output(L3, state)
    GPIO.output(L4, state)

def checkSpecialKeys():
    
    global keypadInput, mainThread2, mainThread1
    pressed = False

    GPIO.output(L3, GPIO.HIGH)

    if (GPIO.input(C4) == 1):
        print("Input reset!")
        pressed = True

    GPIO.output(L3, GPIO.LOW)
    GPIO.output(L1, GPIO.HIGH)

    if (not pressed and GPIO.input(C4) == 1):
        if keypadInput == secretCode:
            thread3 = threading.Thread(target=display , args=("Welcome Admin!"))
            thread4 = threading.Thread(target=servoMotorTask)
            thread3.start()
            thread4.start()
            thread3.join()
            thread4.join()

        elif keypadInput == registerCode:
            mainThread1.pause()
            mainThread2.pause()
            print("Registration code!")   
            id, text = rfid.read_no_block()
            while id==None:
                print("No card has been present yet")
                id, text = rfid.read_no_block()
            
            if id in authIDs:
                print("Id already exists")
            else:
                authIDs.append(id)
                print("User has been added successfully")
            
            mainThread1.resume()
            mainThread2.resume()
        else: 
            display("Incorrect code!")
            
        pressed = True

    GPIO.output(L3, GPIO.LOW)

    if pressed:
        keypadInput = ""

    return pressed

# reads the columns and appends the value, that corresponds
# to the button, to a variable
def readLine(line, characters):
    global keypadInput
    # We have to send a pulse on each line to
    # detect button presses
    GPIO.output(line, GPIO.HIGH)
    if(GPIO.input(C1) == 1):
        keypadInput = keypadInput + characters[0]
    if(GPIO.input(C2) == 1):
        keypadInput = keypadInput + characters[1]
    if(GPIO.input(C3) == 1):
        keypadInput = keypadInput + characters[2]
    if(GPIO.input(C4) == 1):
        keypadInput = keypadInput + characters[3]
    GPIO.output(line, GPIO.LOW)

def keypadTask():

    keypadPressed = -1
    try:
        while True:
            # If a button was previously pressed,
            # check, whether the user has released it yet
            if keypadPressed != -1:
                setAllLines(GPIO.HIGH)
                if GPIO.input(keypadPressed) == 0:
                    keypadPressed = -1
                else:
                    time.sleep(0.1)
            # Otherwise, just read the input
            else:
                if not checkSpecialKeys():
                    readLine(L1, ["1","2","3","A"])
                    readLine(L2, ["4","5","6","B"])
                    readLine(L3, ["7","8","9","C"])
                    readLine(L4, ["*","0","#","D"])
                    time.sleep(0.1)
                else:
                    time.sleep(0.1)
        
    except KeyboardInterrupt:
        print("\nApplication stopped!")




def servoMotorTask():
    kit.servo[0].angle = 180
    kit.continuous_servo[1].throttle = 1
    time.sleep(1)
    kit.continuous_servo[1].throttle = -1
    time.sleep(1)
    kit.servo[0].angle = 0
    kit.continuous_servo[1].throttle = 0


def rfidReadTask():
    id, name = rfid.read()
    return id, name


#def rfidWriteTask():
#    name = input('New data:')
#    print("Now place your name  to write")
#    rfid.write(name)
#    print("Written")


def testId():
    while True:
        id, name = rfidReadTask()
        if id in authIDs:
            greeting = "Welcome " + name.title()
            thread1 = threading.Thread(target=display , args=(greeting))
            thread2 = threading.Thread(target=servoMotorTask)
            thread1.start()
            thread2.start()
            thread1.join()
            thread2.join()

        else:
            display("Acess Denied")




def display(message): #scroooooollllllll message
    message = str_pad + message

    for i in range (0, len(message)):
        lcd_text = message[i:(i+16)]
        mylcd.lcd_display_string(lcd_text,1)
        time.sleep(0.05)
        mylcd.lcd_display_string(str_pad,1)


mainThread1 = CommandThread(target=testId)
mainThread2 = CommandThread(target=keypadTask)
if __name__ == '__main__':
    try:
        mainThread1.start()
        mainThread2.start()
        mainThread1.join()
        mainThread2.join()

    finally:
        GPIO.cleanup()





