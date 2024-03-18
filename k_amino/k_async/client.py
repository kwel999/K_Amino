import base64
import time
import typing_extensions as typing
from .sockets import AsyncWss
from ..lib.objects import (
    Account,
    BlogList,
    Comment,
    CommentList,
    Community,
    CommunityList,
    FromCode,
    ItemList,
    Json,
    Login,
    Message,
    MessageList,
    NoticeList,
    NotificationList,
    Thread,
    ThreadList,
    UserProfile,
    UserProfileList,
    VisitorsList,
    WalletInfo,
    WalletHistory
)
from ..lib.types import (
    FileType,
    FilterType,
    NoticeType,
    ProxyType,
    ProxiesType,
    SortingType,
    ThirdPartType,
    UserType
)
from ..lib.async_sessions import AsyncSession
from ..lib.util import deprecated, generateTransactionId, get_file_type


__all__ = ("AsyncClient",)


class AsyncClient(AsyncSession, AsyncWss):
    """Represents a amino global client.

    Parameters
    ----------
    deviceId : `str`, `optional`
        The device of the client. If not provided, a random one is generated.
    proxy : `ProxyType`, `optional`
        A single proxy for HTTP requests supported by the httpx library.
    proxies : `ProxiesType`, `optional`
        Proxies for HTTP requests supported by the httpx library (https://www.python-httpx.org/advanced/#routing).
    trace : `bool`, `optional`
        Show websocket trace (logs). Default is `False`.
    bot : `bool`, `optional`
        The client is a community bot. Default is `False` (command supported).
    lang : `str`, `optional`
        The HTTP language. e.g. (en-US, es-MX). Default is `None`.
    debug : `bool`, `optional`
        Print api debug information. Default is `False`.
    randomAgent: `bool`, `optional`
        Change the User-Agent header for all requests.
    randomDevice: `bool`, `optional`
        Change the deviceId for all requests.
    timeout: `int`, `optional`
        The timeout for all requests (seconds).

    """

    def __init__(
        self: typing.Self,
        deviceId: typing.Optional[str] = None,
        proxy: typing.Optional[ProxyType] = None,
        proxies: typing.Optional[ProxiesType] = None,
        trace: bool = False,
        bot: bool = False,
        lang: typing.Optional[str] = None,
        debug: bool = False,
        randomAgent: bool = False,
        randomDevice: bool = False,
        timeout: typing.Optional[int] = None
    ) -> None:
        if proxy:
            if proxies:
                raise ValueError('You should not provide an proxy and proxies at the same time')
            proxies = typing.cast(ProxiesType, {'all://': proxy})
        AsyncWss.__init__(self, trace=trace, is_bot=bot)
        AsyncSession.__init__(
            self,
            randomAgent=randomAgent,
            randomDevice=randomDevice,
            debug=debug,
            timeout=timeout,
            lang=lang,
            proxies=proxies,
            deviceId=deviceId
        )

    async def change_lang(
        self: typing.Self,
        lang: str = "en-US"
    ) -> None:
        """Change the content language.

        Parameters
        ----------
        lang : `str`, `optional`
            The country language (ISO 3166-1 alfa-2). Default is `'en-US'`

        """
        self.lang = lang

    async def login_facebook(
        self: typing.Self,
        email: str,
        accessToken: str,
        address: typing.Optional[str] = None,
        socket: bool = False
    ) -> Login:
        """Login via Facebook.

        Parameters
        ----------
        email : `str`
            The account email.
        accessToken : `str`
            The facebook third-party oauth access token.
        address : `str`, `optional`
            The geographical address. Default is `None`.
            Possible values: locality, sub-locality, administrative area, sub-administrative area, address line (without country)
            If the country is specified, it should be separated by a comma `,` e.g., (locality, country)
        socket : `bool`, `optional`
            Run the websocket after login. Default is `False`.

        Returns
        -------
        Login
            The login object.

        """
        req = await self.postRequest("/g/s/auth/login", {
            'secret': f'10 {accessToken}',
            'clientType': 100,
            'clientCallbackURL': 'ndc://relogin',
            'email': email,  # optional ?
            'latitude': 0,
            'longitude': 0,
            'address': address,
            'action': 'normal',
            #'thirdPart': True,  # tag, not value?
            'timestamp': int(time.time() * 1000),
            'deviceID': self.deviceId,
        })
        self.settings(sid=req["sid"], uid=req["auid"], secret=req["secret"])
        if socket or self.is_bot:
            await self.launch()
        return Login(req)

    async def login_google(
        self: typing.Self,
        accessToken: str,
        address: typing.Optional[str] = None,
        socket: bool = False
    ) -> Login:
        """Login via Google.

        Parameters
        ----------
        accessToken : `str`
            The google third-party oauth access token.
        address : `str`, `optional`
            The geographical address. Defaults to None.
            Possible values: locality, sub-locality, administrative area, sub-administrative area, address line (without country)
            If the country is specified, it should be separated by a comma `,` e.g., (locality, country)
        socket : `bool`, `optional`
            Run the websocket after login. Default is `False`.

        Returns
        -------
        Login
            The login object.

        """
        req = await self.postRequest("/g/s/auth/login", {
            'secret': f'30 {accessToken}',
            'clientType': 100,
            # 'clientCallbackURL': 'ndc://relogin',  # ???
            'latitude': 0,
            'longitude': 0,
            'address': address,
            'action': 'normal',
            #'thirdPart': True,  # tag, not value?
            'timestamp': int(time.time() * 1000),
            'deviceID': self.deviceId,
        })
        self.settings(sid=req["sid"], uid=req["auid"], secret=req["secret"])
        if socket or self.is_bot:
            await self.launch()
        return Login(req)

    async def auto_signup_google(
        self: typing.Self,
        email: str,
        password: str,
        nickname: str,
        accessToken: str,
        address: typing.Optional[str] = None,
        socket: bool = False
    ) -> Login:
        """Login via Google.

        Parameters
        ----------
        email : `str`
            The account email address to register. If you are already registered, raise an EmailAlreadyTaken exception.
        password : `str`
            The account password.
        nickname : `str`
            The nickname of the account.
        accessToken : `str`
            The google third-party oauth access token.
        address : `str`, `optional`
            The geographical address. Default is `None`.
            Possible values: locality, sub-locality, administrative area, sub-administrative area, address line (without country)
            If the country is specified, it should be separated by a comma `,` e.g., (locality, country)
        socket : `bool`, `optional`
            Run the websocket after login. Default is `False`.

        Returns
        -------
        Login
            The login object.

        """
        await self.register_check(email=email)
        await self.signup_add_profile(email, password, nickname, accessToken=accessToken, thirdPart='google', address=address)
        req = await self.postRequest("/g/s/auth/login", {
            #"validationContext": None,
            "secret": f"30 {accessToken}",
            "clientType": 100,
            # 'clientCallbackURL': 'ndc://relogin',  # ???
            "action": "auto",
            #'email': email,
            "timestamp": int(time.time() * 1000),
            "deviceID": self.deviceId,
            "latitude": 0,
            "longitude": 0,
            "address": address,
        })
        self.settings(sid=req["sid"], uid=req["auid"], secret=req["secret"])
        if socket or self.is_bot:
            await self.launch()
        return Login(req)

    async def login(
        self: typing.Self,
        email: str,
        password: str,
        socket: bool = False,
    ) -> Login:
        """Login via email.

        Parameters
        ----------
        email : `str`
            The account email.
        password : `str`
            The account password.
        socket : `bool`, `optional`
            Run the websocket after login. Default is `False`.

        Returns
        -------
        Login
            The login object.

        Raises
        ------
        ValueError
            If no valid login info provided.

        """
        data = {
            "email": email,
            "secret": f"0 {password}",
            "clientType": 100,
            "action": "normal",
            "deviceID": self.deviceId,
            "v": 2,
            "timestamp": int(time.time() * 1000),
        }
        req = await self.postRequest("/g/s/auth/login", data)
        self.settings(sid=req["sid"], uid=req["auid"], secret=req["secret"])
        if socket or self.is_bot:
            await self.launch()
        return Login(req)

    async def login_secret(self, secret: str, socket: bool = False) -> Login:
        """Login via secret token.

        Parameters
        ----------
        secret : str
            The account secret token.
        socket : `bool`, `optional`
            Run the websocket after login. Default is `False`.

        Returns
        -------
        Login
            The login object.

        """
        data = {
            "secret": secret,
            "clientType": 100,
            "action": "normal",
            "deviceID": self.deviceId,
            "v": 2,
            "timestamp": int(time.time() * 1000),
        }
        req = await self.postRequest("/g/s/auth/login", data)
        self.settings(sid=req["sid"], uid=req["auid"], secret=secret)
        if socket or self.is_bot:
            await self.launch()
        return Login(req)

    async def sid_login(
        self: typing.Self,
        sid: str,
        socket: bool = False
    ) -> Account:
        """Login via session ID.

        Parameters
        ----------
        sid : `str`
            The amino session ID.
        socket : `bool`, `optional`
            Run the websocket after login. Default is `False`.

        Returns
        -------
        Account
            The user account.

        """
        self.settings(sid=sid)
        info = await self.get_account_info()
        self.settings(uid=info.userId)
        if socket:
            await self.launch()
        return info

    async def logout(self: typing.Self) -> Json:
        """Logout from the account.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "deviceID": self.deviceId,
            "clientType": 100,
            "timestamp": int(time.time() * 1000),
        }
        req = await self.postRequest("/g/s/auth/logout", data)
        self.settings(sid=None, uid=None, secret=None)
        if self.isOpened:
            await self.close()
        return Json(req)

    @typing.overload
    async def update_email(self: typing.Self, email: str, new_email: str, code: str, password: str) -> Json: ...
    @typing.overload
    async def update_email(self: typing.Self, email: str, new_email: str, code: str, *, secret: str) -> Json: ...
    async def update_email(
        self: typing.Self,
        email: str,
        new_email: str,
        code: str,
        password: typing.Optional[str] = None,
        secret: typing.Optional[str] = None
    ) -> Json:
        """Update the account email.

        Parameters
        ----------
        email : `str`
            The current account email.
        new_email : `str`
            The new account email to update.
        code : `str`
            The security verification code.
        password : `str`, `optional`
            The account password. Default is `None`.
        secret : `str`, `optional`
            The account secret password. Defualt is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest('auth/update-email', data={
            "newValidationContext": {
                "secret": f'0 {password}' if password else secret,
                "identity": new_email,
                "data": {"code": code},
                "level": 1,
                "type": 1,
                "deviceID": self.deviceId
            },
            "oldValidationContext": {
                "identity": email,
                "level": 1,
                "data": {"code": code},
                "type": 1,
                "deviceID": self.deviceId
            }
        }))

    async def check_device(self: typing.Self, deviceId: str) -> Json:
        """Check if the device is avalible.

        Parameters
        ----------
        deviceId : `str`
            The device to check.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "deviceID": deviceId,
            "timestamp": int(time.time() * 1000),
            "clientType": 100,
        }
        return Json(await self.postRequest("/g/s/device/", data, newHeaders={"NDCDEVICEID": deviceId}))

    async def upload_media(self: typing.Self, file: typing.Union[typing.BinaryIO, bytes], fileType: FileType) -> str:
        """Upload a media to the amino server.

        Parameters
        ----------
        file : `BinaryIO`, `bytes`
            The file opened in read-byte mode (rb).
        fileType : `str`
            The file type (audio, gif, image, video).

        Returns
        -------
        str
            The url of the uploaded image.

        """
        data = file if isinstance(file, bytes) else file.read()
        if fileType not in typing.get_args(FileType):
            raise ValueError("fileType must be %s not %r." % (', '.join(map(repr, typing.get_args(FileType))), fileType))
        ext = "acc" if fileType == "audio" else "mp4" if fileType == "video" else "gif" if fileType == "gif" else "png"
        newHeaders = {"Content-Type": f"{fileType}/" + get_file_type(getattr(file, 'name', f'.{ext}'))}
        return (await self.postRequest("/g/s/media/upload", data=data, newHeaders=newHeaders))["mediaValue"]

    @typing.deprecated("upload_image is deprecated, use upload_media instead")
    @deprecated(upload_media.__qualname__)
    async def upload_image(self: typing.Self, image: typing.BinaryIO) -> str:
        """Upload an image to the amino server.

        Parameters
        ----------
        image : `BinaryIO`
            The image file opened in read-byte mode (rb).

        Returns
        -------
        str
            The url of the uploaded image.

        """
        return await self.upload_media(image, "image")

    async def send_verify_code(self: typing.Self, email: str, resetPassword: bool = False, key: typing.Optional[str] = None) -> Json:
        """Request verification code via email.

        Parameters
        ----------
        email : `str`
            The email to send the code.
        resetPassword : `bool`, `optional`
            Verification is to reset the password.
        key : `str`, `optional`
            The verification key info.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "identity": email,
            "type": 1,
            "deviceID": self.deviceId,
            "timestamp": int(time.time() * 1000),
        }
        if key:
            data["verifyInfoKey"] = key 
        if resetPassword:
            data["level"] = 2
            data["purpose"] = "reset-password"
        return Json(await self.postRequest("/g/s/auth/request-security-validation", data))

    async def accept_host(self: typing.Self, requestId: str, chatId: str) -> Json:
        """Accept the chat host transfer request.

        Parameters
        ----------
        requestId : `str`
            The transfer request ID.
        chatId : `str`
            The chat ID associated with the transfer.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept"))

    async def verify(
        self: typing.Self,
        email: str,
        code: str,
        deviceId: typing.Optional[str] = None,
        resetPassword: bool = False
    ) -> Json:
        """Confirm an email action.

        Parameters
        ----------
        email : str
            The account email.
        code : str
            The verification code.
        deviceId : str, optional
            The deviceId to send the confirmation. If not provided, the current deviceId is used.
        resetPassword : bool, optional
            The action is to reset the password. Default is `False`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "validationContext": {
                "type": 1,
                "identity": email,
                "data": {"code": code}},
            "deviceID": deviceId or self.deviceId,
            "timestamp": int(time.time() * 1000)
        }
        if resetPassword:
            data["level"] = 2
        return Json(await self.postRequest("/g/s/auth/check-security-validation", data))

    async def verify_account(self, email: str, key: str, code: typing.Optional[str] = None) -> Json:
        """Confirm that an email is yours
    
        Normally, you need to confirm when logging in on other devices for amino to allow you to log in.

        Parameters
        ----------
        email : `str`
            The account email to verify.
        key : `str`
            The verification token received in the mailbox (verifyInfoKey).
        code : `str`, `optional`
            The verification code received in the mailbox.

        Raises
        ------
        InvalidAuthNewDeviceLink
            If the token does not exist or is already used.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest("/g/s/auth/verify-account", data={
            "validationContext": {
                "type": 1,
                "identity": email,
                "data": {"code": code}
            },
            "verifyInfoKey": key,
            "deviceID": self.deviceId,
            "timestamp": int(time.time() * 1000)
        }))

    async def activate_account(self: typing.Self, email: str, code: str) -> Json:
        """Complete the account activation verification.

        Parameters
        ----------
        email : `str`
            The account email to verify.
        code : `str`
            The verification code.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "type": 1,
            "identity": email,
            "data": {"code": code},
            "deviceID": self.deviceId,
        }
        return Json(await self.postRequest("/g/s/auth/activate-email", data))

    @typing.overload
    async def restore(self: typing.Self, email: str, password: str) -> Json: ...
    @typing.overload
    async def restore(self: typing.Self, email: str, *, secret: str) -> Json: ...
    async def restore(
        self: typing.Self,
        email: str,
        password: typing.Optional[str] = None,
        secret: typing.Optional[str] = None
    ) -> Json:
        """Restore an account (after deletion).

        Parameters
        ----------
        email : `str`
            The account email to restore.
        password : `str`
            The account password.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "secret": f"0 {password}" if password else secret,
            "deviceID": self.deviceId,
            "email": email,
            "timestamp": int(time.time() * 1000),
        }
        return Json(await self.postRequest("/g/s/account/delete-request/cancel", data))

    @typing.overload
    async def delete_account(self: typing.Self, password: str) -> Json: ...
    @typing.overload
    async def delete_account(self: typing.Self, *, secret: str) -> Json: ...
    async def delete_account(self: typing.Self, password: typing.Optional[str] = None, secret: typing.Optional[str] = None) -> Json:
        """Delete a user account.

        Parameters
        ----------
        password : `str`, `optional`
            The password of the account.
        secret : `str`, `optional`
            The secret password of the account.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the password and secret is not provided.

        """
        if not (password and secret):
            raise ValueError("Please provide a valid account info")
        data = {
            "deviceID": self.deviceId,
            "secret": f"0 {password}" if password else secret,
            "timestamp": int(time.time() * 1000),
        }
        return Json(await self.postRequest("/g/s/account/delete-request", data))

    async def get_account_info(self: typing.Self) -> Account:
        """Get account information.

        Returns
        -------
        Account
            The user account object.

        """
        return Account((await self.getRequest("/g/s/account"))["account"])

    async def claim_coupon(self: typing.Self) -> Json:
        """Claim the new-user coupon.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest("/g/s/coupon/new-user-coupon/claim"))

    async def change_amino_id(self: typing.Self, aminoId: str) -> Json:
        """Change the account amino ID.

        Parameters
        ----------
        aminoId : `str`
            The new amino ID.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "aminoId": aminoId,
            "timestamp": int(time.time() * 1000)
        }
        return Json(await self.postRequest("/g/s/account/change-amino-id", data))

    async def get_my_communities(self: typing.Self, start: int = 0, size: int = 25) -> CommunityList:
        """Get a list of the user's joined communities.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        CommunityList
            The joined community list object.

        """
        return CommunityList((await self.getRequest(f"/g/s/community/joined?v=1&start={start}&size={size}"))["communityList"]).CommunityList

    async def get_chat_threads(self: typing.Self, start: int = 0, size: int = 25) -> ThreadList:
        """Get a list of the user's joined chats.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is 0.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        ThreadList
            The joined community list object.

        """
        return ThreadList((await self.getRequest(f"/g/s/chat/thread?type=joined-me&start={start}&size={size}"))["threadList"]).ThreadList

    async def get_chat_info(self: typing.Self, chatId: str) -> Thread:
        """Get chat information.

        Parameters
        ----------
        chatId : `str`
            The chat ID to get information.

        Returns
        -------
        Thread
            The chat object.

        """
        return Thread((await self.getRequest(f"/g/s/chat/thread/{chatId}"))["thread"]).Thread

    async def leave_chat(self: typing.Self, chatId: str) -> Json:
        """Leave a chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID to leave.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}"))

    async def join_chat(self: typing.Self, chatId: str) -> Json:
        """Join a chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID to join.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}"))

    async def start_chat(
        self: typing.Self,
        userId: typing.Union[typing.List[str], str],
        title: typing.Optional[str] = None,
        message: typing.Optional[str] = None,
        content: typing.Optional[str] = None,
        chatType: int = 0,
    ) -> Thread:
        """Start a chat.

        Parameters
        ----------
        userId : `list[str]`, `str`
            The user ID to chat or list of user IDs to chat.
        title : `str`, `optional`
            The chat title. Default is `None`.
        message : `str`, `optional`
            The initial message. Default is `None`.
        content : `str`, `optional`
            The chat description. Default is `None`.
        chatType : `int`, `optional`
            The chat type. Default is `0`.
                0: DM
                1: Private
                2: Public

        Returns
        -------
        Thread
            The new chat object.

        """
        if not isinstance(userId, list):
            userId = [userId]
        data = {
            "title": title,
            "inviteeUids": userId,
            "initialMessageContent": message,
            "content": content,
            "type": chatType,
            "timestamp": int(time.time() * 1000),
        }
        return Thread((await self.postRequest(f"/g/s/chat/thread", data))["thread"]).Thread

    async def get_from_link(self: typing.Self, link: str) -> FromCode:
        """Get data from a link.

        Parameters
        ----------
        link : `str`
            The link to get data.

        Returns
        -------
        FromCode
            The link data object.

        """
        return FromCode((await self.getRequest(f"/g/s/link-resolution?q={link}"))["linkInfoV2"]["extensions"]).FromCode

    async def edit_profile(
        self: typing.Self,
        nickname: typing.Optional[str] = None,
        content: typing.Optional[str] = None,
        icon: typing.Optional[typing.Union[typing.BinaryIO, str]] = None,
        backgroundColor: typing.Optional[str] = None,
        backgroundImage: typing.Optional[typing.Union[typing.BinaryIO, str]] = None,
        defaultBubbleId: typing.Optional[str] = None
    ) -> Json:
        """Edit the global profile.

        Parameters
        ----------
        nickname : `str`, `optional`
            The new nickname. Default is `None`.
        content : `str`, `optional`
            The new bio. Default is `None`.
        icon : `BinaryIO`, `str`, `optional`
            The opened file in rb mode, filepath or url. Default is `None`.
        backgroundColor : `str`, `optional`
            The new background color in hex code. Default is `None`.
        backgroundImage : `BinaryIO`, `str`, `optional`
            The opened file in rb mode, filepath or url. Default is `None`.
        defaultBubbleId : `str`, `optional`
            The new default bubble ID. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        extensions: typing.Dict[str, typing.Any] = {}
        data: typing.Dict[str, typing.Any] = {
            "address": None,
            "latitude": 0,
            "longitude": 0,
            "mediaList": None,
            "eventSource": "UserProfileView",
            "timestamp": int(time.time() * 1000),
        }
        if content:
            data["content"] = content
        if nickname:
            data["nickname"] = nickname
        if icon:
            if not isinstance(icon, str):
                icon = await self.upload_media(icon, "image")
            if not icon.startswith('http'):
                with open(icon, 'rb') as f:
                    icon = await self.upload_media(f, "image")
            data["icon"] = icon
        if defaultBubbleId:
            extensions["defaultBubbleId"] = defaultBubbleId
        if backgroundColor:
            extensions["style"] = {"backgroundColor": backgroundColor}
        if backgroundImage:
            if not isinstance(backgroundImage, str):
                backgroundImage = await self.upload_media(backgroundImage, "image")
            if not backgroundImage.startswith('http'):
                with open(backgroundImage, 'rb') as f:
                    backgroundImage = await self.upload_media(f, "image")
            extensions["style"] = {"backgroundMediaList": [[100, backgroundImage, None, None, None]]}
        if extensions:
            data["extensions"] = extensions
        return Json(await self.postRequest(f"/g/s/user-profile/{self.uid}", data))

    async def flag_community(self: typing.Self, comId: str, reason: str, flagType: int = 0) -> Json:
        """Flag a community.

        Parameters
        ----------
        comId : `str`
            The community ID to flag.
        reason : `str`
            The reason for the flag.
        flagType : `int`, `optional`
            The type of the flag. Default is `0`.
                0: bully
                2: spam
                4: off-topic
                106: violence
                107: hate
                108: suicide
                109: troll
                110: nudity

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "objectId": comId,
            "objectType": 16,
            "flagType": flagType,
            "message": reason,
            "timestamp": int(time.time() * 1000),
        }
        return Json(await self.postRequest(f"/x{comId}/s/g-flag", data))

    async def leave_community(self: typing.Self, comId: int) -> Json:
        """Leave a community.

        Parameters
        ----------
        comId : `str`
            The community ID to leave.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest(f"x/{comId}/s/community/leave"))

    async def join_community(self: typing.Self, comId: int, invId: typing.Optional[str] = None) -> Json:
        """Join a community.

        Parameters
        ----------
        comId : `int`
            The community ID to join.
        invId : `str`, `optional`
            The community invitation ID. Default is None.

        Returns
        -------
        Json
            The JSON response.

        """
        data: typing.Dict[str, typing.Any] = {"timestamp": int(time.time() * 1000)}
        if invId:
            data["invitationId"] = invId
        return Json(await self.postRequest(f"/x{comId}/s/community/join", data))

    async def flag(
        self: typing.Self,
        reason: str,
        flagType: int = 0,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        userId: typing.Optional[str] = None,
    ) -> Json:
        """Flag a post or user.

        Parameters
        ----------
        reason : `str`
            The reason of the flag.
        flagType : `int`, `optional`
            The type of the flag. Default is `0`.
                0: bully
                2: spam
                4: off-topic
                106: violence
                107: hate
                108: suicide
                109: troll
                110: nudity
        blogId : `str`, `optional`
            The blog ID to flag.
        wikiId : `str`, `optional`
            The wiki ID to flag.
        userId : `str`, `optional`
            The user ID to flag.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId and userId are not provided.

        """
        data = {
            "message": reason,
            "flagType": flagType,
            "timestamp": int(time.time() * 1000),
        }
        if userId:
            data["objectId"] = userId
            data["objectType"] = 0
        elif blogId:
            data["objectId"] = blogId
            data["objectType"] = 1
        elif wikiId:
            data["objectId"] = wikiId
            data["objectType"] = 2
        else:
            raise ValueError("Please put blog, user or wiki Id")
        return Json(await self.postRequest("/g/s/flag", data))

    async def unfollow(self: typing.Self, userId: str) -> Json:
        """Unfollow a user.

        Parameters
        ----------
        userId : `str`
            The user ID to unfollow.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest(f"/g/s/user-profile/{userId}/member/{self.uid}"))

    async def follow(self: typing.Self, userId: typing.Union[typing.List[str], str]) -> Json:
        """Follow a user or users.

        Parameters
        ----------
        userId : `list[str]`, `str`
            The user ID or list of user IDs to follow.

        Returns
        -------
        Json
            The JSON response.

        """
        data: typing.Dict[str, typing.Any] = {"timestamp": int(time.time() * 1000)}
        if isinstance(userId, list):
            data["targetUidList"] = userId
            link = f"/g/s/user-profile/{self.uid}/joined"
        else:
            link = f"/g/s/user-profile/{userId}/member"
        return Json(await self.postRequest(link, data))

    async def get_member_following(self: typing.Self, userId: str, start: int = 0, size: int = 25) -> UserProfileList:
        """Get user's followings.

        Parameters
        ----------
        userId : `str`
            The user ID to get the list.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        UserProfileList
            The follwing member list object.

        """
        return UserProfileList((await self.getRequest(f"/g/s/user-profile/{userId}/joined?start={start}&size={size}"))["userProfileList"]).UserProfileList

    async def get_member_followers(self: typing.Self, userId: str, start: int = 0, size: int = 25) -> UserProfileList:
        """Get user's followers.

        Parameters
        ----------
        userId : `str`
            The user ID to get the list.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        UserProfileList
            The follower list object.

        """
        return UserProfileList((await self.getRequest(f"/g/s/user-profile/{userId}/member?start={start}&size={size}"))["userProfileList"]).UserProfileList

    async def get_member_visitors(self: typing.Self, userId: str, start: int = 0, size: int = 25) -> VisitorsList:
        """Get user's visitor list.

        Parameters
        ----------
        userId : `str`
            The user ID to get the list.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        VisitorsList
            The visitor list object.
        """
        return VisitorsList((await self.getRequest(f"/g/s/user-profile/{userId}/visitors?start={start}&size={size}"))["visitors"]).VisitorsList

    async def get_blocker_users(self: typing.Self, start: int = 0, size: int = 25) -> typing.List[str]:
        """Get blocker user ID list.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        list
            The blocker user ID list.
        """
        return (await self.getRequest(f"/g/s/block/full-list?start={start}&size={size}"))["blockerUidList"]

    async def get_blocked_users(self: typing.Self, start: int = 0, size: int = 25) -> typing.List[str]:
        """Get blocked user ID list.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        list
            The blocked user ID list.
        """
        return (await self.getRequest(f"/g/s/block/full-list?start={start}&size={size}"))["blockedUidList"]

    async def get_wall_comments(self: typing.Self, userId: str, sorting: SortingType = "newest", start: int = 0, size: int = 25) -> CommentList:
        """Get a list of comment in a user's wall.

        Parameters
        ----------
        userId : `str`
            The user ID to get the list.
        sorting : `str`, `optional`
            The sorting of the list (newest, oldest, vote). Default is 'newest'.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        CommentList
            The wall comment list object.

        Raises
        ------
        ValueError
            If the sorting is invalid.

        """
        if sorting not in typing.get_args(SortingType):
            raise ValueError("Sorting must be one of %s, not %r" % (', '.join(map(repr, typing.get_args(SortingType))), sorting))
        return CommentList((await self.getRequest(f"/g/s/user-profile/{userId}/g-comment?sort={sorting}&start={start}&size={size}"))["commentList"]).CommentList

    @typing.overload
    async def get_blog_comments(
        self: typing.Self,
        wikiId: str,
        *,
        sorting: SortingType = "newest",
        start: int = 0,
        size: int = 25,
    ) -> CommentList: ...
    @typing.overload
    async def get_blog_comments(
        self: typing.Self,
        *,
        blogId: str,
        sorting: SortingType = "newest",
        start: int = 0,
        size: int = 25,
    ) -> CommentList: ...
    async def get_blog_comments(
        self: typing.Self,
        wikiId: typing.Optional[str] = None,
        blogId: typing.Optional[str] = None,
        sorting: SortingType = "newest",
        start: int = 0,
        size: int = 25,
    ) -> CommentList:
        """Get post comments.

        Parameters
        ----------
        wikiId : `str`, `optional`
            The wiki ID to get the list. Default is `None`.
        blogId : `str`, `optional`
            The blog ID to get the list. Default is `None`.
        sorting : `str`, `optional`
            The sorting of the list (newest, oldest, vote). Default is 'newest'.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        CommentList
            The post comment list object.

        Raises
        ------
        ValueError
            If the sorting or post ID is invalid.

        """
        if sorting not in typing.get_args(SortingType):
            raise ValueError("Sorting must be one of %s, not %r" % (', '.join(map(repr, typing.get_args(SortingType))), sorting))
        if blogId:
            link = f"/g/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}"
        elif wikiId:
            link = f"/g/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}"
        else:
            raise ValueError("Please choose a wiki or a blog")
        return CommentList((await self.getRequest(link))["commentList"]).CommentList

    @typing.overload  # sticker
    async def send_message(
        self: typing.Self,
        chatId: str,
        *,
        stickerId: str
    ) -> Json: ...
    @typing.overload  # file
    async def send_message(
        self: typing.Self,
        chatId: str,
        *,
        file: typing.BinaryIO,
        fileType: typing.Literal['audio', 'gif', 'image']
    ) -> Json: ...
    @typing.overload  # video file
    async def send_message(
        self: typing.Self,
        chatId: str,
        *,
        file: typing.BinaryIO,
        fileType: typing.Literal['video'],
        fileCoverImage: typing.Optional[typing.BinaryIO] = None
    ) -> Json: ...
    @typing.overload  # yt-video
    async def send_message(
        self,
        chatId: str, *,
        ytVideo: str,
        replyTo: typing.Optional[str] = None,
        mentionUserIds: typing.Optional[typing.Union[typing.List[str], str]] = None
    ) -> Json: ...
    @typing.overload  # yt-video + embed
    async def send_message(
        self: typing.Self,
        chatId: str,
        *,
        ytVideo: str,
        embedId: str,
        embedType: int,
        embedLink: str,
        embedTitle: str,
        embedContent: typing.Optional[str] = None,
        embedImage: typing.Optional[typing.Union[typing.BinaryIO, str]] = None,
        replyTo: typing.Optional[str] = None,
        mentionUserIds: typing.Optional[typing.Union[typing.List[str], str]] = None
    ) -> Json: ...
    @typing.overload  # yt-video + snippet
    async def send_message(
        self: typing.Self,
        chatId: str,
        *,
        ytVideo: str,
        snippetLink: str,
        snippetImage: typing.BinaryIO,
        replyTo: typing.Optional[str] = None,
        mentionUserIds: typing.Optional[typing.Union[typing.List[str], str]] = None
    ) -> Json: ...
    @typing.overload  # text
    async def send_message(
        self: typing.Self,
        chatId: str,
        message: str,
        messageType: int = 0,
        *,
        replyTo: typing.Optional[str] = None,
        mentionUserIds: typing.Optional[typing.Union[typing.List[str], str]] = None
    ) -> Json: ...
    @typing.overload  # text + embed
    async def send_message(
        self: typing.Self,
        chatId: str,
        message: typing.Optional[str] = None,
        messageType: int = 0,
        *,
        embedId: str,
        embedType: int,
        embedLink: str,
        embedTitle: str,
        embedContent: typing.Optional[str] = None,
        embedImage: typing.Optional[typing.Union[typing.BinaryIO, str]] = None,
        replyTo: typing.Optional[str] = None,
        mentionUserIds: typing.Optional[typing.Union[typing.List[str], str]] = None
    ) -> Json: ...
    @typing.overload  # text + snippet
    async def send_message(
        self,
        chatId: str,
        message: typing.Optional[str] = None,
        messageType: int = 0,
        *,
        snippetLink: str,
        snippetImage: typing.BinaryIO,
        replyTo: typing.Optional[str] = None,
        mentionUserIds: typing.Optional[typing.Union[typing.List[str], str]] = None
    ) -> Json: ...
    async def send_message(
        self: typing.Self,
        chatId: str,
        message: typing.Optional[str] = None,
        messageType: int = 0,
        file: typing.Optional[typing.BinaryIO] = None,
        fileType: typing.Optional[FileType] = None,
        fileCoverImage: typing.Optional[typing.BinaryIO] = None,
        replyTo: typing.Optional[str] = None,
        mentionUserIds: typing.Optional[typing.Union[typing.List[str], str]] = None,
        stickerId: typing.Optional[str] = None,
        snippetLink: typing.Optional[str] = None,
        ytVideo: typing.Optional[str] = None,
        snippetImage: typing.Optional[typing.BinaryIO] = None,
        embedId: typing.Optional[str] = None,
        embedType: typing.Optional[int] = None,
        embedLink: typing.Optional[str] = None,
        embedTitle: typing.Optional[str] = None,
        embedContent: typing.Optional[str] = None,
        embedImage: typing.Optional[typing.Union[typing.BinaryIO, str]] = None,
    ) -> Json:
        """Send a chat message.

        Parameters
        ----------
        chatId : `str`
            The chat ID to send the message.
        message : `str`, `optional`
            The message to send. Default is `None`.
        messageType : `int`, `optional`
            The message type. Default is `0`.
        file : `BinaryIO`, `optional`
            The file to send, opened in read-bytes. Default is `None`.
        fileType : `FileType`, `optional`
            The file type to send (audio, gif, image, video). Default is `None`.
        fileCoverImage : `BinaryIO`, `optional`
            The cover image for the video file. Default is `None`.
        replyTo : `str`, `optional`
            The message ID to reply. Default is `None`.
        mentionUserIds : `list[str]`, `str`, `optional`
            The mention user IDs. Default is `None`.
        stickerId : `str`, `optional`
            The sticker ID to send. Default is `None`.
        snippetLink : `str`, `optional`
            The snippet link to send. Default is `None`.
        ytVideo : `str`, `optional`
            The Youtube video URL to send. Default is `None`.
        snippetImage : `BinaryIO`, `optional`
            The snippet image opened in read-bytes. Default is `None`.
        embedId : `str`, `optional`
            The embed object ID. Default is `None`.
        embedType : `int`, `optional`
            The embed object type. Default is `None`.
        embedLink : `str`, `optional`
            The embed URL. Default is `None`.
        embedTitle : `str`, `optional`
            The embed title. Default is `None`.
        embedContent : `str`, `optional`
            The embed message. Default is `None`.
        embedImage : `BinaryIO`, `str`, `optional`
            The embed image opened in read-bytes. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the file type to send is invalid.

        """
        mentions: typing.List[typing.Any] = []
        embedMedia: typing.List[typing.Any] = []
        extensions: typing.Dict[str, typing.Any] = {}
        files = None
        if message is not None and file is None:
            message = message.replace("[@", "\u200e\u200f").replace("@]", "\u202c\u202d")
        if mentionUserIds:
            if isinstance(mentionUserIds, list):
                mentions.extend({"uid": uid} for uid in mentionUserIds)
            else:
                mentions.append({"uid": mentionUserIds})
            extensions["mentionedArray"] = mentions
        if embedImage:
            if not isinstance(embedImage, str):
                embedMedia = [[100, self.upload_media(embedImage, "image"), None]]
            else:
                embedMedia = [[100, embedImage, None]]
        data = {
            "type": messageType,
            "content": message,
            "attachedObject": None,
            "extensions": extensions,
            "clientRefId": int(time.time() / 10 % 100000000),
            "timestamp": int(time.time() * 1000),
        }
        if any((embedId, embedType, embedLink, embedTitle, embedContent, embedMedia)):
            data["attachedObject"] = {
                "objectId": embedId,
                "objectType": embedType,
                "link": embedLink,
                "title": embedTitle,
                "content": embedContent,
                "mediaList": embedMedia,
            }
        if replyTo:
            data["replyMessageId"] = replyTo
        if stickerId:
            data["content"] = None
            data["stickerId"] = stickerId
            data["type"] = 3
        if snippetLink and snippetImage:
            data["attachedObject"] = None
            extensions["linkSnippetList"] = [{
                "link": snippetLink,
                "mediaType": 100,
                "mediaUploadValue": base64.b64encode(snippetImage.read()).decode(),
                "mediaUploadValueContentType": "image/%s" % get_file_type(snippetImage.name, "png"),
            }]
        if ytVideo:
            data["content"] = None
            data["mediaType"] = 103
            data["mediaValue"] = ytVideo
        if file:
            data["content"] = None
            if fileType == "audio":
                data["type"] = 2
                data["mediaType"] = 110
            elif fileType == "image":
                data["mediaType"] = 100
                data["mediaUploadValueContentType"] = "image/%s" % get_file_type(file.name, "jpg")
                data["mediaUhqEnabled"] = False
            elif fileType == "gif":
                data["mediaType"] = 100
                data["mediaUploadValueContentType"] = "image/gif"
                data["mediaUhqEnabled"] = False
            elif fileType == "video":
                files = {"video.mp4": file}
                videoUpload = {
                    "contentType": "video/mp4",
                    "video": "video.mp4"
                }
                if fileCoverImage:
                    videoUpload["cover"] = "cover.jpg"
                    files["cover.jpg"] = fileCoverImage
                data["videoUpload"] = videoUpload
            else:
                raise ValueError(fileType)
            data["mediaUploadValue"] = base64.b64encode(file.read()).decode()
            data["attachedObject"] = None
            data["extensions"] = None
        return Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/message", data=data, files=files))

    async def get_community_info(self: typing.Self, comId: str) -> Community:
        """Get community information.

        Parameters
        ----------
        comId : `str`
            The community ID to get information.

        Returns
        -------
        Community
            The community object.

        """
        return Community((await self.getRequest("/g/s-x{comId}/community/info?withInfluencerList=1&withTopicList=true&influencerListOrderStrategy=fansCount"))["community"]).Community

    async def mark_as_read(self: typing.Self, chatId: str) -> Json:
        """Mark as read a chat

        Parameters
        ----------
        chatId : `str`
            The chat ID to mark as read.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/mark-as-read"))

    async def delete_message(self: typing.Self, chatId: str, messageId: str) -> Json:
        """Delete a message.

        Parameters
        ----------
        chatId : `str`
            The chat ID associated with the message.
        messageId : `str`
            The message ID to delete.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(f"/g/s/chat/thread/{chatId}/message/{messageId}"))

    async def get_chat_messages(self: typing.Self, chatId: str, start: int = 0, size: int = 25) -> MessageList:
        """Get messages from a chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID to get messages.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        MessageList
            The message list object.

        """
        return MessageList((await self.getRequest(f"/g/s/chat/thread/{chatId}/message?v=2&pagingType=t&start={start}&size={size}"))["messageList"]).MessageList  # is valid?

    async def get_message_info(self: typing.Self, messageId: str, chatId: str) -> Message:
        """The message information.

        Parameters
        ----------
        messageId : `str`
            The message ID to get information.
        chatId : `str`
            The chat ID associated with the message.

        Returns
        -------
        Message
            The message object.

        """
        return Message((await self.getRequest(f"/g/s/chat/thread/{chatId}/message/{messageId}"))["message"]).Message

    @typing.overload
    async def tip_coins(self: typing.Self, coins: int, chatId: str, *, transactionId: typing.Optional[str] = None) -> Json: ...
    @typing.overload
    async def tip_coins(self: typing.Self, coins: int, *, blogId: str, transactionId: typing.Optional[str] = None) -> Json: ...
    async def tip_coins(
        self: typing.Self,
        coins: int,
        chatId: typing.Optional[str] = None,
        blogId: typing.Optional[str] = None,
        transactionId: typing.Optional[str] = None
    ) -> Json:
        """Send props to a post.

        Parameters
        ----------
        coins : `int`
            The amount of coins to send.
        chatId : `str`, `optional`
            The chat ID to send coins. Default is `None`.
        blogId : `str`, `optional`
            The blog ID to send coins. Default is `None`.
        transactionId : `str`, `optional`
            The transaction ID. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the chat or blog is not provided.

        """
        if transactionId is None:
            transactionId = generateTransactionId()
        data = {
            "coins": coins,
            "tippingContext": {"transactionId": transactionId},
            "timestamp": int(time.time() * 1000),
        }
        if chatId:
            link = f"/g/s/blog/{chatId}/tipping"
        elif blogId:
            link = f"/g/s/blog/{blogId}/tipping"
        else:
            raise ValueError("please put chat or blog Id")
        return Json(await self.postRequest(link, data))

    async def reset_password(self: typing.Self, email: str, password: str, code: str, deviceId: typing.Optional[str] = None) -> Json:
        """Reset the account password.

        Parameters
        ----------
        email : `str`
            The user's email.
        password : `str`
            The new password.
        code : `str`
            The verification code.
        deviceId : `str`, `optional`
            The device ID. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        if deviceId is None:
            deviceId = self.deviceId
        data = {
            "updateSecret": f"0 {password}",
            "emailValidationContext": {
                "data": {"code": code},
                "type": 1,
                "identity": email,
                "level": 2,
                "deviceID": deviceId,
            },
            "phoneNumberValidationContext": None,
            "deviceID": deviceId,
            "timestamp": int(time.time() * 1000),
        }
        return Json(await self.postRequest("/g/s/auth/reset-password", data))

    async def change_password(self: typing.Self, password: str, newPassword: str) -> Json:
        """Change the account password without verification.

        Parameters
        ----------
        password : `str`
            The current account password.
        newPassword : `str`
            The new password.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "secret": f"0 {password}",
            "updateSecret": f"0 {newPassword}",
            "validationContext": None,
            "deviceID": self.deviceId,
        }
        return Json(await self.postRequest("/g/s/auth/change-password", data))

    async def get_user_info(self: typing.Self, userId: str) -> UserProfile:
        """Get user profile information.

        Parameters
        ----------
        userId : `str`
            The user ID to get information.

        Returns
        -------
        UserProfile
            The user profile object.

        """
        return UserProfile((await self.getRequest(f"/g/s/user-profile/{userId}"))["userProfile"]).UserProfile

    async def comment(self: typing.Self, comment: str, userId: str, replyTo: typing.Optional[str] = None) -> Json:
        """Comment on user profile.

        Parameters
        ----------
        comment : `str`
            The comment to send.
        userId : `str`
            The user ID to send the comment.
        replyTo : `str`, `optional`
            The comment ID to reply. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "content": comment,
            "stickerId": None,
            "type": 0,
            "eventSource": "UserProfileView",
            "timestamp": int(time.time() * 1000),
        }
        if replyTo:
            data["respondTo"] = replyTo
        return Json(await self.postRequest(f"/g/s/user-profile/{userId}/g-comment", data))

    async def delete_comment(self: typing.Self, commentId: str, userId: str) -> Json:
        """Delete a comment.

        Parameters
        ----------
        userId : `str`
            The user profile ID associated with the comment.
        commentId : `str`
            The ID of the comment.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(f"/g/s/user-profile/{userId}/g-comment/{commentId}"))

    async def invite_by_host(self: typing.Self, chatId: str, userId: typing.Union[typing.List[str], str]) -> Json:
        """Invite a user or users to a live chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID to invite.
        userId : `list[str]`, `str`
            The user ID or user ID list to invite.

        Returns
        -------
        Json
            The JSON response.

        """
        if not isinstance(userId, list):
            userId = [userId]
        data = {
            "uidList": userId,
            "timestamp": int(time.time() * 1000)
        }
        return Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/avchat-members", data))

    async def kick(self: typing.Self, chatId: str, userId: str, rejoin: bool = True) -> Json:
        """Kick a user from the chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID associated with the user.
        userId : `str`
            The user ID to kick.
        rejoin : `bool`, `optional`
            Allow rejoin to the chat. Default is `True`.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(f"/g/s/chat/thread/{chatId}/member/{userId}?allowRejoin={rejoin.real}"))

    async def get_all_users(self: typing.Self, usersType: UserType = "recent", start: int = 0, size: int = 25) -> UserProfileList:
        """Get amino user list.

        Parameters
        ----------
        usersType : `str`, `optional`
            The type of the user (banned, curators, leaders, featured, newest, recent, online). Default is 'recent'.
        start : `int`, `optional`
            The start index. Default is 0.
        size : `int`, `optional`
            The size of the list. Default is 25 (max is 250).

        Returns
        -------
        UserProfileList
            The amino user list object.

        """
        return UserProfileList((await self.getRequest(f"/g/s/user-profile?type={usersType}&start={start}&size={size}"))["userProfileList"]).UserProfileList

    @typing.deprecated("get_invise_users is deprecated, use get_all_users instead")
    @deprecated(get_all_users.__qualname__)
    async def get_invise_users(self: typing.Self, master_type: UserType = "newest", start: int = 0, size: int = 25) -> UserProfileList:
        """Get a list of global user profile.

        Parameters
        ----------
        master_type : `UserType`
            The type of the user (banned, curators, leaders, featured, newest, recent, online). Default is 'newest'.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        Json
            The JSON response.

        """
        return await self.get_all_users(master_type, start=start, size=size)

    async def invite_to_chat(self: typing.Self, chatId: str, userId: typing.Union[typing.List[str], str]) -> Json:
        """Invite a user or users to global chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID to invite.
        userId : `list[str]`, `str`
            The user ID or user ID list to invite.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "uids": userId if isinstance(userId, list) else [userId],
            "timestamp": int(time.time() * 1000),
        }
        return Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/member/invite", data))

    @typing.deprecated("invise_invite is deprecated, use invite_to_chat instead")
    @deprecated(invite_to_chat.__qualname__)
    async def invise_invite(self: typing.Self, chatId: str, userId: typing.Union[typing.List[str], str]) -> Json:
        """Invite a user or users to global chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID to invite.
        userId : `list[str]`, `str`
            The user ID or user ID list to invite.

        Returns
        -------
        Json
            The JSON response.

        """
        return await self.invite_to_chat(chatId=chatId, userId=userId)

    async def block(self: typing.Self, userId: str) -> Json:
        """Block an user.

        Parameters
        ----------
        userId : `str`
            The user ID to block.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest(f"/g/s/block/{userId}"))

    async def unblock(self: typing.Self, userId: str) -> Json:
        """Unblock a user.

        Parameters
        ----------
        userId : `str`
            The user ID to unblock.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(f"/g/s/block/{userId}"))

    async def get_public_chats(self: typing.Self, filterType: FilterType = "recommended", start: int = 0, size: int = 25) -> ThreadList:
        """Get public global chats.

        Parameters
        ----------
        filterType : `FilterType`, `optional`
            The chat type to search. Default is 'recommended'.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        ThreadList
            The public chat list object.

        """
        return ThreadList((await self.getRequest(f"/g/s/chat/thread?type=public-all&filterType={filterType}&start={start}&size={size}"))["threadList"]).ThreadList

    async def get_content_modules(self: typing.Self, version: int = 2) -> Json:
        """Get the home topics

        Parameters
        ----------
        version : `int`, `optional`
            The version of the home. Defualt is `2`.

        Returns
        -------
        Json
            The JSON response.
        """
        return Json(await self.getRequest(f"/g/s/home/discover/content-modules?v={version}"))

    async def get_banner_ads(self: typing.Self, start: int = 0, size: int = 25, pagingType: str = "t") -> ItemList:
        """Get a list of banner ads.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).
        pagingType : `str`, `optional`
            The pagging type. Default is 't'.

        Returns
        -------
        ItemList
            The banner ads list object.

        """
        return ItemList((await self.getRequest(f"/g/s/topic/0/feed/banner-ads?moduleId=711f818f-da0c-4aa7-bfa6-d5b58c1464d0&adUnitId=703798&start={start}&size={size}&pagingType={pagingType}"))["itemList"]).ItemList

    async def get_announcements(self: typing.Self, lang: str = "en", start: int = 0, size: int = 20) -> BlogList:
        return BlogList((await self.getRequest(f"/g/s/announcement?language={lang}&start={start}&size={size}"))["blogList"]).BlogList

    async def get_public_ndc(self: typing.Self, content_language: str = "en", size: int = 25) -> CommunityList:
        """Get public communities.

        Parameters
        ----------
        content_language : `str`, `optional`
            The community content language (en, de, ru, es, pt, fr, ar). Default is 'en'.

        Returns
        -------
        CommunityList
            The public community list object.

        """
        return CommunityList((await self.getRequest(f"/g/s/topic/0/feed/community?language={content_language}&type=web-explore&categoryKey=recommendation&size={size}&pagingType=t"))["communityList"]).CommunityList

    async def search_community(self: typing.Self, q: str, lang: str = "en", start: int = 0, size: int = 25) -> CommunityList:
        """Search communities.

        Parameters
        ----------
        q : `str`
            The search query.
        lang : `str`, `optional`
            The community content language (en, de, ru, es, pt, fr, ar). Default is 'en'.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        CommunityList
            The community search result object.

        """
        return CommunityList((await self.getRequest(f"/g/s/community/search?q={q}&language={lang}&completeKeyword=1&start={start}&size={size}"))["communityList"]).CommunityList

    async def invite_to_voice_chat(self: typing.Self, chatId: str, userId: str) -> Json:
        """Invite a user to talk in a voice chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID of the voice chat.
        userId : `str`
            The user ID to invite.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "uid": userId,
            "timestamp": int(time.time() * 1000)
        }
        return Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/vvchat-presenter/invite", data))

    async def get_wallet_history(self: typing.Self, start: int = 0, size: int = 25) -> WalletHistory:
        """Get account wallet history.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        WalletHistory
            The wallet history object.

        """
        return WalletHistory(await self.getRequest(f"/g/s/wallet/coin/history?start={start}&size={size}")).WalletHistory

    async def get_wallet_info(self: typing.Self) -> WalletInfo:
        """Get account wallet.

        Returns
        -------
        WalletInfo
            The account wallet object.

        """
        req = await self.getRequest("/g/s/wallet")
        return WalletInfo(req["wallet"]).WalletInfo

    async def get_chat_members(self: typing.Self, chatId: str, start: int = 0, size: int = 25) -> UserProfileList:
        """Get chat member list.

        Parameters
        ----------
        chatId : `str`
            The chat ID to get the list of members.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).

        Returns
        -------
        UserProfileList
            The member list object.

        """
        return UserProfileList((await self.getRequest(f"/g/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2"))["memberList"]).UserProfileList

    async def get_from_id(self: typing.Self, objectId: str, objectType: int, comId: typing.Optional[str] = None) -> FromCode:
        """Get info from object ID.

        Parameters
        ----------
        objectId : `str`
            The ID of the object.
        objectType : `int`
            The object type.
                0: user
                1: blog
                2: wiki
                3: comment
                7: chat message
                12: chat
                16: community
                113: sticker
        comId : `str`, `optional`
            The object community ID.

        Returns
        -------
        FromCode
            The amino object info.

        """
        data = {
            "objectId": objectId,
            "targetCode": 1,
            "objectType": objectType,
            "timestamp": int(time.time() * 1000),
        }
        return FromCode((await self.postRequest(f"/g/s-x{comId}/link-resolution" if comId else "/g/s/link-resolution", data))["linkInfoV2"]["extensions"]["linkInfo"]).FromCode

    async def chat_settings(
        self: typing.Self,
        chatId: str,
        doNotDisturb: typing.Optional[bool] = None,
        viewOnly: typing.Optional[bool] = None,
        canInvite: typing.Optional[bool] = None,
        canTip: typing.Optional[bool] = None,
        pin: typing.Optional[bool] = None,
        coHosts: typing.Optional[typing.Union[typing.List[str], str]] = None,
    ) -> typing.List[Json]:
        """Edit a chat setting.

        Parameters
        ----------
        chatId : `str`
            The chat ID to configure.
        doNotDisturb : `bool`, `optional`
            If the value is boolean, sets the option. Default is `None`.
        viewOnly : `bool`, `optional`
            If the value is boolean, sets the option. Default is `None`.
        canInvite : `bool`, `optional`
            If the value is boolean, sets the option. Default is `None`.
        canTip : `bool`, `optional`
            If the value is boolean, sets the option. Default is `None`.
        pin : `bool`, `optional`
            If the value is boolean, sets the option. Default is `None`.
        coHosts : `list[str]`, `str`, `optional`
            The new user ID or user ID list. Default is `None`.

        Returns
        -------
        list[Json]
            The response of the modified settings list.

        """
        res: typing.List[Json] = []
        if isinstance(doNotDisturb, bool):
            data: typing.Dict[str, typing.Any] = {
                "alertOption": doNotDisturb.real + 1,
                "timestamp": int(time.time() * 1000),
            }
            res.append(Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}/alert", data)))
        if isinstance(viewOnly, bool):
            view = "enable" if viewOnly else "disable"
            res.append(Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/view-only/{view}")))
        if isinstance(canInvite, bool):
            can = "enable" if canInvite else "disable"
            res.append(Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/members-can-invite/{can}")))
        if isinstance(canTip, bool):
            can = "enable" if canTip else "disable"
            res.append(Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/tipping-perm-status/{canTip}")))
        if isinstance(pin, bool):
            action = "pin" if pin else "unpin"
            res.append(Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/{action}")))
        if coHosts:
            data = {
                "uidList": coHosts if isinstance(coHosts, list) else [coHosts],
                "timestamp": int(time.time() * 1000),
            }
            res.append(Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/co-host", data)))
        return res

    @typing.overload
    async def like_comment(self, commentId: str, blogId: str) -> Json: ...
    @typing.overload
    async def like_comment(self, commentId: str, *, userId: str) -> Json: ...
    async def like_comment(self: typing.Self, commentId: str, blogId: typing.Optional[str] = None, userId: typing.Optional[str] = None) -> Json:
        """Like a comment (blog or user profile).

        Parameters
        ----------
        commentId : `str`
            The comment ID to like.
        blogId : `str`, `optional`
            The blog ID associated with the comment.
        userId : `str`, `optional`
            The user profile associated with the comment.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId and userId are not provided.

        """
        data = {
            "value": 4,
            "timestamp": int(time.time() * 1000)
        }
        if userId:
            link = f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?cv=1.2&value=1"
        elif blogId:
            link = f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?cv=1.2&value=1"
        else:
            raise ValueError("Please put blogId or userId")
        return Json(await self.postRequest(link, data))

    @typing.overload
    async def unlike_comment(self, commentId: str, blogId: str) -> Json: ...
    @typing.overload
    async def unlike_comment(self, commentId: str, *, userId: str) -> Json: ...
    async def unlike_comment(self: typing.Self, commentId: str, blogId: typing.Optional[str] = None, userId: typing.Optional[str] = None) -> Json:
        """Unlike a comment (blog or user profile).

        Parameters
        ----------
        commentId : `str`
            The comment ID to like.
        userId : `str`, `optional`
            The user profile associated with the comment.
        blogId : `str`, `optional`
            The blog ID associated with the comment.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the userId and blogId are not provided.

        """
        if userId:
            link = f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView"
        elif blogId:
            link = f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView"
        else:
            raise ValueError("Please put blog or user Id")
        return Json(self.deleteRequest(link))

    @typing.overload
    async def register_check(self: typing.Self, *, email: str) -> Json: ...
    @typing.overload
    async def register_check(self: typing.Self, *, phone: str) -> Json: ...
    async def register_check(self: typing.Self, *, email: typing.Optional[str] = None, phone: typing.Optional[str] = None) -> Json:
        """Check if you are registered (email, phone or device ID)

        Parameters
        ----------
        email : `str`, `optional`
            raise an EmailAlreadyTaken exception if the email already has an account.
        phone : `str`, `optional`
            raise an EmailAlreadyTaken exception if the phoneNumber already has an account.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        EmailAlreadyTaken
            If the phone or email already has an account.

        """
        data = {"deviceID": self.deviceId}
        if email and phone:
            raise ValueError('You should not provide an email and phone number at the same time')
        for key, value in dict(email=email, phoneNumber=phone).items():
            if value:
                data[key] = value
        return Json(await self.postRequest("/g/s/auth/register-check", data=data))

    @typing.overload
    async def signup_add_profile(self, email: str, password: str, nickname: str, code: str) -> Json: ...
    @typing.overload
    async def signup_add_profile(self, email: str, password: str, nickname: str, *, accessToken: str, thirdPart: ThirdPartType, address: typing.Optional[str] = None) -> Json: ...
    async def signup_add_profile(
        self: typing.Self,
        email: str,
        password: str,
        nickname: str,
        code: typing.Optional[str] = None,
        *,
        accessToken: typing.Optional[str] = None,
        thirdPart: typing.Optional[ThirdPartType] = None,
        address: typing.Optional[str] = None
    ) -> Json:
        """Register a new account with adding basic profile.

        Parameters
        ----------
        email : `str`
            The account email address.
        password : `str`
            The account password.
        nickname : `str`
            The nickname of the account.
        code : `str`, `optional`
            The verification code. Default is `None`.
        accessToken : `str`, `optional`
            The facebook third-party oauth access token. Default is `None`.
        thirdPart: `ThirdPartType`, `optional`
            The accessToken third-part name. Default is `None`.
        address : `str`, `optional`
            The geographical address. Defaults to `None`.
            Possible values: locality, sub-locality, administrative area, sub-administrative area, address line (without country)
            If the country is specified, it should be separated by a comma `,` e.g., (locality, country)

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "validationContext": {
                "data": {"code": code},
                "type": 1,
                "identity": email
            },
            "clientCallbackURL": "ndc://relogin",
            "clientType": 100,
            "deviceID": self.deviceId,
            "email": email,
            "nickname": nickname,
            "secret": f"0 {password}",
            "latitude": 0,
            "longitude": 0,
            "address": address
        }
        if thirdPart:
            stype = 30 if thirdPart == 'google' else 10
            data.update({
                "secret": f"{stype} {accessToken}",
                "secret2": f"0 {password}",
                "validationContext": None
            })
        return Json(await self.postRequest("/g/s/auth/" + ("login" if thirdPart else "register"), data=data))

    async def register(
        self: typing.Self,
        nickname: str,
        email: str,
        password: str,
        code: str,
        deviceId: typing.Optional[str] = None,
    ) -> Json:
        """Register a new account.

        Parameters
        ----------
        nickname : `str`
            The nickname of the account.
        email : `str`
            The account email address.
        password : `str`
            The account password.
        code : `str`
            The verification code.
        deviceId : `str`, `optional`
            The account device. If not provided the current device is used.

        Returns
        -------
        Json
            The JSON response.

        """
        if not deviceId:
            deviceId = self.deviceId
        data = {
            "secret": f"0 {password}",
            "deviceID": deviceId,
            "email": email,
            "clientType": 100,
            "nickname": nickname,
            "latitude": 0,
            "longitude": 0,
            "address": None,
            "clientCallbackURL": "narviiapp://relogin",
            "validationContext": {"data": {"code": code}, "type": 1, "identity": email},
            "type": 1,
            "identity": email,
            "timestamp": int(time.time() * 1000),
        }
        return Json(await self.postRequest("/g/s/auth/register", data))

    async def edit_chat(
        self: typing.Self,
        chatId: str,
        title: typing.Optional[str] = None,
        content: typing.Optional[str] = None,
        icon: typing.Optional[str] = None,
        background: typing.Optional[str] = None,
        keywords: typing.Optional[typing.List[str]] = None,
        announcement: typing.Optional[str] = None,
        pinAnnouncement: typing.Optional[bool] = None,
    ) -> typing.List[Json]:
        """Edit a chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID to edit.
        title : `str`, `optional`
            The new title. If not provided, is not edited.
        content : `str`, `optional`
            The new chat description. If not provided, is not edited.
        icon : `str`, `optional`
            The new chat icon. If not provided, is not edited.
        background : `str`, `optional`
            The new chat background. If not provided, is not edited.
        keywords : `list[str]`, `optional`
            The new chat keywords. If not provided, is not edited.
        announcement : `str`, `optional`
            The new chat announcement. If not provided, is not edited.
        pinAnnouncement : `bool`, `optional`
            The new chat pin announcement. If not provided, is not edited.

        Returns
        -------
        list
            The JSON response list.

        """
        data: typing.Dict[str, typing.Any] = {
            "timestamp": int(time.time() * 1000)
        }
        extensions: typing.Dict[str, typing.Any] = {}
        res: typing.List[Json] = []
        if title:
            data["title"] = title
        if content:
            data["content"] = content
        if icon:
            data["icon"] = icon
        if keywords:
            data["keywords"] = keywords
        if background:
            data = {
                "media": [100, background, None],
                "timestamp": int(time.time() * 1000),
            }
            res.append(Json(await self.postRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}/background", data)))
        if announcement:
            extensions["announcement"] = announcement
        if pinAnnouncement:
            extensions["pinAnnouncement"] = pinAnnouncement
        if extensions:
            data["extensions"] = extensions
        res.append(Json(await self.postRequest(f"/g/s/chat/thread/{chatId}", data)))
        return res

    async def remove_cohost(self: typing.Self, chatId: str, userId: str) -> Json:
        """Remove a chat co-host.

        Parameters
        ----------
        chatId : `str`
            The chat ID associated with the user.
        userId : `str`
            The cohost user ID.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(f"/g/s/chat/thread/{chatId}/co-host/{userId}"))

    async def edit_comment(self: typing.Self, commentId: str, comment: str, userId: str, replyTo: typing.Optional[str] = None) -> Comment:
        """Edit a user profile comment.

        Parameters
        ----------
        commentId : `str`
            The comment ID to edit.
        comment : `str`
            The new comment content.
        userId : `str`
            The user ID associated with the comment.
        replyTo : `str`, `optional`
            The comment ID to reply. Default is `None`.

        Returns
        -------
        Comment
            The edited comment object.

        """
        data = {"content": comment, "timestamp": int(time.time() * 1000)}
        if replyTo:
            data["respondTo"] = replyTo
        return Comment(await self.postRequest(f"/g/s/user-profile/{userId}/comment/{commentId}", data)).Comments

    async def get_comment_info(self: typing.Self, commentId: str, userId: str) -> Comment:
        """Get user profile comment information.

        Parameters
        ----------
        commentId : `str`
            The comment ID.
        userId : `str`
            The user profile ID associated with the comment.

        Returns
        -------
        Comment
            The comment object.

        """
        return Comment(await self.getRequest(f"/g/s/user-profile/{userId}/comment/{commentId}")).Comments

    async def get_notifications(self: typing.Self, start: int = 0, size: int = 25, pagingType: str = "t") -> NotificationList:
        """Get global notifications.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).
        pagingType : `str`, `optional`
            The paging type to return. Default is 't'.

        Returns
        -------
        NotificationList
            The notification list object.

        """
        return NotificationList(await self.getRequest(f"/g/s/notification?pagingType={pagingType}&start={start}&size={size}")).NotificationList

    async def get_notices(
        self: typing.Self,
        start: int = 0,
        size: int = 25,
        noticeType: NoticeType = "usersV2",
        status: int = 1,
    ) -> NoticeList:
        """Get user global notices.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 250).
        noticeType : `str`, `optional`
            The notice type to return. Default is 'usersV2'.
        status : `int`, `optional`
            The notice status to return. Default is `1`.

        Returns
        -------
        NoticeList
            The notice list object.

        """
        return NoticeList(await self.getRequest(f"/g/s/notice?type={noticeType}&status={status}&start={start}&size={size}")).NoticeList

    async def accept_promotion(self: typing.Self, requestId: str) -> Json:
        """Accept a promotion request.

        Parameters
        ----------
        requestId : `str`
            The request ID to accept.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest(f"/g/s/notice/{requestId}/accept"))

    async def decline_promotion(self: typing.Self, requestId: str) -> Json:
        """Decline a promotion request.

        Parameters
        ----------
        requestId : `str`
            The request ID to decline.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest(f"/g/s/notice/{requestId}/decline"))
