import asyncio
import os
from binascii import hexlify
from time import time as timestamp
from typing import BinaryIO, Union
from uuid import UUID

import aiohttp
import ujson as json

from .sockets import Wss
from ..lib import *
from ..lib.objects import *


class SClient(Wss, Headers):
    def __init__(self, deviceId: str = None, Trace: bool = False):
        self.uid = None
        self.sid = None
        self.secret = None
        self.web_headers = None

        self.Trace = Trace
        headers.staticDevice = deviceId

        Headers.__init__(self)
        Wss.__init__(self, client=self, Session=self.session, Trace=self.Trace)
        
        self.deviceId = self.headers_device
        self.headers = self.app_headers
        self.session = aiohttp.ClientSession()

    async def __aenter__(self) -> "SClient":
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

    async def sid_login(self, sid: str):
        finalSessionId = sid if "sid=" in sid else f"sid={sid}"

        info = (await self.get_account_info())
        self.uid = info.userId
        self.sid = finalSessionId
        headers.userId = self.uid
        headers.definedSession = self.sid
        await self.Start()
        return info

    async def login(self, email: str = None, password: str = None, secret: str = None,socket: bool = False):
        data = {
            "clientType": 100,
            "action": "normal",
            "deviceID": self.deviceId,
            "v": 2,
            "timestamp": int(timestamp() * 1000)
        }
        print(self.headers["NDCDEVICEID"])

        if password and email and not secret:
            data["email"] = email
            data["secret"] = f"0 {password}"
        elif secret: data["secret"] = secret
        else: raise ValueError("Please provide VALID login info")

        data = json.dumps(data)
        async with self.session.post(api(f"/g/s/auth/login"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
        
            self.sid = f'sid={(await req.json())["sid"]}'
            self.secret = (await req.json())["secret"]
            self.uid = (await req.json())["auid"]
            headers.definedSession = self.sid
            headers.userId = self.uid

            if socket: self.Launch()
            return Login(await req.json())

    async def logout(self):
        data = json.dumps({
            "deviceID": self.deviceId,
            "clientType": 100,
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api("/g/s/auth/logout"), headers=self.updateHeaders(data=data), data=data ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            
            self.sid = None
            self.uiduserIdNone
            headers.uid = None

            if self.Ran:await self.close()
            return Json((await req.json()))

    async def check_device(self, deviceId: str):
        data = json.dumps({
            "deviceID": deviceId,
            "timestamp": int(timestamp() * 1000),
            "clientType": 100
        })
        async with self.session.post(api(f"/g/s/device"), headers=self.updateHeaders(data=data), data=data) as req:
            if (await req.json())["api:statuscode"] != 0: return CheckExceptions(await req.json())
            return f"api:message {(await req.json())['api:message']}\napi:statuscode {(await req.json())['api:statuscode']}\nThe device is fine"

    async def upload_image(self, image: BinaryIO):
        data = image.read()

        self.headers["content-type"] = "image/jpg"
        self.headers["content-length"] = str(len(data))

        async with self.session.post(api(f"/g/s/media/upload"), data=data, headers=self.headers) as req:
            return (await req.json())["mediaValue"]

    async def send_verify(self, email: str):
        data = json.dumps({
            "identity": email,
            "type": 1,
            "deviceID": self.deviceId,
            "timestamp": int(timestamp() * 1000)
        })
        async with self.session.post(api(f"/g/s/auth/request-security-validation"), headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def accept_host(self, requestId: str, chatId: str):
        async with self.session.post(api(f"/g/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept"),headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def verify_account(self, email: str, code: str):
        data = json.dumps({
            "type": 1,
            "identity": email,
            "data": {"code": code},
            "deviceID": self.deviceId
        })
        async with self.session.post(api(f"/g/s/auth/activate-email"), headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def restore(self, email: str, password: str):
        data = json.dumps({
            "secret": f"0 {password}",
            "deviceID": self.deviceId,
            "email": email,
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/g/s/account/delete-request/cancel"), headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def delete_account(self, password: str = None):
        data = json.dumps({
            "deviceID": self.deviceId,
            "secret": f"0 {password}",
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/g/s/account/delete-request"), headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def get_account_info(self):
        async with self.session.get(api(f"/g/s/account"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(((await req.json())))
            return Account(((await req.json()))["account"])

    async def claim_coupon(self):
        async with self.session.post(api(f"/g/s/coupon/new-user-coupon/claim"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(((await req.json())))
            return Json(((await req.json())))

    async def change_amino_id(self, aminoId: str = None):
        data = json.dumps({"aminoId": aminoId, "timestamp": int(timestamp() * 1000)})
        async with self.session.post(api(f"/g/s/account/change-amino-id"), data=data, headers=self.updateHeaders(data=data) ) as req:
            if req.status != 200: return CheckExceptions(((await req.json())))
            return Json(((await req.json())))

    async def get_my_communitys(self, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/g/s/community/joined?v=1&start={start}&size={size}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(((await req.json())))
            return CommunityList(((await req.json()))["communityList"]).CommunityList

    async def get_chat_threads(self, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/g/s/chat/thread?type=joined-me&start={start}&size={size}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(((await req.json())))
            return ThreadList(((await req.json()))["threadList"]).ThreadList

    async def get_chat_info(self, chatId: str):
        async with self.session.get(api(f"/g/s/chat/thread/{chatId}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(((await req.json())))
            return Thread(((await req.json()))["thread"]).Thread

    async def leave_chat(self, chatId: str):
        async with self.session.delete(api(f"/g/s/chat/thread/{chatId}/member/{self.uid}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(((await req.json())))
            return Json(((await req.json())))

    async def join_chat(self, chatId: str):
        async with self.session.post(api(f"/g/s/chat/thread/{chatId}/member/{self.uid}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(((await req.json())))
            return Json(((await req.json())))

    async def start_chat(self, userId: Union[str, list], title: str = None, message: str = None, content: str = None,chatType: int = 0):
        if type(userId) is list: userIds = userId
        elif type(userId) is str: userIds = [userId]

        data = json.dumps({
            "title": title,
            "inviteeUids": userIds,
            "initialMessageContent": message,
            "content": content,
            "type": chatType,
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/g/s/chat/thread"), headers=self.updateHeaders(data=data),data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def get_from_link(self, link: str):
        async with self.session.get(api(f"/g/s/link-resolution?q={link}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return FromCode((await req.json())["linkInfoV2"]["extensions"]).FromCode

    async def edit_profile(self, nickname: str = None, content: str = None, icon: BinaryIO = None,
                     backgroundColor: str = None, backgroundImage: str = None, defaultBubbleId: str = None):
        data = {
            "address": None,
            "latitude": 0,
            "longitude": 0,
            "mediaList": None,
            "eventSource": "UserProfileView",
            "timestamp": int(timestamp() * 1000)
        }

        if nickname: data["nickname"] = nickname
        if icon: data["icon"] = self.upload_image(icon)
        if content: data["content"] = content
        if backgroundColor: data["extensions"]["style"] = {"backgroundColor": backgroundColor}
        if backgroundImage: data["extensions"]["style"] = {"backgroundMediaList": [[100, backgroundImage, None, None, None]]}
        if defaultBubbleId: data["extensions"] = {"async defaultBubbleId": defaultBubbleId}

        data = json.dumps(data)
        async with self.session.post(api(f"/g/s/user-profile/{self.uid}"), headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def flag_community(self, comId: str, reason: str, flagType: int):
        data = json.dumps({
            "objectId": comId,
            "objectType": 16,
            "flagType": flagType,
            "message": reason,
            "timestamp": int(timestamp() * 1000)
        })
        async with self.session.post(api(f"/x{comId}/s/g-flag"), headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def leave_community(self, comId: str):
        async with self.session.post(api(f"/x{comId}/s/community/leave"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def join_community(self, comId: str, InviteId: str = None):
        data = {"timestamp": int(timestamp() * 1000)}
        if InviteId: data["invitationId"] = InviteId
        data = json.dumps(data)
        async with self.session.post(api(f"/x{comId}/s/community/join"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

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

        data = json.dumps(data)
        async with self.session.post(api(f"/g/s/flag"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def unfollow(self, userId: str):
        async with self.session.post(api(f"/g/s/user-profile/{userId}/member/{self.uid}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def follow(self, userId: Union[str, list]):
        data = {
            "timestamp": int(timestamp() * 1000)
        }

        if type(userId) is str: url = f"/g/s/user-profile/{userId}/member"
        elif type(userId) is list:
            url = f"/g/s/user-profile/{self.uid}/joined"
            data["targetUidList"] = userId
        
        data = json.dumps(data)
        async with self.session.post(api(url),headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))


    async def get_member_following(self, userId: str, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/g/s/user-profile/{userId}/joined?start={start}&size={size}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return UserProfileList((await req.json())["userProfileList"]).UserProfileList

    async def get_member_followers(self, userId: str, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/g/s/user-profile/{userId}/member?start={start}&size={size}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
        return UserProfileList((await req.json())["userProfileList"]).UserProfileList

    async def get_member_visitors(self, userId: str, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/g/s/user-profile/{userId}/visitors?start={start}&size={size}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return VisitorsList((await req.json())["visitors"]).VisitorsList

    async def get_blocker_users(self, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/g/s/block/full-list?start={start}&size={size}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return (await req.json())["blockerUidList"]

    async def get_blocked_users(self, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/g/s/block/full-list?start={start}&size={size}"), headers=self.headers,
                           ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return (await req.json())["blockedUidList"]

    async def get_wall_comments(self, userId: str, sorting: str = 'newest', start: int = 0, size: int = 25):
        sorting = sorting.lower()
        if sorting == 'top': sorting = "vote"
        if sorting not in ["newest", "oldest", "vote"]: raise TypeError("حط تايب يا حمار")

        async with self.session.get(api(f"/g/s/user-profile/{userId}/g-comment?sort={sorting}&start={start}&size={size}"),
                           headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return CommentList((await req.json())["commentList"]).CommentList

    async def get_blog_comments(self, wikiId:str = None, blogId:str = None, quizId: str = None, sorting: str = 'newest',size: int = 25, start: int = 0):
        sorting = sorting.lower()
        if sorting == 'top': sorting = "vote"
        if sorting not in ["newest", "oldest", "vote"]: raise TypeError("حط تايب يا حمار")

        if quizId: blogId = quizId
        if blogId: url = api(f"/g/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}")
        elif wikiId: url = api(f"/g/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}")

        async with self.session.get(url, headers=self.headers, proxies=self.proxies) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return CommentList((await req.json())["commentList"]).CommentList

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
            if type(embedImage) is not str: embedImage = [[100, self.upload_image(embedImage), None]]
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

            else:
                raise TypeError(fileType)

            data["mediaUploadValue"] = base64.b64encode(file.read()).decode()
            data["attachedObject"] = None
            data["extensions"] = None

        data = json.dumps(data)
        async with self.session.post(api(f"/g/s/chat/thread/{chatId}/message"),headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def get_community_info(self, comId: str):
        async with self.session.get(
            api(f"/g/s-x{comId}/community/info?withInfluencerList=1&withTopicList=true&influencerListOrderStrategy=fansCount"),
            headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Community((await req.json())["community"]).Community

    async def mark_as_read(self, chatId: str):
        async with self.session.post(api(f"/g/s/chat/thread/{chatId}/mark-as-read"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def delete_message(self, messageId: str, chatId: str):
        async with self.session.delete(api(f"/g/s/chat/thread/{chatId}/message/{messageId}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def get_chat_messages(self, chatId: str, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/g/s/chat/thread/{chatId}/message?v=2&pagingType=t&size={size}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return GetMessages((await req.json())["messageList"]).GetMessages

    async def get_message_info(self, messageId: str, chatId: str):
        async with self.session.get(api(f"/g/s/chat/thread/{chatId}/message/{messageId}"), headers=self.headers,
                           ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Message((await req.json())["message"]).Message

    async def tip_coins(self, chatId: str = None, blogId: str = None, coins: int = 0, transactionId: str = None):
        if transactionId is None: transactionId = str(UUID(hexlify(os.urandom(16)).decode("ascii")))
        data = json.dumps({
            "coins": coins,
            "tippingContext": {
                "transactionId": transactionId
            },
            "timestamp": int(timestamp() * 1000)
        })

        if chatId is not None:
            url = api(f"/g/s/blog/{chatId}/tipping")
        elif blogId is not None:
            url = api(f"/g/s/blog/{blogId}/tipping")
        else:
            raise TypeError("please put chat or blog Id")

        async with self.session.post(url, headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def reset_password(self, email: str, password: str, code: str, deviceId: str = None):
        if deviceId is None: deviceId = self.deviceId

        data = json.dumps({
            "updateSecret": f"0 {password}",
            "emailValidationContext": {
                "data": {
                    "code": code
                },
                "type": 1,
                "identity": email,
                "level": 2,
                "deviceID": deviceId
            },
            "phoneNumberValidationContext": None,
            "deviceID": deviceId,
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/g/s/auth/reset-password"), headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def change_password(self, password: str, newPassword: str):
        data = json.dumps({
            "secret": f"0 {password}",
            "updateSecret": f"0 {newPassword}",
            "validationContext": None,
            "deviceID": self.deviceId
        })
        header = self.updateHeaders(data=data)
        header["ndcdeviceid"], header["ndcauth"] = header["NDCDEVICEID"], header["NDCAUTH"]
        async with self.session.post(api("/g/s/auth/change-password"), headers=header, data=data) as req:
            if req.status != 200:
                return CheckExceptions(await req.json())
            else:
                return Json((await req.json()))

    async def get_user_info(self, userId: str):
        async with self.session.get(api(f"/g/s/user-profile/{userId}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return UserProfile((await req.json())["userProfile"]).UserProfile

    async def comment(self, comment: str, userId: str = None, replyTo: str = None):
        data = {
            "content": comment,
            "stickerId": None,
            "type": 0,
            "eventSource": "UserProfileView",
            "timestamp": int(timestamp() * 1000)
        }

        if replyTo: data["respondTo"] = replyTo

        data = json.dumps(data)

        async with self.session.post(api(f"/g/s/user-profile/{userId}/g-comment"), headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def delete_comment(self, userId: str = None, commentId: str = None):
        async with self.session.delete(api(f"/g/s/user-profile/{userId}/g-comment/{commentId}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def invite_by_host(self, chatId: str, userId: Union[str, list]):
        data = json.dumps({"uidList": userId, "timestamp": int(timestamp() * 1000)})

        async with self.session.post(api(f"/g/s/chat/thread/{chatId}/avchat-members"),headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def kick(self, chatId: str, userId: str, rejoin: bool = True):
        if rejoin: rejoin = 1
        if not rejoin: rejoin = 0

        async with self.session.delete(api(f"/g/s/chat/thread/{chatId}/member/{userId}?allowRejoin={rejoin}"),headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def block(self, userId: str):
        async with self.session.post(api(f"/g/s/block/{userId}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def unblock(self, userId: str):
        async with self.session.delete(api(f"/g/s/block/{userId}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def get_public_chats(self, type: str = "recommended", start: int = 0, size: int = 50):
        async with self.session.get(api(f"/g/s/chat/thread?type=public-all&filterType={type}&start={start}&size={size}"),headers=self.headers ) as req:
            if req.status != 200:
                return CheckExceptions(await req.json())
            else:
                return ThreadList((await req.json())["threadList"]).ThreadList

    async def get_content_modules(self, version: int = 2):
        async with self.session.get(api(f"/g/s/home/discover/content-modules?v={version}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def get_banner_ads(self, size: int = 25, pagingType: str = "t"):
        async with self.session.get(
            api(f"/g/s/topic/0/feed/banner-ads?moduleId=711f818f-da0c-4aa7-bfa6-d5b58c1464d0&adUnitId=703798&size={size}&pagingType={pagingType}"),headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return ItemList((await req.json())["itemList"]).ItemList

    async def get_announcements(self, lang: str = "ar", start: int = 0, size: int = 20):
        async with self.session.get(api(f"/g/s/announcement?language={lang}&start={start}&size={size}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return BlogList((await req.json())["blogList"]).BlogList

    async def get_discover(self, type: str = "discover", category: str = "customized", size: int = 25, pagingType: str = "t"):
        async with self.session.get(
            api(f"/g/s/topic/0/feed/community?type={type}&categoryKey={category}&moduleId=64da14e8-0845-47bf-946a-17403bd6aa17&size={size}&pagingType={pagingType}"),headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return CommunityList((await req.json())["communityList"]).CommunityList
        
    async def search_community(self, word: str,lang: str = "ar", start: int = 0, size: int = 25):
        async with self.session.get(api(f"/g/s/community/search?q={word}&language={lang}&completeKeyword=1&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return CommunityList((await req.json())["communityList"]).CommunityList

    async def invite_to_voice_chat(self, userId: str = None, chatId: str = None):
        data = json.dumps({"uid": userId, "timestamp": int(timestamp() * 1000)})
        async with self.session.post(api(f"/g/s/chat/thread/{chatId}/vvchat-presenter/invite"),headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def get_wallet_history(self, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/g/s/wallet/coin/history?start={start}&size={size}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return WalletHistory((await req.json())).WalletHistory

    async def get_wallet_info(self):
        async with self.session.get(api(f"/g/s/wallet"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return WalletInfo((await req.json())["wallet"]).WalletInfo

    async def get_all_users(self, type: str = "recent", start: int = 0, size: int = 25):
        async with self.session.get(api(f"/g/s/user-profile?type={type}&start={start}&size={size}"), headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return UserProfileList((await req.json())["userProfileList"]).UserProfileList

    async def get_chat_members(self, start: int = 0, size: int = 25, chatId: str = None):
        async with self.session.get(api(f"/g/s/chat/thread/{chatId}/member?start={start}&size={size}&type=async default&cv=1.2"),headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return UserProfileList((await req.json())["memberList"]).UserProfileList

    async def get_from_id(self, id: str, comId: str = None, objectType: int = 2):  # never tried
        data = json.dumps({
            "objectId": id,
            "targetCode": 1,
            "objectType": objectType,
            "timestamp": int(timestamp() * 1000)
        })

        if comId is None:url = api(f"/g/s/link-resolution")
        elif comId is not None:url = api(f"/g/s-x{comId}/link-resolution")
        else:raise TypeError("please put a comId")

        async with self.session.post(url, headers=self.updateHeaders(data=data) , data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return FromCode((await req.json())["linkInfoV2"]["extensions"]["linkInfo"]).FromCode

    async def chat_settings(self, chatId: str, viewOnly: bool = None, doNotDisturb: bool = None, canInvite: bool = False,canTip: bool = None, pin: bool = None):
        res = []
        if doNotDisturb is not None:
            if doNotDisturb: opt = 2
            if not doNotDisturb:
                opt = 1
            else:
                raise TypeError("Do not disturb should be True or False")

            data = json.dumps({"alertOption": opt, "timestamp": int(timestamp() * 1000)})
            async with self.session.post(api(f"/g/s/chat/thread/{chatId}/member/{self.uid}/alert"), data=data,headers=self.updateHeaders(data=data) ) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json((await req.json())))

        if viewOnly is not None:
            if viewOnly: viewOnly = "enable"
            if not viewOnly:
                viewOnly = "disable"
            else:
                raise TypeError("viewOnly should be True or False")

            async with self.session.post(api(f"/g/s/chat/thread/{chatId}/view-only/{viewOnly}"), headers=self.headers ) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json((await req.json())))

        if canInvite is not None:
            if canInvite: canInvite = "enable"
            if not canInvite:
                canInvite = "disable"
            else:
                raise TypeError("can invite should be True or False")

            async with self.session.post(api(f"/g/s/chat/thread/{chatId}/members-can-invite/{canInvite}"), headers=self.headers ) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json((await req.json())))

        if canTip is not None:
            if canTip: canTip = "enable"
            if not canTip:
                canTip = "disable"
            else:
                raise TypeError("can tip should be True or False")

            async with self.session.post(api(f"/g/s/chat/thread/{chatId}/tipping-perm-status/{canTip}"), headers=self.headers ) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json((await req.json())))

        if pin is not None:
            if pin: pin = "pin"
            if not pin:
                pin = "unpin"
            else:
                raise TypeError("pin should be True or False")

            async with self.session.post(api(f"/g/s/chat/thread/{chatId}/{pin}"), headers=self.headers ) as req:
                if req.status != 200: return CheckExceptions(await req.json())
                res.append(Json((await req.json())))

        return res

    async def like_comment(self, commentId: str, userId: str = None, blogId: str = None):
        data = json.dumps({"value": 4, "timestamp": int(timestamp() * 1000)})

        if userId:
            url = api(f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?cv=1.2&value=1")
        elif blogId:
            url = api(f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?cv=1.2&value=1")
        else:
            raise TypeError("Please put blogId or wikiId")

        async with self.session.post(url, data=data, headers=self.updateHeaders(data=data) ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def unlike_comment(self, commentId: str, blogId: str = None, userId: str = None):
        if userId:
            url = api(f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView")
        elif blogId:
            url = api(f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView")
        else:
            raise TypeError("Please put blog or user Id")

        async with self.session.delete(url, headers=self.headers ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def register(self, nickname: str, email: str, password: str, deviceId: str = None):
        if deviceId is None: deviceId = self.deviceId

        data = json.dumps({
            "secret": f"0 {password}",
            "deviceID": deviceId,
            "email": email,
            "clientType": 100,
            "nickname": nickname,
            "latitude": 0,
            "longitude": 0,
            "address": None,
            "clientCallbackURL": "narviiapp://relogin",
            "type": 1,
            "identity": email,
            "timestamp": int(timestamp() * 1000)
        })

        async with self.session.post(api(f"/g/s/auth/register"), data=data, headers=self.updateHeaders(data=data) ) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json((await req.json()))

    async def remove_host(self, chatId: str, userId: str):
        async with self.session.delete(api(f"/g/s/chat/thread/{chatId}/co-host/{userId}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())

    async def edit_comment(self, commentId: str, comment: str, userId: str):
        data = {"content": comment, "timestamp": int(timestamp() * 1000)}
        data = json.dumps(data)
        async with self.session.post(api(f"/g/s/user-profile/{userId}/comment/{commentId}"), data=data, headers=self.updateHeaders(data=data)) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Comment(await req.json()).Comments

    async def get_comment_info(self, commentId: str, userId: str):
        async with self.session.get(api(f"/g/s/user-profile/{userId}/comment/{commentId}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Comment(await req.json()).Comments

    async def get_notifications(self, size: int = 25, pagingType: str = "t"):
        async with self.session.get(api(f"/g/s/notification?pagingType={pagingType}&size={size}"), headers = self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return NotificationList(await req.json()).NotificationList

    async def get_notices(self, start: int = 0, size: int = 25, type: str = "usersV2", status: int = 1):
        async with self.session.get(api(f"/g/s/notice?type={type}&status={status}&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return NoticeList(await req.json()).NoticeList

    async def accept_promotion(self, requestId: str):
        if not isinstance(requestId, str): raise Exception(f"Please use a string not {type(requestId)}")
        async with self.session.post(api(f"/g/s/notice/{requestId}/accept"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())
    
    async def decline_promotion(self, requestId: str):
        if not isinstance(requestId, str): raise Exception(f"Please use a string not {type(requestId)}")
        async with self.session.post(api(f"/g/s/notice/{requestId}/decline"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            return Json(await req.json())