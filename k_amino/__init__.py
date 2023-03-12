from json import loads
from requests import get

from .acm import *
from .client import *
from .local import *
from .sockets import *
from .bot import *


__version__ = "1.0.7"


__newest__ = loads(get("https://pypi.python.org/pypi/k-amino.py/json").text)["info"]["version"]

if __version__ != __newest__:
    print(f"\033[1;31;38mk_amino New Version!: {__newest__} (You are using {__version__})\033[1;36;33m\nDiscord server: \"https://discord.gg/zd8gyFJquT\"\033[1;0m")
else:
    print(f"\033[1;31;32mk_amino version : {__version__}\033[1;36;33m\nDiscord server: \"https://discord.gg/zd8gyFJquT\"\033[1;0m")
