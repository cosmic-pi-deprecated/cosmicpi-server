# Send notifications to registered mobile phones
# Currently I am using pushover and the client has to install the
# pushover app and register a user and application token.
# The client supplies the keys on the cosmic pi client launch command line
import httplib
import urllib


class Notifications(object):
    def send_ntf(self, kyp, msg):
        nstr = kyp.split('-')

        self.conn = httplib.HTTPSConnection("api.pushover.net:443")

        self.conn.request("POST", "/1/messages.json",
                          urllib.urlencode({"token": nstr[1],
                                            "user": nstr[0],
                                            "sound": "Cosmic",
                                            "message": msg}),
                          {"Content-type": "application/x-www-form-urlencoded"})

        self.conn.getresponse()