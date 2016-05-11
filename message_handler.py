import json
import os
import threading
import pika
import time

import sys

from event import Event
from notifications import Notifications
from registrations import Registrations


class MessageHandler(object):

    def __init__(self, host, port, username, password, logdir, logflg):

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, port=port, credentials=pika.PlainCredentials(username, password)))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='events', type='fanout')
        self.queue_name = self.channel.queue_declare(exclusive=True).method.queue
        self.channel.queue_bind(exchange='events', queue=self.queue_name)

        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True

        self.nfs = Notifications()
        self.reg = Registrations()
        self.logflg = logflg
        self.newsqn = False
        self.badhard = False

        ts = time.strftime("%d-%b-%Y-%H-%M-%S", time.gmtime(time.time()))
        lgf = "%s/cosmicpi-logs/%s.log" % (logdir, ts)
        dir = os.path.dirname(lgf)
        if not os.path.exists(dir):
            os.makedirs(dir)
        try:
            self.log = open(lgf, "w")
        except Exception as e:
            msg = "Exception: Cant open log file: %s" % (e)
            print "Fatal: %s" % msg
            sys.exit(1)

    def start(self):
        self.thread.start()

    def run(self):
        self.channel.basic_consume(self.on_message, queue=self.queue_name, no_ack=True)
        self.channel.start_consuming()

    def join(self):
        self.thread.join()

    def on_message(self, ch, method, properties, body):
        print("received: %r" % body)

        if len(body):
            event = Event(json.loads(body))

            if hasattr(event, 'event'):
                self.newsqn = True
                print 'Cosmic event received'
                print "Event.........: %s" % event.event
                print "ADC...........: %s" % event.adc
                print "Timing........: %s" % event.timing
                print "Date..........: %s" % event.date

            elif hasattr(event, 'vibration'):
                self.newsqn = True
                print 'Vibration event received'
                print "Vibration.....: %s" % event.vibration
                print "Accelerometer.: %s" % event.accelerometer
                print "Magnetometer..: %s" % event.magnetometer
                print "Timing........: %s" % event.timing

            elif hasattr(event, 'temperature'):
                self.newsqn = True
                print 'Weather event received'
                print "Thermometer...: %s" % event.temperature
                print "Barometer.....: %s" % event.barometer
                print "Timing........: %s" % event.timing

            elif hasattr(event, 'PAT'):
                pat = event.PAT
                print
                print "Notification..: Pat:%s Ntf:%s" % (pat["Pat"], pat["Ntf"])
                if pat["Ntf"] == True:
                    msg = "Your are now registered to recieve pi server notifications"
                else:
                    msg = "You will no longer recieve pi server notifications"

                self.nfs.send_ntf(pat["Pat"], msg)

                r = self.reg.get_create_reg("Ipa", pat)
                r["Pat"] = pat["Pat"]
                r["Ntf"] = pat["Ntf"]
                self.reg.set_reg(r)

            elif hasattr(event, 'status'):
                sts = event.status
                r = self.reg.get_create_reg("Ipa", sts)
                r["temp_status"] = sts["temp_status"]
                r["baro_status"] = sts["baro_status"]
                r["accel_status"] = sts["accel_status"]
                r["mag_status"] = sts["mag_status"]
                r["gps_status"] = sts["gps_status"]
                self.reg.set_reg(r)

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
                    if self.badhard == False:
                        self.badhard = True
                        if r["Ntf"]:
                            self.nfs.send_ntf(event.PAT["Pat"], msg)
                        print "Hardware error:%s %s" % (sts, msg)
                else:
                    if self.badhard == True:
                        self.badhard = False
                        msg = "Hardware OK again"
                        if r["Ntf"]:
                            self.nfs.send_ntf(event.PAT["Pat"], msg)
                        print "%s:%s" % (msg, sts)
            if self.newsqn:
                self.newsqn = False
                sqn = event.sequence
                r = self.reg.get_create_reg("Ipa", sqn)
                j = int(r["Sqn"])
                i = int(sqn["number"])
                if i != j + 1 and j != 0:
                    msg = "Sequence error: %s %d-%d" % (sqn, i, j)
                    print msg
                    if r["Ntf"]:
                        self.nfs.send_ntf(event.PAT["Pat"], msg)

                r["number"] = i
                self.reg.set_reg(r)

            # if self.logflg:
            #     line = "%s - %s" % (str(recv[0]), str(recv[1]))
            #     self.log.write(line)
            #     self.log.write("\n\n")

    def close(self):
        self.connection.close()
