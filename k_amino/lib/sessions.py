import typing_extensions as typing
import json_minify
import ujson
import colorama
import httpx
from .exception import check_exceptions, check_server_exceptions
from .headers import Headers
from .util import api, webApi
from .types import ProxiesType

__all__ = ("Session",)


class Session(Headers):
    """Base class for client sessions.

    Parameters
    ----------
    randomAgent: `bool`
        Change the User-Agent header for all requests.
    randomDevice: `bool`
        Change the deviceId for all requests.
    debug : `bool`
        Print api debug information.
    timeout : `int`
        The timeout for all requests (seconds).
    lang : `str`, `optional`
        The HTTP language. e.g. (en-US, es-MX). Default is `None`.
    client : `Session`, `optional`
        A Session subclass instance. Default is `None`.
    proxies : `ProxiesType`, `optional`
        Proxies for HTTP requests supported by the httpx library (https://www.python-httpx.org/advanced/#routing)
    deviceId: `str`, `optional`
        The device of the client.

    """
    @typing.overload
    def __init__(
        self: typing.Self,
        *,
        client: 'Session',
        randomAgent: typing.Optional[bool] = None,
        randomDevice: typing.Optional[bool] = None,
        debug: typing.Optional[bool] = None,
        timeout: typing.Optional[int] = None,
        lang: typing.Optional[str] = None,
        proxies: typing.Optional[ProxiesType] = None,
        deviceId: typing.Optional[str] = None
    ) -> None: ...
    @typing.overload
    def __init__(
        self: typing.Self,
        *,
        randomAgent: bool,
        randomDevice: bool,
        debug: bool,
        timeout: typing.Optional[int] = None,
        lang: typing.Optional[str] = None,
        proxies: typing.Optional[ProxiesType] = None,
        deviceId: typing.Optional[str] = None
    ) -> None: ...
    def __init__(
        self: typing.Self,
        *,
        client: typing.Optional['Session'] = None,
        randomAgent: typing.Optional[bool] = None,
        randomDevice: typing.Optional[bool] = None,
        debug: typing.Optional[bool] = None,
        timeout: typing.Optional[int] = None,
        lang: typing.Optional[str] = None,
        proxies: typing.Optional[ProxiesType] = None,
        deviceId: typing.Optional[str] = None
    ) -> None:
        secret, sid, uid = None, None, None
        if client:
            randomAgent = randomAgent if isinstance(randomAgent, bool) else client.randomAgent
            randomDevice = randomDevice if isinstance(randomDevice, bool) else client.randomDevice
            debug = debug if isinstance(debug, bool) else client.debug
            timeout = timeout if isinstance(timeout, int) else client.timeout
            lang = lang if isinstance(lang, str) else client.lang
            proxies = proxies if proxies is not None else client.proxies
            deviceId = deviceId if isinstance(deviceId, str) else client.deviceId
            secret = client.secret
            sid = client.sid
            uid = client.uid
        assert isinstance(randomAgent, bool), "randomAgent must be a boolean, not %r" % randomAgent
        assert isinstance(randomDevice, bool), "randomDevice must be a boolean, not %r" % randomDevice
        assert isinstance(debug, bool), "debug must be a boolean, not %r" % debug
        super().__init__(
            randomAgent=randomAgent,
            randomDevice=randomDevice,
            lang=lang,
            deviceId=deviceId,
            sid=sid,
            uid=uid
        )
        self.proxies = proxies
        self.debug = debug
        self.timeout = timeout
        self.secret = secret

    @property
    def proxies(self: typing.Self) -> typing.Optional[ProxiesType]:
        return getattr(self, '_proxies')

    @proxies.setter
    def proxies(self: typing.Self, value: typing.Optional[ProxiesType]) -> None:
        setattr(self, '_proxies', value)

    @property
    def debug(self: typing.Self) -> bool:
        return getattr(self, '_debug')

    @debug.setter
    def debug(self: typing.Self, value: bool) -> None:
        setattr(self, '_debug', value)

    @property
    def timeout(self: typing.Self) -> typing.Optional[int]:
        return getattr(self, '_timeout')

    @timeout.setter
    def timeout(self: typing.Self, value: typing.Optional[int]) -> None:
        setattr(self, '_timeout', value)

    @property
    def secret(self: typing.Self) -> typing.Optional[str]:
        return getattr(self, '_secret')

    @secret.setter
    def secret(self: typing.Self, value: typing.Optional[str]) -> None:
        setattr(self, '_secret', value)

    def messageDebug(self, statusCode: int, method: str, url: str) -> None:
        print(f"{colorama.Fore.GREEN if statusCode == 200 else colorama.Fore.RED}{method.upper()}{colorama.Fore.RESET} | {url} - {statusCode}")

    @typing.overload
    def settings(self: typing.Self) -> None: ...
    @typing.overload
    def settings(self: typing.Self, *, sid: typing.Optional[str] = ..., uid: typing.Optional[str] = ..., secret: typing.Optional[str] = ...) -> None: ...
    def settings(self: typing.Self, **kwargs: typing.Optional[str]) -> None:
        """Update the instance settings.

        Parameters
        ----------
        sid : `str`, `optional`
            The new session ID. If not provided, the current value will be used
        uid : `str`, `optional`
            The new user ID. If not provided, the current value will be used
        secret : `str`, `optional`
            The new secret password. If not provided, the current value will be used

        """
        self.sid = kwargs.pop("sid", self.sid)
        self.uid = kwargs.pop("uid", self.uid)
        self.secret = kwargs.pop("secret", self.secret)

    def postRequest(
        self: typing.Self,
        url: str,
        data: typing.Optional[typing.Union[typing.Dict[str, typing.Any], bytes, str]] = None,
        files: typing.Optional[typing.Dict[str, typing.BinaryIO]] = None,
        newHeaders: typing.Optional[typing.Dict[str, str]] = None,
        webRequest: bool = False,
        minify: bool = False
    ) -> typing.Union[typing.Dict[str, typing.Any], typing.NoReturn]:
        """Make a POST request to the amino API.

        Parameters
        ----------
        url : `str`
            The API url/path.
        data : `dict[str, Any]`, `bytes`, `str`, `optional`
            The json data to send. Default is `None`.
        files : `dict[str, BinaryIO]`, `optional`
            The files to upload. Default is `None`.
        newHeaders : `dict[str, str]`, `optional`
            The HTTP headers to include in request. Default is `None`.
        webRequest : `bool`, `optional`
            Make web request. Default is `False`.
        minify : `bool`, `optional`
            Json minify the data. Default is `False`.

        Returns
        -------
        dict
            The response from the API.

        Raises
        ------
        AminoBaseException
            If the request fails.

        """
        if isinstance(data, dict):
            data = ujson.dumps(data)
        if isinstance(data, str):
            if minify:
                data = typing.cast(str, json_minify.json_minify(data))  # type: ignore
            data = data.encode()
        if webRequest:
            headers, url = self.web_headers(sid=self.sid), webApi(url)
        else:
            headers, url = self.app_headers(data=data, files=bool(files), sid=self.sid), api(url)
        if newHeaders:
            headers.update(newHeaders)
        with httpx.Client(proxies=self.proxies, timeout=self.timeout) as session:  # type: ignore
            response = session.post(url=url, content=data, files=files, headers=headers)
            if self.debug:
                self.messageDebug(statusCode=response.status_code, method='post', url=url)
            try:
                content = ujson.loads(response.text)
            except ujson.JSONDecodeError:
                raise check_server_exceptions(response.status_code, response.reason_phrase) from None
            if response.status_code != 200:
                raise check_exceptions(content) from None
            return content

    def getRequest(self: typing.Self, url: str, params: typing.Optional[typing.Dict[str, typing.Any]] = None) -> typing.Union[typing.Dict[str, typing.Any], typing.NoReturn]:
        """Make a GET request to the amino API.

        Parameters
        ----------
        url : `str`
            The API url/path.

        Returns
        -------
        dict
            The response from the API.

        Raises
        ------
        AminoBaseException
            If the request fails.

        """
        headers, url = self.app_headers(sid=self.sid), api(url)
        with httpx.Client(proxies=self.proxies, timeout=self.timeout) as session:  # type: ignore
            response = session.get(url=url, params=params, headers=headers)
            if self.debug:
                self.messageDebug(statusCode=response.status_code, method='get', url=url)
            try:
                content = ujson.loads(response.text)
            except ujson.JSONDecodeError:
                raise check_server_exceptions(response.status_code, response.reason_phrase) from None
            if response.status_code != 200:
                raise check_exceptions(content) from None
            return content

    def deleteRequest(self: typing.Self, url: str) -> typing.Union[typing.Dict[str, typing.Any], typing.NoReturn]:
        """Make a DELETE request to the amino API.

        Parameters
        ----------
        url : `str`
            The API url/path.

        Returns
        -------
        dict
            The response from the API.

        Raises
        ------
        AminoBaseException
            If the request fails.

        """
        headers, url = self.app_headers(sid=self.sid), api(url)
        with httpx.Client(proxies=self.proxies, timeout=self.timeout) as session:  # type: ignore
            response = session.delete(url=url, headers=headers)
            if self.debug:
                self.messageDebug(statusCode=response.status_code, method='delete', url=url)
            try:
                content = ujson.loads(response.text)
            except ujson.JSONDecodeError:
                raise check_server_exceptions(response.status_code, response.reason_phrase) from None
            if response.status_code != 200:
                raise check_exceptions(content) from None
            return content
