import ast

# This is the event object, it builds a dictionary from incoming json strings
# and provides access to the dictionary entries containing the data for each field.
class Event(object):
    def __init__(self):

        # These are the UDP packets containing json strings we are expecting

        self.temperature = {"temperature": "0.0", "humidity": "0.0"}
        self.barometer = {"temperature": "0.0", "pressure": "0.0", "altitude": "0.0"}
        self.vibration = {"direction": "0", "count": "0"}
        self.magnetometer = {"x": "0.0", "y": "0.0", "z": "0.0"}
        self.MOG = {"Mox": "0.0", "Moy": "0.0", "Moz": "0.0"}
        self.accelerometer = {"x": "0.0", "y": "0.0", "z": "0.0"}
        self.AOL = {"Aox": "0.0", "Aoy": "0.0", "Aoz": "0.0"}
        self.location = {"latitude": "0.0", "longitude": "0.0", "altitude": "0.0"}
        self.timing = {"uptime": "0", "counter_frequency": "0", "time_string": "0"}
        self.status = {"queue_size": "0", "missed_events": "0", "buffer_error": "0", "temp_status": "0",
                       "baro_status": "0", "accel_status": "0", "mag_status": "0", "gps_status": "0"}
        self.event = {"event_number": "0", "counter_frequency": "0", "ticks": "0", "timestamp": "0.0",
                      "adc": "[[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]"}
        self.date = {"date": "s"}

        # Add ons

        self.date = {"date": "s"}  # Date
        self.sequence = {"number": "0"}  # Sequence number
        self.PAT = {"Pat": "s", "Ntf": "0"}  # Pushover application token

        # Now build the main dictionary with one entry for each json string we will process

        self.recd = {"temperature": self.temperature, "barometer": self.barometer, "vibration": self.vibration,
                     "magnetometer": self.magnetometer, "MOG": self.MOG,
                     "accelerometer": self.accelerometer, "AOL": self.AOL, "location": self.location,
                     "timing": self.timing, "status": self.status,
                     "event": self.event, "date": self.date, "sequence": self.sequence, "PAT": self.PAT}

        self.newpat = False
        self.newsqn = False

    # Convert the incomming json strings into entries in the dictionary

    def parse(self, line):  # parse the incomming json strings from arduino
        nstr = line.replace('\n', '')  # Throw away <crtn>, we dont want them
        try:
            dic = ast.literal_eval(nstr)  # Build a dictionary entry
            kys = dic.keys()  # Get key names, the first is the address
            if self.recd.has_key(kys[0]):  # Check we know about records with this key
                self.recd[kys[0]] = dic[kys[0]]  # and put it in the dictionary at that address

            if kys[0] == "PAT":
                self.newpat = True

            if kys[0] == "sequence":
                self.newsqn = True

        except Exception, e:
            pass  # Didnt understand, throw it away

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