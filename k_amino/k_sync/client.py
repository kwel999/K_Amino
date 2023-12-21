import os
from base64 import b64encode
from binascii import hexlify
from time import time as timestamp
from typing import BinaryIO, Dict, List, Literal, Optional, Union, overload
from uuid import UUID
from ..lib.objects import *
from ..lib.sessions import Session
from ..lib.util import deprecated, get_file_type
from .sockets import Wss

__all__ = ("Client",)


class Client(Wss, Session):
    """Represents a amino global client.

    Parameters
    ----------
    deviceId : str, optional
        The device of the client. If not provided, a random one is generated.
    proxies : dict, optional
        Proxies for HTTP requests supported by the httpx library (https://www.python-httpx.org/advanced/#routing)
    trace : bool, optional
        Show websocket trace (logs). Default is False.
    bot : bool, optional
        The client is a community bot. Default is False (command supported).

    Attributes
    ----------
    deviceId : str
        The device of the client.
    proxies : dict, None
        The proxies of the client.
    secret : str, None
        The secret password of the user account.
    sid : str, optional
        The session ID of the user account.
    uid : str, optional
        The user ID of the user account.
    trace : bool
        Show websocket trace (logs).
    session : httpx.Client
        The HTTP client object.
    app_headers : dict
        The HTTP headers of the app client.
    web_headers : dict
        The HTTP headers of the web client.

    """

    def __init__(
        self,
        deviceId: Optional[str] = None,
        proxies: Optional[Dict[str, str]] = None,
        trace: bool = False,
        bot: bool = False,
        debug: bool = False,
    ) -> None:
        self.trace = trace
        Wss.__init__(self, self, trace=self.trace, is_bot=bot)
        Session.__init__(self, proxies=proxies, deviceId=deviceId, debug=debug)

    def change_lang(self, lang: str = "en") -> None:
        """Change the content language.

        Parameters
        ----------
        lang : str, optional
            The country language (ISO 3166-1 alfa-2), by default "en"

        """
        self.updateHeaders(lang=lang)

    def sid_login(self, sid: str, socket=False) -> Account:
        """Login via session ID.

        Parameters
        ----------
        sid : str
            The amino session ID.
        socket : bool, optional
            Run the websocket after login. Default is False.

        Returns
        -------
        Account
            The user account.

        """
        self.settings(sid=sid)
        info = self.get_account_info()
        self.settings(uid=info.userId)
        if socket:
            self.launch()
        return info

    def login_facebook(
        self,
        email: str,
        accessToken: str,
        address: Optional[str] = None,
        socket: bool = True
    ) -> Login:
        """Login via Facebook.

        Parameters
        ----------
        email : str
            The account email.
        accessToken : str
            The facebook third-party oauth access token.
        address : str, optional
            The geographical address. Defaults to None.
            Possible values: locality, sub-locality, administrative area, sub-administrative area, address line (without country)
            If the country is specified, it should be separated by a comma `,` e.g., (locality, country)
        socket : bool, optional
            Run the websocket after login. Default is True.

        Returns
        -------
        Login
            The login object.

        """
        req = self.postRequest("/g/s/auth/login", {
            'secret': f'10 {accessToken}',
            'clientType': 100,
            'clientCallbackURL': 'ndc://relogin',
            'email': email,  # optional ?
            'latitude': 0,
            'longitude': 0,
            'address': address,
            'action': 'normal',
            #'thirdPart': True,  # tag, not value?
            'timestamp': int(timestamp() * 1000),
            'deviceID': self.deviceId,
        })
        self.settings(sid=req["sid"], uid=req["auid"], secret=req["secret"])
        if socket or self.is_bot:
            self.launch()
        return Login(req)

    def login_google(
        self,
        accessToken: str,
        address: Optional[str] = None,
        socket: bool = True
    ) -> Login:
        """Login via Google.

        Parameters
        ----------
        accessToken : str
            The google third-party oauth access token.
        address : str, optional
            The geographical address. Defaults to None.
            Possible values: locality, sub-locality, administrative area, sub-administrative area, address line (without country)
            If the country is specified, it should be separated by a comma `,` e.g., (locality, country)
        socket : bool, optional
            Run the websocket after login. Default is False.

        Returns
        -------
        Login
            The login object.

        """
        req = self.postRequest("/g/s/auth/login", {
            'secret': f'30 {accessToken}',
            'clientType': 100,
            # 'clientCallbackURL': 'ndc://relogin',  # ???
            'latitude': 0,
            'longitude': 0,
            'address': address,
            'action': 'normal',
            #'thirdPart': True,  # tag, not value?
            'timestamp': int(timestamp() * 1000),
            'deviceID': self.deviceId,
        })
        self.settings(sid=req["sid"], uid=req["auid"], secret=req["secret"])
        if socket or self.is_bot:
            self.launch()
        return Login(req)

    def auto_signup_google(
        self,
        email: str,
        password: str,
        nickname: str,
        accessToken: str,
        address: Optional[str] = None,
        socket: bool = False
    ) -> Login:
        """Login via Google.

        Parameters
        ----------
        email : str
            The account email address to register. If you are already registered, raise an EmailAlreadyTaken exception.
        password : str
            The account password.
        nickname : str
            The nickname of the account.
        accessToken : str
            The google third-party oauth access token.
        address : str, optional
            The geographical address. Default is None.
            Possible values: locality, sub-locality, administrative area, sub-administrative area, address line (without country)
            If the country is specified, it should be separated by a comma `,` e.g., (locality, country)
        socket : bool, optional
            Run the websocket after login. Default is False.

        Returns
        -------
        Login
            The login object.

        """
        self.register_check(email=email)
        self.signup_add_profile(email, password, nickname, accessToken=accessToken, thirdPart='google', address=address)
        req = self.postRequest("/g/s/auth/login", {
            #"validationContext": None,
            "secret": f"30 {accessToken}",
            "clientType": 100,
            # 'clientCallbackURL': 'ndc://relogin',  # ???
            "action": "auto",
            #'email': email,
            "timestamp": int(timestamp() * 1000),
            "deviceID": self.deviceId,
            "latitude": 0,
            "longitude": 0,
            "address": address,
        })
        self.settings(sid=req["sid"], uid=req["auid"], secret=req["secret"])
        if socket or self.is_bot:
            self.launch()
        return Login(req)

    # SID param removed: use sid_login()
    def login(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        secret: Optional[str] = None,
        socket: bool = False,
    ) -> Login:
        """Login via email.

        Parameters
        ----------
        email : str, optional
            The account email. Default is None.
        password : str, optional
            The account password. Default is None.
        secret : str, optional
            The account secret password. Default is None.
        socket : bool, optional
            Run the websocket after login. Default is False.

        Returns
        -------
        Login
            The login object.

        Raises
        ------
        ValueError
            If no valid login info provided.

        """
        if not (email and (password or secret)):
            raise ValueError("Please provide VALID login info")
        data = {
            "email": email if email else "",
            "secret": f"0 {password}" if password else secret,
            "clientType": 100,
            "action": "normal",
            "deviceID": self.deviceId,
            "v": 2,
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest("/g/s/auth/login", data)
        self.settings(sid=req["sid"], uid=req["auid"], secret=req["secret"])
        if socket or self.is_bot:
            self.launch()
        return Login(req)

    def logout(self) -> Json:
        """Logout from the account.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "deviceID": self.deviceId,
            "clientType": 100,
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest("/g/s/auth/logout", data)
        self.settings(sid=None, uid=None, secret=None)
        if self.isOpened:
            self.close()
        return Json(req)

    def update_email(
        self,
        email: str,
        new_email: str,
        code: str,
        password: Optional[str] = None,
        secret: Optional[str] = None
    ) -> Json:
        """Update the account email.

        Parameters
        ----------
        email : str
            The current account email.
        new_email : str
            The new account email to update.
        code : str
            The security verification code.
        password : str, optional
            The account password. Defaults to None.
        secret : str, optional
            The account secret password. Defualts to None.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest('auth/update-email', data={
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
        })
        return Json(req)

    def check_device(self, deviceId: str) -> Json:
        """Check if the device is avalible.

        Parameters
        ----------
        deviceId : str
            The device to check.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "deviceID": deviceId,
            "timestamp": int(timestamp() * 1000),
            "clientType": 100,
        }
        req = self.postRequest(
            "/g/s/device/", data, newHeaders={"NDCDEVICEID": deviceId}
        )
        return Json(req)

    def upload_media(self, file: BinaryIO, fileType: Literal["audio", "image"]) -> str:
        """Upload a media to the amino server.

        Parameters
        ----------
        file : BinaryIO
            The file opened in read-byte mode (rb).
        fileType : str
            The file type (audio, image).

        Returns
        -------
        str
            The url of the uploaded image.

        """
        if fileType not in ("image", "audio"):
            raise ValueError("fileType must be 'audio' or 'image' not %r." % fileType)
        if fileType == "audio":
            ftype = "audio/" + get_file_type(file.name, "acc")
        else:
            ftype = "image/" + get_file_type(file.name, "jpg")
        newHeaders = {"content-type": ftype, "content-length": str(len(file.read()))}
        req = self.postRequest("/g/s/media/upload", data=file, newHeaders=newHeaders)
        return req["mediaValue"]

    @deprecated(upload_media.__name__)
    def upload_image(self, image: BinaryIO) -> str:
        """Upload an image to the amino server.

        Parameters
        ----------
        image : BinaryIO
            The image file opened in read-byte mode (rb).

        Returns
        -------
        str
            The url of the uploaded image.

        """
        return self.upload_media(image, "image")

    def send_verify_code(self, email: str) -> Json:
        """Request verification code via email.

        Parameters
        ----------
        email : str
            The email to send the code.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "identity": email,
            "type": 1,
            "deviceID": self.deviceId,
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest("/g/s/auth/request-security-validation", data)
        return Json(req)

    def accept_host(self, requestId: str, chatId: str) -> Json:
        """Accept the chat host transfer request.

        Parameters
        ----------
        requestId : str
            The transfer request ID.
        chatId : str
            The chat ID associated with the transfer.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(
            f"/g/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept"
        )
        return Json(req)

    def verify_account(self, email: str, code: str) -> Json:
        """Complete the account verification.

        Parameters
        ----------
        email : str
            The account email to verify.
        code : str
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
        req = self.postRequest("/g/s/auth/activate-email", data)
        return Json(req)

    def restore(self, email: str, password: str) -> Json:
        """Restore an account (after deletion).

        Parameters
        ----------
        email : str
            The account email to restore.
        password : str
            The account password.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "secret": f"0 {password}",
            "deviceID": self.deviceId,
            "email": email,
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest("/g/s/account/delete-request/cancel", data)
        return Json(req)

    def delete_account(
        self, password: Optional[str] = None, secret: Optional[str] = None
    ) -> Json:
        """Delete a user account.

        Parameters
        ----------
        password : str, optional
            The password of the account.
        secret : str, optional
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
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest("/g/s/account/delete-request", data)
        return Json(req)

    def get_account_info(self) -> Account:
        """Get account information.

        Returns
        -------
        Account
            The user account object.

        """
        req = self.getRequest("/g/s/account")
        return Account(req["account"])

    def claim_coupon(self) -> Json:
        """Claim the new-user coupon.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest("/g/s/coupon/new-user-coupon/claim")
        return Json(req)

    def change_amino_id(self, aminoId: str) -> Json:
        """Change the account amino ID.

        Parameters
        ----------
        aminoId : str
            The new amino ID.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"aminoId": aminoId, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest("/g/s/account/change-amino-id", data)
        return Json(req)

    def get_my_communities(self, start: int = 0, size: int = 25) -> CommunityList:
        """Get a list of the user's joined communities.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        CommunityList
            The joined community list object.

        """
        req = self.getRequest(f"/g/s/community/joined?v=1&start={start}&size={size}")
        return CommunityList(req["communityList"]).CommunityList

    def get_chat_threads(self, start: int = 0, size: int = 25) -> ThreadList:
        """Get a list of the user's joined chats.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        ThreadList
            The joined community list object.

        """
        req = self.getRequest(
            f"/g/s/chat/thread?type=joined-me&start={start}&size={size}"
        )
        return ThreadList(req["threadList"]).ThreadList

    def get_chat_info(self, chatId: str) -> Thread:
        """Get chat information.

        Parameters
        ----------
        chatId : str
            The chat ID to get information.

        Returns
        -------
        Thread
            The chat object.

        """
        req = self.getRequest(f"/g/s/chat/thread/{chatId}")
        return Thread(req["thread"]).Thread

    def leave_chat(self, chatId: str) -> Json:
        """Leave a chat.

        Parameters
        ----------
        chatId : str
            The chat ID to leave.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.deleteRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}")
        return Json(req)

    def join_chat(self, chatId: str) -> Json:
        """Join a chat.

        Parameters
        ----------
        chatId : str
            The chat ID to join.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}")
        return Json(req)

    def start_chat(
        self,
        userId: Union[str, list],
        title: Optional[str] = None,
        message: Optional[str] = None,
        content: Optional[str] = None,
        chatType: int = 0,
    ) -> Thread:
        """Start a chat.

        Parameters
        ----------
        userId : str, list
            The user ID to chat or list of user IDs to chat.
        title : str, optional
            The chat title. Default is None.
        message : str, optional
            The initial message. Default is None.
        content : str, optional
            The chat description. Default is None.
        chatType : int, optional
            The chat type. Default is 0.
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
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/g/s/chat/thread", data)
        return Thread(req["thread"]).Thread

    def get_from_link(self, link: str) -> FromCode:
        """Get data from a link.

        Parameters
        ----------
        link : str
            The link to get data.

        Returns
        -------
        FromCode
            The link data object.

        """
        req = self.getRequest(f"/g/s/link-resolution?q={link}")
        return FromCode(req["linkInfoV2"]["extensions"]).FromCode

    def edit_profile(
        self,
        nickname: Optional[str] = None,
        content: Optional[str] = None,
        icon: Optional[BinaryIO] = None,
        backgroundColor: Optional[str] = None,
        backgroundImage: Optional[str] = None,
        defaultBubbleId: Optional[str] = None,
    ) -> Json:
        """Edit the global profile.

        Parameters
        ----------
        nickname : str, optional
            The new nickname. Default is None.
        content : str, optional
            The new bio. Default is None.
        icon : BinaryIO, optional
            The opened file in read bytes mode. Default is None.
        backgroundColor : str, optional
            The new background color in hex code. Default is None.
        backgroundImage : str, optional
            The new background image. Default is None.
        defaultBubbleId : str, optional
            The new default bubble ID. Default is None.

        Returns
        -------
        Json
            The JSON response.

        """
        extensions, data = {}, {
            "address": None,
            "latitude": 0,
            "longitude": 0,
            "mediaList": None,
            "eventSource": "UserProfileView",
            "timestamp": int(timestamp() * 1000),
        }
        if content:
            data["content"] = content
        if nickname:
            data["nickname"] = nickname
        if icon:
            data["icon"] = self.upload_media(icon, "image")
        if defaultBubbleId:
            extensions["defaultBubbleId"] = defaultBubbleId
        if backgroundColor:
            extensions["style"] = {"backgroundColor": backgroundColor}
        if backgroundImage:
            extensions["style"] = {
                "backgroundMediaList": [[100, backgroundImage, None, None, None]]
            }
        if extensions:
            data["extensions"] = extensions
        req = self.postRequest(f"/g/s/user-profile/{self.uid}", data)
        return Json(req)

    def flag_community(self, comId: str, reason: str, flagType: int = 0) -> Json:
        """Flag a community.

        Parameters
        ----------
        comId : str
            The community ID to flag.
        reason : str
            The reason for the flag.
        flagType : int, optional
            The type of the flag. Default is 0.
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
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{comId}/s/g-flag", data)
        return Json(req)

    def leave_community(self, comId: int) -> Json:
        """Leave a community.

        Parameters
        ----------
        comId : str
            The community ID to leave.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(f"x/{comId}/s/community/leave")
        return Json(req)

    def join_community(self, comId: int, invId: Optional[str] = None) -> Json:
        """Join a community.

        Parameters
        ----------
        comId : int
            The community ID to join.
        invId : str, optional
            The community invitation ID. Default is None.

        Returns
        -------
        Json
            The JSON response.

        """
        data: Dict[str, Union[str, int]] = {"timestamp": int(timestamp() * 1000)}
        if invId:
            data["invitationId"] = invId
        req = self.postRequest(f"/x{comId}/s/community/join", data)
        return Json(req)

    def flag(
        self,
        reason: str,
        flagType: int = 0,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        userId: Optional[str] = None,
    ) -> Json:
        """Flag a post or user.

        Parameters
        ----------
        reason : str
            The reason of the flag.
        flagType : int, optional
            The type of the flag. Default is 0.
                0: bully
                2: spam
                4: off-topic
                106: violence
                107: hate
                108: suicide
                109: troll
                110: nudity
        blogId : str, optional
            The blog ID to flag.
        wikiId : str, optional
            The wiki ID to flag.
        userId : str, optional
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
            "timestamp": int(timestamp() * 1000),
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
        req = self.postRequest("/g/s/flag", data)
        return Json(req)

    def unfollow(self, userId: str) -> Json:
        """Unfollow a user.

        Parameters
        ----------
        userId : str
            The user ID to unfollow.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(f"/g/s/user-profile/{userId}/member/{self.uid}")
        return Json(req)

    def follow(self, userId: Union[str, list]) -> Json:
        """Follow a user or users.

        Parameters
        ----------
        userId : str, list
            The user ID or list of user IDs to follow.

        Returns
        -------
        Json
            The JSON response.

        """
        data: Dict[str, Union[list, int]] = {"timestamp": int(timestamp() * 1000)}
        if isinstance(userId, str):
            link = f"/g/s/user-profile/{userId}/member"
        elif isinstance(userId, list):
            data["targetUidList"] = userId
            link = f"/g/s/user-profile/{self.uid}/joined"
        req = self.postRequest(link, data)
        return Json(req)

    def get_member_following(
        self, userId: str, start: int = 0, size: int = 25
    ) -> UserProfileList:
        """Get user's followings.

        Parameters
        ----------
        userId : str
            The user ID to get the list.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        UserProfileList
            The follwing member list object.

        """
        req = self.getRequest(
            f"/g/s/user-profile/{userId}/joined?start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_member_followers(
        self, userId: str, start: int = 0, size: int = 25
    ) -> UserProfileList:
        """Get user's followers.

        Parameters
        ----------
        userId : str
            The user ID to get the list.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        UserProfileList
            The follower list object.

        """
        req = self.getRequest(
            f"/g/s/user-profile/{userId}/member?start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_member_visitors(
        self, userId: str, start: int = 0, size: int = 25
    ) -> VisitorsList:
        """Get user's visitor list.

        Parameters
        ----------
        userId : str
            The user ID to get the list.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        VisitorsList
            The visitor list object.
        """
        req = self.getRequest(
            f"/g/s/user-profile/{userId}/visitors?start={start}&size={size}"
        )
        return VisitorsList(req["visitors"]).VisitorsList

    def get_blocker_users(self, start: int = 0, size: int = 25) -> List[str]:
        """Get blocker user ID list.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        list
            The blocker user ID list.
        """
        req = self.getRequest(f"/g/s/block/full-list?start={start}&size={size}")
        return req["blockerUidList"]

    def get_blocked_users(self, start: int = 0, size: int = 25) -> List[str]:
        """Get blocked user ID list.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        list
            The blocked user ID list.
        """
        req = self.getRequest(f"/g/s/block/full-list?start={start}&size={size}")
        return req["blockedUidList"]

    def get_wall_comments(
        self, userId: str, sorting: str = "newest", start: int = 0, size: int = 25
    ) -> CommentList:
        """Get a list of comment in a user's wall.

        Parameters
        ----------
        userId : str
            The user ID to get the list.
        sorting : str, optional
            The sorting of the list (newest, oldest, vote). Default is 'newest'.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        CommentList
            The wall comment list object.

        Raises
        ------
        ValueError
            If the sorting is invalid.

        """
        sorting = sorting.lower().replace("top", "vote")
        if sorting not in ["newest", "oldest", "vote"]:
            raise ValueError(
                "Sorting must be one of 'newest', 'oldest', or 'vote', not %r" % sorting
            )
        req = self.getRequest(
            f"/g/s/user-profile/{userId}/g-comment?sort={sorting}&start={start}&size={size}"
        )
        return CommentList(req["commentList"]).CommentList

    def get_blog_comments(
        self,
        wikiId: Optional[str] = None,
        blogId: Optional[str] = None,
        sorting: str = "newest",
        start: int = 0,
        size: int = 25,
    ) -> CommentList:
        """Get post comments.

        Parameters
        ----------
        wikiId : str, optional
            The wiki ID to get the list. Default is None.
        blogId : str, optional
            The blog ID to get the list. Default is None.
        sorting : str, optional
            The sorting of the list (newest, oldest, vote). Default is 'newest'.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        CommentList
            The post comment list object.

        Raises
        ------
        ValueError
            If the sorting or post ID is invalid.

        """
        sorting = sorting.lower().replace("top", "vote")
        if sorting not in ["newest", "oldest", "vote"]:
            raise ValueError("Please insert a valid sorting")
        if blogId:
            link = (
                f"/g/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}"
            )
        elif wikiId:
            link = (
                f"/g/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}"
            )
        else:
            raise ValueError("Please choose a wiki or a blog")
        req = self.getRequest(link)
        return CommentList(req["commentList"]).CommentList

    def send_message(
        self,
        chatId: str,
        message: Optional[str] = None,
        messageType: int = 0,
        file: Optional[BinaryIO] = None,
        fileType: Optional[Literal["audio", "image", "gif"]] = None,
        replyTo: Optional[str] = None,
        mentionUserIds: Union[List[str], str, None] = None,
        stickerId: Optional[str] = None,
        snippetLink: Optional[str] = None,
        ytVideo: Optional[str] = None,
        snippetImage: Optional[BinaryIO] = None,
        embedId: Optional[str] = None,
        embedType: Optional[int] = None,
        embedLink: Optional[str] = None,
        embedTitle: Optional[str] = None,
        embedContent: Optional[str] = None,
        embedImage: Union[BinaryIO, str, None] = None,
    ) -> Json:
        """Send a chat message.

        Parameters
        ----------
        chatId : str
            The chat ID to send the message.
        message : str, optional
            The message to send. Default is None.
        messageType : int, optional
            The message type. Default is 0.
        file : BinaryIO, optional
            The file to send, opened in read-bytes. Default is None
        fileType : str, optional
            The file type to send (audio, image, gif). Default is None
        replyTo : str, optional
            The message ID to reply. Default is None.
        mentionUserIds : list, str, optional
            The mention user IDs. Default is None
        stickerId : str, optional
            The sticker ID to send. Default is None.
        snippetLink : str, optional
            The snippet link to send. Default is None.
        ytVideo : str, optional
            The Youtube video URL to send. Default is None.
        snippetImage : BinaryIO, optional
            The snippet image opened in read-bytes. Default is None.
        embedId : str, optional
            The embed object ID. Default is None.
        embedType : int, optional
            The embed object type. Default is None.
        embedLink : str, optional
            The embed URL. Default is None.
        embedTitle : str, optional
            The embed title. Default is None.
        embedContent : str, optional
            The embed message. Default is None.
        embedImage : BinaryIO, str, optional
            The embed image opened in read-bytes. Default is None.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the file type to send is invalid.

        """
        mentions, embedMedia = [], []
        if message is not None and file is None:
            message = message.replace("[@", "‎‏").replace("@]", "‬‭")
        if mentionUserIds:
            if isinstance(mentionUserIds, list):
                mentions.extend({"uid": uid} for uid in mentionUserIds)
            else:
                mentions.append({"uid": mentionUserIds})
        if embedImage:
            if not isinstance(embedImage, str):
                embedMedia = [[100, self.upload_media(embedImage, "image"), None]]
            else:
                embedMedia = [[100, embedImage, None]]
        data = {
            "type": messageType,
            "content": message,
            "attachedObject": {
                "objectId": embedId,
                "objectType": embedType,
                "link": embedLink,
                "title": embedTitle,
                "content": embedContent,
                "mediaList": embedMedia,
            },
            "extensions": {"mentionedArray": mentions},
            "clientRefId": int(timestamp() / 10 % 100000000),
            "timestamp": int(timestamp() * 1000),
        }
        if replyTo:
            data["replyMessageId"] = replyTo
        if stickerId:
            data["content"] = None
            data["stickerId"] = stickerId
            data["type"] = 3
        if snippetLink and snippetImage:
            data["attachedObject"] = None
            data["extensions"]["linkSnippetList"] = [
                {
                    "link": snippetLink,
                    "mediaType": 100,
                    "mediaUploadValue": b64encode(snippetImage.read()).decode(),
                    "mediaUploadValueContentType": "image/%s"
                    % get_file_type(snippetImage.name, "png"),
                }
            ]
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
                data["mediaUploadValueContentType"] = "image/%s" % get_file_type(
                    file.name, "jpg"
                )
                data["mediaUhqEnabled"] = False
            elif fileType == "gif":
                data["mediaType"] = 100
                data["mediaUploadValueContentType"] = "image/gif"
                data["mediaUhqEnabled"] = False
            else:
                raise ValueError(fileType)
            data["mediaUploadValue"] = b64encode(file.read()).decode()
            data["attachedObject"] = None
            data["extensions"] = None
        req = self.postRequest(f"/g/s/chat/thread/{chatId}/message", data)
        return Json(req)

    def get_community_info(self, comId: str) -> Community:
        """Get community information.

        Parameters
        ----------
        comId : str
            The community ID to get information.

        Returns
        -------
        Community
            The community object.

        """
        link = (
            f"/g/s-x{comId}/community/info"
            f"?withInfluencerList=1"
            f"&withTopicList=true"
            f"&influencerListOrderStrategy=fansCount"
        )
        req = self.getRequest(link)
        return Community(req["community"]).Community

    def mark_as_read(self, chatId: str) -> Json:
        """Mark as read a chat

        Parameters
        ----------
        chatId : str
            The chat ID to mark as read.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(f"/g/s/chat/thread/{chatId}/mark-as-read")
        return Json(req)

    def delete_message(self, chatId: str, messageId: str) -> Json:
        """Delete a message.

        Parameters
        ----------
        chatId : str
            The chat ID associated with the message.
        messageId : str
            The message ID to delete.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.deleteRequest(f"/g/s/chat/thread/{chatId}/message/{messageId}")
        return Json(req)

    def get_chat_messages(
        self, chatId: str, start: int = 0, size: int = 25
    ) -> MessageList:
        """Get messages from a chat.

        Parameters
        ----------
        chatId : str
            The chat ID to get messages.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        MessageList
            The message list object.

        """
        req = self.getRequest(
            f"/g/s/chat/thread/{chatId}/message?v=2&pagingType=t&start={start}&size={size}"
        )
        return MessageList(req["messageList"]).MessageList  # is valid?

    def get_message_info(self, messageId: str, chatId: str) -> Message:
        """The message information.

        Parameters
        ----------
        messageId : str
            The message ID to get information.
        chatId : str
            The chat ID associated with the message.

        Returns
        -------
        Message
            The message object.

        """
        req = self.getRequest(f"/g/s/chat/thread/{chatId}/message/{messageId}")
        return Message(req["message"]).Message

    def tip_coins(
        self,
        coins: int,
        chatId: Optional[str] = None,
        blogId: Optional[str] = None,
        transactionId: Optional[str] = None,
    ) -> Json:
        """Send props to a post.

        Parameters
        ----------
        coins : int
            The amount of coins to send.
        chatId : str, optional
            The chat ID to send coins. Default is None.
        blogId : str, optional
            The blog ID to send coins. Default is None.
        transactionId : str, optional
            The transaction ID. Default is None.

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
            transactionId = str(UUID(hexlify(os.urandom(16)).decode("ascii")))
        data = {
            "coins": coins,
            "tippingContext": {"transactionId": transactionId},
            "timestamp": int(timestamp() * 1000),
        }
        if chatId:
            link = f"/g/s/blog/{chatId}/tipping"
        elif blogId:
            link = f"/g/s/blog/{blogId}/tipping"
        else:
            raise ValueError("please put chat or blog Id")
        req = self.postRequest(link, data)
        return Json(req)

    def reset_password(
        self, email: str, password: str, code: str, deviceId: Optional[str] = None
    ) -> Json:
        """Reset the account password.

        Parameters
        ----------
        email : str
            The user's email.
        password : str
            The new password.
        code : str
            The verification code.
        deviceId : str, optional
            The device ID. Default is None.

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
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest("/g/s/auth/reset-password", data)
        return Json(req)

    def change_password(self, password: str, newPassword: str) -> Json:
        """Change the account password without verification.

        Parameters
        ----------
        password : str
            The current account password.
        newPassword : str
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
        req = self.postRequest("/g/s/auth/change-password", data)
        return Json(req)

    def get_user_info(self, userId: str) -> UserProfile:
        """Get user profile information.

        Parameters
        ----------
        userId : str
            The user ID to get information.

        Returns
        -------
        UserProfile
            The user profile object.

        """
        req = self.getRequest(f"/g/s/user-profile/{userId}")
        return UserProfile(req["userProfile"]).UserProfile

    def comment(self, comment: str, userId: str, replyTo: Optional[str] = None) -> Json:
        """Comment on user profile.

        Parameters
        ----------
        comment : str
            The comment to send.
        userId : str
            The user ID to send the comment.
        replyTo : str, optional
            The comment ID to reply. Default is None.

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
            "timestamp": int(timestamp() * 1000),
        }
        if replyTo:
            data["respondTo"] = replyTo
        req = self.postRequest(f"/g/s/user-profile/{userId}/g-comment", data)
        return Json(req)

    def delete_comment(self, commentId: str, userId: str) -> Json:
        """Delete a comment.

        Parameters
        ----------
        userId : str
            The user profile ID associated with the comment.
        commentId : str
            The ID of the comment.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.deleteRequest(f"/g/s/user-profile/{userId}/g-comment/{commentId}")
        return Json(req)

    def invite_by_host(self, chatId: str, userId: Union[str, list]) -> Json:
        """Invite a user or users to a live chat.

        Parameters
        ----------
        chatId : str
            The chat ID to invite.
        userId : str, list
            The user ID or user ID list to invite.

        Returns
        -------
        Json
            The JSON response.

        """
        if not isinstance(userId, list):
            userId = [userId]
        data = {"uidList": userId, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/g/s/chat/thread/{chatId}/avchat-members", data)
        return Json(req)

    def kick(self, chatId: str, userId: str, rejoin: bool = True) -> Json:
        """Kick a user from the chat.

        Parameters
        ----------
        chatId : str
            The chat ID associated with the user.
        userId : str
            The user ID to kick.
        rejoin : bool, optional
            Allow rejoin to the chat. Default is True.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.deleteRequest(
            f"/g/s/chat/thread/{chatId}/member/{userId}?allowRejoin={rejoin.real}"
        )
        return Json(req)

    def get_invise_users(
        self, master_type="newest", start: int = 0, size: int = 25
    ) -> UserProfileList:
        """Get a list of global user profile.

        Parameters
        ----------
        master_type : str
            The type of the user profile (newest, online). Default is 'newest'.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.getRequest(
            f"/g/s/user-profile?type={master_type}&start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def invite_to_chat(self, chatId: str, userId: Union[str, List[str]]) -> Json:
        """Invite a user or users to global chat.

        Parameters
        ----------
        chatId : str
            The chat ID to invite.
        userId : str, list
            The user ID or user ID list to invite.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "uids": userId if isinstance(userId, list) else [userId],
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/g/s/chat/thread/{chatId}/member/invite", data)
        return Json(req)

    @deprecated(invite_to_chat.__qualname__)
    def invise_invite(self, chatId: str, userId: Union[str, List[str]]) -> Json:
        """Invite a user or users to global chat.

        Parameters
        ----------
        chatId : str
            The chat ID to invite.
        userId : str, list
            The user ID or user ID list to invite.

        Returns
        -------
        Json
            The JSON response.

        """
        return self.invite_to_chat(chatId=chatId, userId=userId)

    def block(self, userId: str) -> Json:
        """Block an user.

        Parameters
        ----------
        userId : str
            The user ID to block.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(f"/g/s/block/{userId}")
        return Json(req)

    def unblock(self, userId: str) -> Json:
        """Unblock a user.

        Parameters
        ----------
        userId : str
            The user ID to unblock.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.deleteRequest(f"/g/s/block/{userId}")
        return Json(req)

    def get_public_chats(
        self, filterType: str = "recommended", start: int = 0, size: int = 50
    ) -> ThreadList:
        """Get public global chats.

        Parameters
        ----------
        filterType : str, optional
            The chat type to search. Default is 'recommended'.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        ThreadList
            The public chat list object.

        """
        req = self.getRequest(
            f"/g/s/chat/thread?type=public-all&filterType={filterType}&start={start}&size={size}"
        )
        return ThreadList(req["threadList"]).ThreadList

    def get_content_modules(self, version: int = 2) -> Json:
        req = self.getRequest(f"/g/s/home/discover/content-modules?v={version}")
        return Json(req)

    def get_banner_ads(self, size: int = 25, pagingType: str = "t") -> ItemList:
        """Get a list of banner ads.

        Parameters
        ----------
        size : int, optional
            The size of the list. Default is 25 (max is 100).
        pagingType : str, optional
            The pagging type. Default is 't'.

        Returns
        -------
        ItemList
            The banner ads list object.

        """
        link = (
            f"/g/s/topic/0/feed/banner-ads"
            f"?moduleId=711f818f-da0c-4aa7-bfa6-d5b58c1464d0&adUnitId=703798"
            f"&size={size}"
            f"&pagingType={pagingType}"
        )
        req = self.getRequest(link)
        return ItemList(req["itemList"]).ItemList

    def get_announcements(
        self, lang: str = "en", start: int = 0, size: int = 20
    ) -> BlogList:
        req = self.getRequest(
            f"/g/s/announcement?language={lang}&start={start}&size={size}"
        )
        return BlogList(req["blogList"]).BlogList

    def get_public_ndc(
        self, content_language: str = "en", size: int = 25
    ) -> CommunityList:
        """Get public communities.

        Parameters
        ----------
        content_language : str, optional
            The community content language (en, de, ru, es, pt, fr, ar). Default is 'en'.

        Returns
        -------
        CommunityList
            The public community list object.

        """
        req = self.getRequest(
            f"/g/s/topic/0/feed/community?language={content_language}&type=web-explore&categoryKey=recommendation&size={size}&pagingType=t"
        )
        return CommunityList(req["communityList"]).CommunityList

    def search_community(
        self, q: str, lang: str = "en", start: int = 0, size: int = 25
    ) -> CommunityList:
        """Search communities.

        Parameters
        ----------
        q : str
            The search query.
        lang : str, optional
            The community content language (en, de, ru, es, pt, fr, ar). Default is 'en'.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        CommunityList
            The community search result object.

        """
        req = self.getRequest(
            f"/g/s/community/search?q={q}&language={lang}&completeKeyword=1&start={start}&size={size}"
        )
        return CommunityList(req["communityList"]).CommunityList

    def invite_to_voice_chat(self, chatId: str, userId: str) -> Json:
        """Invite a user to talk in a voice chat.

        Parameters
        ----------
        chatId : str
            The chat ID of the voice chat.
        userId : str
            The user ID to invite.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"uid": userId, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(
            f"/g/s/chat/thread/{chatId}/vvchat-presenter/invite", data
        )
        return Json(req)

    def get_wallet_history(self, start: int = 0, size: int = 25) -> WalletHistory:
        """Get account wallet history.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        WalletHistory
            The wallet history object.

        """
        req = self.getRequest(f"/g/s/wallet/coin/history?start={start}&size={size}")
        return WalletHistory(req).WalletHistory

    def get_wallet_info(self) -> WalletInfo:
        """Get account wallet.

        Returns
        -------
        WalletInfo
            The account wallet object.

        """
        req = self.getRequest("/g/s/wallet")
        return WalletInfo(req["wallet"]).WalletInfo

    def get_all_users(
        self, usersType: str = "recent", start: int = 0, size: int = 25
    ) -> UserProfileList:
        """Get amino user list.

        Parameters
        ----------
        usersType : str, optional
            The user type (recent, banned, featured, leaders, curators). Default is'recent'.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        UserProfileList
            The amino user list object.

        """
        req = self.getRequest(
            f"/g/s/user-profile?type={usersType}&start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_chat_members(
        self, chatId: str, start: int = 0, size: int = 25
    ) -> UserProfileList:
        """Get chat member list.

        Parameters
        ----------
        chatId : str
            The chat ID to get the list of members.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        UserProfileList
            The member list object.

        """
        req = self.getRequest(
            f"/g/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2"
        )
        return UserProfileList(req["memberList"]).UserProfileList

    def get_from_id(
        self, objectId: str, objectType: int, comId: Optional[str] = None
    ) -> FromCode:
        """Get info from object ID.

        Parameters
        ----------
        objectId : str
            The ID of the object.
        objectType : int
            The object type.
                0: user
                1: blog
                2: wiki
                3: comment
                7: chat message
                12: chat
                16: community
                113: sticker
        comId : str, optional
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
            "timestamp": int(timestamp() * 1000),
        }
        link = f"/g/s/link-resolution"
        if comId:
            link = f"/g/s-x{comId}/link-resolution"
        req = self.postRequest(link, data)
        return FromCode(req["linkInfoV2"]["extensions"]["linkInfo"]).FromCode

    def chat_settings(
        self,
        chatId: str,
        doNotDisturb: Optional[bool] = None,
        viewOnly: Optional[bool] = None,
        canInvite: Optional[bool] = None,
        canTip: Optional[bool] = None,
        pin: Optional[bool] = None,
        coHosts: Union[str, List[str], None] = None,
    ) -> List[Json]:
        """Edit a chat setting.

        Parameters
        ----------
        chatId : str
            The chat ID to configure.
        doNotDisturb : bool, optional
            If the value is boolean, sets the option. Default is None.
        viewOnly : bool, optional
            If the value is boolean, sets the option. Default is None.
        canInvite : bool, optional
            If the value is boolean, sets the option. Default is None.
        canTip : bool, optional
            If the value is boolean, sets the option. Default is None.
        pin : bool, optional
            If the value is boolean, sets the option. Default is None.
        coHosts : str, list, optional
            The new user ID or user ID list. Default is None.

        Returns
        -------
        list
            The response of the modified settings list.

        """
        res = []
        if isinstance(doNotDisturb, bool):
            data = {
                "alertOption": doNotDisturb.real + 1,
                "timestamp": int(timestamp() * 1000),
            }
            req = self.postRequest(
                f"/g/s/chat/thread/{chatId}/member/{self.uid}/alert", data
            )
            res.append(Json(req))
        if isinstance(viewOnly, bool):
            view = "enable" if viewOnly else "disable"
            req = self.postRequest(f"/g/s/chat/thread/{chatId}/view-only/{view}")
            res.append(Json(req))
        if isinstance(canInvite, bool):
            can = "enable" if canInvite else "disable"
            req = self.postRequest(
                f"/g/s/chat/thread/{chatId}/members-can-invite/{can}"
            )
            res.append(Json(req))
        if isinstance(canTip, bool):
            can = "enable" if canTip else "disable"
            req = self.postRequest(
                f"/g/s/chat/thread/{chatId}/tipping-perm-status/{canTip}"
            )
            res.append(Json(req))
        if isinstance(pin, bool):
            action = "pin" if pin else "unpin"
            req = self.postRequest(f"/g/s/chat/thread/{chatId}/{action}")
            res.append(Json(req))
        if coHosts:
            data = {
                "uidList": coHosts if isinstance(coHosts, list) else [coHosts],
                "timestamp": int(timestamp() * 1000),
            }
            req = self.postRequest(f"/g/s/chat/thread/{chatId}/co-host", data)
            res.append(Json(req))
        return res

    def like_comment(
        self, commentId: str, blogId: Optional[str] = None, userId: Optional[str] = None
    ) -> Json:
        """Like a comment (blog or user profile).

        Parameters
        ----------
        commentId : str
            The comment ID to like.
        blogId : str, optional
            The blog ID associated with the comment.
        userId : str, optional
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
        data = {"value": 4, "timestamp": int(timestamp() * 1000)}
        if userId:
            link = (
                f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?cv=1.2&value=1"
            )
        elif blogId:
            link = f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?cv=1.2&value=1"
        else:
            raise ValueError("Please put blog or user Id")
        req = self.postRequest(link, data)
        return Json(req)

    def unlike_comment(
        self, commentId: str, blogId: Optional[str] = None, userId: Optional[str] = None
    ) -> Json:
        """Unlike a comment (blog or user profile).

        Parameters
        ----------
        commentId : str
            The comment ID to like.
        userId : str, optional
            The user profile associated with the comment.
        blogId : str, optional
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
        req = self.deleteRequest(link)
        return Json(req)

    @overload
    def register_check(self, *, email: str) -> Json: ...
    @overload
    def register_check(self, *, phone: str) -> Json: ...
    def register_check(self, *, email: Optional[str] = None, phone: Optional[str] = None) -> Json:
        """Check if you are registered (email, phone or device ID)

        Parameters
        ----------
        email : str, optional
            raise an EmailAlreadyTaken exception if the email already has an account.
        phone : str, optional
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
        return Json(self.postRequest("/g/s/auth/register-check", data=data))

    @overload
    def signup_add_profile(
        self,
        email: str,
        password: str,
        nickname: str,
        code: str
    ) -> Json: ...
    @overload
    def signup_add_profile(
        self,
        email: str,
        password: str,
        nickname: str,
        *,
        accessToken: str,
        thirdPart: Literal["facebook", "google"],
        address: Optional[str] = None
    ) -> Json: ...
    def signup_add_profile(
        self,
        email: str,
        password: str,
        nickname: str,
        code: Optional[str] = None,
        *,
        accessToken: Optional[str] = None,
        thirdPart: Optional[Literal["facebook", "google"]] = None,
        address: Optional[str] = None
    ) -> Json:
        """Register a new account with adding basic profile.

        Parameters
        ----------
        email : str
            The account email address.
        password : str
            The account password.
        nickname : str
            The nickname of the account.
        code : str, optional
            The verification code. Default is None.
        accessToken : str, optional
            The facebook third-party oauth access token. Default is None.
        thirdPart: Literal["facebook", "google"], optional
            The accessToken third-part name. Default is None.
        address : str, optional
            The geographical address. Defaults to None.
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
        url = "/g/s/auth/" + ("login" if thirdPart else "register")
        return Json(self.postRequest(url, data=data))

    def register(
        self,
        nickname: str,
        email: str,
        password: str,
        code: str,
        deviceId: Optional[str] = None,
    ) -> Json:
        """Register a new account.

        Parameters
        ----------
        nickname : str
            The nickname of the account.
        email : str
            The account email address.
        password : str
            The account password.
        code : str
            The verification code.
        deviceId : str, optional
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
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest("/g/s/auth/register", data)
        return Json(req)

    def edit_chat(
        self,
        chatId: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        icon: Optional[str] = None,
        background: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        announcement: Optional[str] = None,
        pinAnnouncement: Optional[bool] = None,
    ) -> List[Json]:
        """Edit a chat.

        Parameters
        ----------
        chatId : str
            The chat ID to edit.
        title : str, optional
            The new title. If not provided, is not edited.
        content : str, optional
            The new chat description. If not provided, is not edited.
        icon : str, optional
            The new chat icon. If not provided, is not edited.
        background : str, optional
            The new chat background. If not provided, is not edited.
        keywords : list, optional
            The new chat keywords. If not provided, is not edited.
        announcement : str, optional
            The new chat announcement. If not provided, is not edited.
        pinAnnouncement : bool, optional
            The new chat pin announcement. If not provided, is not edited.

        Returns
        -------
        list
            The JSON response list.

        """
        data: Dict[str, Union[int, str, list, dict]] = {
            "timestamp": int(timestamp() * 1000)
        }
        extensions = {}
        res = []
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
                "timestamp": int(timestamp() * 1000),
            }
            req = self.postRequest(
                f"/g/s/chat/thread/{chatId}/member/{self.uid}/background", data
            )
            res.append(Json(req))
        if announcement:
            extensions["announcement"] = announcement
        if pinAnnouncement:
            extensions["pinAnnouncement"] = pinAnnouncement
        if extensions:
            data["extensions"] = extensions
        req = self.postRequest(f"/g/s/chat/thread/{chatId}", data)
        res.append(Json(req))
        return res

    def remove_cohost(self, chatId: str, userId: str) -> Json:
        """Remove a chat co-host.

        Parameters
        ----------
        chatId : str
            The chat ID associated with the user.
        userId : str
            The cohost user ID.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.deleteRequest(f"/g/s/chat/thread/{chatId}/co-host/{userId}")
        return Json(req)

    def edit_comment(
        self, commentId: str, comment: str, userId: str, replyTo: Optional[str] = None
    ) -> Comment:
        """Edit a user profile comment.

        Parameters
        ----------
        commentId : str
            The comment ID to edit.
        comment : str
            The new comment content.
        userId : str
            The user ID associated with the comment.
        replyTo : str, optional
            The comment ID to reply. Default is None.

        Returns
        -------
        Comment
            The edited comment object.

        """
        data = {"content": comment, "timestamp": int(timestamp() * 1000)}
        if replyTo:
            data["respondTo"] = replyTo
        req = self.postRequest(f"/g/s/user-profile/{userId}/comment/{commentId}", data)
        return Comment(req).Comments

    def get_comment_info(self, commentId: str, userId: str) -> Comment:
        """Get user profile comment information.

        Parameters
        ----------
        commentId : str
            The comment ID.
        userId : str
            The user profile ID associated with the comment.

        Returns
        -------
        Comment
            The comment object.

        """
        req = self.getRequest(f"/g/s/user-profile/{userId}/comment/{commentId}")
        return Comment(req).Comments

    def get_notifications(
        self, start: int = 0, size: int = 25, pagingType: str = "t"
    ) -> NotificationList:
        """Get global notifications.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).
        pagingType : str, optional
            The paging type to return. Default is 't'.

        Returns
        -------
        NotificationList
            _description_
        """
        req = self.getRequest(
            f"/g/s/notification?pagingType={pagingType}&start={start}&size={size}"
        )
        return NotificationList(req).NotificationList

    def get_notices(
        self,
        start: int = 0,
        size: int = 25,
        noticeType: str = "usersV2",
        status: int = 1,
    ) -> NoticeList:
        """Get user global notices.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).
        noticeType : str, optional
            The notice type to return. Default is 'usersV2'.
        status : int, optional
            The notice status to return. Default is 1.

        Returns
        -------
        NoticeList
            The notice list object.

        """
        req = self.getRequest(
            f"/g/s/notice?type={noticeType}&status={status}&start={start}&size={size}"
        )
        return NoticeList(req).NoticeList

    def accept_promotion(self, requestId: str) -> Json:
        """Accept a promotion request.

        Parameters
        ----------
        requestId : str
            The request ID to accept.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(f"/g/s/notice/{requestId}/accept")
        return Json(req)

    def decline_promotion(self, requestId: str) -> Json:
        """Decline a promotion request.

        Parameters
        ----------
        requestId : str
            The request ID to decline.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(f"/g/s/notice/{requestId}/decline")
        return Json(req)
