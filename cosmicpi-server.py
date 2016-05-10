#!	/usr/bin/python
#	coding: utf8

"""
Handle UDP packets from the cosmic pi and log then
julian.lewis lewis.julian@gmail.com 26/Feb/2016
"""

import sys
import socket
import select
import serial
import time
import traceback
import os
import termios
import fcntl
import re
import ast
from optparse import OptionParser
import httplib, urllib

# Handle keyboard input

class KeyBoard(object):

	def __init__(self):
		self.fd = sys.stdin.fileno()

	def echo_off(self):
		self.oldterm = termios.tcgetattr(self.fd)
		self.newattr = termios.tcgetattr(self.fd)
		self.newattr[3] = self.newattr[3] & ~termios.ICANON & ~termios.ECHO
		termios.tcsetattr(self.fd, termios.TCSANOW, self.newattr)
		self.oldflags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
		fcntl.fcntl(self.fd, fcntl.F_SETFL, self.oldflags | os.O_NONBLOCK)

	def echo_on(self):
		termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.oldterm)
		fcntl.fcntl(self.fd, fcntl.F_SETFL, self.oldflags)

	def test_input(self):
		res = False

		try:
			c = sys.stdin.read(1)
			if c == '>':
				res = True
		except IOError: pass
		return res

class Socket_io(object):

	def __init__(self,ipport):
		try:
			self.sik = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.sik.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
			self.sik.setblocking(0)
			self.sik.bind(("",ipport))

		except Exception, e:
			msg = "Exception: Can't open Socket: %s" % (e)
			print msg
			sys.exit(1)

	def recv_event_pkt(self):
		try:
			available = select.select([self.sik], [], [], 1)
			if available[0]:
				recv = self.sik.recvfrom(2048)
				return recv

		except Exception, e:
			msg = "Exception: Can't recvfrom: %s" % (e)
			print msg

		return ["",""]

	def close(self):
		self.sik.close()

# Send notifications to registered mobile phones
# Currently I am using pushover and the client has to install the
# pushover app and register a user and application token.
# The client supplies the keys on the cosmic pi client launch command line

class Notifications(object):

	def send_ntf(self,kyp,msg):

		nstr = kyp.split('-')

		self.conn = httplib.HTTPSConnection("api.pushover.net:443")

		self.conn.request(	"POST", "/1/messages.json",
					urllib.urlencode({	"token"  : nstr[1],
    								"user"   : nstr[0],
    								"sound"  : "Cosmic",
    								"message": msg}),
				{ "Content-type": "application/x-www-form-urlencoded" })

		self.conn.getresponse()

# Each cosmic pi client can register with the server
# We check package sequence numbers, hardware status

class Registrations(object):

	def __init__(self):

		self.reg = {"Ipa":"s","Sqn":0,"Pat":"s","Ntf":False,"Htu":"0","Bmp":"0","Acl":"0","Mag":"0"}
		self.regs = []

	def get_len(self):
		return len(self.regs)

	def get_index_by_value(self,knam,kval):
		if self.reg.has_key(knam):
			for i in range(0,len(self.regs)):
				if self.regs[i][knam] == kval:
					return i
		return False

	def get_reg_by_value(self,knam,kval):
		if self.reg.has_key(knam):
			for i in range(0,len(self.regs)):
				if self.regs[i][knam] == kval:
					return self.regs[i]
		return False

	def get_reg_by_index(self,indx):
	  	if indx in range(0,len(self.regs)):
			return self.regs[indx]
		return False

	def get_create_reg(self,knam,kval):
		r = self.get_reg_by_value(knam,kval)
		if r == False:
			i = len(self.regs)
			self.regs.append(self.reg.copy())
			self.regs[i][knam] = kval
			return self.regs[i]
		else:
			return r

	def set_reg(self,r):
		i = self.get_index_by_value("Ipa",r["Ipa"])
		if i == False:
			return False
		self.regs[i] = r.copy()
		return True

# This is the event object, it builds a dictionary from incomming json strings
# and provides access to the dictionary entries containing the data for each field.

class Event(object):

	def __init__(self):

		# These are the UDP packets containing json strings we are expecting

		self.temperature = { "temperature":"0.0","humidity":"0.0" }
		self.barometer = { "temperature":"0.0","pressure":"0.0","altitude":"0.0" }
		self.vibration = { "direction":"0","count":"0" }
		self.magnetometer = { "x":"0.0","y":"0.0","z":"0.0" }
		self.MOG = { "Mox":"0.0","Moy":"0.0","Moz":"0.0" }
		self.accelerometer = { "x":"0.0","y":"0.0","z":"0.0" }
		self.AOL = { "Aox":"0.0","Aoy":"0.0","Aoz":"0.0" }
		self.location = { "latitude":"0.0","longitude":"0.0","altitude":"0.0" }
		self.timing = { "uptime":"0","counter_frequency":"0","time_string":"0" }
		self.status = { "queue_size":"0","missed_events":"0","buffer_error":"0","temp_status":"0","baro_status":"0","accel_status":"0","mag_status":"0","gps_status":"0" }
		self.event = { "event_number":"0","counter_frequency":"0","ticks":"0","timestamp":"0.0","adc":"[[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]" }
		self.date = { "date":"s" }

		# Add ons

		self.date = { "date":"s" }		# Date
		self.sequence = { "number":"0" }		# Sequence number
		self.PAT = { "Pat":"s","Ntf":"0" }	# Pushover application token

		# Now build the main dictionary with one entry for each json string we will process

		self.recd = {	"temperature":self.temperature, "barometer":self.barometer, "vibration":self.vibration, "magnetometer":self.magnetometer, "MOG":self.MOG,
				"accelerometer":self.accelerometer, "AOL":self.AOL, "location":self.location, "timing":self.timing, "status":self.status,
				"event":self.event, "date":self.date, "sequence":self.sequence, "PAT":self.PAT }

		self.newpat = False
		self.newsqn = False

	# Convert the incomming json strings into entries in the dictionary

	def parse(self, line):					# parse the incomming json strings from arduino
		nstr = line.replace('\n','')			# Throw away <crtn>, we dont want them
		try:
			dic = ast.literal_eval(nstr)		# Build a dictionary entry
			kys = dic.keys()			# Get key names, the first is the address
			if self.recd.has_key(kys[0]):		# Check we know about records with this key
				self.recd[kys[0]] = dic[kys[0]]	# and put it in the dictionary at that address

			if kys[0] == "PAT":
				self.newpat = True

			if kys[0] == "sequence":
				self.newsqn = True

		except Exception, e:
			pass					# Didnt understand, throw it away

	# Here we just return dictionaries

	def get_vib(self):
		return self.recd["vibration"]

	def get_tim(self):
		return self.recd["timing"]

	def get_loc(self):
		return self.recd["location"]

	def get_sts(self):
		return self.recd["status"]

	def get_bmp(self):
		return self.recd["barometer"]

	def get_acl(self):
		return self.recd["accelerometer"]

	def get_mag(self):
		return self.recd["magnetometer"]

	def get_htu(self):
		return self.recd["temperature"]

	def get_evt(self):
		return self.recd["event"]

	def get_dat(self):
		return self.recd["date"]

	def get_sqn(self):
		return self.recd["sequence"]

	def get_pat(self):
		return self.recd["PAT"]


def main():
	use = "Usage: %prog [--port=4901 --odir=/tmp]"
	parser = OptionParser(usage=use, version="cosmic_pi_server version 1.0")
	parser.add_option("-p", "--port",  help="Server portnumber", dest="ipport", type="int", default="15443")
	parser.add_option("-d", "--debug", help="Debug Option", dest="debug", default=False, action="store_true")
	parser.add_option("-o", "--odir",  help="Path to log directory", dest="logdir", default="/tmp")
	parser.add_option("-n", "--nolog", help="Event Logging", dest="logflg", default=True, action="store_false")

	options, args = parser.parse_args()

	ipport = options.ipport
	logdir = options.logdir
	debug  = options.debug
	logflg = options.logflg

	print ""
	print "cosmic_pi server running, hit '>' for commands\n"

	print "options (Server Port number)	port:%d" % ipport
	print "options (Logging directory)	odir:%s" % logdir
	print "options (Event logging)		log: %s" % logflg

	file_name = "/tmp/pi-server-lock"
	fp = open(file_name, 'w')
	try:
		fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
	except Exception, e:
		print "Lock file:%s is in use" % (file_name)
		print "Only one instance of the server can run at any one time"
		print "Please kill the other instance or remove the lock file"
		sys.exit(1)

	ts = time.strftime("%d-%b-%Y-%H-%M-%S",time.gmtime(time.time()))
	lgf = "%s/cosmicpi-logs/%s.log" % (logdir,ts)
	dir = os.path.dirname(lgf)
	if not os.path.exists(dir):
		os.makedirs(dir)
	try:
		log = open(lgf, "w");
	except Exception, e:
		msg = "Exception: Cant open log file: %s" % (e)
		print "Fatal: %s" % msg
		sys.exit(1)

	if options.debug:
		print "\n"
		print "Log file is: %s" % lgf

	kbrd = KeyBoard()
	kbrd.echo_off()

	sio = Socket_io(ipport)

	evt = Event()

	nfs = Notifications()

	reg = Registrations()

	newsqn = False
	badhard = False

	try:
		while(True):

			recv = sio.recv_event_pkt()
			if len(recv[0]):

				print "FromIP:%s" % (str(recv[1]))

				nstr = recv[0].split('*')
				for i in range(0,len(nstr)):
					nstr[i] = nstr[i].replace('\n','')
					#print "Parse:%s" % nstr[i]
					evt.parse(nstr[i])

				if nstr[0].find("event") != -1:
					newsqn = True
					evd = evt.get_evt()
					tim = evt.get_tim()
					dat = evt.get_dat()
					print
					print "Cosmic Event..: event_number:%s counter_frequency:%s ticks:%s timestamp:%s" \
						  % (evd["event_number"],evd["counter_frequency"],evd["ticks"],evd["timestamp"])
					print "adc[[Ch0][Ch1]: adc:%s" % (str(evd["adc"]))
					print "Time..........: uptime:%s time_string:%s" % (tim["uptime"],tim["time_string"])
					print "Date..........: date:%s" % (dat["date"])

				elif nstr[0].find("vibration") != -1:
					newsqn = True
					mag = evt.get_mag()
					vib = evt.get_vib()
					tim = evt.get_tim()
					acl = evt.get_acl()
					sqn = evt.get_sqn()
					print
					print "Vibration.....: direction:%s count:%s sequence_number:%d" % (vib["direction"],vib["count"],sqn["number"])
					print "Time..........: time_string:%s" % (tim["time_string"])
					print "Accelarometer.: x:%s y:%s z:%s" % (acl["x"],acl["y"],acl["z"])
					print "Magnetometer..: x:%s y:%s z:%s" % (mag["x"],mag["y"],mag["z"])

				elif nstr[0].find("temperature") != -1:
					newsqn = True
					tim = evt.get_tim()
					bmp = evt.get_bmp()
					htu = evt.get_htu()
					loc = evt.get_loc()
					print
					print "Barometer.....: temperature:%s pressure:%s altitude:%s" % (bmp["temperature"],bmp["pressure"],bmp["altitude"])
					print "Humidity......: temperature:%s humidity:%s altitude:%s" % (htu["temperature"],htu["humidity"],loc["altitude"])
					print "Time..........: time_string:%s\n" % (tim["time_string"])

				elif nstr[0].find("PAT") != -1:
					pat = evt.get_pat()
					print
					print "Notification..: Pat:%s Ntf:%s" % (pat["Pat"],pat["Ntf"])
					if pat["Ntf"] == True:
						msg = "Your are now registered to recieve pi server notifications"
					else:
						msg = "You will no longer recieve pi server notifications"

					nfs.send_ntf(pat["Pat"],msg)

					r = reg.get_create_reg("Ipa",str(recv[1]))
					r["Pat"] = pat["Pat"]
					r["Ntf"] = pat["Ntf"]
					reg.set_reg(r)

				elif nstr[0].find("status") != -1:
					sts = evt.get_sts()
					r = reg.get_create_reg("Ipa",str(recv[1]))
					r["temp_status"] = sts["temp_status"]
					r["baro_status"] = sts["baro_status"]
					r["accel_status"] = sts["accel_status"]
					r["mag_status"] = sts["mag_status"]
					r["gps_status"] = sts["gps_status"]
					reg.set_reg(r)

					msg = ""
					if int(r["temp_status"]) == 0:
						msg = msg + "temp_status down: "
					if int(r["baro_status"]) == 0:
						msg = msg + "baro_status down: "
					if int(r["accel_status"]) == 0:
						msg = msg + "accel_status down: "
					if int(r["mag_status"]) == 0:
						msg = msg + "mag_status down: "
					if int(r["gps_status"]) == 0:
						msg = msg + "gps_status down: "

					if len(msg) > 0:
						if badhard == False:
							badhard = True
							if r["Ntf"]:
								nfs.send_ntf(pat["Pat"],msg)
							print "Hardware error:%s %s" % (str(recv[1],msg))
					else:
						if badhard == True:
							badhard = False
							msg = "Hardware OK again"
							if r["Ntf"]:
								nfs.send_ntf(pat["Pat"],msg)
							print "%s:%s" % (msg,str(recv[1]))
				if newsqn:
					newsqn = False
					sqn = evt.get_sqn()
					r = reg.get_create_reg("Ipa",str(recv[1]))
					j = int(r["Sqn"])
					i = int(sqn["number"])
					if i != j+1 and j != 0:
						msg = "Sequence error: %s %d-%d" % (str(recv[1],i,j))
						print msg
						if r["Ntf"]:
							nfs.send_ntf(pat["Pat"],msg)

					r["number"] = i
					reg.set_reg(r)

				if logflg:
					line = "%s - %s" % (str(recv[0]),str(recv[1]))
					log.write(line)
					log.write("\n\n")

			if kbrd.test_input():
				kbrd.echo_on()
				print "\n"
				cmd = raw_input(">")

				if cmd.find("h") != -1:
					print "Commands: h=help, r=registrations, s=status q=quit"

				if cmd.find("q") != -1:
					break

				if cmd.find("s") != -1:
					print "Server Status"
					print "Log file......:%s" % (lgf)
					print "Registrations.:%d" % (reg.get_len())

				if cmd.find("r") != -1:
					k = reg.get_len()
					if k>0:
						print "Client registrations and status"
						for i in range(0,k):
							r = reg.get_reg_by_index(i)
							print "Idx:%d Ipa:%s Pat:%s Sqn:%d Ntf:%d" % (i,r["Ipa"],r["Pat"],r["Sqn"],r["Ntf"])
							print "Idx:%d Htu:%s Bmp:%s Acl:%s Mag:%s Gps:%s" % (i,r["Htu"],r["Bmp"],r["Acl"],r["Mag"],r["Gps"])
							print ""
				kbrd.echo_off()

			ts = time.strftime("%d/%b/%Y %H:%M:%S",time.gmtime(time.time()))
			s = "cosmic_pi_server:[%s]\r" % (ts)
			sys.stdout.write(s)
			sys.stdout.flush()

	except Exception, e:
		msg = "Exception: main: %s" % (e)
		print "Fatal: %s" % msg

	finally:
		kbrd.echo_on()
		print "Quitting ..."
		log.close()
		sio.close()
		time.sleep(1)
		sys.exit(0)

if __name__ == '__main__':

    main()
