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

        self.evt = Event()
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
        recv = body

        if len(recv[0]):

            print "FromIP:%s" % (str(recv[1]))

            nstr = recv[0].split('*')
            for i in range(0, len(nstr)):
                nstr[i] = nstr[i].replace('\n', '')
                # print "Parse:%s" % nstr[i]
                self.evt.parse(nstr[i])

            if nstr[0].find("event") != -1:
                newsqn = True
                evd = self.evt.get_evt()
                tim = self.evt.get_tim()
                dat = self.evt.get_dat()
                print
                print "Cosmic Event..: event_number:%s counter_frequency:%s ticks:%s timestamp:%s" \
                      % (evd["event_number"], evd["counter_frequency"], evd["ticks"], evd["timestamp"])
                print "adc[[Ch0][Ch1]: adc:%s" % (str(evd["adc"]))
                print "Time..........: uptime:%s time_string:%s" % (tim["uptime"], tim["time_string"])
                print "Date..........: date:%s" % (dat["date"])

            elif nstr[0].find("vibration") != -1:
                newsqn = True
                mag = self.evt.get_mag()
                vib = self.evt.get_vib()
                tim = self.evt.get_tim()
                acl = self.evt.get_acl()
                sqn = self.evt.get_sqn()
                print
                print "Vibration.....: direction:%s count:%s sequence_number:%d" % (
                    vib["direction"], vib["count"], sqn["number"])
                print "Time..........: time_string:%s" % (tim["time_string"])
                print "Accelarometer.: x:%s y:%s z:%s" % (acl["x"], acl["y"], acl["z"])
                print "Magnetometer..: x:%s y:%s z:%s" % (mag["x"], mag["y"], mag["z"])

            elif nstr[0].find("temperature") != -1:
                newsqn = True
                tim = self.evt.get_tim()
                bmp = self.evt.get_bmp()
                htu = self.evt.get_htu()
                loc = self.evt.get_loc()
                print
                print "Barometer.....: temperature:%s pressure:%s altitude:%s" % (
                    bmp["temperature"], bmp["pressure"], bmp["altitude"])
                print "Humidity......: temperature:%s humidity:%s altitude:%s" % (
                    htu["temperature"], htu["humidity"], loc["altitude"])
                print "Time..........: time_string:%s\n" % (tim["time_string"])

            elif nstr[0].find("PAT") != -1:
                pat = self.evt.get_pat()
                print
                print "Notification..: Pat:%s Ntf:%s" % (pat["Pat"], pat["Ntf"])
                if pat["Ntf"] == True:
                    msg = "Your are now registered to recieve pi server notifications"
                else:
                    msg = "You will no longer recieve pi server notifications"

                self.nfs.send_ntf(pat["Pat"], msg)

                r = self.reg.get_create_reg("Ipa", str(recv[1]))
                r["Pat"] = pat["Pat"]
                r["Ntf"] = pat["Ntf"]
                self.reg.set_reg(r)

            elif nstr[0].find("status") != -1:
                sts = self.evt.get_sts()
                r = self.reg.get_create_reg("Ipa", str(recv[1]))
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
                            self.nfs.send_ntf(self.evt.get_pat()["Pat"], msg)
                        print "Hardware error:%s %s" % (str(recv[1], msg))
                else:
                    if self.badhard == True:
                        self.badhard = False
                        msg = "Hardware OK again"
                        if r["Ntf"]:
                            self.nfs.send_ntf(self.evt.get_pat()["Pat"], msg)
                        print "%s:%s" % (msg, str(recv[1]))
            if self.newsqn:
                self.newsqn = False
                sqn = self.evt.get_sqn()
                r = self.reg.get_create_reg("Ipa", str(recv[1]))
                j = int(r["Sqn"])
                i = int(sqn["number"])
                if i != j + 1 and j != 0:
                    msg = "Sequence error: %s %d-%d" % (str(recv[1], i, j))
                    print msg
                    if r["Ntf"]:
                        self.nfs.send_ntf(self.evt.get_pat()["Pat"], msg)

                r["number"] = i
                self.reg.set_reg(r)

            if self.logflg:
                line = "%s - %s" % (str(recv[0]), str(recv[1]))
                self.log.write(line)
                self.log.write("\n\n")

    def close(self):
        self.connection.close()
