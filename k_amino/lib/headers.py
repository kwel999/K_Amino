from typing import Dict, Optional
from .util import (
    generateDevice,
    generateSig,
    generateUserAgent,
    uuidString
)

__all__ = ('Headers',)


class Headers:
    """Base class for http client headers.

    Parameters
    ----------
    deviceId : str, optional
        Device ID. defaults is None.

    Attributes
    ----------
    deviceId : str
        The client device ID.
    app_headers : str
        The HTTP headers of the app client.
    web_headers : str
        The HTTP headers of the web client.

    """

    def __init__(self, deviceId: Optional[str] = None) -> None:
        self.deviceId = deviceId if deviceId else generateDevice()
        self.app_headers = {
            "NDCDEVICEID": self.deviceId,
            "NDCLANG": "en",
            "Accept-Language": "en-US",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": generateUserAgent(),
            "Host": "service.aminoapps.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        self.web_headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "ar,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "sec-ch-ua": '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            "x-requested-with": "xmlhttprequest"
        }

    def updateHeaders(self, data: Optional[str] = None, lang: Optional[str] = None, updateDevice: Optional[str] = None, sid: Optional[str] = None) -> Dict[str, str]:
        """Update the HTTP headers.

        Parameters
        ----------
        data : str, optional
            The data to encode.
        lang : str, optional
            The language of the client.
        updateDevice : bool, optional
            The new device for the client.
        sid : str, optional
            The new sid for the client.

        Returns
        -------
        dict
            The updated headers (app headers).

        """
        self.app_headers.update({
            "AUID": uuidString(),
            "User-Agent": generateUserAgent(),
            "SMDEVICEID": uuidString(),
            "NDCDEVICEID": self.deviceId or generateDevice(),
            "Content-Type": "application/x-www-form-urlencoded"
        })
        if data:
            self.app_headers.update(
                {"NDC-MSG-SIG": generateSig(data), "Content-Type": "application/json; charset=utf-8"})
        if updateDevice:
            self.app_headers.update({"NDCDEVICEID": updateDevice})
        if lang:
            ndclang = lang[:lang.index(
                "-")] if len(lang) > 4 and not lang.lower().startswith('zh-') else lang
            self.app_headers.update(
                {"NDCLANG": ndclang, "Accept-Language": lang})
        if sid:
            self.web_headers.update({"cookie": sid})
            self.app_headers.update({"NDCAUTH": sid if sid.startswith('sid=') else f'sid={sid}'})
        self.headers_device = self.app_headers.get("NDCDEVICEID", None)
        return self.app_headers
