from json import loads
from requests import get

from .k_sync.acm import Acm
from .k_sync.client import Client
from .k_sync.local import SubClient
# from .k_sync.sockets import *
from .k_sync.bot import Bot

from .k_async.acm import AsyncAcm
from .k_async.client import AsyncClient
from .k_async.local import AsyncSubClient
# from .k_async.sockets import *
from .k_async.bot import AsyncBot


__version__ = "1.4.0"


__newest__ = loads(get("https://pypi.python.org/pypi/k-amino.py/json").text)["info"]["version"]

if __version__ != __newest__:
    print(f"\033[1;31;38mk_amino New Version!: {__newest__} (You are using {__version__})\033[1;36;33m\nDiscord server: \"https://discord.gg/zd8gyFJquT\"\033[1;0m")
else:
    print(f"\033[1;31;32mk_amino version : {__version__}\033[1;36;33m\nDiscord server: \"https://discord.gg/zd8gyFJquT\"\033[1;0m")
