import json


class Event(object):
    """This is the event object, it builds a dictionary from incoming json strings
    and provides access to the dictionary entries containing the data for each field."""

    def __init__(self, string):
        self.__dict__ = json.loads(string)
