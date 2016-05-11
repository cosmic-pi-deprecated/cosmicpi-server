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
from message_handler import MessageHandler
from keyboard import KeyBoard


def main():
    use = "Usage: %prog [--port=4901 --odir=/tmp]"
    parser = OptionParser(usage=use, version="cosmic_pi_server version 1.0")
    parser.add_option("-i", "--host", help="Message broker host", dest="host", default="localhost")
    parser.add_option("-p", "--port", help="Message broker port", dest="port", type="int", default="5672")
    parser.add_option("-x", "--credentials", help="Message broker credentials", dest="credentials", default="test:test")
    parser.add_option("-d", "--debug", help="Debug Option", dest="debug", default=False, action="store_true")
    parser.add_option("-o", "--odir", help="Path to log directory", dest="logdir", default="/tmp")
    parser.add_option("-n", "--nolog", help="Event Logging", dest="logflg", default=True, action="store_false")

    options, args = parser.parse_args()

    host = options.host
    port = options.port
    logdir = options.logdir
    debug = options.debug
    logflg = options.logflg

    credentials = options.credentials.split(':')
    username = credentials[0]
    password = credentials[1]

    print ""
    print "cosmic_pi server running, hit '>' for commands\n"

    print "options (Server Port number)    port:%d" % port
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

    # kbrd = KeyBoard()
    # kbrd.echo_off()

    message_handler = MessageHandler(host, port, username, password, logdir, logflg)
    message_handler.start()
    message_handler.join()

    # try:
    #     while (True):
    #
    #         if kbrd.test_input():
    #             kbrd.echo_on()
    #             print "\n"
    #             cmd = raw_input(">")
    #
    #             if cmd.find("h") != -1:
    #                 print "Commands: h=help, r=registrations, s=status q=quit"
    #
    #             if cmd.find("q") != -1:
    #                 break
    #
    #             if cmd.find("s") != -1:
    #                 print "Server Status"
    #                 print "Log file......:%s" % (lgf)
    #                 print "Registrations.:%d" % (reg.get_len())
    #
    #             if cmd.find("r") != -1:
    #                 k = reg.get_len()
    #                 if k > 0:
    #                     print "Client registrations and status"
    #                     for i in range(0, k):
    #                         r = reg.get_reg_by_index(i)
    #                         print "Idx:%d Ipa:%s Pat:%s Sqn:%d Ntf:%d" % (i, r["Ipa"], r["Pat"], r["Sqn"], r["Ntf"])
    #                         print "Idx:%d Htu:%s Bmp:%s Acl:%s Mag:%s Gps:%s" % (
    #                         i, r["Htu"], r["Bmp"], r["Acl"], r["Mag"], r["Gps"])
    #                         print ""
    #             kbrd.echo_off()
    #
    #         ts = time.strftime("%d/%b/%Y %H:%M:%S", time.gmtime(time.time()))
    #         s = "cosmic_pi_server:[%s]\r" % (ts)
    #         sys.stdout.write(s)
    #         sys.stdout.flush()
    #
    # except Exception, e:
    #     msg = "Exception: main: %s" % (e)
    #     print "Fatal: %s" % msg
    #
    # finally:
    #     kbrd.echo_on()
    #     print "Quitting ..."
    #     log.close()
    #     sio.close()
    #     time.sleep(1)
    #     sys.exit(0)


if __name__ == '__main__':
    main()
