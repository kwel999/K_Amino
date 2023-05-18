import os
from base64 import b64encode
from binascii import hexlify
from time import time as timestamp
from time import timezone as timezones
from typing import Union, BinaryIO
from uuid import UUID

from ..lib.objects import *
from ..lib.sessions import Session
from .acm import Acm


class SubClient(Acm, Session):
    def __init__(self, comId: str, proxies: dict = None, acm: bool = False):
        self.proxies = proxies
        self.comId = comId

        if acm:
            Acm.__init__(self, comId=self.comId, proxies=self.proxies)
        else:
            Session.__init__(self, proxies=self.proxies)

    def get_video_rep_info(self, chatId: str):
        req = self.getRequest(
            f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation"
        )
        return RepInfo(req)

    def claim_video_rep(self, chatId: str):
        req = self.postRequest(
            f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation"
        )
        return RepInfo(req)

    def join_chat(self, chatId: str = None):
        req = self.postRequest(
            f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}"
        )
        return Json(req)

    def upload_media(self, file: BinaryIO, fileType: str):
        if fileType == "audio":
            fileType = "audio/aac"
        elif fileType == "image":
            fileType = "image/jpg"
        else:
            raise TypeError(fileType)

        data = file.read()
        newHeaders = {"content-type": fileType, "content-length": str(len(data))}

        req = self.postRequest("/g/s/media/upload", data=data, newHeaders=newHeaders)
        return req["mediaValue"]

    def leave_chat(self, chatId: str = None):
        req = self.deleteRequest(
            f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}"
        )
        return Json(req)

    def get_member_following(self, userId: str = None, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/user-profile/{userId}/joined?start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_member_followers(self, userId: str = None, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/user-profile/{userId}/member?start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_chat_threads(self, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/chat/thread?type=joined-me&start={start}&size={size}"
        )
        return ThreadList(req["threadList"]).ThreadList

    def get_member_visitors(self, userId: str, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/user-profile/{userId}/visitors?start={start}&size={size}"
        )
        return VisitorsList(req["visitors"]).VisitorsList

    def get_chat_messages(self, chatId: str, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/chat/thread/{chatId}/message?v=2&pagingType=t&size={size}"
        )
        return MessageList(req["messageList"]).MessageList

    def get_user_info(self, userId: str):
        req = self.getRequest(f"/x{self.comId}/s/user-profile/{userId}")
        return UserProfile(req["userProfile"]).UserProfile

    def get_user_blogs(self, userId: str, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/blog?type=user&q={userId}&start={start}&size={size}"
        )
        return BlogList(req["blogList"]).BlogList

    def get_user_wikis(self, userId: str, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/item?type=user-all&start={start}&size={size}&cv=1.2&uid={userId}"
        )
        return WikiList(req["itemList"]).WikiList

    def get_all_users(self, usersType: str = "recent", start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/user-profile?type={usersType}&start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_chat_members(self, start: int = 0, size: int = 25, chatId: str = None):
        req = self.getRequest(
            f"/x{self.comId}/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2"
        )
        return UserProfileList(req["memberList"]).UserProfileList

    def get_chat_info(self, chatId: str):
        req = self.getRequest(f"/x{self.comId}/s/chat/thread/{chatId}")
        return Thread(req["thread"]).Thread

    def get_online_users(self, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:online-members&start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def get_public_chats(
        self, filterType: str = "recommended", start: int = 0, size: int = 50
    ):
        req = self.getRequest(
            f"/x{self.comId}/s/chat/thread?type=public-all&filterType={filterType}&start={start}&size={size}"
        )
        return ThreadList(req["threadList"]).ThreadList

    def full_embed(self, link: str, image: BinaryIO, message: str, chatId: str):
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
        return Json(self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message", data))

    def send_message(
        self,
        chatId: str,
        message: str = None,
        messageType: int = 0,
        file: BinaryIO = None,
        fileType: str = None,
        replyTo: str = None,
        mentionUserIds: Union[list, str] = None,
        stickerId: str = None,
        snippetLink: str = None,
        ytVideo: str = None,
        snippetImage: BinaryIO = None,
        embedId: str = None,
        embedType: int = None,
        embedLink: str = None,
        embedTitle: str = None,
        embedContent: str = None,
        embedImage: BinaryIO = None,
    ):

        if message is not None and file is None:
            message = message.replace("[@", "‎‏").replace("@]", "‬‭")

        mentions = []
        if mentionUserIds:
            if isinstance(mentionUserIds, list):
                for mention_uid in mentionUserIds:
                    mentions.append({"uid": mention_uid})
            mentions.append({"uid": mentionUserIds})

        if embedImage:
            if not isinstance(embedImage, str):
                embedImage = [[100, self.upload_image(embedImage, "image"), None]]
            embedImage = [[100, embedImage, None]]

        data = {
            "type": messageType,
            "content": message,
            "attachedObject": {
                "objectId": embedId,
                "objectType": embedType,
                "link": embedLink,
                "title": embedTitle,
                "content": embedContent,
                "mediaList": embedImage,
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
                    "mediaUploadValueContentType": "image/png",
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
                data["mediaUploadValueContentType"] = "image/jpg"
                data["mediaUhqEnabled"] = False

            elif fileType == "gif":
                data["mediaType"] = 100
                data["mediaUploadValueContentType"] = "image/gif"
                data["mediaUhqEnabled"] = False

            else:
                raise TypeError(fileType)

            data["mediaUploadValue"] = b64encode(file.read()).decode()
            data["attachedObject"] = None
            data["extensions"] = None

        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/message", data)
        return Json(req)

    def send_web_message(
        self,
        chatId: str,
        message: str = None,
        messageType: int = 0,
        icon: str = None,
        comId: str = None,
    ):
        if comId:
            self.comId = comId

        data = {
            "ndcId": f"x{self.comId}",
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

        return Json(self.postRequest("/add-chat-message", data, webRequest=True))

    def unfollow(self, userId: str):
        req = self.postRequest(
            f"/x{self.comId}/s/user-profile/{userId}/member/{self.uid}"
        )
        return Json(req)

    def follow(self, userId: Union[str, list]):
        data = {"timestamp": int(timestamp() * 1000)}

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
        title: str = None,
        message: str = None,
        content: str = None,
        chatType: int = 0,
    ):
        if isinstance(userId, str):
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

    def invite_to_chat(self, userId: Union[str, list], chatId: str = None):
        if isinstance(userId, str):
            userId = [userId]

        data = {"uids": userId, "timestamp": int(timestamp() * 1000)}

        req = self.postRequest(
            f"/x{self.comId}/s/chat/thread/{chatId}/member/invite", data=data
        )
        return Json(req)

    def edit_profile(
        self,
        nickname: str = None,
        content: str = None,
        icon: BinaryIO = None,
        backgroundColor: str = None,
        backgroundImage: str = None,
        defaultBubbleId: str = None,
    ):
        data = {
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
            data["extensions"] = {"defaultBubbleId": defaultBubbleId}
        if backgroundColor:
            data["extensions"]["style"]["backgroundColor"] = backgroundColor
        if backgroundImage:
            data["extensions"]["style"]["backgroundMediaList"] = [
                [100, backgroundImage, None, None, None]
            ]

        req = self.postRequest(f"/x{self.comId}/s/user-profile/{self.uid}", data)
        return Json(req)

    def edit_chat(
        self,
        chatId: str,
        title: str = None,
        content: str = None,
        icon: str = None,
        background: str = None,
        keywords: list = None,
        announcement: str = None,
        pinAnnouncement: bool = None,
    ):
        res, data = [], {"timestamp": int(timestamp() * 1000)}

        if title:
            data["title"] = title
        if content:
            data["content"] = content
        if icon:
            data["icon"] = icon
        if keywords:
            data["keywords"] = keywords
        if announcement:
            data["extensions"]["announcement"] = announcement
        if pinAnnouncement:
            data["extensions"]["pinAnnouncement"] = pinAnnouncement
        if background:
            data = {
                "media": [100, background, None],
                "timestamp": int(timestamp() * 1000),
            }
            req = self.postRequest(
                f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}/background",
                data,
            )
            res.append(Json(req))

        req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}", data)
        res.append(Json(req))

        return res

    def chat_settings(
        self,
        chatId: str,
        viewOnly: bool = False,
        doNotDisturb: bool = True,
        canInvite: bool = False,
        canTip: bool = None,
        pin: bool = None,
        coHosts: Union[str, list] = None,
    ):
        res = []

        if doNotDisturb:
            if doNotDisturb:
                opt = 2
            else:
                opt = 1

            data = {"alertOption": opt, "timestamp": int(timestamp() * 1000)}
            req = self.postRequest(
                f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}/alert", data
            )
            res.append(Json(req))

        if viewOnly:
            if viewOnly:
                viewOnly = "enable"
            else:
                viewOnly = "disable"

            req = self.postRequest(
                f"/x{self.comId}/s/chat/thread/{chatId}/view-only/{viewOnly}"
            )
            res.append(Json(req))

        if canInvite:
            if canInvite:
                canInvite = "enable"
            else:
                canInvite = "disable"

            req = self.postRequest(
                f"/x{self.comId}/s/chat/thread/{chatId}/members-can-invite/{canInvite}"
            )
            res.append(Json(req))

        if canTip:
            if canTip:
                canTip = "enable"
            else:
                canTip = "disable"
            req = self.postRequest(
                f"/x{self.comId}/s/chat/thread/{chatId}/tipping-perm-status/{canTip}"
            )
            res.append(Json(req))

        if pin:
            if pin:
                pin = "pin"
            else:
                pin = "unpin"

            req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/{pin}")
            res.append(Json(req))

        if coHosts:
            data = {"uidList": coHosts, "timestamp": int(timestamp() * 1000)}
            req = self.postRequest(f"{self.comId}/s/chat/thread/{chatId}/co-host", data)
            res.append(Json(req))

        return res

    def like_blog(self, blogId: str = None, wikiId: str = None):
        data = {"value": 4, "timestamp": int(timestamp() * 1000)}

        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/vote?cv=1.2&value=4"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/vote?cv=1.2&value=4"
        else:
            raise TypeError("Please put wiki or blog Id")

        req = self.postRequest(link, data)
        return Json(req)

    def unlike_blog(self, blogId: str = None, wikiId: str = None):
        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/vote?eventSource=FeedList"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/vote?eventSource=FeedList"
        else:
            raise TypeError("Please put wikiId or blogId")

        req = self.deleteRequest(link)
        return Json(req)

    def change_titles(self, userId: str, titles: list, colors: list):
        t = []
        for title, color in zip(titles, colors):
            t.append({"title": title, "color": color})
        data = {
            "adminOpName": 207,
            "adminOpValue": {"titles": t},
            "timestamp": int(timestamp() * 1000),
        }

        req = self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
        return Json(req)

    def like_comment(
        self, commentId: str, blogId: str = None, wikiId: str = None, userId: str = None
    ):
        data = {"value": 1}

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
            raise TypeError("Please put a wiki or user or blog Id")

        req = self.postRequest(link, data)
        return Json(req)

    def unlike_comment(
        self, commentId: str, blogId: str = None, wikiId: str = None, userId: str = None
    ):
        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}/g-vote?eventSource=PostDetailView"
        elif userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView"
        else:
            raise TypeError("Please put a wiki or user or blog Id")

        req = self.deleteRequest(link)
        return Json(req)

    def comment(
        self,
        comment: str,
        userId: str = None,
        blogId: str = None,
        wikiId: str = None,
        replyTo: str = None,
        isGuest: bool = False,
    ):
        data = {"content": comment, "timestamp": int(timestamp() * 1000)}

        if replyTo:
            data["respondTo"] = replyTo
        if isGuest:
            comType = "g-comment"
        else:
            comType = "comment"

        if userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/{comType}"
        elif blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/{comType}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/{comType}"
        else:
            raise TypeError("Please put a wiki or user or blog Id")

        req = self.postRequest(link, data)
        return Json(req)

    def delete_comment(
        self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None
    ):
        if userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}"
        elif blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}"
        else:
            raise TypeError("Please put blog or wiki or user Id")

        req = self.deleteRequest(link)
        return Json(req)

    def edit_comment(
        self,
        commentId: str,
        comment: str,
        userId: str = None,
        blogId: str = None,
        wikiId: str = None,
        replyTo: str = None,
        isGuest: bool = False,
    ):
        data = {"content": comment, "timestamp": int(timestamp() * 1000)}
        if replyTo:
            data["respondTo"] = replyTo
        if isGuest:
            comType = "g-comment"
        else:
            comType = "comment"

        if userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/{comType}/{commentId}"
        elif blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/{comType}/{commentId}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/{comType}/{commentId}"
        else:
            raise TypeError("Please put blog or wiki or user Id")

        req = self.postRequest(link, data)
        return Comment(req).Comments

    def get_comment_info(
        self,
        commentId: str,
        userId: str = None,
        blogId: str = None,
        wikiId: str = None,
        isGuest: bool = False,
    ):
        if isGuest:
            comType = "g-comment"
        else:
            comType = "comment"

        if userId:
            link = f"/x{self.comId}/s/user-profile/{userId}/{comType}/{commentId}"
        elif blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/{comType}/{commentId}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/{comType}/{commentId}"
        else:
            raise TypeError("Please put blog or wiki or user Id")

        req = self.getRequest(link)
        return Comment(req).Comments

    def get_wall_comments(
        self, userId: str, sorting: str = "newest", start: int = 0, size: int = 25
    ):
        sorting = sorting.lower().replace("top", "vote")
        if sorting not in ["newest", "oldest", "vote"]:
            raise TypeError("حط تايب يا حمار")

        req = self.getRequest(
            f"/x{self.comId}/s/user-profile/{userId}/comment?sort={sorting}&start={start}&size={size}"
        )
        return CommentList(req["commentList"]).CommentList

    def get_blog_comments(
        self,
        wikiId: str = None,
        blogId: str = None,
        quizId: str = None,
        sorting: str = "newest",
        size: int = 25,
        start: int = 0,
    ):
        sorting = sorting.lower().replace("top", "vote")
        if sorting not in ["newest", "oldest", "vote"]:
            raise TypeError("حط تايب يا حمار")

        if quizId:
            blogId = quizId
        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}"
        else:
            raise TypeError("Please choose a wiki or a blog")

        req = self.getRequest(link)
        return CommentList(req["commentList"]).CommentList

    def vote_comment(self, blogId: str, commentId: str, value: bool = True):
        if value:
            value = 1
        else:
            value = -1

        data = {"value": value, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(
            f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=1",
            data,
        )
        return Json(req)

    def vote_poll(self, blogId: str, optionId: str):
        data = {"value": 1, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(
            f"/x{self.comId}/s/blog/{blogId}/poll/option/{optionId}/vote", data
        )
        return Json(req)

    def get_blog_info(
        self, blogId: str = None, wikiId: str = None, folderId: str = None
    ):
        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}"
        elif folderId:
            link = f"/x{self.comId}/s/shared-folder/files/{folderId}"
        else:
            raise TypeError("Please put a wiki or blog Id")

        req = self.getRequest(link)
        return GetInfo(req).GetInfo

    def get_blogs(self, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/feed/featured?start={start}&size={size}"
        )
        return BlogList(req["featuredList"]).BlogList

    def get_blogs_more(self, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/feed/featured-more?start={start}&size={size}"
        )
        return BlogList(req["blogList"]).BlogList

    def get_blogs_all(self, start: int = 0, size: int = 25, pagingType: str = "t"):
        req = self.getRequest(
            f"/x{self.comId}/s/feed/blog-all?pagingType={pagingType}&start={start}&size={size}"
        )
        return RecentBlogs(req["blogList"]).RecentBlogs

    def tip_coins(
        self,
        coins: int,
        chatId: str = None,
        blogId: str = None,
        wikiId: str = None,
        transactionId: str = None,
    ):
        if transactionId is None:
            transactionId = str(UUID(hexlify(os.urandom(16)).decode("ascii")))
        data = {
            "coins": int(coins),
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
            raise TypeError("Please put a wiki or chat or blog Id")

        req = self.postRequest(link, data)
        return Json(req)

    def check_in(self, timezone: int = 180):
        data = {"timezone": timezone, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/x{self.comId}/s/check-in", data)
        return Json(req)

    def check_in_lottery(self, timezone: int = 180):
        data = {"timezone": timezone, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/x{self.comId}/s/check-in/lottery", data)
        return Json(req)

    def delete_message(
        self, chatId: str, messageId: str, asStaff: bool = False, reason: str = None
    ):
        data = {"adminOpName": 102, "timestamp": int(timestamp() * 1000)}

        if asStaff and reason:
            data["adminOpNote"] = {"content": reason}
            req = self.postRequest(
                f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}/admin", data
            )
        else:
            req = self.deleteRequest(
                f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}"
            )

        return Json(req)

    def invite_by_host(self, chatId: str, userId: Union[str, list]):
        req = self.postRequest(
            f"/x{self.comId}/s/chat/thread/{chatId}/member/{userId}/invite-av-chat"
        )
        return Json(req)

    def strike(self, userId: str, time: str, title: str = None, reason: str = None):
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

    def ban(self, userId: str, reason: str, banType: int = None):
        data = {
            "reasonType": banType,
            "note": {"content": reason},
            "timestamp": int(timestamp() * 1000),
        }

        req = self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/ban", data)
        return Json(req)

    def unban(self, userId: str, reason: str = "هذا العضو كان شاطر اخر كم يوم"):
        data = {"note": {"content": reason}, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/unban", data)
        return Json(req)

    def hide(
        self,
        note: str = None,
        blogId: str = None,
        userId: str = None,
        wikiId: str = None,
        chatId: str = None,
    ):
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
            raise TypeError("Please put a wiki or user or chat or blog Id")
        if note:
            data["adminOpNote"] = {"content": note}

        req = self.postRequest(link, data)
        return Json(req)

    def unhide(
        self,
        note: str = None,
        blogId: str = None,
        userId: str = None,
        wikiId: str = None,
        chatId: str = None,
    ):
        data = {
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
            raise TypeError("Please put a wiki or user or chat or blog Id")
        if note:
            data["adminOpNote"] = {"content": note}

        req = self.postRequest(link, data)
        return Json(req)

    def send_warning(self, userId: str, reason: str = None):
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

    def invite_to_voice_chat(self, userId: str = None, chatId: str = None):
        data = {"uid": userId, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(
            f"/g/x{self.comId}/chat/thread/{chatId}/vvchat-presenter/invite", data
        )
        return Json(req)

    def post_blog(self, title: str, content: str, fansOnly: bool = False):
        data = {
            "extensions": {"fansOnly": fansOnly},
            "content": content,
            "latitude": 0,
            "longitude": 0,
            "title": title,
            "type": 0,
            "contentLanguage": "ar",
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
        icon: str = None,
        backgroundColor: str = None,
        keywords: Union[str, list] = None,
    ):
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

    def delete_blog(self, blogId: str):
        req = self.deleteRequest(f"/x{self.comId}/s/blog/{blogId}")
        return Json(req)

    def delete_wiki(self, wikiId: str):
        req = self.deleteRequest(f"/x{self.comId}/s/item/{wikiId}")
        return Json(req)

    def activate_status(self, status: int = 1):
        data = {
            "onlineStatus": status,
            "duration": 86400,
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(
            f"/x{self.comId}/s/user-profile/{self.uid}/online-status", data
        )
        return Json(req)

    def subscribe(self, userId: str, autoRenew: str = False, transactionId: str = None):
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

    def submit_wiki(self, wikiId: str, message: str = None):
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
        blogId: str = None,
        wikiId: str = None,
        fansOnly: bool = False,
        backgroundColor: str = None,
        media: list = None,
    ):
        data = {
            "title": title,
            "content": content,
            "timestamp": int(timestamp() * 1000),
        }

        if media:
            data["mediaList"] = [[100, media, None, "XYZ", None, {"fileName": "Amino"}]]
        if fansOnly:
            data["extensions"]["fansOnly"] = True
        if backgroundColor:
            data["extensions"] = {"backgroundColor": backgroundColor}

        if blogId:
            link = f"/x{self.comId}/s/blog/{blogId}"
        elif wikiId:
            link = f"/x{self.comId}/s/item/{wikiId}"
        else:
            raise TypeError("Please put blogId or wikiId")

        req = self.postRequest(link, data)
        return Json(req)

    def get_chat_bubbles(self, start: int = 0, size: int = 20):
        req = self.getRequest(
            f"/x{self.comId}/s/chat/chat-bubble?type=all-my-bubbles&start={start}&size={size}"
        )
        return BubbleList(req["chatBubbleList"]).BubbleList

    def select_bubble(self, bubbleId: str, apply: int = 0, chatId: str = None):
        data = {
            "bubbleId": bubbleId,
            "applyToAll": apply,
            "timestamp": int(timestamp() * 1000),
        }
        if chatId:
            data["threadId"] = chatId

        req = self.postRequest(f"/x{self.comId}/s/chat/thread/apply-bubble")
        return Json(req)

    def delete_chat_bubble(self, bubbleId: str):
        req = self.deleteRequest(url=f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}")
        return Json(req)

    def get_chat_bubble_templates(self, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/chat/chat-bubble/templates?start={start}&size={size}"
        )
        return BubbleTemplates(req["templateList"])

    def upload_custom_bubble(self, templateId: str):
        req = self.postRequest(
            f"/x{self.comId}/s/chat/chat-bubble/templates/{templateId}/generate"
        )
        return Json(req)

    def kick(self, chatId: str, userId: str, rejoin: bool = True):
        if rejoin:
            rejoin = 1
        if not rejoin:
            rejoin = 0

        req = self.deleteRequest(
            f"/x{self.comId}/s/chat/thread/{chatId}/member/{userId}?allowRejoin={rejoin}"
        )
        return Json(req)

    def block(self, userId: str):
        req = self.postRequest(f"/x{self.comId}/s/block/{userId}")
        return Json(req)

    def flag(
        self,
        reason: str,
        flagType: str = "spam",
        userId: str = None,
        wikiId: str = None,
        blogId: str = None,
    ):
        types = {
            "violence": 106,
            "hate": 107,
            "suicide": 108,
            "troll": 109,
            "nudity": 110,
            "bully": 0,
            "off-topic": 4,
            "spam": 2,
        }

        data = {"message": reason, "timestamp": int(timestamp() * 1000), "flagType": types.get(flagType, 106)}

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
            raise TypeError("choose a certain type to report")

        req = self.postRequest(f"/x{self.comId}/s/flag", data)
        return Json(req)
#thanks to V¡ktor#9475 for ideas
    def send_active_time(self, tz: int = int(-timezones // 1000), timers: list = None):
        data = {
            "userActiveTimeChunkList": timers if timers else [{"start": int(timestamp()), "end": int(timestamp() + 300)}],
            "timestamp": int(timestamp() * 1000),
            "optInAdsFlags": 2147483647,
            "timezone": tz,
        }

        req = self.postRequest(
            f"/x{self.comId}/s/community/stats/user-active-time", data, minify=True
        )
        return Json(req)

    def transfer_host(self, chatId: str, userIds: list):
        data = {"uidList": userIds, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(
            f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer", data
        )
        return Json(req)

    def accept_host(self, chatId: str, requestId: str):
        data = {"timestamp": int(timestamp() * 1000)}
        req = self.postRequest(
            f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept",
            data,
        )
        return Json(req)

    def set_cohost(self, chatId : str, asistent_id : [str, list]):
         data = {
            "uidList": asistent_id,
            "timestamp": int(timestamp() * 1000)
        }

         req = self.postRequest(f"/x{self.comId}/s/chat/thread/{chatId}/co-host", data)
         return Json(req)


    def del_cohost(self, chatId : str, userId : str):
           req = self.deleteRequest(f"/x{self.comId}/s/chat/thread/{chatId}/co-host/{userId}")
           return Json(req)

    def get_quizzes(self, quizzesType: str = "recent", start: int = 0, size: int = 25):
        link = {
            "recent": f"x{self.comId}/s/blog?type=quizzes-recent&start={start}&size={size}",
            "trending": f"x{self.comId}/s/feed/quiz-trending?start={start}&size={size}",
            "best": f"x{self.comId}/s/feed/quiz-best-quizzes?start={start}&size={size}",
        }.get(quizzesType)

        req = self.getRequest(link)
        return BlogList(req["blogList"]).BlogList

    def get_quiz_questions(self, quizId: str):
        req = self.getRequest(f"/x{self.comId}/s/blog/{quizId}?action=review")
        return QuizQuestionList(req["blog"]["quizQuestionList"]).QuizQuestionList

    def play_quiz(self, quizId: str, questions: list, answers: list, mode: int = 0):
        data = {
            "mode": mode,
            "quizAnswerList": [
                {"optIdList": [answer], "quizQuestionId": question, "timeSpent": 0.0}
                for answer, question in zip(answers, questions)
            ],
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{self.comId}/s/blog/{quizId}/quiz/result", data)
        return req

    def get_quiz_rankings(self, quizId: str, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/blog/{quizId}/quiz/result?start={start}&size={size}"
        )
        return QuizRankings(req).QuizRankings

    def search_user(self, username: str, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/user-profile?type=name&q={username}&start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def search_blog(self, words: str, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/blog?type=keywords&q={words}&start={start}&size={size}"
        )
        return BlogList(req["blogList"]).BlogList

    def get_notifications(self, size: int = 25, pagingType: str = "t"):
        req = self.getRequest(
            f"/x{self.comId}/s/notification?pagingType={pagingType}&size={size}"
        )
        return NotificationList(req).NotificationList

    def get_notices(
        self, start: int = 0, size: int = 25, noticeType: str = "usersV2", status: int = 1
    ):
        req = self.getRequest(
            f"/x{self.comId}/s/notice?type={noticeType}&status={status}&start={start}&size={size}"
        )
        return NoticeList(req).NoticeList

    def accept_promotion(self, requestId: str):
        if not isinstance(requestId, str):
            raise TypeError(f"Please use a string not {type(requestId)}")
        req = self.postRequest(f"/x{self.comId}/s/notice/{requestId}/accept")
        return Json(req)

    def decline_promotion(self, requestId: str):
        if not isinstance(requestId, str):
            raise TypeError(f"Please use a string not {type(requestId)}")
        req = self.postRequest(f"/x{self.comId}/s/notice/{requestId}/decline")
        return Json(req)

    def sendWebActive(self):
        data = {"ndcId": self.comId}
        return self.postRequest(
            "/community/stats/web-user-active-time", data, webRequest=True
        )

    def get_recent_blogs(self, pageToken: str = None, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/feed/blog-all?pagingType=t&start={start}&size={size}"
        )
        return RecentBlogs(req["BlogList"]).RecentBlogs

    def publish_to_featured(
        self,
        time: int,
        userId: str = None,
        chatId: str = None,
        blogId: str = None,
        wikiId: str = None,
    ):
        time = (
            {1: 3600, 2: 7200, 3: 10800}.get(time)
            if chatId
            else {1: 86400, 2: 172800, 3: 259200}.get(time)
        )

        data = {
            "adminOpName": 114,
            "adminOpValue": {"featuredDuration": time},
            "timestamp": int(timestamp() * 1000),
        }

        if userId:
            featuredType, endpoint = 4, f"user-profile/{userId}"
        elif blogId:
            featuredType, endpoint = 1, f"blog/{blogId}"
        elif wikiId:
            featuredType, endpoint = 1, f"item/{blogId}"
        elif chatId:
            featuredType, endpoint = 5, f"chat/thread/{chatId}"
        else:
            raise TypeError("Please Specify Object ID")

        data["adminOpValue"]["featuredType"] = featuredType
        req = self.postRequest(f"/x{self.comId}/s/{endpoint}/admin", data)
        return Json(req)

    def remove_from_featured(
        self,
        userId: str = None,
        chatId: str = None,
        blogId: str = None,
        wikiId: str = None,
    ):
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
            raise TypeError("Please Specify Object ID")

        req = self.postRequest(f"/x{self.comId}/s/{endpoint}/admin", data)
        return Json(req)
