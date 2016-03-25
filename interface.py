#! /usr/bin/env python

import serial,time
import struct
import binascii
import thread
from collections import deque

def f2b(i):
    return struct.pack('<f', i)


port_name = '/dev/ttyACM0'

ser = serial.Serial(
    port=port_name,
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)


class DobotStatusMessage():
	def __init__(self):
		pass
	
	message_length = 42	
	position = [-1,-1,-1, -1]  # x, y, z, yaw
	angles = [-1,-1,-1,-1]     # base, long, short, servo
	isGrab = False
	gripperAngle = -1
	
	def get_base_angle(self):
		return angles[0]
	
	def get_long_arm_angle(self):
		return angles[1]
	
	def get_short_arm_angle(self):
		return angles[2]

	def get_servo_angle(self):
		return angles[3]
		
	def parseAscii(self, ascii_list):
		assert isinstance(ascii_list, list)
		assert len(ascii_list) == self.message_length
		assert isinstance(ascii_list[0], str)
		assert ascii_list[0] == 'a5'
		assert ascii_list[-1] == '5a'
		
		for i in range(10):
			first_byte = i*4+1
			# and back to binary... TODO: remove ascii detour
			b = binascii.a2b_hex("".join(e for e in ascii_list[first_byte:first_byte+4])) 
			as_float = struct.unpack( '<f', b)[0]
			
			if i < 4:
				self.position[i] =  as_float 
			if i < 8:
				self.angles[i-4] =  as_float
			if i == 8:
				self.isGrab = as_float > 0
			if i == 9: # tenth float
				self.gripperAngle = as_float
		
		print self.isGrab, self.gripperAngle
		print self.position, self.angles
		
		

class DobotSerialInterface:
	
	def __init__(self):
		thread.start_new_thread(self.read_loop,())
	
	
	
	read_buffer = deque() # 

	def read_loop(self):
		while True:
			r = ser.read(20) 
			ascii =  binascii.b2a_hex(r) # b2a_hex(r) # hexlify
			for i in range(len(ascii)/2):
				self.read_buffer.append(ascii[2*i]+ascii[2*i+1])
			
			n = len(self.read_buffer)
			# print n
			if n < DobotStatusMessage.message_length:
				continue;
				
				
			# should not be triggered
			if len(self.read_buffer) > 100:
				print "read Buffer is expanding too fast"
		
			# remove stuff in front of 'A5'
			while len(self.read_buffer):
				s = self.read_buffer[0]
				if s == 'a5':
					break;
				self.read_buffer.popleft()
			
			n_cleaned = len(self.read_buffer)
			
			# print "Removed", (n-n_cleaned), "characters"
			if (n_cleaned < DobotStatusMessage.message_length):
				continue
				
			message = list()
			
			for i in range(DobotStatusMessage.message_length):
				message.append(self.read_buffer.popleft())
			
			# sanity check
			if message[-1] != '5a':
				print "Message was not terminated by '5a', but", message[-1], "ignoring message"
				continue
				
			# print "New message", message
			# TODO: do something with message
			msg = DobotStatusMessage()
			msg.parseAscii(message)
	
	
dobot_interface = DobotSerialInterface()


# Open Serial port will reset dobot, wait seconds
print "Wait 1 seconds..."
time.sleep(2) 

def dobot_cmd_send( cmd_str_10 ):
    global cmd_str_42
    cmd_str_42 = [ '\x00' for i in range(42) ]
    cmd_str_42[0]  = '\xA5'
    cmd_str_42[41] = '\x5A'
    for i in range(10):
        str4 = struct.pack( '<f', float(cmd_str_10[i]) )
        cmd_str_42[4*i+1] = str4[0]
        cmd_str_42[4*i+2] = str4[1]
        cmd_str_42[4*i+3] = str4[2]
        cmd_str_42[4*i+4] = str4[3]
    cmd_str = ''.join( cmd_str_42 )
    print "sending", binascii.b2a_hex( cmd_str )
    
    ser.write( cmd_str )

#state 3
def dobot_cmd_send_3( x = 265, y = 0, z = -30 ):
    global cmd_str_10
    cmd_str_10 = [ 0 for i in range(10) ]
    cmd_str_10[0] = 3
    cmd_str_10[2] = x
    cmd_str_10[3] = y
    cmd_str_10[4] = z
    cmd_str_10[7] = 2 # MOVL
    dobot_cmd_send( cmd_str_10 )

def dobot_cmd_send_9():
    global cmd_str_10
    cmd_str_10 = [ 0 for i in range(10) ]
    cmd_str_10[0] = 9
    cmd_str_10[1] = 1
    cmd_str_10[2] = 200 #JointVel
    cmd_str_10[3] = 200 #JointAcc
    cmd_str_10[4] = 200 #ServoVel
    cmd_str_10[5] = 200 #ServoAcc
    cmd_str_10[6] = 800 #LinearVel
    cmd_str_10[7] = 1000 #LinearAcc
    dobot_cmd_send( cmd_str_10 )

def dobot_cmd_send_10( VelRat = 100, AccRat = 100 ):
    global cmd_str_10
    cmd_str_10 = [ 0 for i in range(10) ]
    cmd_str_10[0] = 10
    cmd_str_10[2] = VelRat
    cmd_str_10[3] = AccRat
    dobot_cmd_send( cmd_str_10 )

sleep_duration = 2

dobot_cmd_send_9() #config
time.sleep( sleep_duration )
dobot_cmd_send_10() #config
time.sleep( sleep_duration )

while True:
	#print "Dobot Test Begin"
	#print i
	#i += 1
	dobot_cmd_send_3( 260, 0, 30 ) #MOVL
	time.sleep( sleep_duration )
	dobot_cmd_send_3( 240, 50, 0 ) #MOVL
	time.sleep( sleep_duration )
	# print "Dobot Test End"
