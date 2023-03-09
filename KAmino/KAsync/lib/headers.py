import json
from sys import version_info as version

from .util import generateDevice, generateSig, uuidString

uid = None
sid = None
deviceId = None
lang = None


class Headers:
    def __init__(self, data=None):
        if deviceId:
            self.deviceId = deviceId
        else:
            self.deviceId = generateDevice()

        self.headers = {
            "NDCDEVICEID": self.deviceId,
            "AUID": uuidString(),
            "SMDEVICEID": uuidString(),
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": f"python/{version.major}.{version.minor}.{version.micro} (python-requests/2.25; SAmino/2.3.1)",
            "Host": "service.narvii.com",
            "Accept-Encoding": "gzip",
            "Connection": "Upgrade"
        }
        self.web_headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "ar,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "sec-ch-ua": '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            "x-requested-with": "xmlhttprequest"
        }

        if sid:
            self.headers["NDCAUTH"] = sid
            self.web_headers["cookie"] = sid

        if uid:
            self.uid = uid

        if data:
            self.headers["Content-Length"] = str(len(data))

            if type(data) is not str:
                data = json.dumps(data)

            self.headers["NDC-MSG-SIG"] = generateSig(data)

        if lang:
            self.headers.update({"NDCLANG": lang[:lang.index("-")], "Accept-Language": lang})
