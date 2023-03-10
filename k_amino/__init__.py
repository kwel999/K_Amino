from json import loads
from requests import get

from .acm import *
from .client import *
from .local import *
from .sockets import *
from .bot import *


__version__ = "1.0.4"


__newest__ = loads(get("https://pypi.python.org/pypi/k-amino.py/json").text)["info"]["version"]

if __version__ != __newest__:
    print(f"New version of {__title__} available: {__newest__} (Using {__version__})")
else:
    print(f"version : {__version__}")
