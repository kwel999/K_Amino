from requests import get
#from .KAsync import *
from .acm import Acm
from .client import Client
from .lib.exception import CheckExceptions
from .local import Local

version = "1.0.1"
#newest = get("https://pypi.org/pypi/samino/json").json()["info"]["version"]

#if version != newest:
#    print(f"\033[1;31;33mSAmino New Version!: {newest} (Your Using {version})\033[1;36;33m\nJoin our discord server: \"https://discord.gg/vhBtt2QB\"\033[1;0m")
