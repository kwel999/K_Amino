import typing_extensions as typing
from .util import (
    generateDevice,
    generateSig,
    generateUserAgent,
    uuidString
)

__all__ = ('Headers',)

DEFAULT_DEVICE_ID = generateDevice()
DEFAULT_LANG = 'en-US'
DEFAULT_USER_AGENT = "Apple iPhone13 iOS v16.1.2 Main/3.13.1"


def split_lang(lang: str) -> typing.Tuple[str, str]:
    if not lang.count('-'):
        lang = '-'.join([lang.lower(), lang.upper()])
    code = lang if lang.lower().startswith('zh-') else lang.split('-')[0]
    return code.lower(), lang.upper()


class Headers:
    """Base class for http client headers.

    Parameters
    ----------
    randomAgent: `bool`
        Change the User-Agent header for all requests.
    randomDevice: `bool`
        Change the deviceId for all requests.
    lang : `str`, `optional`
        The HTTP language. e.g. (en-US, es-MX). Default is `None`.
    deviceId : `str`, `optional`
        The session device ID.
    sid : `str`, `optional`
        The account session ID. Default is `None`.
    uid : `str`, `optional`
        The account user ID. Default is `None`.

    """

    def __init__(
        self,
        randomAgent: bool,
        randomDevice: bool,
        lang: typing.Optional[str] = None,
        deviceId: typing.Optional[str] = None,
        sid: typing.Optional[str] = None,
        uid: typing.Optional[str] = None
    ) -> None:
        self.randomAgent = randomAgent
        self.randomDevice = randomDevice
        self.lang = lang or DEFAULT_LANG
        self.deviceId = deviceId or generateDevice()
        self.sid = sid
        self.uid = uid

    @property
    def randomDevice(self) -> bool:
        return getattr(self, '_randomDevice')

    @randomDevice.setter
    def randomDevice(self, value: bool) -> None:
        setattr(self, '_randomDevice', bool(value))

    @property
    def deviceId(self) -> str:
        """The session device ID."""
        if self.randomDevice:
            setattr(self, '_deviceId', generateDevice())
        return getattr(self, '_deviceId', DEFAULT_DEVICE_ID)

    @deviceId.setter
    def deviceId(self, value: str) -> None:
        setattr(self, '_deviceId', value)

    @property
    def randomAgent(self) -> bool:
        return getattr(self, '_randomAgent')

    @randomAgent.setter
    def randomAgent(self, value: bool) -> None:
        setattr(self, '_randomAgent', bool(value))

    @property
    def agent(self) -> str:
        """The HTTP header User-Agent."""
        if self.randomAgent:
            setattr(self, '_agent', generateUserAgent())
        return getattr(self, '_agent', DEFAULT_USER_AGENT)

    @agent.setter
    def agent(self, value: str) -> None:
        setattr(self, '_agent', value)

    @property
    def uid(self) -> typing.Optional[str]:
        """The account user ID"""
        return getattr(self, '_uid', None)

    @uid.setter
    def uid(self, value: typing.Optional[str]) -> None:
        setattr(self, '_uid', value)

    @property
    def sid(self) -> typing.Optional[str]:
        """The account session ID"""
        return getattr(self, '_sid', None)

    @sid.setter
    def sid(self, value: typing.Optional[str]) -> None:
        setattr(self, '_sid', value)

    @property
    def lang(self) -> str:
        """The HTTP language. e.g. (en-US, es-MX). Default is None."""
        return getattr(self, '_lang', None) or DEFAULT_LANG

    @lang.setter
    def lang(self, value: typing.Optional[str]) -> None:
        setattr(self, '_lang', value)

    def app_headers(
        self,
        data: typing.Optional[bytes] = None,
        files: bool = False,
        sid: typing.Optional[str] = None,
        lang: typing.Optional[str] = None,
        deviceId: typing.Optional[str] = None
    ) -> typing.Dict[str, str]:
        """The HTTP headers of the app client.

        Parameters
        ----------
        data : `bytes`, `optional`
            The raw data for the request (body). Default is `None`.
        sid : `str`, `optional`
            The account session ID. Default is `None`.
        lang : `str`, `optional`
            The response language e.g. ('en-US', 'es-MX'). Default is `None`.
        diviceId : `str`, `optional`
            The session divice ID. Default is `None`.

        """
        headers = {
            "AUID": uuidString(),
            "SMDEVICEID": uuidString(),
            "NDCDEVICEID": deviceId or self.deviceId,
            "NDCLANG": "en",
            "Accept-Language": DEFAULT_LANG,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": self.agent,
            "Host": "service.aminoapps.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        if data:
            headers.update({
                "NDC-MSG-SIG": generateSig(data),
                "Content-Type": "application/json; charset=utf-8"
            })
        if files:
            headers.update({
                "Content-Type": "multipart/form-data; boundary=" + uuidString()
            })
        lang = lang or self.lang
        if lang:
            lcode, lheader = split_lang(lang)
            headers.update({"NDCLANG": lcode, "Accept-Language": lheader})
        sid = sid or self.sid
        if sid:
            headers.update({"NDCAUTH": sid if sid.startswith('sid=') else f'sid={sid}'})
        if self.uid:
            headers.update({"AUID": self.uid})
        return headers

    def web_headers(
        self,
        sid: typing.Optional[str] = None,
        lang: typing.Optional[str] = None
    ) -> typing.Dict[str, str]:
        """The HTTP headers of the web client.

        Parameters
        ----------
        sid : `str`, `optional`
            The account session ID. Default is `None`.
        lang : `str`, `optional`
            The response language e.g. ('en-US', 'es-MX'). Default is `None`.

        """
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": DEFAULT_LANG,
            "content-type": "application/json",
            "sec-ch-ua": '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            "x-requested-with": "xmlhttprequest"
        }
        sid = sid or self.sid
        if sid:
            headers.update({"cookie": sid})
        lang = lang or self.lang
        if lang:
            lcode, lheader = split_lang(lang)
            headers.update({"NDCLANG": lcode, "Accept-Language": lheader})
        return headers
