#! /usr/bin/python
# coding: utf8

"""
Handle UDP packets from the cosmic pi and log then
julian.lewis lewis.julian@gmail.com 26/Feb/2016
"""

import sys
import time
import os
import fcntl
from optparse import OptionParser

from event import Event
from socket import Socket_io
from keyboard import KeyBoard
from notifications import Notifications
from registrations import Registrations


def main():
    use = "Usage: %prog [--port=4901 --odir=/tmp]"
    parser = OptionParser(usage=use, version="cosmic_pi_server version 1.0")
    parser.add_option("-p", "--port", help="Server portnumber", dest="ipport", type="int", default="15443")
    parser.add_option("-d", "--debug", help="Debug Option", dest="debug", default=False, action="store_true")
    parser.add_option("-o", "--odir", help="Path to log directory", dest="logdir", default="/tmp")
    parser.add_option("-n", "--nolog", help="Event Logging", dest="logflg", default=True, action="store_false")

    options, args = parser.parse_args()

    ipport = options.ipport
    logdir = options.logdir
    debug = options.debug
    logflg = options.logflg

    print ""
    print "cosmic_pi server running, hit '>' for commands\n"

    print "options (Server Port number)    port:%d" % ipport
    print "options (Logging directory)    odir:%s" % logdir
    print "options (Event logging)        log: %s" % logflg

    file_name = "/tmp/pi-server-lock"
    fp = open(file_name, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception, e:
        print "Lock file:%s is in use" % (file_name)
        print "Only one instance of the server can run at any one time"
        print "Please kill the other instance or remove the lock file"
        sys.exit(1)

    ts = time.strftime("%d-%b-%Y-%H-%M-%S", time.gmtime(time.time()))
    lgf = "%s/cosmicpi-logs/%s.log" % (logdir, ts)
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
        while (True):

            recv = sio.recv_event_pkt()
            if len(recv[0]):

                print "FromIP:%s" % (str(recv[1]))

                nstr = recv[0].split('*')
                for i in range(0, len(nstr)):
                    nstr[i] = nstr[i].replace('\n', '')
                    # print "Parse:%s" % nstr[i]
                    evt.parse(nstr[i])

                if nstr[0].find("event") != -1:
                    newsqn = True
                    evd = evt.get_evt()
                    tim = evt.get_tim()
                    dat = evt.get_dat()
                    print
                    print "Cosmic Event..: event_number:%s counter_frequency:%s ticks:%s timestamp:%s" \
                          % (evd["event_number"], evd["counter_frequency"], evd["ticks"], evd["timestamp"])
                    print "adc[[Ch0][Ch1]: adc:%s" % (str(evd["adc"]))
                    print "Time..........: uptime:%s time_string:%s" % (tim["uptime"], tim["time_string"])
                    print "Date..........: date:%s" % (dat["date"])

                elif nstr[0].find("vibration") != -1:
                    newsqn = True
                    mag = evt.get_mag()
                    vib = evt.get_vib()
                    tim = evt.get_tim()
                    acl = evt.get_acl()
                    sqn = evt.get_sqn()
                    print
                    print "Vibration.....: direction:%s count:%s sequence_number:%d" % (
                    vib["direction"], vib["count"], sqn["number"])
                    print "Time..........: time_string:%s" % (tim["time_string"])
                    print "Accelarometer.: x:%s y:%s z:%s" % (acl["x"], acl["y"], acl["z"])
                    print "Magnetometer..: x:%s y:%s z:%s" % (mag["x"], mag["y"], mag["z"])

                elif nstr[0].find("temperature") != -1:
                    newsqn = True
                    tim = evt.get_tim()
                    bmp = evt.get_bmp()
                    htu = evt.get_htu()
                    loc = evt.get_loc()
                    print
                    print "Barometer.....: temperature:%s pressure:%s altitude:%s" % (
                    bmp["temperature"], bmp["pressure"], bmp["altitude"])
                    print "Humidity......: temperature:%s humidity:%s altitude:%s" % (
                    htu["temperature"], htu["humidity"], loc["altitude"])
                    print "Time..........: time_string:%s\n" % (tim["time_string"])

                elif nstr[0].find("PAT") != -1:
                    pat = evt.get_pat()
                    print
                    print "Notification..: Pat:%s Ntf:%s" % (pat["Pat"], pat["Ntf"])
                    if pat["Ntf"] == True:
                        msg = "Your are now registered to recieve pi server notifications"
                    else:
                        msg = "You will no longer recieve pi server notifications"

                    nfs.send_ntf(pat["Pat"], msg)

                    r = reg.get_create_reg("Ipa", str(recv[1]))
                    r["Pat"] = pat["Pat"]
                    r["Ntf"] = pat["Ntf"]
                    reg.set_reg(r)

                elif nstr[0].find("status") != -1:
                    sts = evt.get_sts()
                    r = reg.get_create_reg("Ipa", str(recv[1]))
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
                                nfs.send_ntf(pat["Pat"], msg)
                            print "Hardware error:%s %s" % (str(recv[1], msg))
                    else:
                        if badhard == True:
                            badhard = False
                            msg = "Hardware OK again"
                            if r["Ntf"]:
                                nfs.send_ntf(pat["Pat"], msg)
                            print "%s:%s" % (msg, str(recv[1]))
                if newsqn:
                    newsqn = False
                    sqn = evt.get_sqn()
                    r = reg.get_create_reg("Ipa", str(recv[1]))
                    j = int(r["Sqn"])
                    i = int(sqn["number"])
                    if i != j + 1 and j != 0:
                        msg = "Sequence error: %s %d-%d" % (str(recv[1], i, j))
                        print msg
                        if r["Ntf"]:
                            nfs.send_ntf(pat["Pat"], msg)

                    r["number"] = i
                    reg.set_reg(r)

                if logflg:
                    line = "%s - %s" % (str(recv[0]), str(recv[1]))
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
                    if k > 0:
                        print "Client registrations and status"
                        for i in range(0, k):
                            r = reg.get_reg_by_index(i)
                            print "Idx:%d Ipa:%s Pat:%s Sqn:%d Ntf:%d" % (i, r["Ipa"], r["Pat"], r["Sqn"], r["Ntf"])
                            print "Idx:%d Htu:%s Bmp:%s Acl:%s Mag:%s Gps:%s" % (
                            i, r["Htu"], r["Bmp"], r["Acl"], r["Mag"], r["Gps"])
                            print ""
                kbrd.echo_off()

            ts = time.strftime("%d/%b/%Y %H:%M:%S", time.gmtime(time.time()))
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
