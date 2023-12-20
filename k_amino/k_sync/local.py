from __future__ import annotations
import os
from base64 import b64encode
from binascii import hexlify
from time import time as timestamp
from typing import Dict, List, Literal, Optional, TYPE_CHECKING, Union, BinaryIO
from uuid import UUID
from ..lib.objects import *
from ..lib.sessions import Session
from ..lib.util import active_time, get_file_type
from .acm import Acm
if TYPE_CHECKING:
    from .client import Client

__all__ = ('SubClient',)


class SubClient(Acm, Session):
    """Represents an amino client from a community.

    Parameters
    ----------
    comId : int
        The community ID.
    client : Client
        The amino global client object.
    proxies : dict, optional
        Proxies for HTTP requests supported by the httpx
        library (https://www.python-httpx.org/advanced/#routing). Default is None.
    acm : bool, optional
        The client is amino community manager (ACM)

    Attributes
    ----------
    comId : int
        The client community ID.
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

    def __init__(self, comId: int, client: Client, proxies: Optional[dict] = None, acm: bool = False, debug: bool = False):
        self.comId = comId
        if acm:
            Acm.__init__(self, comId=self.comId, client=client, proxies=proxies)
        else:
            Session.__init__(self, client=client, proxies=proxies, debug=debug)

    def get_video_rep_info(self, chatId: str) -> RepInfo:
        """Get screening-room video reputation information.

        Parameters
        ----------
        chatId : str
            The chat ID of screening room.

        Returns
        -------
        RepInfo
            The reputation info object.

        """
        req = self.getRequest(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation")
        return RepInfo(req)

    def claim_video_rep(self, chatId: str) -> RepInfo:
        """Claim screening-room video reputation.

        Parameters
        ----------
        chatId : str
            The chat ID of screening room.

        Returns
        -------
        RepInfo
            The claimed reputation object.

        """
        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation")
        return RepInfo(req)

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
        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}")
        return Json(req)

    def upload_media(self, file: BinaryIO, fileType: Literal['audio', 'image']) -> str:
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
        if fileType not in ('image', 'audio'):
            raise ValueError("fileType must be 'audio' or 'image' not %r." % fileType)
        if fileType == "audio":
            ftype = "audio/" + get_file_type(file.name, 'acc')
        else:
            ftype = "image/" + get_file_type(file.name, 'jpg')
        newHeaders = {"content-type": ftype, "content-length": str(len(file.read()))}
        req = self.postRequest("/g/s/media/upload", data=file, newHeaders=newHeaders)
        return req["mediaValue"]

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
        req = self.deleteRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}")
        return Json(req)

    def get_member_following(self, userId: str, start: int = 0, size: int = 25) -> UserProfileList:
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
        req = self.getRequest(f"/x{self.comId}/s/user-profile/{userId}/joined?start={start}&size={size}")
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_member_followers(self, userId: str, start: int = 0, size: int = 25) -> UserProfileList:
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
        req = self.getRequest(f"/x{self.comId}/s/user-profile/{userId}/member?start={start}&size={size}")
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_member_visitors(self, userId: str, start: int = 0, size: int = 25) -> VisitorsList:
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
        req = self.getRequest(f"/x{self.comId}/s/user-profile/{userId}/visitors?start={start}&size={size}")
        return VisitorsList(req["visitors"]).VisitorsList

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
        req = self.getRequest(f"/x{self.comId}/s/chat/thread?type=joined-me&start={start}&size={size}")
        return ThreadList(req["threadList"]).ThreadList

    def get_chat_messages(self, chatId: str, start: int = 0, size: int = 25) -> MessageList:
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
        req = self.getRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message?v=2&pagingType=t&start={start}&size={size}")
        return MessageList(req["messageList"]).MessageList

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
        req = self.getRequest(f"/x{self.comId}/s/user-profile/{userId}")
        return UserProfile(req["userProfile"]).UserProfile

    def get_user_blogs(self, userId: str, start: int = 0, size: int = 25) -> BlogList:
        """Get user blog list.

        Parameters
        ----------
        userId : str
            The user ID.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        BlogList
            The blog list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/blog?type=user&q={userId}&start={start}&size={size}")
        return BlogList(req["blogList"]).BlogList

    def get_user_wikis(self, userId: str, start: int = 0, size: int = 25) -> WikiList:
        """Get user wiki list.

        Parameters
        ----------
        userId : str
            The user ID.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        WikiList
            The wiki list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/item?type=user-all&start={start}&size={size}&cv=1.2&uid={userId}")
        return WikiList(req["itemList"]).WikiList

    def get_all_users(self, usersType: str = "recent", start: int = 0, size: int = 25) -> UserProfileList:
        """Get community user list.

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
        req = self.getRequest(f"/x{self.comId}/s/user-profile?type={usersType}&start={start}&size={size}")
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_chat_members(self, chatId: str, start: int = 0, size: int = 25) -> UserProfileList:
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
        req = self.getRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2")
        return UserProfileList(req["memberList"]).UserProfileList

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
        req = self.getRequest(f"/x{self.comId}/s/chat/thread/{chatId}")
        return Thread(req["thread"]).Thread

    def get_online_users(self, start: int = 0, size: int = 25) -> UserProfileList:
        """Get community online user list.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        UserProfileList
            The user list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:online-members&start={start}&size={size}")
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_public_chats(self, filterType: str = "recommended", start: int = 0, size: int = 25) -> ThreadList:
        """Get community public chats.

        Parameters
        ----------
        filterType : str, optional
            The chat filter type. Default is 'recommended'.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        ThreadList
            The chat list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/chat/thread?type=public-all&filterType={filterType}&start={start}&size={size}")
        return ThreadList(req["threadList"]).ThreadList

    def full_embed(self, chatId: str, link: str, image: BinaryIO, message: str) -> Json:
        """Send embed chat message.

        Parameters
        ----------
        link : str
            The embed link.
        image : BinaryIO
            The embed image file opened in read-byte mode (rb).
        message : str
            The embed message.
        chatId : str
            The chat ID to send.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "type": 0,
            "content": message,
            "extensions": {
                "linkSnippetList": [{
                    "link": link,
                    "mediaType": 100,
                    "mediaUploadValue": b64encode(image.read()).decode(),
                    "mediaUploadValueContentType": "image/png"
                }]
            },
            "clientRefId": int(timestamp() / 10 % 100000000),
            "timestamp": int(timestamp() * 1000),
            "attachedObject": None
        }
        res = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message", data)
        return Json(res)

    def send_message(
        self,
        chatId: str,
        message: Optional[str] = None,
        messageType: int = 0,
        file: Optional[BinaryIO] = None,
        fileType: Optional[Literal['audio', 'image', 'gif']] = None,
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
                embedMedia = [[100, self.upload_media(embedImage, 'image'), None]]
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
            data["extensions"]["linkSnippetList"] = [{
                "link": snippetLink,
                "mediaType": 100,
                "mediaUploadValue": b64encode(snippetImage.read()).decode(),
                "mediaUploadValueContentType": 'image/%s' % get_file_type(snippetImage.name, 'png')
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
                data["mediaUploadValueContentType"] = 'image/%s' % get_file_type(file.name, 'jpg')
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
        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message", data)
        return Json(req)

    def send_web_message(
        self,
        chatId: str,
        message: Optional[str] = None,
        messageType: int = 0,
        icon: Optional[str] = None,
        comId: Optional[int] = None,
    ) -> Json:
        """Send a chat message as web client.

        Parameters
        ----------
        chatId : str
            The chat ID to send the message.
        message : str, optional
            The message to send. Default is None.
        messageType : int, optional
            The message type. Default is 0.
        icon : str, optional
            The image url. Default is None.
        comId : int, optional
            The community ID associated with the chat.

        Returns
        -------
        Json
            The JSON response.

        """
        if not comId:
            comId = self.comId
        data = {
            "ndcId": f"x{comId}",
            "threadId": chatId,
            "message": {
                "content": message,
                "mediaType": 0,
                "type": messageType,
                "sendFailed": False,
                "clientRefId": 0,
            },
        }
        if icon:
            data["message"]["content"] = None
            data["message"]["uploadId"] = 0
            data["message"]["mediaType"] = 100
            data["message"]["mediaValue"] = icon
        res = self.postRequest("/add-chat-message", data, webRequest=True)
        return Json(res)

    def unfollow(self, userId: str) -> Json:
        """Unfollow a community user.

        Parameters
        ----------
        userId : str
            The user ID to unfollow.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/member/{self.uid}")
        return Json(req)

    def follow(self, userId: Union[str, list]) -> Json:
        """Follow a community user or users.

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
            link = f"/x{self.comId}/s/user-profile/{userId}/member"
        elif isinstance(userId, list):
            link = f"/x{self.comId}/s/user-profile/{self.uid}/joined"
            data["targetUidList"] = userId
        req = self.postRequest(link, data)
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
        req = self.postRequest(f"/x{self.comId}/s/chat/thread", data)
        return Thread(req['thread']).Thread

    def invite_to_chat(self, chatId: str, userId: Union[str, list]) -> Json:
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
            "timestamp": int(timestamp() * 1000)
        }
        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/invite", data=data)
        return Json(req)

    def edit_profile(
        self,
        nickname: Optional[str] = None,
        content: Optional[str] = None,
        icon: Optional[BinaryIO] = None,
        backgroundColor: Optional[str] = None,
        backgroundImage: Optional[str] = None,
        defaultBubbleId: Optional[str] = None
    ) -> Json:
        """Edit the community profile.

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
            data["icon"] = self.upload_media(icon, 'image')
        if defaultBubbleId:
            extensions["defaultBubbleId"] = defaultBubbleId
        if backgroundColor:
            extensions["style"] = {"backgroundColor": backgroundColor}
        if backgroundImage:
            extensions["style"] = {"backgroundMediaList": [[100, backgroundImage, None, None, None]]}
        if extensions:
            data["extensions"] = extensions
        req = self.postRequest(f"/x{self.comId}/s/user-profile/{self.uid}", data)
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
        data: Dict[str, Union[int, str, list, dict]] = {"timestamp": int(timestamp() * 1000)}
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
                "timestamp": int(timestamp() * 1000)
            }
            req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}/background", data)
            res.append(Json(req))
        if announcement:
            extensions["announcement"] = announcement
        if pinAnnouncement:
            extensions["pinAnnouncement"] = pinAnnouncement
        if extensions:
            data['extensions'] = extensions
        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}", data)
        res.append(Json(req))
        return res

    def chat_settings(
        self,
        chatId: str,
        doNotDisturb: Optional[bool] = None,
        viewOnly: Optional[bool] = None,
        canInvite: Optional[bool] = None,
        canTip: Optional[bool] = None,
        pin: Optional[bool] = None,
        coHosts: Union[str, List[str], None] = None
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
            data = {"alertOption": doNotDisturb.real + 1, "timestamp": int(timestamp() * 1000)}
            req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}/alert", data)
            res.append(Json(req))
        if isinstance(viewOnly, bool):
            view = "enable" if viewOnly else "disable"
            req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/view-only/{view}")
            res.append(Json(req))
        if isinstance(canInvite, bool):
            can = "enable" if canInvite else "disable"
            req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/members-can-invite/{can}")
            res.append(Json(req))
        if isinstance(canTip, bool):
            can = "enable" if canTip else "disable"
            req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/tipping-perm-status/{can}")
            res.append(Json(req))
        if isinstance(pin, bool):
            action = "pin" if pin else "unpin"
            req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/{action}")
            res.append(Json(req))
        if coHosts:
            data = {
                "uidList": coHosts if isinstance(coHosts, list) else [coHosts],
                "timestamp": int(timestamp() * 1000)
            }
            req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/co-host", data)
            res.append(Json(req))
        return res

    def like_blog(self, blogId: Optional[str] = None, wikiId: Optional[str] = None) -> Json:
        """Like a blog or wiki.

        Parameters
        ----------
        blogId : str, optional
            The blog ID to like. Default is None.
        wikiId : str, optional
            The wiki ID to like. Default is None.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId and wikiId are not provided.

        """
        data = {"value": 4, "timestamp": int(timestamp() * 1000)}
        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/vote?cv=1.2&value=4"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/vote?cv=1.2&value=4"
        else:
            raise ValueError("Please put wiki or blog Id")
        req = self.postRequest(link, data)
        return Json(req)

    def unlike_blog(self, blogId: Optional[str] = None, wikiId: Optional[str] = None):
        """Unlike a blog or wiki.

        Parameters
        ----------
        blogId : str, optional
            The blog ID to like. Default is None.
        wikiId : str, optional
            The wiki ID to like. Default is None.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId and wikiId are not provided.

        """
        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/vote?eventSource=FeedList"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/vote?eventSource=FeedList"
        else:
            raise ValueError("Please put wikiId or blogId")
        req = self.deleteRequest(link)
        return Json(req)

    def change_titles(self, userId: str, titles: List[str], colors: List[str]) -> Json:
        """Change the user titles.

        Parameters
        ----------
        userId : str
            The user ID to change titles.
        titles : list
            The title name list.
        colors : list
            The title color list (hex color).

        Returns
        -------
        Json
            The JSON response.

        """
        t = [{"title": t, "color": c} for t, c in zip(titles, colors)]
        data = {
            "adminOpName": 207,
            "adminOpValue": {"titles": t},
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
        return Json(req)

    def like_comment(self, commentId: str, blogId: Optional[str] = None, wikiId: Optional[str] = None, userId: Optional[str] = None) -> Json:
        """Like a comment (blog, wiki or user profile).

        Parameters
        ----------
        commentId : str
            The comment ID to like.
        blogId : str, optional
            The blog ID associated with the comment.
        wikiId : str, optional
            The wiki ID associated with the comment.
        userId : str, optional
            The user profile associated with the comment.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId and userId are not provided.

        """
        data: Dict[str, Union[str, int]] = {"value": 1, "timestamp": int(timestamp() * 1000)}
        if blogId:
            data["eventSource"] = "PostDetailView"
            link = f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=1"
        elif wikiId:
            data["eventSource"] = "PostDetailView"
            link = f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}/vote?cv=1.2&value=1"
        elif userId:
            data["eventSource"] = "UserProfileView"
            link = f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}/vote?cv=1.2&value=1"
        else:
            raise ValueError("Please put a blogId, wikiId or userId")
        req = self.postRequest(link, data)
        return Json(req)

    def unlike_comment(self, commentId: str, blogId: Optional[str] = None, wikiId: Optional[str] = None, userId: Optional[str] = None) -> Json:
        """Unlike a comment (blog, wiki or user profile).

        Parameters
        ----------
        commentId : str
            The comment ID to like.
        blogId : str, optional
            The blog ID associated with the comment.
        wikiId : str, optional
            The wiki ID associated with the comment.
        userId : str, optional
            The user profile associated with the comment.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId and userId are not provided.

        """
        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}/g-vote?eventSource=PostDetailView"
        elif userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView"
        else:
            raise ValueError("Please put a wiki or user or blog Id")
        req = self.deleteRequest(link)
        return Json(req)

    def comment(
        self,
        comment: str,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        userId: Optional[str] = None,
        replyTo: Optional[str] = None,
        isGuest: bool = False,
    ) -> Json:
        """Comment on blog, wiki or user profile.

        Parameters
        ----------
        comment : str
            The comment to send.
        blogId : str, optional
            The blog ID to send the comment.
        wikiId : str, optional
            The wiki ID to send the comment.
        userId : str
            The user ID to send the comment.
        replyTo : str, optional
            The comment ID to reply. Default is None.
        isGuest : bool, optional
            Is guest comment. Default is False.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"content": comment, "timestamp": int(timestamp() * 1000)}
        if replyTo:
            data["respondTo"] = replyTo
        ctype = "g-comment" if isGuest else "comment"
        if userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/{ctype}"
        elif blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/{ctype}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/{ctype}"
        else:
            raise ValueError("Please put a wiki or user or blog Id")
        req = self.postRequest(link, data)
        return Json(req)

    def delete_comment(self, commentId: str, blogId: Optional[str] = None, wikiId: Optional[str] = None, userId: Optional[str] = None) -> Json:
        """Delete a comment.

        Parameters
        ----------
        commentId : str
            The comment ID to delete.
        blogId : str, optional
            The blog ID associated with the comment. Default is None.
        wikiId : str, optional
            The wiki ID associated with the comment. Default is None.
        userId : str
            The user profile ID associated with the comment. Default is None.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId and userId are not provided.

        """
        if userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}"
        elif blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}"
        else:
            raise ValueError("Please put blog or wiki or user Id")
        req = self.deleteRequest(link)
        return Json(req)

    def edit_comment(
        self,
        commentId: str,
        comment: str,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        userId: Optional[str] = None,
        replyTo: Optional[str] = None,
        isGuest: bool = False,
    ) -> Comment:
        """Edit a comment.

        Parameters
        ----------
        commentId : str
            The comment ID to edit.
        comment : str
            The new comment content.
        blogId : str, optional
            The blog ID associated with the comment. Default is None.
        wikiId : str, optional
            The wiki ID associated with the comment. Default is None.
        userId : str, optional
            The user ID associated with the comment. Default is None.
        replyTo : str, optional
            The comment ID to reply. Default is None.
        isGuest : bool, optional
            Is guest comment. Default is False.

        Returns
        -------
        Comment
            The edited comment object.

        Raises
        ------
        ValueError
            If the blogId, wikiId and userId are not provided.

        """
        data = {"content": comment, "timestamp": int(timestamp() * 1000)}
        if replyTo:
            data["respondTo"] = replyTo
        ctype = "g-comment" if isGuest else "comment"
        if userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/{ctype}/{commentId}"
        elif blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/{ctype}/{commentId}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/{ctype}/{commentId}"
        else:
            raise ValueError("Please put blog or wiki or user Id")
        req = self.postRequest(link, data)
        return Comment(req).Comments

    def get_comment_info(
        self,
        commentId: str,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        userId: Optional[str] = None,
        isGuest: bool = False,
    ) -> Comment:
        """Get comment information.

        Parameters
        ----------
        commentId : str
            The comment ID.
        blogId : str, optional
            The blog ID associated with the comment. Default is None.
        wikiId : str, optional
            The wiki ID associated with the comment. Default is None.
        userId : str, optional
            The user ID associated with the comment. Default is None.
        isGuest : bool, optional
            Is guest comment. Default is False.

        Returns
        -------
        Comment
            The comment object.

        Raises
        ------
        ValueError
            If the blogId, wikiId and userId are not provided.

        """
        ctype = "g-comment" if isGuest else "comment"
        if userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/{ctype}/{commentId}"
        elif blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/{ctype}/{commentId}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/{ctype}/{commentId}"
        else:
            raise ValueError("Please put blog or wiki or user Id")
        req = self.getRequest(link)
        return Comment(req).Comments

    def get_wall_comments(
        self,
        userId: str,
        sorting: Literal["newest", "oldest", "vote"] = "newest",
        start: int = 0,
        size: int = 25
    ) -> CommentList:
        """Get user wall comment list.

        Parameters
        ----------
        userId : str
            The user profile ID to get comment list.
        sorting : str, optional
            The comment sorting (newest, oldest, vote). Default is 'newest'.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        CommentList
            The comment list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/user-profile/{userId}/comment?sort={sorting}&start={start}&size={size}")
        return CommentList(req["commentList"]).CommentList

    def get_blog_comments(
        self,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        quizId: Optional[str] = None,
        sorting: Literal["newest", "oldest", "vote"] = "newest",
        start: int = 0,
        size: int = 25
    ) -> CommentList:
        """Get post comments.

        Parameters
        ----------
        blogId : str, optional
            The blog ID associated with the comment. Default is None.
        wikiId : str, optional
            The wiki ID associated with the comment. Default is None.
        quizId : str, optional
            The quiz ID associated with the comment. Default is None.
        sorting : str, optional
            The comment sorting (newest, oldest, vote). Default is 'newest'.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        CommentList
            The comment list object.

        Raises
        ------
        ValueError
            If the blogId, wikiId and quizId are not provided.

        """
        if quizId:
            blogId = quizId
        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}"
        else:
            raise ValueError("Please choose a wiki or a blog")
        req = self.getRequest(link)
        return CommentList(req["commentList"]).CommentList

    def vote_comment(self, commentId: str, blogId: str, value: bool = True) -> Json:
        """Vote a comment.

        Parameters
        ----------
        commentId : str
            The comment ID to vote.
        blogId : str
            The blog ID associated with the comment.
        value : bool, optional
            The vote value. Default is True.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"value": value.real or -1, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=1", data)
        return Json(req)

    def vote_poll(self, optionId: str, blogId: str) -> Json:
        """Vote a poll option.

        Parameters
        ----------
        optionId : str
            The option ID ot vote.
        blogId : str
            The poll blog ID.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"value": 1, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/x{self.comId}/s/blog/{blogId}/poll/option/{optionId}/vote", data)
        return Json(req)

    def get_blog_info(self, blogId: Optional[str] = None, wikiId: Optional[str] = None, folderId: Optional[str] = None) -> GetInfo:
        """Get community blog, wiki or folder information.

        Parameters
        ----------
        blogId : str, optional
            The blog ID to get information. Default is None.
        wikiId : str, optional
            The wiki ID to get information. Default is None.
        folderId : str, optional
            The shared-folder ID to get information. Default is None.

        Returns
        -------
        GetInfo
            The blog, wiki, folder info object.

        Raises
        ------
        ValueError
            If the blogId, wikiId and folderId are not provided.

        """
        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}"
        elif folderId:
            link = f"/x{self.comId}/s/shared-folder/files/{folderId}"
        else:
            raise ValueError("Please put a wiki or blog Id")
        req = self.getRequest(link)
        return GetInfo(req).GetInfo

    def get_blogs(self, start: int = 0, size: int = 25) -> BlogList:
        """Get featured blog list.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        BlogList
            The blog list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/feed/featured?start={start}&size={size}")
        return BlogList(req["featuredList"]).BlogList

    def get_blogs_more(self, start: int = 0, size: int = 25) -> BlogList:
        """Get more featured blog list.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        BlogList
            The blog list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/feed/featured-more?start={start}&size={size}")
        return BlogList(req["blogList"]).BlogList

    def get_blogs_all(self, start: int = 0, size: int = 25, pagingType: str = "t") -> BlogList:
        """Get community blog list.

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
        BlogList
            The blog list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/feed/blog-all?pagingType={pagingType}&start={start}&size={size}")
        return RecentBlogs(req["blogList"]).RecentBlogs

    def tip_coins(
        self,
        coins: int,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        chatId: Optional[str] = None,
        transactionId: Optional[str] = None
    ) -> Json:
        """Send props to blog, wiki or chat.

        Parameters
        ----------
        coins : int
            The amount of coins to send.
        blogId : str, optional
            The blog ID to send coins. Default is None.
        wikiId : str, optional
            The wiki ID to send coins. Default is None.
        chatId : str, optional
            The chat ID to send coins. Default is None.
        transactionId : str, optional
            The transaction ID. Default is None.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId and chatId are not provided.

        """
        if transactionId is None:
            transactionId = str(UUID(hexlify(os.urandom(16)).decode("ascii")))
        data = {
            "coins": coins,
            "tippingContext": {"transactionId": transactionId},
            "timestamp": int(timestamp() * 1000),
        }
        if chatId:
            link = f"/x{self.comId}/s/chat/thread/{chatId}/tipping"
        elif blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/tipping"
        elif wikiId:
            link = f"/x{self.comId}/s/tipping"
            data["objectType"] = 2
            data["objectId"] = wikiId
        else:
            raise ValueError("Please put a wiki or chat or blog Id")
        req = self.postRequest(link, data)
        return Json(req)

    def check_in(self, timezone: int = 0) -> Json:
        """Community check-in

        Parameters
        ----------
        timezone : int, optional
            The timezone (utc * 60). Default is 0.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"timezone": timezone, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/x{self.comId}/s/check-in", data)
        return Json(req)

    def check_in_lottery(self, timezone: int = 0) -> Json:
        """Play lottery.

        Parameters
        ----------
        timezone : int, optional
            The timezone (utc * 60). Default is 0.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"timezone": timezone, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/x{self.comId}/s/check-in/lottery", data)
        return Json(req)

    def delete_message(self, chatId: str, messageId: str, asStaff: bool = False, reason: Optional[str] = None) -> Json:
        """Delete a chat message.

        Parameters
        ----------
        chatId : str
            The chat ID associated with the message.
        messageId : str
            The message ID to delete.
        asStaff : bool, optional
            Delete with staff moderation. Default is False
        reason : str, optional
            The reason for deleting the message as staff. Default is None.

        Returns
        -------
        Json
            The JSON response.

        """
        data: Dict[str, Union[dict, int]] = {"adminOpName": 102, "timestamp": int(timestamp() * 1000)}
        if asStaff and reason:
            data["adminOpNote"] = {"content": reason}
            req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}/admin", data)
        else:
            req = self.deleteRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}")
        return Json(req)

    def invite_by_host(self, chatId: str, userId: str) -> Json:
        """Invite a user or users to a live chat.

        Parameters
        ----------
        chatId : str
            The chat ID to invite.
        userId : str
            The user ID to invite.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{userId}/invite-av-chat")
        return Json(req)

    def strike(
        self,
        userId: str,
        time: Literal["1-Hours", "3-Hours", "6-Hours", "12-Hours", "24-Hours"] = "3-Hours",
        title: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Json:
        """Strike a community member.

        Parameters
        ----------
        userId : str
            The user ID to strike.
        time : str, optional
            The strike duration ('1-Hours', '3-Hours', '6-Hours', '12-Hours', '24-Hours'). Default is '3-Hours'.
        title : str, optional
            The title of the strike. Default is None.
        reason : str, optional
            The reason for the strike. Default is None.

        Returns
        -------
        Json
            The JSON response.

        """
        times = {
            "1-Hours": 3600,
            "3-Hours": 10800,
            "6-Hours": 21600,
            "12-Hours": 43200,
            "24-Hours": 86400,
        }.get(time, 3600)
        data = {
            "uid": userId,
            "title": title,
            "content": reason,
            "attachedObject": {"objectId": userId, "objectType": 0},
            "penaltyType": 1,
            "penaltyValue": times,
            "adminOpNote": {},
            "noticeType": 4,
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{self.comId}/s/notice", data)
        return Json(req)

    def ban(self, userId: str, reason: str, banType: Optional[int] = None) -> Json:
        """Ban a community member.

        Parameters
        ----------
        userId : str
            The user ID to ban.
        reason : str
            The reason for the ban.
        banType : int, optional
            The ban type. Default is None.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "reasonType": banType,
            "note": {"content": reason},
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/ban", data)
        return Json(req)

    def unban(self, userId: str, note: str) -> Json:
        """Unban a community member.

        Parameters
        ----------
        userId : str
            The user ID to unban.
        note : str
            The note to the banned user.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"note": {"content": note}, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/unban", data)
        return Json(req)

    def hide(
        self,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        chatId: Optional[str] = None,
        userId: Optional[str] = None,
        note: Optional[str] = None
    ) -> Json:
        """Hide a blog, wiki, chat or user.

        Parameters
        ----------
        blogId : str, optional
            The blog ID to hide. Default is None.
        wikiId : str, optional
            The wiki ID to hide. Default is None.
        chatId : str, optional
            The chat ID to hide. Default is None.
        userId : str, optional
            The user ID to hide. Default is None.
        note : str, optional
            The note for the hide. Default is None.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId, chatId and userId are not provided.

        """
        data = {
            "adminOpName": 18 if userId else 110,
            "adminOpValue": None if userId else 9,
            "timestamp": int(timestamp() * 1000),
        }
        if userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/admin"
        elif blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/admin"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/admin"
        elif chatId:
            link = f"/x{self.comId}/s/chat/thread/{chatId}/admin"
        else:
            raise ValueError("Please put a wiki or user or chat or blog Id")
        if note:
            data["adminOpNote"] = {"content": note}
        req = self.postRequest(link, data)
        return Json(req)

    def unhide(
        self,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        chatId: Optional[str] = None,
        userId: Optional[str] = None,
        note: Optional[str] = None
    ) -> Json:
        """Unhide a blog, wiki, chat or user.

        Parameters
        ----------
        blogId : str, optional
            The blog ID to unhide. Default is None.
        wikiId : str, optional
            The wiki ID to unhide. Default is None.
        chatId : str, optional
            The chat ID to unhide. Default is None.
        userId : str, optional
            The user ID to unhide. Default is None.
        note : str, optional
            The note for the unhide. Default is None.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId, chatId and userId are not provided.

        """
        data: Dict[str, Union[dict, int]] = {
            "adminOpName": 19 if userId else 110,
            "adminOpValue": 0,
            "timestamp": int(timestamp() * 1000),
        }
        if userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/admin"
        elif blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/admin"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/admin"
        elif chatId:
            link = f"/x{self.comId}/s/chat/thread/{chatId}/admin"
        else:
            raise ValueError("Please put a wiki or user or chat or blog Id")
        if note:
            data["adminOpNote"] = {"content": note}
        req = self.postRequest(link, data)
        return Json(req)

    def send_warning(self, userId: str, reason: Optional[str] = None) -> Json:
        """Warn a user.

        Parameters
        ----------
        userId : str
            The user ID to warn.
        reason : str, optional
            The warning message.

        Returns
        -------
        Json
            _description_
        """
        data = {
            "uid": userId,
            "title": "Custom",
            "content": reason,
            "attachedObject": {"objectId": userId, "objectType": 0},
            "penaltyType": 0,
            "adminOpNote": {},
            "noticeType": 7,
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{self.comId}/s/notice", data)
        return Json(req)

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
        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/vvchat-presenter/invite", data)
        return Json(req)

    def post_blog(self, title: str, content: str, fansOnly: bool = False) -> Json:
        """Post a blog.

        Parameters
        ----------
        title : str
            The blog title.
        content : str
            The blog content.
        fansOnly : bool, optional
            The blog is for fans only (vip users only). Default is False.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "extensions": {"fansOnly": fansOnly},
            "content": content,
            "latitude": 0,
            "longitude": 0,
            "title": title,
            "type": 0,
            "contentLanguage": "en",
            "eventSource": "GlobalComposeMenu",
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{self.comId}/s/blog", data)
        return Json(req)

    def post_wiki(
        self,
        title: str,
        content: str,
        fansOnly: bool = False,
        icon: Optional[str] = None,
        backgroundColor: Optional[str] = None,
        keywords: Union[str, List[str], None] = None,
    ) -> Json:
        """Post a wiki.

        Parameters
        ----------
        title : str
            The wiki title.
        content : str
            The wiki content.
        fansOnly : bool, optional
            The wiki is for fans only (vip users only). Default is False.
        icon : str, optional
            The wiki icon. Default is None.
        backgroundColor : str, optional
            The wiki background color (hex color). Default is None.
        keywords : str, list, optional
            The wiki keywords. Default is None.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "extensions": {
                "fansOnly": fansOnly,
                "props": [],
                "style": {"backgroundColor": backgroundColor},
            },
            "content": content,
            "keywords": keywords,
            "label": title,
            "latitude": 0,
            "longitude": 0,
            "eventSource": "UserProfileView",
            "timestamp": int(timestamp() * 1000),
        }
        if icon:
            data["icon"] = icon
        req = self.postRequest(f"/x{self.comId}/s/item", data)
        return Json(req)

    def delete_blog(self, blogId: str) -> Json:
        """Delete a blog.

        Parameters
        ----------
        blogId : str
            The blog ID to delete.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.deleteRequest(f"/x{self.comId}/s/blog/{blogId}")
        return Json(req)

    def delete_wiki(self, wikiId: str) -> Json:
        """Delete a wiki.

        Parameters
        ----------
        wikiId : str
            The wiki ID to delete.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.deleteRequest(f"/x{self.comId}/s/item/{wikiId}")
        return Json(req)

    def activate_status(self, status: int = 1) -> Json:
        """Set the online status.

        Parameters
        ----------
        status : int, optional
            The online status. Default is 1.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "onlineStatus": status,
            "duration": 86400,
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{self.comId}/s/user-profile/{self.uid}/online-status", data)
        return Json(req)

    def subscribe(self, userId: str, autoRenew: bool = False, transactionId: Optional[str] = None) -> Json:
        """Subscribe to the vip user fan club.

        Parameters
        ----------
        userId : str
            The vip user ID to subscribe.
        autoRenew : bool, optional
            Auto renew the subscription. Default is False.
        transactionId : str, optional
            The transaction ID. Default is None.

        Returns
        -------
        Json
            The JSON response.

        """
        if transactionId is None:
            transactionId = str(UUID(hexlify(os.urandom(16)).decode("ascii")))
        data = {
            "paymentContext": {
                "transactionId": transactionId,
                "isAutoRenew": autoRenew,
            },
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{self.comId}/s/influencer/{userId}/subscribe", data)
        return Json(req)

    def submit_wiki(self, wikiId: str, message: Optional[str] = None) -> Json:
        """Submit a wiki to curate.

        Parameters
        ----------
        wikiId : str
            The wiki ID to submit.
        message : str, optional
            The submit message. Default is None.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "message": message,
            "itemId": wikiId,
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{self.comId}/s/knowledge-base-request", data)
        return Json(req)

    def edit_blog(
        self,
        title: str,
        content: str,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        fansOnly: bool = False,
        backgroundColor: Optional[str] = None,
        media: Optional[List[str]] = None,
    ) -> Json:
        """Edit a blog or wiki.

        Parameters
        ----------
        title : str
            The post title.
        content : str
            The post content.
        blogId : str, optional
            The blog ID to edit. Default is None.
        wikiId : str, optional
            The wiki ID to edit. Default is None.
        fansOnly : bool, optional
            The post is for fans only (vip users only). Default is False.
        backgroundColor : Optional[str], optional
            _description_, by default None
        media : list, optional
            The media url list. Default is None.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If no blogId or wikiId are not provided.

        """
        data = {
            "title": title,
            "content": content,
            "timestamp": int(timestamp() * 1000),
        }
        if media:
            data["mediaList"] = [[100, m, None, None] for m in media]
        if fansOnly:
            data["extensions"]["fansOnly"] = True
        if backgroundColor:
            data["extensions"] = {"backgroundColor": backgroundColor}
        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}"
        else:
            raise ValueError("Please put blogId or wikiId")
        req = self.postRequest(link, data)
        return Json(req)

    def get_chat_bubbles(self, start: int = 0, size: int = 25) -> BubbleList:
        """Get user's chat bubble list.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        BubbleList
            The chat bubble list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/chat/chat-bubble?type=all-my-bubbles&start={start}&size={size}")
        return BubbleList(req["chatBubbleList"]).BubbleList

    def select_bubble(self, bubbleId: str, applyToAll: bool = False, chatId: Optional[str] = None) -> Json:
        """Apply a chat bubble.

        Parameters
        ----------
        bubbleId : str
            The chat bubble ID to apply.
        applyToAll : bool, optional
            Apply to all chats. Default is False.
        chatId : str, optional
            The chat ID to apply. Default is None.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "bubbleId": bubbleId,
            "applyToAll": applyToAll.real,
            "timestamp": int(timestamp() * 1000),
        }
        if chatId and not applyToAll:
            data["threadId"] = chatId
        req = self.postRequest(f"/x{self.comId}/s/chat/thread/apply-bubble")
        return Json(req)

    def delete_chat_bubble(self, bubbleId: str) -> Json:
        """Delete a custom chat bubble.

        Parameters
        ----------
        bubbleId : str
            The chat bubble ID to delete.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.deleteRequest(url=f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}")
        return Json(req)

    def get_chat_bubble_templates(self, start: int = 0, size: int = 25) -> BubbleTemplates:
        """Get chat bubble template list.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        BubbleTemplates
            The chat bubble list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/chat/chat-bubble/templates?start={start}&size={size}")
        return BubbleTemplates(req["templateList"])

    def upload_custom_bubble(self, templateId: str) -> Json:
        """Upload a custom chat bubble.

        Parameters
        ----------
        templateId : str
            The template ID to upload.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(f"/x{self.comId}/s/chat/chat-bubble/templates/{templateId}/generate")
        return Json(req)

    def kick(self, chatId: str, userId: str, rejoin: bool = True) -> Json:
        """Kick a user from a chat.

        Parameters
        ----------
        chatId : str
            The chat ID associated with the user.
        userId : str
            The user ID to kick.
        rejoin : bool, optional
            Allow the user to rejoin the chat. Default is True.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.deleteRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{userId}?allowRejoin={rejoin.real}")
        return Json(req)

    def block(self, userId: str) -> Json:
        """Block a user.

        Parameters
        ----------
        userId : str
            The user ID to block.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.postRequest(f"/x{self.comId}/s/block/{userId}")
        return Json(req)

    def flag(
        self,
        reason: str,
        flagType: int = 0,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        userId: Optional[str] = None
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
            "timestamp": int(timestamp() * 1000)
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
            raise ValueError("choose a certain type to report")
        req = self.postRequest(f"/x{self.comId}/s/flag", data)
        return Json(req)

    # thanks to V¡ktor#9475 for ideas
    def send_active_time(self, tz: int = 0, timers: Optional[List[Dict[str, int]]] = None) -> Json:
        """Send user active time.

        Parameters
        ----------
        tz : int, optional
            The timezone (utc * 60). Default is 0.
        timers : list, optional
            The active chunk list. Default is None.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "userActiveTimeChunkList": timers if timers else active_time(minutes=5),
            "timestamp": int(timestamp() * 1000),
            "optInAdsFlags": 2147483647,
            "timezone": tz,
        }
        req = self.postRequest(f"/x{self.comId}/s/community/stats/user-active-time", data, minify=True)
        return Json(req)

    def transfer_host(self, chatId: str, userIds: List[str]) -> Json:
        """Transfer the chat host title.

        Parameters
        ----------
        chatId : str
            The chat ID associated with the host.
        userIds : str, list
            The user ID or user ID list to transfer.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "uidList": userIds if isinstance(userIds, list) else [userIds],
            "timestamp": int(timestamp() * 1000)
        }
        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer", data)
        return Json(req)

    def accept_host(self, chatId: str, requestId: str) -> Json:
        """Accept the transfer host request.

        Parameters
        ----------
        chatId : str
            The chat ID associated with the host.
        requestId : str
            The host request ID to accept.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept", data)
        return Json(req)

    def set_cohost(self, chatId: str, userId: Union[str, List[str]]) -> Json:
        """Add a new chat co-host.

        Parameters
        ----------
        chatId : str
            The chat ID to add the co-host.
        userId : str, list
            The user ID or user ID list to add.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "uidList": userId if isinstance(userId, list) else [userId],
            "timestamp": int(timestamp() * 1000)
        }
        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/co-host", data)
        return Json(req)

    def del_cohost(self, chatId : str, userId : str) -> Json:
        """Remove a chat co-host.

        Parameters
        ----------
        chatId : str
            The chat ID to remove the co-host.
        userId : str
            The co-host user ID to remove.

        Returns
        -------
        Json
            The JSON response.

        """
        req = self.deleteRequest(f"/x{self.comId}/s/chat/thread/{chatId}/co-host/{userId}")
        return Json(req)

    def get_quizzes(
        self,
        quizType: Literal["best", "trending", "recent"] = "recent",
        start: int = 0,
        size: int = 25
    ) -> BlogList:
        """Get community quiz list.

        Parameters
        ----------
        quizType : str, optional
            The quiz filter type (best, trending, recent). Default is 'recent'.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        BlogList
            The quiz list object.

        """
        if quizType == "best":
            link = f"x{self.comId}/s/feed/quiz-best-quizzes?start={start}&size={size}"
        elif quizType == "trending":
            link = f"x{self.comId}/s/feed/quiz-trending?start={start}&size={size}"
        else:
            link = f"x{self.comId}/s/blog?type=quizzes-recent&start={start}&size={size}"
        req = self.getRequest(link)
        return BlogList(req["blogList"]).BlogList

    def get_quiz_questions(self, quizId: str) -> QuizQuestionList:
        """Get quiz question list.

        Parameters
        ----------
        quizId : str
            The quiz ID.

        Returns
        -------
        QuizQuestionList
            The question list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/blog/{quizId}?action=review")
        return QuizQuestionList(req["blog"]["quizQuestionList"]).QuizQuestionList

    def play_quiz(self, quizId: str, questions: List[str], answers: List[str], mode: Literal[0, 1] = 0) -> Json:
        """Play a quiz.

        Parameters
        ----------
        quizId : str
            The quiz ID to play.
        questions : list
            The questionId list.
        answers : list
            The optionId list.
        mode : int, optional
            Play mode. Default is 0.
                0: normal mode
                1: hell mode

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "mode": mode,
            "quizAnswerList": [
                {"optIdList": [answer], "quizQuestionId": question, "timeSpent": 0.0}
                for answer, question in zip(answers, questions)
            ],
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{self.comId}/s/blog/{quizId}/quiz/result", data)
        return Json(req)

    def get_quiz_rankings(self, quizId: str, start: int = 0, size: int = 25) -> QuizRankings:
        """Get quiz ranking list.

        Parameters
        ----------
        quizId : str
            The quiz ID.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        QuizRankings
            The quiz ranking list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/blog/{quizId}/quiz/result?start={start}&size={size}")
        return QuizRankings(req).QuizRankings

    def search_user(self, username: str, start: int = 0, size: int = 25) -> UserProfileList:
        """Search user in the community.

        Parameters
        ----------
        username : str
            The user nickname.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        UserProfileList
            The search result object.

        """
        req = self.getRequest(f"/x{self.comId}/s/user-profile?type=name&q={username}&start={start}&size={size}")
        return UserProfileList(req["userProfileList"]).UserProfileList

    def search_blog(self, words: str, start: int = 0, size: int = 25) -> BlogList:
        """Search blog in the community by keywords.

        Parameters
        ----------
        words : str
            The quiz keyword.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        BlogList
            The search result object.
        """
        req = self.getRequest(f"/x{self.comId}/s/blog?type=keywords&q={words}&start={start}&size={size}")
        return BlogList(req["blogList"]).BlogList

    def get_notifications(self, start: int = 0, size: int = 25, pagingType: str = "t") -> NotificationList:
        """Get community notification list.

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
            The notification list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/notification?pagingType={pagingType}&start={start}&size={size}")
        return NotificationList(req).NotificationList

    def get_notices(self, start: int = 0, size: int = 25, noticeType: str = "usersV2", status: int = 1) -> NoticeList:
        """Get community notice list.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).
        noticeType : str, optional
            The notice type to return. Default is 'usersV2'
        status : int, optional
            The notice status. Default is 1

        Returns
        -------
        NoticeList
            The notice list object.

        """
        req = self.getRequest(f"/x{self.comId}/s/notice?type={noticeType}&status={status}&start={start}&size={size}")
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
        req = self.postRequest(f"/x{self.comId}/s/notice/{requestId}/accept")
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
        req = self.postRequest(f"/x{self.comId}/s/notice/{requestId}/decline")
        return Json(req)

    def sendWebActive(self) -> Json:
        """Send active time as web client.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"ndcId": self.comId}
        res = self.postRequest("/community/stats/web-user-active-time", data, webRequest=True)
        return Json(res)

    def get_recent_blogs(self, pageToken: Optional[str] = None, start: int = 0, size: int = 25) -> BlogList:
        """Get community recent blog list.

        Parameters
        ----------
        pageToken : str, optional
            The next or previous page token. Default is None.
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        RecentBlogs
            The recent blog list object.
        """
        req = self.getRequest(f"/x{self.comId}/s/feed/blog-all?pagingType=t&start={start}&size={size}&pageToken={pageToken}")
        return RecentBlogs(req["BlogList"]).RecentBlogs

    def publish_to_featured(
        self,
        time: Literal[1, 2, 3] = 1,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        chatId: Optional[str] = None,
        userId: Optional[str] = None
    ) -> Json:
        """Feature a blog, wiki, chat or user.

        Parameters
        ----------
        time : int, optional
            The feature duration (1, 2, 3). Default is 1.
        blogId : str, optional
            The blog ID to feature. Default is None.
        wikiId : str, optional
            The wiki ID to feature. Default is None.
        chatId : str, optional
            The chat ID to feature. Default is None.
        userId : str, optional
            The user ID to feature. Default is None.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId, chatId and userId are not provided.

        """
        duration = time * (3600 if chatId else 86400)
        data = {
            "adminOpName": 114,
            "adminOpValue": {"featuredDuration": duration},
            "timestamp": int(timestamp() * 1000),
        }
        if chatId:
            featuredType, endpoint = 5, f"chat/thread/{chatId}"
        elif userId:
            featuredType, endpoint = 4, f"user-profile/{userId}"
        elif blogId:
            featuredType, endpoint = 1, f"blog/{blogId}"
        elif wikiId:
            featuredType, endpoint = 1, f"item/{blogId}"
        else:
            raise ValueError("Please put the blogId, wikiId, userId or chatId")
        data["adminOpValue"]["featuredType"] = featuredType
        req = self.postRequest(f"/x{self.comId}/s/{endpoint}/admin", data)
        return Json(req)

    def remove_from_featured(
        self,
        blogId: Optional[str] = None,
        wikiId: Optional[str] = None,
        chatId: Optional[str] = None,
        userId: Optional[str] = None
    ) -> Json:
        """Remove a blog, wiki, chat or user from featured.

        Parameters
        ----------
        blogId : str, optional
            The blog ID to unfeature. Default is None.
        wikiId : str, optional
            The wiki ID to unfeature. Default is None.
        chatId : str, optional
            The chat ID to unfeature. Default is None.
        userId : str, optional
            The user ID to unfeature. Default is None.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId, chatId and userId are not provided.

        """
        data = {
            "adminOpName": 114,
            "adminOpValue": {"featuredType": 0},
            "timestamp": int(timestamp() * 1000),
        }
        if userId:
            endpoint = f"user-profile/{userId}"
        elif blogId:
            endpoint = f"blog/{blogId}"
        elif wikiId:
            endpoint = f"item/{blogId}"
        elif chatId:
            endpoint = f"chat/thread/{chatId}"
        else:
            raise ValueError("Please put the blogId, wikiId, userId or chatId")
        req = self.postRequest(f"/x{self.comId}/s/{endpoint}/admin", data)
        return Json(req)
