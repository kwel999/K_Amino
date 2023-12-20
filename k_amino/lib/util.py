from base64 import b64encode, urlsafe_b64decode
from time import time as timestamp
from typing import Dict, List, Optional
from functools import wraps
from random import randint
from hashlib import sha1
from uuid import uuid4
from json import loads
from hmac import new
import inspect
import warnings
import os

__all__ = (
    'active_time',
    'decode_sid',
    'deprecated',
    'generateDevice',
    'generateSig',
    'generateUserAgent',
    'get_file_type',
    'sid_created_time',
    'sid_to_client_type',
    'sid_to_ip_address',
    'sid_to_uid',
    'updateDevice',
    'uuidString'
)

# constants
PREFIX = '19'
SIGKEY = 'dfa5ed192dda6e88a12fe12130dc6206b1251e44'
DEVKEY = 'e7309ecc0953c6fa60005b2765f99dbbc965c8e9'

# tapjoy = "https://ads.tapdaq.com/v4/analytics/reward"
webApi = "https://aminoapps.com/api{}".format
api = "https://service.aminoapps.com/api/v1{}".format


def generateSig(data: str) -> str:
    return b64encode(
        bytes.fromhex(PREFIX) + new(
            bytes.fromhex(SIGKEY),
            data.encode(), sha1
        ).digest()
    ).decode()


def generateDevice(id: Optional[bytes] = None) -> str:
    info = bytes.fromhex(PREFIX) + (id or os.urandom(20))
    device = info + new(
        bytes.fromhex(DEVKEY),
        info, sha1
    ).digest()
    return device.hex().upper()


def updateDevice(device: str) -> str:
    return generateDevice(bytes.fromhex(device)[1:21])


def generateUserAgent() -> str:
    return f"Apple iPhone{randint(0,99999)},1 iOS v16.5 Main/3.19.0"


def uuidString() -> str:
    return str(uuid4())


def active_time(*, seconds=0, minutes=0, hours=0) -> List[Dict[str, int]]:
    total = seconds + minutes*60 + hours*60*60
    return [
        {
            'start': int(timestamp()),
            'end': int(timestamp() + 300)
        } for _ in range(total // 300)
    ] + [
        {
            'start': int(timestamp()),
            'end': int(timestamp() + total % 300)
        }
    ]


def decode_sid(sid: str) -> dict:
    """Decode an amino session ID string.

    Parameters
    ----------
    sid : str
        The sid string to decode.

    Returns
    -------
    dict
        The decoded data.

    """
    return loads(urlsafe_b64decode(sid + "=" * (4 - len(sid) % 4))[1:-20])


def sid_to_uid(sid: str) -> str:
    """Convert an amino session ID to user ID.

    Parameters
    ----------
    sid : str
        The sid string to convert.

    Returns
    -------
    str
        The user ID.

    """
    return decode_sid(sid)["2"]


def sid_to_ip_address(sid: str) -> str:
    """Convert an amino session ID to IP address.

    Parameters
    ----------
    sid : str
        The sid string to convert.

    Returns
    -------
    str
        The IP address string.

    """
    return decode_sid(sid)["4"]


def sid_created_time(sid: str) -> str:
    """Convert an amino session ID to created-time (datetime).

    Parameters
    ----------
    sid : str
        The sid string to convert.

    Returns
    -------
    str
        The sid created time (datetime)

    """
    return decode_sid(sid)["5"]


def sid_to_client_type(sid: str) -> int:
    """Convert an amino session ID to session client type.

    Parameters
    ----------
    sid : str
        The sid string to convert.

    Returns
    -------
    int
        The client type.

    """
    return decode_sid(sid)["6"]


def get_file_type(name: str, default: str = "jpg") -> str:
    """Get the file type from the given file name.

    Parameters
    ----------
    name : str
        The file name.
    default : str, optional
        The file type to return. Default is 'jpg'.

    Returns
    -------
    str
        The file type.

    """
    try:
        return name[::-1][:name[::-1].index('.')][::-1]
    except (ValueError, IndexError):
        return default


def deprecated(instead: Optional[str] = None):
    """Set deprecated functions without altering operation by decoration.

    Parameters
    ----------
    instead: str, optional
        The function instead name.

    Returns
    -------
    Callable
        The decorator function

    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.simplefilter('always', DeprecationWarning)  # turn off filter
            if instead:
                fmt = "{0.__name__} is deprecated, use {1} instead."
            else:
                fmt = '{0.__name__} is deprecated.'
            warnings.warn(fmt.format(func, instead), stacklevel=3, category=DeprecationWarning)
            warnings.simplefilter('default', DeprecationWarning)  # reset filter
            return func(*args, **kwargs)
        wrapper.__signature__ = inspect.signature(func)  # type: ignore
        return wrapper
    return decorator
