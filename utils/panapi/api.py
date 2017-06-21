import requests
from .errors import *

API_BASE = "https://api.pandentia.cf/"

class Struct:
    def __init__(self, thing, **entries):
        self.__dict__.update(entries)
        self.thing = thing
    def __repr__(self):
        return '<' + self.thing + '>'

def get_user(user_id:int):
    resp = requests.get(API_BASE + "discord/user/" + str(user_id))
    json = resp.json()
    if json["code"] == 200:
        return Struct("User", **json["response"])
