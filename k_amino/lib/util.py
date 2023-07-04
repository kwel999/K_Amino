from base64 import b64encode, urlsafe_b64decode
from time import time as timestamp
from typing import Dict, List, Optional, Final
from hashlib import sha1
from uuid import uuid4
from json import loads
from hmac import new
import os


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
    return loads(urlsafe_b64decode(sid + "=" * (4 - len(sid) % 4))[1:-20])

def sid_to_uid(SID: str) -> str:
    return decode_sid(SID)["2"]

def sid_to_ip_address(SID: str) -> str:
    return decode_sid(SID)["4"]

def sid_created_time(SID: str) -> str:
    return decode_sid(SID)["5"]

def sid_to_client_type(SID: str) -> str:
    return decode_sid(SID)["6"]
