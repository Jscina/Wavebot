import time
import board
import busio
import adafruit_pca9685
from adafruit_servokit import ServoKit

# Initalize the Servokit with 16 channels (default for PCA9685)
kit = ServoKit(channels=16)

# Set up the PCA9685 via I2C communication

i2c = busio.I2C(board.SCL, board.SDA)

pwm = adafruit_pca9685.PCA9685(i2c)

pwm.set_pwm_freq(60)


def move_servo_180_degress(channel, delay=0.1):
	"""
	Function to move a servo from 0 degrees to 180 degress
	"""
	
	# Move from 0 to 180 degress
	
	for angle in range(0, 181,5): #Incremenet by 5 degree
		kit.servo[channel].angle = angle
		time.sleep(delay)
		
		
	# Move back from 180 degree to 0 degress
	
	for angle in range(180, 0, -5) #Decremenet by 5 degress
		kit.servo[channel].angle = angle
		time.sleep(delay)
		

#Test the function with the servo connected to channel 15
move_servo_180_degress(channel=15, delay=0.1)
