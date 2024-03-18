import base64
import time
import typing_extensions as typing
from ..lib.objects import (
    BlogList,
    BubbleList,
    BubbleTemplates,
    Comment,
    CommentList,
    GetInfo,
    Json,
    MessageList,
    NoticeList,
    NotificationList,
    QuizQuestionList,
    QuizRankings,
    RecentBlogs,
    RepInfo,
    Thread,
    ThreadList,
    UserProfile,
    UserProfileList,
    VisitorsList,
    WikiList,
)
from ..lib.sessions import Session
from ..lib.types import FileType, FilterType, ProxiesType, SortingType, UserType
from ..lib.util import active_time, generateTransactionId, get_file_type
from .acm import Acm
from .client import Client

__all__ = ('SubClient',)


class SubClient(Acm, Session):
    """Represents an amino client from a community.

    Parameters
    ----------
    comId : `int`
        The community ID.
    client : `Client`
        The amino global client object.
    proxies : `ProxiesType`, `optional`
        Proxies for HTTP requests supported by the httpx library (https://www.python-httpx.org/advanced/#routing)
    acm : `bool`, `optional`
        The client is amino community manager (ACM)
    debug : `bool`, `optional`
        Print api debug information. Default is `False`.

    """

    def __init__(
        self,
        comId: int,
        client: Client,
        proxies: typing.Optional[ProxiesType] = None,
        acm: bool = False,
        debug: bool = False
    ) -> None:
        if acm:
            Acm.__init__(self, comId=comId, client=client, proxies=proxies)
        else:
            self.comId = comId
            Session.__init__(self, client=client, debug=debug, proxies=proxies)

    def get_video_rep_info(self, chatId: str) -> RepInfo:
        """Get screening-room video reputation information.

        Parameters
        ----------
        chatId : `str`
            The chat ID of screening room.

        Returns
        -------
        RepInfo
            The reputation info object.

        """
        return RepInfo(self.getRequest(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation"))

    def claim_video_rep(self, chatId: str) -> RepInfo:
        """Claim screening-room video reputation.

        Parameters
        ----------
        chatId : `str`
            The chat ID of screening room.

        Returns
        -------
        RepInfo
            The claimed reputation object.

        """
        return RepInfo(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation"))

    def join_chat(self, chatId: str) -> Json:
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
        return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}"))

    def upload_media(self, file: typing.Union[typing.BinaryIO, bytes], fileType: FileType) -> str:
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
        return self.postRequest("/g/s/media/upload", data=data, newHeaders=newHeaders)["mediaValue"]

    def leave_chat(self, chatId: str) -> Json:
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
        return Json(self.deleteRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}"))

    def get_member_following(self, userId: str, start: int = 0, size: int = 25) -> UserProfileList:
        """Get user's followings.

        Parameters
        ----------
        userId : `str`
            The user ID to get the list.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        UserProfileList
            The follwing member list object.

        """
        return UserProfileList(self.getRequest(f"/x{self.comId}/s/user-profile/{userId}/joined?start={start}&size={size}")["userProfileList"]).UserProfileList

    def get_member_followers(self, userId: str, start: int = 0, size: int = 25) -> UserProfileList:
        """Get user's followers.

        Parameters
        ----------
        userId : `str`
            The user ID to get the list.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        UserProfileList
            The follower list object.

        """
        return UserProfileList(self.getRequest(f"/x{self.comId}/s/user-profile/{userId}/member?start={start}&size={size}")["userProfileList"]).UserProfileList

    def get_member_visitors(self, userId: str, start: int = 0, size: int = 25) -> VisitorsList:
        """Get user's visitor list.

        Parameters
        ----------
        userId : `str`
            The user ID to get the list.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        VisitorsList
            The visitor list object.

        """
        return VisitorsList(self.getRequest(f"/x{self.comId}/s/user-profile/{userId}/visitors?start={start}&size={size}")["visitors"]).VisitorsList

    def get_chat_threads(self, start: int = 0, size: int = 25) -> ThreadList:
        """Get a list of the user's joined chats.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        ThreadList
            The joined community list object.

        """
        return ThreadList(self.getRequest(f"/x{self.comId}/s/chat/thread?type=joined-me&start={start}&size={size}")["threadList"]).ThreadList

    def get_chat_messages(self, chatId: str, start: int = 0, size: int = 25) -> MessageList:
        """Get messages from a chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID to get messages.
        start : `int`, `optional`
            The start index. Default is 0.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        MessageList
            The message list object.

        """
        return MessageList(self.getRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message?v=2&pagingType=t&start={start}&size={size}")["messageList"]).MessageList

    def get_user_info(self, userId: str) -> UserProfile:
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
        return UserProfile(self.getRequest(f"/x{self.comId}/s/user-profile/{userId}")["userProfile"]).UserProfile

    def get_user_blogs(self, userId: str, start: int = 0, size: int = 25) -> BlogList:
        """Get user blog list.

        Parameters
        ----------
        userId : `str`
            The user ID.
        start : `int`, `optional`
            The start index. Default is 0.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        BlogList
            The blog list object.

        """
        return BlogList(self.getRequest(f"/x{self.comId}/s/blog?type=user&q={userId}&start={start}&size={size}")["blogList"]).BlogList

    def get_user_wikis(self, userId: str, start: int = 0, size: int = 25) -> WikiList:
        """Get user wiki list.

        Parameters
        ----------
        userId : `str`
            The user ID.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        WikiList
            The wiki list object.

        """
        return WikiList(self.getRequest(f"/x{self.comId}/s/item?type=user-all&start={start}&size={size}&cv=1.2&uid={userId}")["itemList"]).WikiList

    def get_all_users(self, usersType: UserType = "recent", start: int = 0, size: int = 25) -> UserProfileList:
        """Get community user list.

        Parameters
        ----------
        usersType : `str`, `optional`
            The user type (recent, banned, featured, leaders, curators). Default is'recent'.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        UserProfileList
            The amino user list object.

        """
        return UserProfileList(self.getRequest(f"/x{self.comId}/s/user-profile?type={usersType}&start={start}&size={size}")["userProfileList"]).UserProfileList

    def get_chat_members(self, chatId: str, start: int = 0, size: int = 25) -> UserProfileList:
        """Get chat member list.

        Parameters
        ----------
        chatId : `str`
            The chat ID to get the list of members.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        UserProfileList
            The member list object.

        """
        return UserProfileList(self.getRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2")["memberList"]).UserProfileList

    def get_chat_info(self, chatId: str) -> Thread:
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
        return Thread(self.getRequest(f"/x{self.comId}/s/chat/thread/{chatId}")["thread"]).Thread

    def get_online_users(self, start: int = 0, size: int = 25) -> UserProfileList:
        """Get community online user list.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        UserProfileList
            The user list object.

        """
        return UserProfileList(self.getRequest(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:online-members&start={start}&size={size}")["userProfileList"]).UserProfileList

    def get_public_chats(self, filterType: FilterType = "recommended", start: int = 0, size: int = 25) -> ThreadList:
        """Get community public chats.

        Parameters
        ----------
        filterType : `str`, `optional`
            The chat filter type. Default is 'recommended'.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        ThreadList
            The chat list object.

        """
        return ThreadList(self.getRequest(f"/x{self.comId}/s/chat/thread?type=public-all&filterType={filterType}&start={start}&size={size}")["threadList"]).ThreadList

    def full_embed(self, chatId: str, link: str, image: typing.BinaryIO, message: str) -> Json:
        """Send embed chat message.

        Parameters
        ----------
        link : `str`
            The embed link.
        image : `BinaryIO`
            The embed image file opened in read-byte mode (rb).
        message : `str`
            The embed message.
        chatId : `str`
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
                    "mediaUploadValue": base64.b64encode(image.read()).decode(),
                    "mediaUploadValueContentType": "image/png"
                }]
            },
            "clientRefId": int(time.time() / 10 % 100000000),
            "timestamp": int(time.time() * 1000),
            "attachedObject": None
        }
        return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message", data))

    @typing.overload  # sticker
    def send_message(
        self: typing.Self,
        chatId: str,
        *,
        stickerId: str
    ) -> Json: ...
    @typing.overload  # file
    def send_message(
        self: typing.Self,
        chatId: str,
        *,
        file: typing.BinaryIO,
        fileType: typing.Literal['audio', 'gif', 'image']
    ) -> Json: ...
    @typing.overload  # video file
    def send_message(
        self: typing.Self,
        chatId: str,
        *,
        file: typing.BinaryIO,
        fileType: typing.Literal['video'],
        fileCoverImage: typing.Optional[typing.BinaryIO] = None
    ) -> Json: ...
    @typing.overload  # yt-video
    def send_message(
        self,
        chatId: str, *,
        ytVideo: str,
        replyTo: typing.Optional[str] = None,
        mentionUserIds: typing.Optional[typing.Union[typing.List[str], str]] = None
    ) -> Json: ...
    @typing.overload  # yt-video + embed
    def send_message(
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
    def send_message(
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
    def send_message(
        self: typing.Self,
        chatId: str,
        message: str,
        messageType: int = 0,
        *,
        replyTo: typing.Optional[str] = None,
        mentionUserIds: typing.Optional[typing.Union[typing.List[str], str]] = None
    ) -> Json: ...
    @typing.overload  # text + embed
    def send_message(
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
    def send_message(
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
    def send_message(
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
                "mediaUploadValueContentType": "image/%s" % get_file_type(getattr(snippetImage, "name", ""), "png"),
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
                data["mediaUploadValueContentType"] = "image/%s" % get_file_type(getattr(file, "name", ""), "jpeg")
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
        return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message", data=data, files=files))

    def send_web_message(
        self,
        chatId: str,
        message: typing.Optional[str] = None,
        messageType: int = 0,
        icon: typing.Optional[str] = None,
        comId: typing.Optional[int] = None
    ) -> Json:
        """Send a chat message as web client.

        Parameters
        ----------
        chatId : `str`
            The chat ID to send the message.
        message : `str`, `optional`
            The message to send. Default is `None`.
        messageType : `int`, `optional`
            The message type. Default is `0`.
        icon : `str`, `optional`
            The image url. Default is `None`.
        comId : `int`, `optional`
            The community ID associated with the chat. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        if not comId:
            comId = self.comId
        data: typing.Dict[str, typing.Any] = {
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
            data["message"]["mediaType"] = 100
            data["message"]["uploadId"] = 0
            data["message"]["mediaValue"] = icon
        return Json(self.postRequest("/add-chat-message", data, webRequest=True))

    def unfollow(self, userId: str) -> Json:
        """Unfollow a community user.

        Parameters
        ----------
        userId : `str`
            The user ID to unfollow.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/member/{self.uid}"))

    def follow(self, userId: typing.Union[typing.List[str], str]) -> Json:
        """Follow a community user or users.

        Parameters
        ----------
        userId : list[str], str
            The user ID or list of user IDs to follow.

        Returns
        -------
        Json
            The JSON response.

        """
        data: typing.Dict[str, typing.Any] = {"timestamp": int(time.time() * 1000)}
        if isinstance(userId, list):
            link = f"/x{self.comId}/s/user-profile/{self.uid}/joined"
            data["targetUidList"] = userId
        else:
            link = f"/x{self.comId}/s/user-profile/{userId}/member"
        return Json(self.postRequest(link, data))

    def start_chat(
        self,
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
        return Thread(self.postRequest(f"/x{self.comId}/s/chat/thread", data)['thread']).Thread

    def invite_to_chat(self, chatId: str, userId: typing.Union[typing.List[str], str]) -> Json:
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
            "timestamp": int(time.time() * 1000)
        }
        return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/invite", data=data))

    def edit_profile(
        self,
        nickname: typing.Optional[str] = None,
        content: typing.Optional[str] = None,
        icon: typing.Optional[typing.BinaryIO] = None,
        backgroundColor: typing.Optional[str] = None,
        backgroundImage: typing.Optional[str] = None,
        defaultBubbleId: typing.Optional[str] = None
    ) -> Json:
        """Edit the community profile.

        Parameters
        ----------
        nickname : `str`, `optional`
            The new nickname. Default is `None`.
        content : `str`, `optional`
            The new bio. Default is `None`.
        icon : `BinaryIO`, `optional`
            The opened file in read bytes mode. Default is `None`.
        backgroundColor : `str`, `optional`
            The new background color in hex code. Default is `None`.
        backgroundImage : `str`, `optional`
            The new background image. Default is `None`.
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
            data["icon"] = self.upload_media(icon, 'image')
        if defaultBubbleId:
            extensions["defaultBubbleId"] = defaultBubbleId
        if backgroundColor:
            extensions["style"] = {"backgroundColor": backgroundColor}
        if backgroundImage:
            extensions["style"] = {"backgroundMediaList": [[100, backgroundImage, None, None, None]]}
        if extensions:
            data["extensions"] = extensions
        return Json(self.postRequest(f"/x{self.comId}/s/user-profile/{self.uid}", data))

    def edit_chat(
        self,
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
        list[Json]
            The JSON response list.

        """
        data: typing.Dict[str, typing.Any] = {"timestamp": int(time.time() * 1000)}
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
                "timestamp": int(time.time() * 1000)
            }
            res.append(Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}/background", data)))
        if announcement:
            extensions["announcement"] = announcement
        if pinAnnouncement:
            extensions["pinAnnouncement"] = pinAnnouncement
        if extensions:
            data['extensions'] = extensions
        res.append(Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}", data)))
        return res

    def chat_settings(
        self,
        chatId: str,
        doNotDisturb: typing.Optional[bool] = None,
        viewOnly: typing.Optional[bool] = None,
        canInvite: typing.Optional[bool] = None,
        canTip: typing.Optional[bool] = None,
        pin: typing.Optional[bool] = None,
        coHosts: typing.Optional[typing.Union[typing.List[str], str]] = None
    ) -> typing.List[Json]:
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
        res: typing.List[Json] = []
        if isinstance(doNotDisturb, bool):
            data: typing.Dict[str, typing.Any] = {"alertOption": doNotDisturb.real + 1, "timestamp": int(time.time() * 1000)}
            res.append(Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}/alert", data)))
        if isinstance(viewOnly, bool):
            view = "enable" if viewOnly else "disable"
            res.append(Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/view-only/{view}")))
        if isinstance(canInvite, bool):
            can = "enable" if canInvite else "disable"
            res.append(Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/members-can-invite/{can}")))
        if isinstance(canTip, bool):
            can = "enable" if canTip else "disable"
            res.append(Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/tipping-perm-status/{can}")))
        if isinstance(pin, bool):
            action = "pin" if pin else "unpin"
            res.append(Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/{action}")))
        if coHosts:
            data = {
                "uidList": coHosts if isinstance(coHosts, list) else [coHosts],
                "timestamp": int(time.time() * 1000)
            }
            res.append(Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/co-host", data)))
        return res

    def like_blog(self, blogId: typing.Optional[str] = None, wikiId: typing.Optional[str] = None) -> Json:
        """Like a blog or wiki.

        Parameters
        ----------
        blogId : `str`, `optional`
            The blog ID to like. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID to like. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId and wikiId are not provided.

        """
        data = {
            "vale": 4,
            "timestamp": int(time.time() * 1000)}
        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/vote?cv=1.2&value=4"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/vote?cv=1.2&value=4"
        else:
            raise ValueError("Please put wiki or blog Id")
        return Json(self.postRequest(link, data))

    def unlike_blog(self, blogId: typing.Optional[str] = None, wikiId: typing.Optional[str] = None):
        """Unlike a blog or wiki.

        Parameters
        ----------
        blogId : `str`, `optional`
            The blog ID to like. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID to like. Default is `None`.

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
        return Json(self.deleteRequest(link))

    def change_titles(self, userId: str, titles: typing.List[str], colors: typing.List[str]) -> Json:
        """Change the user titles.

        Parameters
        ----------
        userId : `str`
            The user ID to change titles.
        titles : `list[str]`
            The title name list.
        colors : `list[str]`
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
            "timestamp": int(time.time() * 1000),
        }
        return Json(self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/admin", data))

    @typing.overload
    def like_comment(self, commentId: str, blogId: str) -> Json: ...
    @typing.overload
    def like_comment(self, commentId: str, *, wikiId: str) -> Json: ...
    @typing.overload
    def like_comment(self, commentId: str, *, userId: str) -> Json: ...
    def like_comment(self, commentId: str, blogId: typing.Optional[str] = None, wikiId: typing.Optional[str] = None, userId: typing.Optional[str] = None) -> Json:
        """Like a comment (blog, wiki or user profile).

        Parameters
        ----------
        commentId : `str`
            The comment ID to like.
        blogId : `str`, `optional`
            The blog ID associated with the comment.
        wikiId : `str`, `optional`
            The wiki ID associated with the comment.
        userId : `str`, `optional`
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
        data: typing.Dict[str, typing.Any] = {"value": 1, "timestamp": int(time.time() * 1000)}
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
        return Json(self.postRequest(link, data))

    @typing.overload
    def unlike_comment(self, commentId: str, blogId: str) -> Json: ...
    @typing.overload
    def unlike_comment(self, commentId: str, *, wikiId: str) -> Json: ...
    @typing.overload
    def unlike_comment(self, commentId: str, *, userId: str) -> Json: ...
    def unlike_comment(self, commentId: str, blogId: typing.Optional[str] = None, wikiId: typing.Optional[str] = None, userId: typing.Optional[str] = None) -> Json:
        """Unlike a comment (blog, wiki or user profile).

        Parameters
        ----------
        commentId : `str`
            The comment ID to like.
        blogId : `str`, `optional`
            The blog ID associated with the comment.
        wikiId : `str`, `optional`
            The wiki ID associated with the comment.
        userId : `str`, `optional`
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
        return Json(self.deleteRequest(link))

    @typing.overload
    def comment(self, comment: str, blogId: str, *, replyTo: typing.Optional[str] = None, isGuest: bool = False) -> Json: ...
    @typing.overload
    def comment(self, comment: str, *, wikiId: str, replyTo: typing.Optional[str] = None, isGuest: bool = False) -> Json: ...
    @typing.overload
    def comment(self, comment: str, *, userId: str, replyTo: typing.Optional[str] = None, isGuest: bool = False) -> Json: ...
    def comment(
        self,
        comment: str,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        userId: typing.Optional[str] = None,
        replyTo: typing.Optional[str] = None,
        isGuest: bool = False,
    ) -> Json:
        """Comment on blog, wiki or user profile.

        Parameters
        ----------
        comment : `str`
            The comment to send.
        blogId : `str`, `optional`
            The blog ID to send the comment.
        wikiId : `str`, `optional`
            The wiki ID to send the comment.
        userId : `str`, `optional`
            The user ID to send the comment. 
        replyTo : `str`, `optional`
            The comment ID to reply. Default is `None`.
        isGuest : bool, optional
            Is guest comment. Default is `False`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"content": comment, "timestamp": int(time.time() * 1000)}
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
        return Json(self.postRequest(link, data))

    @typing.overload
    def delete_comment(self, commentId: str, blogId: str) -> Json: ...
    @typing.overload
    def delete_comment(self, commentId: str, *, wikiId: str) -> Json: ...
    @typing.overload
    def delete_comment(self, commentId: str, *, userId: str) -> Json: ...
    def delete_comment(self, commentId: str, blogId: typing.Optional[str] = None, wikiId: typing.Optional[str] = None, userId: typing.Optional[str] = None) -> Json:
        """Delete a comment.

        Parameters
        ----------
        commentId : `str`
            The comment ID to delete.
        blogId : `str`, `optional`
            The blog ID associated with the comment. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID associated with the comment. Default is `None`.
        userId : `str`, `optional`
            The user profile ID associated with the comment. Default is `None`.

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
        return Json(self.deleteRequest(link))

    @typing.overload
    def edit_comment(
        self,
        commentId: str,
        comment: str,
        blogId: str,
        *,
        replyTo: typing.Optional[str] = None,
        isGuest: bool = False,
    ) -> Comment: ...
    @typing.overload
    def edit_comment(
        self,
        commentId: str,
        comment: str,
        *,
        wikiId: str,
        replyTo: typing.Optional[str] = None,
        isGuest: bool = False,
    ) -> Comment: ...
    @typing.overload
    def edit_comment(
        self,
        commentId: str,
        comment: str,
        *,
        userId: str,
        replyTo: typing.Optional[str] = None,
        isGuest: bool = False,
    ) -> Comment: ...
    def edit_comment(
        self,
        commentId: str,
        comment: str,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        userId: typing.Optional[str] = None,
        replyTo: typing.Optional[str] = None,
        isGuest: bool = False,
    ) -> Comment:
        """Edit a comment.

        Parameters
        ----------
        commentId : `str`
            The comment ID to edit.
        comment : `str`
            The new comment content.
        blogId : `str`, `optional`
            The blog ID associated with the comment. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID associated with the comment. Default is `None`.
        userId : `str`, `optional`
            The user ID associated with the comment. Default is `None`.
        replyTo : `str`, `optional`
            The comment ID to reply. Default is `None`.
        isGuest : `bool`, `optional`
            Is guest comment. Default is `False`.

        Returns
        -------
        Comment
            The edited comment object.

        Raises
        ------
        ValueError
            If the blogId, wikiId and userId are not provided.

        """
        data = {
            "content": comment,
            "timestamp": int(time.time() * 1000)
        }
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
        return Comment(self.postRequest(link, data)).Comments

    @typing.overload
    def get_comment_info(self, commentId: str, blogId: str, *, isGuest: bool = False) -> Comment: ...
    @typing.overload
    def get_comment_info(self, commentId: str, *, wikiId: str, isGuest: bool = False) -> Comment: ...
    @typing.overload
    def get_comment_info(self, commentId: str, *, userId: str, isGuest: bool = False) -> Comment: ...
    def get_comment_info(
        self,
        commentId: str,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        userId: typing.Optional[str] = None,
        isGuest: bool = False,
    ) -> Comment:
        """Get comment information.

        Parameters
        ----------
        commentId : `str`
            The comment ID.
        blogId : `str`, `optional`
            The blog ID associated with the comment. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID associated with the comment. Default is `None`.
        userId : `str`, `optional`
            The user ID associated with the comment. Default is `None`.
        isGuest : `bool`, `optional`
            Is guest comment. Default is `False`.

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
        return Comment(self.getRequest(link)).Comments

    def get_wall_comments(
        self,
        userId: str,
        sorting: SortingType = "newest",
        start: int = 0,
        size: int = 25
    ) -> CommentList:
        """Get user wall comment list.

        Parameters
        ----------
        userId : `str`
            The user profile ID to get comment list.
        sorting : `str`, `optional`
            The comment sorting (newest, oldest, vote). Default is 'newest'.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        CommentList
            The comment list object.

        """
        return CommentList(self.getRequest(f"/x{self.comId}/s/user-profile/{userId}/comment?sort={sorting}&start={start}&size={size}")["commentList"]).CommentList

    @typing.overload
    def get_blog_comments(
        self,
        blogId: str,
        *,
        sorting: SortingType = "newest",
        start: int = 0,
        size: int = 25
    ) -> CommentList: ...
    @typing.overload
    def get_blog_comments(
        self,
        *,
        wikiId: str,
        sorting: SortingType = "newest",
        start: int = 0,
        size: int = 25
    ) -> CommentList: ...
    @typing.overload
    def get_blog_comments(
        self,
        *,
        quizId: str,
        sorting: SortingType = "newest",
        start: int = 0,
        size: int = 25
    ) -> CommentList: ...
    def get_blog_comments(
        self,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        quizId: typing.Optional[str] = None,
        sorting: SortingType = "newest",
        start: int = 0,
        size: int = 25
    ) -> CommentList:
        """Get post comments.

        Parameters
        ----------
        blogId : `str`, `optional`
            The blog ID associated with the comment. Default is None.
        wikiId : `str`, `optional`
            The wiki ID associated with the comment. Default is None.
        quizId : `str`, `optional`
            The quiz ID associated with the comment. Default is None.
        sorting : `str`, `optional`
            The comment sorting (newest, oldest, vote). Default is 'newest'.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

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
        return CommentList(self.getRequest(link)["commentList"]).CommentList

    def vote_comment(self, commentId: str, blogId: str, value: bool = True) -> Json:
        """Vote a comment.

        Parameters
        ----------
        commentId : `str`
            The comment ID to vote.
        blogId : `str`
            The blog ID associated with the comment.
        value : `bool`, `optional`
            The vote value. Default is `True`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "value": value.real or -1,
            "timestamp": int(time.time() * 1000)
        }
        return Json(self.postRequest(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=1", data))

    def vote_poll(self, optionId: str, blogId: str) -> Json:
        """Vote a poll option.

        Parameters
        ----------
        optionId : `str`
            The option ID ot vote.
        blogId : `str`
            The poll blog ID.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "value": 1,
            "timestamp": int(time.time() * 1000)
        }
        return Json(self.postRequest(f"/x{self.comId}/s/blog/{blogId}/poll/option/{optionId}/vote", data))

    @typing.overload
    def get_blog_info(self, blogId: str) -> GetInfo: ...
    @typing.overload
    def get_blog_info(self, *, wikiId: str) -> GetInfo: ...
    @typing.overload
    def get_blog_info(self, *, folderId: str) -> GetInfo: ...
    def get_blog_info(self, blogId: typing.Optional[str] = None, wikiId: typing.Optional[str] = None, folderId: typing.Optional[str] = None) -> GetInfo:
        """Get community blog, wiki or folder information.

        Parameters
        ----------
        blogId : `str`, `optional`
            The blog ID to get information. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID to get information. Default is None.
        folderId : `str`, `optional`
            The shared-folder ID to get information. Default is `None`.

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
        return GetInfo(self.getRequest(link)).GetInfo

    def get_blogs(self, start: int = 0, size: int = 25) -> BlogList:
        """Get featured blog list.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        BlogList
            The blog list object.

        """
        return BlogList(self.getRequest(f"/x{self.comId}/s/feed/featured?start={start}&size={size}")["featuredList"]).BlogList

    def get_blogs_more(self, start: int = 0, size: int = 25) -> BlogList:
        """Get more featured blog list.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        BlogList
            The blog list object.

        """
        return BlogList(self.getRequest(f"/x{self.comId}/s/feed/featured-more?start={start}&size={size}")["blogList"]).BlogList

    def get_blogs_all(self, start: int = 0, size: int = 25, pagingType: str = "t") -> BlogList:
        """Get community blog list.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).
        pagingType : `str`, `optional`
            The paging type to return. Default is 't'.

        Returns
        -------
        BlogList
            The blog list object.

        """
        return RecentBlogs(self.getRequest(f"/x{self.comId}/s/feed/blog-all?pagingType={pagingType}&start={start}&size={size}")["blogList"]).RecentBlogs

    @typing.overload
    def tip_coins(self: typing.Self, coins: int, blogId: str, *, transactionId: typing.Optional[str] = None) -> Json: ...
    @typing.overload
    def tip_coins(self: typing.Self, coins: int, *, wikiId: str, transactionId: typing.Optional[str] = None) -> Json: ...
    @typing.overload
    def tip_coins(self: typing.Self, coins: int, *, chatId: str, transactionId: typing.Optional[str] = None) -> Json: ...
    def tip_coins(
        self,
        coins: int,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        chatId: typing.Optional[str] = None,
        transactionId: typing.Optional[str] = None
    ) -> Json:
        """Send props to blog, wiki or chat.

        Parameters
        ----------
        coins : `int`
            The amount of coins to send.
        blogId : `str`, `optional`
            The blog ID to send coins. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID to send coins. Default is `None`.
        chatId : `str`, `optional`
            The chat ID to send coins. Default is `None`.
        transactionId : `str`, `optional`
            The transaction ID. Default is `None`.

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
            transactionId = generateTransactionId()
        data: typing.Dict[str, typing.Any] = {
            "coins": coins,
            "tippingContext": {"transactionId": transactionId},
            "timestamp": int(time.time() * 1000),
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
        return Json(self.postRequest(link, data))

    def check_in(self, timezone: int = 0) -> Json:
        """Community check-in

        Parameters
        ----------
        timezone : `int`, `optional`
            The timezone (utc * 60). Default is `0`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "timezone": timezone,
            "timestamp": int(time.time() * 1000)
        }
        return Json(self.postRequest(f"/x{self.comId}/s/check-in", data))

    def check_in_lottery(self, timezone: int = 0) -> Json:
        """Play lottery.

        Parameters
        ----------
        timezone : `int`, `optional`
            The timezone (utc * 60). Default is `0`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "timezone": timezone,
            "timestamp": int(time.time() * 1000)
        }
        return Json(self.postRequest(f"/x{self.comId}/s/check-in/lottery", data))

    @typing.overload
    def delete_message(self, chatId: str, messageId: str, asStaff: typing.Literal[False] = False, reason: None = None) -> Json: ...
    @typing.overload
    def delete_message(self, chatId: str, messageId: str, asStaff: typing.Literal[True], reason: str) -> Json: ...
    def delete_message(self, chatId: str, messageId: str, asStaff: bool = False, reason: typing.Optional[str] = None) -> Json:
        """Delete a chat message.

        Parameters
        ----------
        chatId : `str`
            The chat ID associated with the message.
        messageId : `str`
            The message ID to delete.
        asStaff : `bool`, `optional`
            Delete with staff moderation. Default is `False`.
        reason : `str`, `optional`
            The reason for deleting the message as staff. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        data: typing.Dict[str, typing.Any] = {"adminOpName": 102, "timestamp": int(time.time() * 1000)}
        if asStaff and reason:
            data["adminOpNote"] = {"content": reason}
            return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}/admin", data))
        else:
            return Json(self.deleteRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}"))

    def invite_by_host(self, chatId: str, userId: str) -> Json:
        """Invite a user or users to a live chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID to invite.
        userId : `str`
            The user ID to invite.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{userId}/invite-av-chat"))

    def strike(
        self,
        userId: str,
        hours: typing.Literal[1, 3, 6, 12, 24] = 3,
        title: typing.Optional[str] = None,
        reason: typing.Optional[str] = None
    ) -> Json:
        """Strike a community member.

        Parameters
        ----------
        userId : `str`
            The user ID to strike.
        hours : `int`, `optional`
            The strike duration (1, 3, 6, 12, 24). Default is `3`.
        title : `str`, `optional`
            The title of the strike. Default is `None`.
        reason : `str`, `optional`
            The reason for the strike. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        seconds = 60 * 60 * hours
        data: typing.Dict[str, typing.Any] = {
            "uid": userId,
            "title": title,
            "content": reason,
            "attachedObject": {"objectId": userId, "objectType": 0},
            "penaltyType": 1,
            "penaltyValue": seconds,
            "adminOpNote": {},
            "noticeType": 4,
            "timestamp": int(time.time() * 1000)
        }
        return Json(self.postRequest(f"/x{self.comId}/s/notice", data))

    def ban(self, userId: str, reason: str, banType: typing.Optional[int] = None) -> Json:
        """Ban a community member.

        Parameters
        ----------
        userId : `str`
            The user ID to ban.
        reason : `str`
            The reason for the ban.
        banType : `int`, `optional`
            The ban type. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "reasonType": banType,
            "note": {"content": reason},
            "timestamp": int(time.time() * 1000),
        }
        return Json(self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/ban", data))

    def unban(self, userId: str, note: str) -> Json:
        """Unban a community member.

        Parameters
        ----------
        userId : `str`
            The user ID to unban.
        note : `str`
            The note to the banned user.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "note": {"content": note},
            "timestamp": int(time.time() * 1000)
        }
        return Json(self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/unban", data))

    @typing.overload
    def hide(self, blogId: str, *, note: typing.Optional[str] = None) -> Json: ...
    @typing.overload
    def hide(self, *, wikiId: str, note: typing.Optional[str] = None) -> Json: ...
    @typing.overload
    def hide(self, *, chatId: str, note: typing.Optional[str] = None) -> Json: ...
    @typing.overload
    def hide(self, *, userId: str, note: typing.Optional[str] = None) -> Json: ...
    def hide(
        self,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        chatId: typing.Optional[str] = None,
        userId: typing.Optional[str] = None,
        note: typing.Optional[str] = None
    ) -> Json:
        """Hide a blog, wiki, chat or user.

        Parameters
        ----------
        blogId : `str`, `optional`
            The blog ID to hide. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID to hide. Default is `None`.
        chatId : `str`, `optional`
            The chat ID to hide. Default is `None`.
        userId : `str`, `optional`
            The user ID to hide. Default is `None`.
        note : `str`, `optional`
            The note for the hide. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId, chatId and userId are not provided.

        """
        data: typing.Dict[str, typing.Any] = {
            "adminOpName": 18 if userId else 110,
            "adminOpValue": None if userId else 9,
            "timestamp": int(time.time() * 1000),
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
        return Json(self.postRequest(link, data))

    @typing.overload
    def unhide(self, blogId: str, *, note: typing.Optional[str] = None) -> Json: ...
    @typing.overload
    def unhide(self, *, wikiId: str, note: typing.Optional[str] = None) -> Json: ...
    @typing.overload
    def unhide(self, *, chatId: str, note: typing.Optional[str] = None) -> Json: ...
    @typing.overload
    def unhide(self, *, userId: str, note: typing.Optional[str] = None) -> Json: ...
    def unhide(
        self,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        chatId: typing.Optional[str] = None,
        userId: typing.Optional[str] = None,
        note: typing.Optional[str] = None
    ) -> Json:
        """Unhide a blog, wiki, chat or user.

        Parameters
        ----------
        blogId : `str`, `optional`
            The blog ID to unhide. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID to unhide. Default is `None`.
        chatId : `str`, `optional`
            The chat ID to unhide. Default is `None`.
        userId : `str`, `optional`
            The user ID to unhide. Default is `None`.
        note : `str`, `optional`
            The note for the unhide. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId, chatId and userId are not provided.

        """
        data: typing.Dict[str, typing.Any] = {
            "adminOpName": 19 if userId else 110,
            "adminOpValue": 0,
            "timestamp": int(time.time() * 1000),
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
        return Json(self.postRequest(link, data))

    def send_warning(self, userId: str, reason: typing.Optional[str] = None) -> Json:
        """Warn a user.

        Parameters
        ----------
        userId : `str`
            The user ID to warn.
        reason : `str`, `optional`
            The warning message.

        Returns
        -------
        Json
            The JSON response.

        """
        data: typing.Dict[str, typing.Any] = {
            "uid": userId,
            "title": "Custom",
            "content": reason,
            "attachedObject": {"objectId": userId, "objectType": 0},
            "penaltyType": 0,
            "adminOpNote": {},
            "noticeType": 7,
            "timestamp": int(time.time() * 1000)
        }
        return Json(self.postRequest(f"/x{self.comId}/s/notice", data))

    def invite_to_voice_chat(self, chatId: str, userId: str) -> Json:
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
        return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/vvchat-presenter/invite", data))

    def post_blog(self, title: str, content: str, fansOnly: bool = False) -> Json:
        """Post a blog.

        Parameters
        ----------
        title : `str`
            The blog title.
        content : `str`
            The blog content.
        fansOnly : `bool`, `optional`
            The blog is for fans only (vip users only). Default is `False`.

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
            "timestamp": int(time.time() * 1000),
        }
        return Json(self.postRequest(f"/x{self.comId}/s/blog", data))

    def post_wiki(
        self,
        title: str,
        content: str,
        fansOnly: bool = False,
        icon: typing.Optional[str] = None,
        backgroundColor: typing.Optional[str] = None,
        keywords: typing.Optional[typing.Union[typing.List[str], str]] = None,
    ) -> Json:
        """Post a wiki.

        Parameters
        ----------
        title : `str`
            The wiki title.
        content : `str`
            The wiki content.
        fansOnly : `bool`, `optional`
            The wiki is for fans only (vip users only). Default is `False`.
        icon : `str`, `optional`
            The wiki icon. Default is `None`.
        backgroundColor : `str`, `optional`
            The wiki background color (hex color). Default is `None`.
        keywords : `list[str]`, `str`, `optional`
            The wiki keywords. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        data: typing.Dict[str, typing.Any] = {
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
            "timestamp": int(time.time() * 1000),
        }
        if icon:
            data["icon"] = icon
        return Json(self.postRequest(f"/x{self.comId}/s/item", data))

    def delete_blog(self, blogId: str) -> Json:
        """Delete a blog.

        Parameters
        ----------
        blogId : `str`
            The blog ID to delete.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(f"/x{self.comId}/s/blog/{blogId}"))

    def delete_wiki(self, wikiId: str) -> Json:
        """Delete a wiki.

        Parameters
        ----------
        wikiId : `str`
            The wiki ID to delete.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(f"/x{self.comId}/s/item/{wikiId}"))

    def activate_status(self, status: int = 1) -> Json:
        """Set the online status.

        Parameters
        ----------
        status : `int`, `optional`
            The online status. Default is `1`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "onlineStatus": status,
            "duration": 86400,
            "timestamp": int(time.time() * 1000),
        }
        return Json(self.postRequest(f"/x{self.comId}/s/user-profile/{self.uid}/online-status", data))

    def subscribe(self, userId: str, autoRenew: bool = False, transactionId: typing.Optional[str] = None) -> Json:
        """Subscribe to the vip user fan club.

        Parameters
        ----------
        userId : `str`
            The vip user ID to subscribe.
        autoRenew : `bool`, `optional`
            Auto renew the subscription. Default is `False`.
        transactionId : `str`, `optional`
            The transaction ID. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        if transactionId is None:
            transactionId = generateTransactionId()
        data = {
            "paymentContext": {
                "transactionId": transactionId,
                "isAutoRenew": autoRenew,
            },
            "timestamp": int(time.time() * 1000),
        }
        return Json(self.postRequest(f"/x{self.comId}/s/influencer/{userId}/subscribe", data))

    def submit_wiki(self, wikiId: str, message: typing.Optional[str] = None) -> Json:
        """Submit a wiki to curate.

        Parameters
        ----------
        wikiId : `str`
            The wiki ID to submit.
        message : `str`, `optional`
            The submit message. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "message": message,
            "itemId": wikiId,
            "timestamp": int(time.time() * 1000),
        }
        return Json(self.postRequest(f"/x{self.comId}/s/knowledge-base-request", data))

    def edit_blog(
        self,
        title: str,
        content: str,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        fansOnly: bool = False,
        backgroundColor: typing.Optional[str] = None,
        media: typing.Optional[typing.List[str]] = None,
    ) -> Json:
        """Edit a blog or wiki.

        Parameters
        ----------
        title : `str`
            The post title.
        content : `str`
            The post content.
        blogId : `str`, `optional`
            The blog ID to edit. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID to edit. Default is `None`.
        fansOnly : `bool`, `optional`
            The post is for fans only (vip users only). Default is `False`.
        backgroundColor : str, `optional`
            The hex color. Default is `None`.
        media : `list[str]`, `optional`
            The media url list. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If no blogId or wikiId are not provided.

        """
        data: typing.Dict[str, typing.Any] = {
            "title": title,
            "content": content,
            "timestamp": int(time.time() * 1000)
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
        return Json(self.postRequest(link, data))

    def get_chat_bubbles(self, start: int = 0, size: int = 25) -> BubbleList:
        """Get user's chat bubble list.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        BubbleList
            The chat bubble list object.

        """
        return BubbleList(self.getRequest(f"/x{self.comId}/s/chat/chat-bubble?type=all-my-bubbles&start={start}&size={size}")["chatBubbleList"]).BubbleList

    def select_bubble(self, bubbleId: str, applyToAll: bool = False, chatId: typing.Optional[str] = None) -> Json:
        """Apply a chat bubble.

        Parameters
        ----------
        bubbleId : `str`
            The chat bubble ID to apply.
        applyToAll : `bool`, `optional`
            Apply to all chats. Default is `False`.
        chatId : `str`, `optional`
            The chat ID to apply. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "bubbleId": bubbleId,
            "applyToAll": applyToAll.real,
            "timestamp": int(time.time() * 1000),
        }
        if chatId and not applyToAll:
            data["threadId"] = chatId
        return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/apply-bubble"))

    def delete_chat_bubble(self, bubbleId: str) -> Json:
        """Delete a custom chat bubble.

        Parameters
        ----------
        bubbleId : `str`
            The chat bubble ID to delete.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(url=f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}"))

    def get_chat_bubble_templates(self, start: int = 0, size: int = 25) -> BubbleTemplates:
        """Get chat bubble template list.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        BubbleTemplates
            The chat bubble list object.

        """
        return BubbleTemplates(self.getRequest(f"/x{self.comId}/s/chat/chat-bubble/templates?start={start}&size={size}")["templateList"])

    def upload_custom_bubble(self, templateId: str) -> Json:
        """Upload a custom chat bubble.

        Parameters
        ----------
        templateId : `str`
            The template ID to upload.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.postRequest(f"/x{self.comId}/s/chat/chat-bubble/templates/{templateId}/generate"))

    def kick(self, chatId: str, userId: str, rejoin: bool = True) -> Json:
        """Kick a user from a chat.

        Parameters
        ----------
        chatId : `str`
            The chat ID associated with the user.
        userId : `str`
            The user ID to kick.
        rejoin : `bool`, `optional`
            Allow the user to rejoin the chat. Default is `True`.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(f"/x{self.comId}/s/chat/thread/{chatId}/member/{userId}?allowRejoin={rejoin.real}"))

    def block(self, userId: str) -> Json:
        """Block a user.

        Parameters
        ----------
        userId : `str`
            The user ID to block.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.postRequest(f"/x{self.comId}/s/block/{userId}"))

    @typing.overload
    def flag(self, reason: str, blogId: str, *, flagType: int = 0) -> Json: ...
    @typing.overload
    def flag(self, reason: str, *, wikiId: str, flagType: int = 0) -> Json: ...
    @typing.overload
    def flag(self, reason: str, *, userId: str, flagType: int = 0) -> Json: ...
    def flag(
        self,
        reason: str,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        userId: typing.Optional[str] = None,
        flagType: int = 0
    ) -> Json:
        """Flag a post or user.

        Parameters
        ----------
        reason : `str`
            The reason of the flag.
        blogId : `str`, `optional`
            The blog ID to flag.
        wikiId : `str`, `optional`
            The wiki ID to flag.
        userId : `str`, `optional`
            The user ID to flag.
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

        Raises
        ------
        ValueError
            If the blogId, wikiId and userId are not provided.

        """
        data = {
            "message": reason,
            "flagType": flagType,
            "timestamp": int(time.time() * 1000)
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
        return Json(self.postRequest(f"/x{self.comId}/s/flag", data))

    # thanks to V¡ktor#9475 for ideas
    def send_active_time(self, tz: int = 0, timers: typing.Optional[typing.List[typing.Dict[typing.Literal["start", "end"], int]]] = None) -> Json:
        """Send user active time.

        Parameters
        ----------
        tz : `int`, `optional`
            The timezone (utc * 60). Default is `0`.
        timers : `list[dict[str, int]]`, `optional`
            The active chunk list. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "userActiveTimeChunkList": timers if timers else active_time(minutes=5),
            "timestamp": int(time.time() * 1000),
            "optInAdsFlags": 2147483647,
            "timezone": tz,
        }
        return Json(self.postRequest(f"/x{self.comId}/s/community/stats/user-active-time", data, minify=True))

    def transfer_host(self, chatId: str, userIds: str) -> Json:
        """Transfer the chat host title.

        Parameters
        ----------
        chatId : `str`
            The chat ID associated with the host.
        userIds : `list[str]`, `str`
            The user ID or user ID list to transfer.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "uidList": [userIds],
            "timestamp": int(time.time() * 1000)
        }
        return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer", data))

    def accept_host(self, chatId: str, requestId: str) -> Json:
        """Accept the transfer host request.

        Parameters
        ----------
        chatId : `str`
            The chat ID associated with the host.
        requestId : `str`
            The host request ID to accept.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"timestamp": int(time.time() * 1000)}
        return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept", data))

    def set_cohost(self, chatId: str, userId: typing.Union[str, typing.List[str]]) -> Json:
        """Add a new chat co-host.

        Parameters
        ----------
        chatId : `str`
            The chat ID to add the co-host.
        userId : `list[str]`, `str`
            The user ID or user ID list to add.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "uidList": userId if isinstance(userId, list) else [userId],
            "timestamp": int(time.time() * 1000)
        }
        return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/co-host", data))

    def del_cohost(self, chatId : str, userId : str) -> Json:
        """Remove a chat co-host.

        Parameters
        ----------
        chatId : `str`
            The chat ID to remove the co-host.
        userId : `str`
            The co-host user ID to remove.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(f"/x{self.comId}/s/chat/thread/{chatId}/co-host/{userId}"))

    def get_quizzes(
        self,
        quizType: typing.Literal["best", "trending", "recent"] = "recent",
        start: int = 0,
        size: int = 25
    ) -> BlogList:
        """Get community quiz list.

        Parameters
        ----------
        quizType : `str`, `optional`
            The quiz filter type (best, trending, recent). Default is 'recent'.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

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
        return BlogList(self.getRequest(link)["blogList"]).BlogList

    def get_quiz_questions(self, quizId: str) -> QuizQuestionList:
        """Get quiz question list.

        Parameters
        ----------
        quizId : `str`
            The quiz ID.

        Returns
        -------
        QuizQuestionList
            The question list object.

        """
        return QuizQuestionList(self.getRequest(f"/x{self.comId}/s/blog/{quizId}?action=review")["blog"]["quizQuestionList"]).QuizQuestionList

    def play_quiz(self, quizId: str, questions: typing.List[str], answers: typing.List[str], mode: typing.Literal[0, 1] = 0) -> Json:
        """Play a quiz.

        Parameters
        ----------
        quizId : `str`
            The quiz ID to play.
        questions : `list[str]`
            The questionId list.
        answers : list[str]
            The optionId list.
        mode : `int`, `optional`
            Play mode. Default is `0`.
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
            "timestamp": int(time.time() * 1000),
        }
        return Json(self.postRequest(f"/x{self.comId}/s/blog/{quizId}/quiz/result", data))

    def get_quiz_rankings(self, quizId: str, start: int = 0, size: int = 25) -> QuizRankings:
        """Get quiz ranking list.

        Parameters
        ----------
        quizId : `str`
            The quiz ID.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        QuizRankings
            The quiz ranking list object.

        """
        return QuizRankings(self.getRequest(f"/x{self.comId}/s/blog/{quizId}/quiz/result?start={start}&size={size}")).QuizRankings

    def search_user(self, username: str, start: int = 0, size: int = 25) -> UserProfileList:
        """Search user in the community.

        Parameters
        ----------
        username : `str`
            The user nickname.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        UserProfileList
            The search result object.

        """
        return UserProfileList(self.getRequest(f"/x{self.comId}/s/user-profile?type=name&q={username}&start={start}&size={size}")["userProfileList"]).UserProfileList

    def search_blog(self, words: str, start: int = 0, size: int = 25) -> BlogList:
        """Search blog in the community by keywords.

        Parameters
        ----------
        words : `str`
            The quiz keyword.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        BlogList
            The search result object.

        """
        return BlogList(self.getRequest(f"/x{self.comId}/s/blog?type=keywords&q={words}&start={start}&size={size}")["blogList"]).BlogList

    def get_notifications(self, start: int = 0, size: int = 25, pagingType: str = "t") -> NotificationList:
        """Get community notification list.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).
        pagingType : `str`, `optional`
            The paging type to return. Default is 't'.

        Returns
        -------
        NotificationList
            The notification list object.

        """
        return NotificationList(self.getRequest(f"/x{self.comId}/s/notification?pagingType={pagingType}&start={start}&size={size}")).NotificationList

    def get_notices(self, start: int = 0, size: int = 25, noticeType: str = "usersV2", status: int = 1) -> NoticeList:
        """Get community notice list.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).
        noticeType : `str`, `optional`
            The notice type to return. Default is 'usersV2'
        status : `int`, `optional`
            The notice status. Default is `1`

        Returns
        -------
        NoticeList
            The notice list object.

        """
        return NoticeList(self.getRequest(f"/x{self.comId}/s/notice?type={noticeType}&status={status}&start={start}&size={size}")).NoticeList

    def accept_promotion(self, requestId: str) -> Json:
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
        return Json(self.postRequest(f"/x{self.comId}/s/notice/{requestId}/accept"))

    def decline_promotion(self, requestId: str) -> Json:
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
        return Json(self.postRequest(f"/x{self.comId}/s/notice/{requestId}/decline"))

    def sendWebActive(self) -> Json:
        """Send active time as web client.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"ndcId": self.comId}
        return Json(self.postRequest("/community/stats/web-user-active-time", data, webRequest=True))

    def get_recent_blogs(self, pageToken: typing.Optional[str] = None, start: int = 0, size: int = 25) -> BlogList:
        """Get community recent blog list.

        Parameters
        ----------
        pageToken : `str`, `optional`
            The next or previous page token. Default is `None`.
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        RecentBlogs
            The recent blog list object.

        """
        return RecentBlogs(self.getRequest(f"/x{self.comId}/s/feed/blog-all?pagingType=t&start={start}&size={size}&pageToken={pageToken}")["BlogList"]).RecentBlogs

    @typing.overload
    def publish_to_featured(self, blogId: str, *, duration: typing.Literal[1, 2, 3] = 1) -> Json: ...
    @typing.overload
    def publish_to_featured(self, *, wikiId: str, duration: typing.Literal[1, 2, 3] = 1) -> Json: ...
    @typing.overload
    def publish_to_featured(self, *, chatId: str, duration: typing.Literal[1, 2, 3] = 1) -> Json: ...
    @typing.overload
    def publish_to_featured(self, *, userId: str, duration: typing.Literal[1, 2, 3] = 1) -> Json: ...
    def publish_to_featured(
        self,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        chatId: typing.Optional[str] = None,
        userId: typing.Optional[str] = None,
        duration: typing.Literal[1, 2, 3] = 1
    ) -> Json:
        """Feature a blog, wiki, chat or user.

        Parameters
        ----------
        duration : `int`, `optional`
            The feature duration (1, 2, 3). Default is `1`.
        blogId : `str`, `optional`
            The blog ID to feature. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID to feature. Default is `None`.
        chatId : `str`, `optional`
            The chat ID to feature. Default is `None`.
        userId : `str`, `optional`
            The user ID to feature. Default is `None`.

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the blogId, wikiId, chatId and userId are not provided.

        """
        data: typing.Dict[str, typing.Any] = {
            "adminOpName": 114,
            "adminOpValue": {"featuredDuration": duration * (3600 if chatId else 86400)},
            "timestamp": int(time.time() * 1000),
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
        return Json(self.postRequest(f"/x{self.comId}/s/{endpoint}/admin", data))

    @typing.overload
    def remove_from_featured(self, blogId: str) -> Json: ...
    @typing.overload
    def remove_from_featured(self, *, wikiId: str) -> Json: ...
    @typing.overload
    def remove_from_featured(self, *, chatId: str) -> Json: ...
    @typing.overload
    def remove_from_featured(self, *, userId: str) -> Json: ...
    def remove_from_featured(
        self,
        blogId: typing.Optional[str] = None,
        wikiId: typing.Optional[str] = None,
        chatId: typing.Optional[str] = None,
        userId: typing.Optional[str] = None
    ) -> Json:
        """Remove a blog, wiki, chat or user from featured.

        Parameters
        ----------
        blogId : `str`, `optional`
            The blog ID to unfeature. Default is `None`.
        wikiId : `str`, `optional`
            The wiki ID to unfeature. Default is `None`.
        chatId : `str`, `optional`
            The chat ID to unfeature. Default is `None`.
        userId : `str`, `optional`
            The user ID to unfeature. Default is `None`.

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
            "timestamp": int(time.time() * 1000),
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
        return Json(self.postRequest(f"/x{self.comId}/s/{endpoint}/admin", data))
