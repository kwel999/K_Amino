import asyncio
import os
from binascii import hexlify
from time import time as timestamp
from time import timezone
from typing import Union, BinaryIO
from uuid import UUID

import aiohttp
import ujson as json
from json_minify import json_minify

from ..lib import *
from ..lib.objects import *


class SLocal(Headers):
    def __init__(self, comId: str):
        self.comId = comId
        self.uid = headers.userId

        Headers.__init__(self)

        self.session = aiohttp.ClientSession()
        self.headers = self.app_headers
        self.web_headers = self.web_headers

    async def __aenter__(self) -> "SLocal":
        return self

    async def __aexit__(self, *args) -> None:
        await self.session.close()

    def __del__(self):
        loop = asyncio.get_event_loop()
        try:
            loop.create_task(self._close_session())
        except RuntimeError:
            loop.run_until_complete(self._close_session())

    async def _close_session(self):
        await self.session.close()

    async def get_video_rep_info(self, chatId: str):
        async with self.session.get(api(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return RepInfo((await req.json()))

    async def claim_video_rep(self, chatId: str):
        async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return RepInfo((await req.json()))

    async def join_chat(self, chatId: str = None):
        async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json((await req.json()))

    async def upload_media(self, file: BinaryIO, fileType: str):
        if fileType == "audio": type = "audio/aac"
        elif fileType == "image": type = "image/jpg"
        else: raise TypeError("Wrong fileType")

        data = file.read()
        self.headers["content-type"] = type
        self.headers["content-length"] = str(len(data))

        async with self.session.post(api("/g/s/media/upload"), data=data, headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return (await req.json())["mediaValue"]

    async def leave_chat(self, chatId: str = None):
        async with self.session.delete(api(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json((await req.json()))

    async def get_member_following(self, userId: str = None, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/user-profile/{userId}/joined?start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return UserProfileList((await req.json())["userProfileList"]).UserProfileList

    async def get_member_followers(self, userId: str = None, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/user-profile/{userId}/member?start={start}&size={size}"), headers = self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return UserProfileList((await req.json())["userProfileList"]).UserProfileList

    async def get_chat_threads(self, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/chat/thread?type=joined-me&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return ThreadList((await req.json())["threadList"]).ThreadList

    async def get_member_visitors(self, userId: str, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/user-profile/{userId}/visitors?start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return VisitorsList((await req.json())["visitors"]).VisitorsList

    async def get_chat_messages(self, chatId: str, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/chat/thread/{chatId}/message?v=2&pagingType=t&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return MessageList((await req.json())["messageList"]).MessageList

    async def get_user_info(self, userId: str):
        async with self.session.get(api(f"/x{self.comId}/s/user-profile/{userId}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return UserProfile((await req.json())["userProfile"]).UserProfile

    async def get_all_users(self, type: str = "recent", start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/user-profile?type={type}&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return UserProfileList((await req.json())["userProfileList"]).UserProfileList

    async def get_chat_members(self, start: int = 0, size: int = 25, chatId: str = None):
        async with self.session.get(api(f"/x{self.comId}/s/chat/thread/{chatId}/member?start={start}&size={size}&type=async default&cv=1.2"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return UserProfileList((await req.json())["memberList"]).UserProfileList

    async def get_chat_info(self, chatId: str):
        async with self.session.get(api(f"/x{self.comId}/s/chat/thread/{chatId}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Thread((await req.json())["thread"]).Thread

    async def get_online_users(self, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:online-members&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return UserProfileList((await req.json())["userProfileList"]).UserProfileList

    async def get_public_chats(self, type: str = "recommended", start: int = 0, size: int = 50):
        async with self.session.get(api(f"/x{self.comId}/s/chat/thread?type=public-all&filterType={type}&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return ThreadList((await req.json())["threadList"]).ThreadList

    async def send_message(self, chatId: str, message: str = None, messageType: int = 0, file: BinaryIO = None,
                     fileType: str = None, replyTo: str = None, mentionUserIds: Union[list, str] = None, stickerId: str = None,
                     snippetLink: str = None, ytVideo: str = None, snippetImage: BinaryIO = None, embedId: str = None,
                     embedType: int = None, embedLink: str = None, embedTitle: str = None, embedContent: str = None,
                     embedImage: BinaryIO = None):

        if message is not None and file is None: message = message.replace("[@", "‎‏").replace("@]", "‬‭")

        mentions = []
        if mentionUserIds:
            if type(mentionUserIds) is list:
                for mention_uid in mentionUserIds: mentions.append({"uid": mention_uid})
            mentions.append({"uid": mentionUserIds})

        if embedImage:
            if type(embedImage) is not str: embedImage = [[100, self.upload_image(embedImage, "image"), None]]
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
                "mediaList": embedImage
            },
            "extensions": {"mentionedArray": mentions},
            "clientRefId": int(timestamp() / 10 % 100000000),
            "timestamp": int(timestamp() * 1000)
        }

        if replyTo: data["replyMessageId"] = replyTo

        if stickerId:
            data["content"] = None
            data["stickerId"] = stickerId
            data["type"] = 3

        if snippetLink and snippetImage:
            data["attachedObject"] = None
            data["extensions"]["linkSnippetList"] = [{
                "link": snippetLink,
                "mediaType": 100,
                "mediaUploadValue": base64.b64encode(snippetImage.read()).decode(),
                "mediaUploadValueContentType": "image/png"
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
                data["mediaUploadValueContentType"] = "image/jpg"
                data["mediaUhqEnabled"] = False

            elif fileType == "gif":
                data["mediaType"] = 100
                data["mediaUploadValueContentType"] = "image/gif"
                data["mediaUhqEnabled"] = False

            else: raise TypeError(fileType)

            data["mediaUploadValue"] = base64.b64encode(file.read()).decode()
            data["attachedObject"] = None
            data["extensions"] = None

        data = json.dumps(data)
        async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/message"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def send_web_message(self, chatId: str, message: str = None, messageType: int = 0, icon: str = None, comId: str = None):
        if comId: self.comId = comId

        data = {
            "ndcId": f"x{self.comId}",
            "threadId": chatId,
            "message": {"content": message, "mediaType": 0, "type": messageType, "sendFailed": False, "clientRefId": 0}
        }

        if icon:
            data["message"]["content"] = None
            data["message"]["uploadId"] = 0
            data["message"]["mediaType"] = 100
            data["message"]["mediaValue"] = icon

        async with self.session.post(webApi("/add-chat-message"), json=data, headers=self.web_headers) as req:
            try:
                if (await req.json())["code"] != 200: return CheckExceptions(await req.json())
                else: Json(await req.json())
            except: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def unfollow(self, userId: str):
        async with self.session.post(api(f"/x{self.comId}/s/user-profile/{userId}/member/{self.uid}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def follow(self, userId: Union[str, list]):
        data = {"timestamp": int(timestamp() * 1000)}

        if isinstance(userId, str): 
            url = api(f"/x{self.comId}/s/user-profile/{userId}/member")
        elif isinstance(userId, list):
            url = api(f"/x{self.comId}/s/user-profile/{self.uid}/joined")
            data["targetUidList"] = userId
        else: raise TypeError("Please put str or list of userId")

        data = json.dumps(data)
        async with self.session.post(url, headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def start_chat(self, userId: Union[str, list], title: str = None, message: str = None, content: str = None, type: int = 0):
        if isinstance(userId, list): userIds = userId
        elif isinstance(userId, str): userIds = [userId]

        data = json.dumps({
            "title": title,
            "inviteeUids": userIds,
            "initialMessageContent": message,
            "content": content,
            "type": type,
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/x{self.comId}/s/chat/thread"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def invite_to_chat(self, userId: Union[str, list], chatId: str = None):
        if isinstance(userId, str): userIds = [userId]
        elif isinstance(userId, list): userIds = userId

        data = json.dumps({"uids": userIds, "timestamp": int(timestamp() * 1000)})

        async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/member/invite"), data=data, headers=self.updateHeaders(data=data), ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def edit_profile(self, nickname: str = None, content: str = None, icon: BinaryIO = None, backgroundColor: str = None, backgroundImage: str = None, defaultBubbleId: str = None):
        data = {
            "address": None,
            "latitude": 0,
            "longitude": 0,
            "mediaList": None,
            "eventSource": "UserProfileView",
            "timestamp": int(timestamp() * 1000)
        }

        if nickname: data["nickname"] = nickname
        if icon: data["icon"] = self.upload_media(icon, "image")
        if content: data["content"] = content
        if backgroundColor: data["extensions"]["style"] = {"backgroundColor": backgroundColor}
        if backgroundImage: data["extensions"]["style"] = {"backgroundMediaList": [[100, backgroundImage, None, None, None]]}
        if defaultBubbleId: data["extensions"] = {"async defaultBubbleId": defaultBubbleId}

        data = json.dumps(data)
        async with self.session.post(api(f"/x{self.comId}/s/user-profile/{self.uid}"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def edit_chat(self, chatId: str, title: str = None, content: str = None, icon: str = None, background: str = None, keywords: list = None, announcement: str = None, pinAnnouncement: bool = None):
        res, data = [], {"timestamp": int(timestamp() * 1000)}

        if title: data["title"] = title
        if content: data["content"] = content
        if icon: data["icon"] = icon
        if keywords: data["keywords"] = keywords
        if announcement: data["extensions"]["announcement"] = announcement
        if pinAnnouncement: data["extensions"]["pinAnnouncement"] = pinAnnouncement
        if background:
            data = json.dumps({"media": [100, background, None], "timestamp": int(timestamp() * 1000)})
            async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}/background"), data=data, headers=self.updateHeaders(data=data), ) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json(await req.json()))

        data = json.dumps(data)
        async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}"), data=data, headers=self.updateHeaders(data=data), ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            res.append(Json(await req.json()))
            return res

    async def chat_settings(self, chatId: str, viewOnly: bool = False, doNotDisturb: bool = True, canInvite: bool = False, canTip: bool = None, pin: bool = None, coHosts: Union[str, list] = None):
        res = []

        if doNotDisturb:
            if doNotDisturb: opt = 2
            else: opt = 1

            data = json.dumps({"alertOption": opt, "timestamp": int(timestamp() * 1000)})
            async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.uid}/alert"), data=data, headers=self.updateHeaders(data=data), ) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json(await req.json()))

        if viewOnly:
            if viewOnly: viewOnly = "enable"
            else: viewOnly = "disable"

            async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/view-only/{viewOnly}"), headers=self.headers) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json(await req.json()))

        if canInvite:
            if canInvite: canInvite = "enable"
            else: canInvite = "disable"

            async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/members-can-invite/{canInvite}"), headers=self.headers) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json(await req.json()))

        if canTip:
            if canTip: canTip = "enable"
            else: canTip = "disable"

            async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/tipping-perm-status/{canTip}"), headers=self.headers) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json(await req.json()))

        if pin:
            if pin: pin = "pin"
            else: pin = "unpin"

            async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/{pin}"), headers=self.headers) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json(await req.json()))

        if coHosts:
            data = json.dumps({"uidList": coHosts, "timestamp": int(timestamp() * 1000)})
            async with self.session.post(api(f"{self.comId}/s/chat/thread/{chatId}/co-host"), data=data, headers=self.updateHeaders(data=data)) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json(await req.json()))

        return res

    async def like_blog(self, blogId: str = None, wikiId: str = None):
        data = json.dumps({"value": 4, "timestamp": int(timestamp() * 1000)})

        if blogId: url = api(f"/x{self.comId}/s/blog/{blogId}/vote?cv=1.2&value=4")
        elif wikiId: url = api(f"/x{self.comId}/s/item/{wikiId}/vote?cv=1.2&value=4")
        else: raise TypeError("Please put wiki or blog Id")

        async with self.session.post(url, headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def unlike_blog(self, blogId: str = None, wikiId: str = None):
        if blogId: url = api(f"/x{self.comId}/s/blog/{blogId}/vote?eventSource=FeedList")
        elif wikiId: url = api(f"/x{self.comId}/s/item/{wikiId}/vote?eventSource=FeedList")
        else: raise TypeError("Please put wikiId or blogId")

        async with self.session.delete(url, headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def change_titles(self, userId: str, titles: list, colors: list):
        t = []
        for title, color in zip(titles, colors): t.append({"title": title, "color": color})
        data = json.dumps({"adminOpName": 207, "adminOpValue": {"titles": t}, "timestamp": int(timestamp() * 1000)})
        async with self.session.post(api(f"/x{self.comId}/s/user-profile/{userId}/admin"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def like_comment(self, commentId: str, blogId: str = None, wikiId: str = None, userId: str = None):
        data = {"value": 1}
        if blogId:
            data["eventSource"] = "PostDetailView"
            url = api(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=1")
        elif wikiId:
            data["eventSource"] = "PostDetailView"
            url = api(f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}/vote?cv=1.2&value=1")
        elif userId:
            data["eventSource"] = "UserProfileView"
            url = api(f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}/vote?cv=1.2&value=1")
        else: raise TypeError("Please put a wiki or user or blog Id")

        data = json.dumps(data)
        async with self.session.post(url, data=data, headers=self.updateHeaders(data=data)) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def unlike_comment(self, commentId: str, blogId: str = None, wikiId: str = None, userId: str = None):
        if blogId: url = api(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView")
        elif wikiId: url = api(f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}/g-vote?eventSource=PostDetailView")
        elif userId: url = api(f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView")
        else: raise TypeError("Please put a wiki or user or blog Id")

        async with self.session.delete(url, headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def comment(self, comment: str, userId: str = None, blogId: str = None, wikiId: str = None, replyTo: str = None, isGuest: bool = False):
        data = {"content": comment, "timestamp": int(timestamp() * 1000)}

        if replyTo: data["respondTo"] = replyTo
        if isGuest: comType = "g-comment"
        else: comType = "comment"
        if userId: url = api(f"/x{self.comId}/s/user-profile/{userId}/{comType}")
        elif blogId: url = api(f"/x{self.comId}/s/blog/{blogId}/{comType}")
        elif wikiId: url = api(f"/x{self.comId}/s/item/{wikiId}/{comType}")
        else: raise TypeError("Please put a wiki or user or blog Id")

        data = json.dumps(data)
        async with self.session.post(url, data=data, headers=self.updateHeaders(data=data), ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def delete_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None):
        if userId: url = api(f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}")
        elif blogId: url = api(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}")
        elif wikiId: url = api(f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}")
        else: raise TypeError(" ")

        async with self.session.delete(url, headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def edit_comment(self, commentId: str, comment: str, userId: str = None, blogId: str = None, wikiId: str = None,replyTo: str = None, isGuest: bool = False):
        data = {"content": comment, "timestamp": int(timestamp() * 1000)}

        if isGuest:comType = "g-comment"
        else:comType = "comment"
        if userId:url = api(f"/x{self.comId}/s/user-profile/{userId}/{comType}/{commentId}")
        elif blogId:url = api(f"/x{self.comId}/s/blog/{blogId}/{comType}/{commentId}")
        elif wikiId:url = api(f"/x{self.comId}/s/item/{wikiId}/{comType}/{commentId}")

        data = json.dumps(data)
        async with self.session.post(url, data=data, headers=self.updateHeaders(data=data)) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Comment(await req.json()).Comments

    async def get_comment_info(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None, replyTo: str = None, isGuest: bool = False):
        if isGuest:comType = "g-comment"
        else:comType = "comment"
        if userId: url = api(f"/x{self.comId}/s/user-profile/{userId}/{comType}/{commentId}")
        elif blogId: url = api(f"/x{self.comId}/s/blog/{blogId}/{comType}/{commentId}")
        elif wikiId: url = api(f"/x{self.comId}/s/item/{wikiId}/{comType}/{commentId}")

        async with self.session.get(url, headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Comment(await req.json()).Comments

    async def get_wall_comments(self, userId: str, sorting: str = 'newest', start: int = 0, size: int = 25):
        sorting = sorting.lower()
        if sorting == 'top': sorting = "vote"
        if sorting not in ["newest", "oldest", "vote"]: raise TypeError("حط تايب يا حمار")

        async with self.session.get(api(f"/x{self.comId}/s/user-profile/{userId}/comment?sort={sorting}&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return CommentList((await req.json())["commentList"]).CommentList

    async def get_blog_comments(self, wikiId: str = None, blogId: str = None, quizId: str = None, sorting: str = 'newest', size: int = 25, start: int = 0):
        sorting = sorting.lower()
        if sorting == 'top': sorting = "vote"
        if sorting not in ["newest", "oldest", "vote"]: raise TypeError("حط تايب يا حمار")

        if quizId: blogId = quizId
        if blogId: url = api(f"/x{self.comId}/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}")
        elif wikiId: url = api(f"/x{self.comId}/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}")

        async with self.session.get(url, headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return CommentList((await req.json())["commentList"]).CommentList

    async def vote_comment(self, blogId: str, commentId: str, value: bool = True):
        if value: value = 1
        else: value = -1

        data = json.dumps({"value": value, "timestamp": int(timestamp() * 1000)})
        async with self.session.post(api(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=1"), data=data, headers=self.updateHeaders(data=data), ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def vote_poll(self, blogId: str, optionId: str):
        data = json.dumps({"value": 1, "timestamp": int(timestamp() * 1000)})
        async with self.session.post(api(f"/x{self.comId}/s/blog/{blogId}/poll/option/{optionId}/vote"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def get_blog_info(self, blogId: str = None, wikiId: str = None, folderId: str = None):
        if blogId: url = api(f"/x{self.comId}/s/blog/{blogId}")
        elif wikiId: url = api(f"/x{self.comId}/s/item/{wikiId}")
        elif folderId: url = api(f"/x{self.comId}/s/shared-folder/files/{folderId}")
        else: raise TypeError("Please put a wiki or blog Id")

        async with self.session.get(url, headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return GetInfo(await req.json()).GetInfo

    async def get_blogs(self, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/feed/featured?start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return BlogList((await req.json())["featuredList"]).BlogList

    async def get_blogs_more(self, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/feed/featured-more?start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return BlogList((await req.json())["blogList"]).BlogList

    async def get_blogs_all(self, start: int = 0, size: int = 25, pagingType: str = "t"):
        async with self.session.get(api(f"/x{self.comId}/s/feed/blog-all?pagingType={pagingType}&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return RecentBlogs((await req.json())["blogList"]).RecentBlogs

    async def tip_coins(self, coins: int, chatId: str = None, blogId: str = None, wikiId: str = None, transactionId: str = None):
        if transactionId is None: transactionId = str(UUID(hexlify(os.urandom(16)).decode("ascii")))
        data = {"coins": int(coins), "tippingContext": {"transactionId": transactionId}, "timestamp": int(timestamp() * 1000)}

        if chatId: url = api(f"/x{self.comId}/s/chat/thread/{chatId}/tipping")
        elif blogId: url = api(f"/x{self.comId}/s/blog/{blogId}/tipping")
        elif wikiId:
            url = api(f"/x{self.comId}/s/tipping")
            data["objectType"] = 2
            data["objectId"] = wikiId
        else: raise TypeError("Please put a wiki or chat or blog Id")

        data = json.dumps(data)
        async with self.session.post(url, headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def check_in(self, timezone: int = 180):
        data = json.dumps({"timezone": timezone, "timestamp": int(timestamp() * 1000)})
        async with self.session.post(api(f"/x{self.comId}/s/check-in"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def check_in_lottery(self, timezone: int = 180):
        data = json.dumps({"timezone": timezone, "timestamp": int(timestamp() * 1000)})
        async with self.session.post(api(f"/x{self.comId}/s/check-in/lottery"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def delete_message(self, chatId: str, messageId: str, asStaff: bool = False, reason: str = None):
        data = {"adminOpName": 102, "timestamp": int(timestamp() * 1000)}
        if asStaff and reason: data["adminOpNote"] = {"content": reason}
        data = json.dumps(data)
        if asStaff:
            async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}/admin"), data=data, headers=self.updateHeaders(data=data), ) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                else: return Json(await req.json())
        else:
            async with self.session.delete(api(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}"), headers=self.headers) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                else: return Json(await req.json())

    async def invite_by_host(self, chatId: str, userId: Union[str, list]):
        async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/member/{userId}/invite-av-chat"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def strike(self, userId: str, time: str, title: str = None, reason: str = None):
        times = {
            "1-Hours": 3600,
            "3-Hours": 10800,
            "6-Hours": 21600,
            "12-Hours": 43200,
            "24-Hours": 86400,
        }
        StrikeTime = times.get(time, 3600)

        data = json.dumps({
            "uid": userId,
            "title": title,
            "content": reason,
            "attachedObject": {"objectId": userId, "objectType": 0},
            "penaltyType": 1,
            "penaltyValue": StrikeTime,
            "adminOpNote": {},
            "noticeType": 4,
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/x{self.comId}/s/notice"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def ban(self, userId: str, reason: str, banType: int = None):
        data = json.dumps({
            "reasonType": banType,
            "note": {
                "content": reason
            },
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/x{self.comId}/s/user-profile/{userId}/ban"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def unban(self, userId: str, reason: str = "هذا العضو كان شاطر اخر كم يوم"):
        data = json.dumps({
            "note": {"content": reason},
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/x{self.comId}/s/user-profile/{userId}/unban"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def hide(self, note: str = None, blogId: str = None, userId: str = None, wikiId: str = None, chatId: str = None):
        opN, opV = 110, 9
        if userId:
            opN = 18
            opV = None
            url = api(f"/x{self.comId}/s/user-profile/{userId}/admin")
        elif blogId: url = api(f"/x{self.comId}/s/blog/{blogId}/admin")
        elif wikiId: url = api(f"/x{self.comId}/s/item/{wikiId}/admin")
        elif chatId: url = api(f"/x{self.comId}/s/chat/thread/{chatId}/admin")
        else: raise TypeError("Please put a wiki or user or chat or blog Id")

        data = {
            "adminOpName": opN,
            "adminOpValue": opV,
            "timestamp": int(timestamp() * 1000)
        }
        if note: data["adminOpNote"] = {"content": note}
        data = json.dumps(data)
        
        async with self.session.post(url, headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def unhide(self, note: str = None, blogId: str = None, userId: str = None, wikiId: str = None, chatId: str = None):
        opN, opV = 110, 0

        if userId:
            opN = 19
            url = api(f"/x{self.comId}/s/user-profile/{userId}/admin")
        elif blogId: url = api(f"/x{self.comId}/s/blog/{blogId}/admin")
        elif wikiId: url = api(f"/x{self.comId}/s/item/{wikiId}/admin")
        elif chatId: url = api(f"/x{self.comId}/s/chat/thread/{chatId}/admin")
        else: raise TypeError("Please put a wiki or user or chat or blog Id")

        data = {
            "adminOpName": opN,
            "adminOpValue": opV,
            "timestamp": int(timestamp() * 1000)
        }
        if note: data["adminOpNote"] = {"content": note}
        data = json.dumps(data)

        async with self.session.post(url, headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def send_warning(self, userId: str, reason: str = None):
        data = json.dumps({
            "uid": userId,
            "title": "Custom",
            "content": reason,
            "attachedObject": {"objectId": userId,"objectType": 0},
            "penaltyType": 0,
            "adminOpNote": {},
            "noticeType": 7,
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/x{self.comId}/s/notice"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def invite_to_voice_chat(self, userId: str = None, chatId: str = None):
        data = json.dumps({"uid": userId, "timestamp": int(timestamp() * 1000)})
        async with self.session.post(api(f"/g/x{self.comId}/chat/thread/{chatId}/vvchat-presenter/invite"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def post_blog(self, title: str, content: str, fansOnly: bool = False):
        data = {
            "extensions": {"fansOnly": fansOnly},
            "content": content,
            "latitude": 0,
            "longitude": 0,
            "title": title,
            "type": 0,
            "contentLanguage": "ar",
            "eventSource": "GlobalComposeMenu",
            "timestamp": int(timestamp() * 1000)
        }
        data = json.dumps(data)

        async with self.session.post(api(f"/x{self.comId}/s/blog"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def post_wiki(self, title: str, content: str, fansOnly: bool = False, icon: str = None, backgroundColor: str = None, keywords: Union[str, list] = None):
        data = {
            "extensions": {"fansOnly": fansOnly, "props": [], "style": {"backgroundColor": backgroundColor}},
            "content": content,
            "keywords": keywords,
            "label": title,
            "latitude": 0,
            "longitude": 0,
            "eventSource": "UserProfileView",
            "timestamp": int(timestamp() * 1000)
        }
        if icon: data["icon"] = icon

        data = json.dumps(data)
        async with self.session.post(api(f"/x{self.comId}/s/item"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def delete_blog(self, blogId: str):
        async with self.session.delete(api(f"/x{self.comId}/s/blog/{blogId}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def delete_wiki(self, wikiId: str):
        async with self.session.delete(api(f"/x{self.comId}/s/item/{wikiId}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def activate_status(self, status: int = 1):
        data = json.dumps({"onlineStatus": status,"duration": 86400,"timestamp": int(timestamp() * 1000)})
        async with self.session.post(api(f"/x{self.comId}/s/user-profile/{self.uid}/online-status"), data=data, headers=self.updateHeaders(data=data), ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def subscribe(self, userId: str, autoRenew: str = False, transactionId: str = None):
        if transactionId is None: transactionId = str(UUID(hexlify(os.urandom(16)).decode("ascii")))
        data = json.dumps({
            "paymentContext": {
                "transactionId": transactionId,
                "isAutoRenew": autoRenew
            },
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/x{self.comId}/s/influencer/{userId}/subscribe"), data=data, headers=self.updateHeaders(data=data), ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def submit_wiki(self, wikiId: str, message: str = None):
        data = {
            "message": message,
            "itemId": wikiId,
            "timestamp": int(timestamp() * 1000)
        }
        data = json.dumps(data)
        async with self.session.post(api(f"/x{self.comId}/s/knowledge-base-request"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def edit_blog(self, title: str, content: str, blogId: str = None, wikiId: str = None, fansOnly: bool = False, backgroundColor: str = None,media: list = None):
        data = {
            "title": title,
            "content": content,
            "timestamp": int(timestamp() * 1000)
        }
        
        if media: data["mediaList"] = [[100, media, None,"XYZ",None,{"fileName": "Amino"}]]
        if fansOnly: data["extensions"]["fansOnly"] = True
        if backgroundColor: data["extensions"] = {"backgroundColor": backgroundColor}
        if blogId: url = api(f"/x{self.comId}/s/blog/{blogId}")
        elif wikiId: url = api(f"/x{self.comId}/s/item/{wikiId}")
        else: raise TypeError("Please put blogId or wikiId")

        data = json.dumps(data)
        async with self.session.post(url, headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def get_chat_bubbles(self, start: int = 0, size: int = 20):
        async with self.session.get(api(f"/x{self.comId}/s/chat/chat-bubble?type=all-my-bubbles&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return BubbleList(await req.json()["chatBubbleList"]).BubbleList

    async def select_bubble(self, bubbleId: str, apply: int = 0, chatId: str = None):
        data = {"bubbleId": bubbleId, "applyToAll": apply, "timestamp": int(timestamp() * 1000)}
        if chatId: data["threadId"] = chatId
        data = json.dumps(data)
        async with self.session.post(api(f"/x{self.comId}/s/chat/thread/apply-bubble"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def delete_chat_bubble(self, bubbleId: str):
        async with self.session.delete(url=api(f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def get_chat_bubble_templates(self, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/chat/chat-bubble/templates?start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return BubbleTemplates(await req.json()["templateList"])

    async def upload_custom_bubble(self, templateId: str, bubble: BinaryIO):
        async with self.session.post(api(f"/x{self.comId}/s/chat/chat-bubble/templates/{templateId}/generate"), headers=self.headers,data=bubble) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def kick(self, chatId: str, userId: str, rejoin: bool = True):
        if rejoin: rejoin = 1
        if not rejoin: rejoin = 0

        async with self.session.delete(api(f"/x{self.comId}/s/chat/thread/{chatId}/member/{userId}?allowRejoin={rejoin}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def web_active_time(self):
        try:
            data = {"ndcId": self.comId}
            async with self.session.post("https://aminoapps.com/api/community/stats/web-user-active-time", json=data, headers=self.web_headers) as req:
                try:
                    if (await req.json())["code"] != 200: return CheckExceptions(await req.json())
                    else: Json(await req.json())
                except: return CheckExceptions(await req.json())
                return Json(await req.json())
        except: raise Exception("Unknown error")

    async def block(self, userId: str):
        async with self.session.post(api(f"/x{self.comId}/s/block/{userId}"), headers=self.headers) as req:
            if "OK" not in (await req.json())["api:message"]: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def flag(self, reason: str, type: str = "spam", userId: str = None, wikiId: str = None, blogId: str = None):
        types = {"violence": 106, "hate": 107, "suicide": 108, "troll": 109, "nudity": 110, "bully": 0, "off-topic": 4, "spam": 2}

        data = {
            "message": reason,
            "timestamp": int(timestamp() * 1000)
        }

        if type in types:
            data["flagType"] = types[type]

        if userId:
            data["objectId"] = userId
            data['objectType'] = 0

        elif blogId:
            data["objectId"] = blogId
            data['objectType'] = 1

        elif wikiId:
            data["objectId"] = wikiId
            data["objectType"] = 2
        else: raise TypeError("choose a certain type to report")

        data = json.dumps(data)
        async with self.session.post(api(f"/x{self.comId}/s/flag", headers=self.updateHeaders(data=data), data=data)) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def send_active_time(self,tz: int = int(-timezone // 1000), timers: list = None):
        data = {
            "userActiveTimeChunkList": [{"start": int(timestamp()), "end": int(timestamp() + 300)}],
            "timestamp": int(timestamp() * 1000),
            "optInAdsFlags": 2147483647,
            "timezone": tz
        }
        if timers: data["userActiveTimeChunkList"] = timers

        data = json_minify(json.dumps(data))
        async with self.session.post(api(f"/x{self.comId}/s/community/stats/user-active-time"), headers=self.updateHeaders(data=data), proxies=self.proxies, data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def transfer_host(self, chatId: str, userIds: list):
        data = json.dumps({
            "uidList": userIds,
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def accept_host(self, chatId: str, requestId: str):
        data = json.dumps({'timestamp': int(timestamp() * 1000)})
        async with self.session.post(api(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def remove_host(self, chatId: str, userId: str):
        async with self.session.delete(api(f"/x{self.comId}/s/chat/thread/{chatId}/co-host/{userId}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def get_quizes(self, type: str = "recent", start: int = 0, size: int = 25):
        if type == "recent":url = api(f"x{self.comId}/s/blog?type=quizzes-recent&start={start}&size={size}")
        elif type == "trending":url = api(f"x{self.comId}/s/feed/quiz-trending?start={start}&size={size}")
        elif type == "best":url = api(f"x{self.comId}/s/feed/quiz-best-quizzes?start={start}&size={size}")
        else:raise TypeError("only 3 types (recent , best , trending)")

        async with self.session.get(url, headers=self.headers) as req:
            if req.status != 200:return CheckExceptions(await req.json())
            else:return BlogList((await req.json())["blogList"]).BlogList

    async def get_quiz_questions(self, quizId: str):
        async with self.session.get(api(f"/x{self.comId}/s/blog/{quizId}?action=review"), headers=self.headers) as req:
            if req.status != 200:return CheckExceptions(await req.json())
            else:return QuizQuestionList((await req.json())["blog"]["quizQuestionList"]).QuizQuestionList

    async def play_quiz(self, quizId: str, questions: list, answers: list, mode: int = 0):
        data = json.dumps({
            "mode": mode,
            "quizAnswerList": [{
                "optIdList": [answer],
                "quizQuestionId": question,
                "timeSpent": 0.0
            } for answer, question in zip(answers, questions)],
            "timestamp": int(timestamp() * 1000)
        })
        async with self.session.post(api(f"/x{self.comId}/s/blog/{quizId}/quiz/result"),headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200:return CheckExceptions(await req.json())
            else:return req.status

    async def get_quiz_rankings(self, quizId: str, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/blog/{quizId}/quiz/result?start={start}&size={size}"),headers=self.headers) as req:
            if req.status != 200:return CheckExceptions(await req.json())
            else:return QuizRankings(await req.json()).QuizRankings

    async def search_user(self, username: str, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/user-profile?type=name&q={username}&start={start}&size={size}"),headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return UserProfileList((await req.json())["userProfileList"]).UserProfileList

    async def search_blog(self, words: str, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/blog?type=keywords&q={words}&start={start}&size={size}"),headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return BlogList((await req.json())["blogList"]).BlogList

    async def get_notifications(self, size: int = 25, pagingType: str = "t"):
        async with self.session.get(api(f"/x{self.comId}/s/notification?pagingType={pagingType}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return NotificationList(await req.json()).NotificationList

    async def get_notices(self, start: int = 0, size: int = 25, type: str = "usersV2", status: int = 1):
        async with self.session.get(api(f"/x{self.comId}/s/notice?type={type}&status={status}&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return NoticeList(await req.json()).NoticeList

    async def accept_promotion(self, requestId: str):
        if not isinstance(requestId, str): raise Exception(f"Please use a string not {type(requestId)}")
        async with self.session.post(api(f"/x{self.comId}/s/notice/{requestId}/accept"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())
    
    async def decline_promotion(self, requestId: str):
        if not isinstance(requestId, str): raise Exception(f"Please use a string not {type(requestId)}")
        async with self.session.post(api(f"/x{self.comId}/s/notice/{requestId}/decline"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def sendWebActive(self):
        data = {"ndcId": self.comId}
        async with self.session.post(webApi("/community/stats/web-user-active-time"), json=data, headers=self.web_headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return await req.json()

    async def publish_to_featured(self, time: int, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None):
        time = {
            1: 3600,
            2: 7200,
            3: 10800
        }.get(time) if chatId else {
            1: 86400,
            2: 172800,
            3: 259200
        }.get(time)

        data = {
            "adminOpName": 114,
            "adminOpValue": {
                "featuredDuration": time
            },
            "timestamp": int(timestamp() * 1000)
        }

        if userId: featuredType, endpoint = 4, f"user-profile/{userId}"
        elif blogId: featuredType, endpoint = 1, f"blog/{blogId}"
        elif wikiId: featuredType, endpoint = 1, f"item/{blogId}"
        elif chatId: featuredType, endpoint = 5, f"chat/thread/{chatId}"
        else: raise TypeError("Please Specify Object ID")

        data["adminOpValue"]["featuredType"] = featuredType
        data = json.dumps(data)
        async with self.session.post(api(f"/x{self.comId}/s/{endpoint}/admin"), headers=self.updateHeaders(data=data), data=data) as req:
            return CheckExceptions(await req.json()) if req.status != 200 else Json(await req.json())

    async def remove_from_featured(self, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None):
        data = {
            "adminOpName": 114,
            "adminOpValue": {
                "featuredType": 0
            },
            "timestamp": int(timestamp() * 1000)
        }

        if userId: featuredType, endpoint = f"user-profile/{userId}"
        elif blogId: featuredType, endpoint = f"blog/{blogId}"
        elif wikiId: featuredType, endpoint = f"item/{blogId}"
        elif chatId:  featuredType, endpoint = f"chat/thread/{chatId}"
        else: raise TypeError("Please Specify Object ID")

        data["adminOpValue"]["featuredType"] = featuredType
        data = json.dumps(data)
        async with self.session.post(api(f"/x{self.comId}/s/{endpoint}/admin"), headers=self.updateHeaders(data=data), data=data) as req:
            return CheckExceptions(await req.json()) if req.status != 200 else Json(await req.json())