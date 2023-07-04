import os
from base64 import b64encode
from binascii import hexlify
from time import time as timestamp
from typing import BinaryIO, Union
from uuid import UUID
import asyncio

from ..lib.objects import *
from ..lib.async_sessions import AsyncSession as Session
from ..lib.util import updateDevice, generateDevice
from .sockets import Wss


class AsyncClient(Wss, Session):
    def __init__(self, deviceId: str = None, proxies: dict = None, trace: bool = False, bot: bool = False):
        self.trace = trace
        self.proxies = proxies
        self.deviceId = updateDevice(deviceId) if deviceId else generateDevice()

        Wss.__init__(self, self, trace=self.trace, is_bot=bot)
        Session.__init__(self, proxies=self.proxies, staticDevice=self.deviceId)

    def change_lang(self, lang: str = "en"):
        self.updateHeaders(lang=lang)

    def run(
            self,
            email: str = None,
            password: str = None,
            secret: str = None,
            socket: bool = False,
            sid: str = None
        ):
        if sid:
            asyncio.run(sid_login(sid, socket))
        else:
            asyncio.run(self.login(email, password, secret, socket))

    async def sid_login(self, sid: str, socket = False):
        finalSessionId = sid if "sid=" in sid else f"sid={sid}"

        info = self.get_account_info()
        self.settings(
            user_userId=info.userId,
            user_session=finalSessionId,
        )

        if socket or self.is_bot:
            await self.launch()
        return info

    async def login(
        self,
        email: str = None,
        password: str = None,
        secret: str = None,
        socket: bool = False,
    ):

        if not ((email and password) or secret):
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

        req = await self.postRequest("/g/s/auth/login", data)
        self.settings(
            user_userId=req["auid"],
            user_session=f'sid={req["sid"]}',
            user_secret=secret if secret else req["secret"],
        )
        if socket or self.is_bot:
            await self.launch()
        return Login(req)

    async def logout(self):
        data = {
            "deviceID": self.deviceId,
            "clientType": 100,
            "timestamp": int(timestamp() * 1000),
        }

        req = await self.postRequest("/g/s/auth/logout", data)
        self.settings()  # Resets the sid and uid and secret to None in sessions.py

        if self.isOpened: await self.close()
        return Json(req)

    async def check_device(self, deviceId: str) -> str:
        data = {
            "deviceID": deviceId,
            "timestamp": int(timestamp() * 1000),
            "clientType": 100,
        }
        self.headers["NDCDEVICEID"] = deviceId
        req = await self.postRequest("/g/s/device/", data)
        return Json(req)

    async def upload_image(self, image: BinaryIO):
        newHeaders = {"content-type": "image/jpg", "content-length": str(len(image.read()))}
        return await self.postRequest("/g/s/media/upload", data=image, newHeaders=newHeaders)["mediaValue"]

    async def send_verify_code(self, email: str):
        data = {
            "identity": email,
            "type": 1,
            "deviceID": self.deviceId,
            "timestamp": int(timestamp() * 1000),
        }

        req = await self.postRequest("/g/s/auth/request-security-validation", data)
        return Json(req)

    async def accept_host(self, requestId: str, chatId: str):
        req = await self.postRequest(
            f"/g/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept"
        )
        return Json(req)

    async def verify_account(self, email: str, code: str):
        data = {
            "type": 1,
            "identity": email,
            "data": {"code": code},
            "deviceID": self.deviceId,
        }
        req = await self.postRequest("/g/s/auth/activate-email", data)
        return Json(req)

    async def restore(self, email: str, password: str):
        data = {
            "secret": f"0 {password}",
            "deviceID": self.deviceId,
            "email": email,
            "timestamp": int(timestamp() * 1000),
        }

        req = await self.postRequest("/g/s/account/delete-request/cancel", data)
        return Json(req)

    async def delete_account(self, password: str = None):
        data = {
            "deviceID": self.deviceId,
            "secret": f"0 {password}",
            "timestamp": int(timestamp() * 1000),
        }

        req = await self.postRequest("/g/s/account/delete-request", data)
        return Json(req)

    async def get_account_info(self):
        req = await self.getRequest("/g/s/account")
        return Account(req["account"])

    async def claim_coupon(self):
        req = await self.postRequest("/g/s/coupon/new-user-coupon/claim")
        return Json(req)

    async def change_amino_id(self, aminoId: str = None):
        data = {"aminoId": aminoId, "timestamp": int(timestamp() * 1000)}
        req = await self.postRequest("/g/s/account/change-amino-id", data)
        return Json(req)

    async def get_my_communities(self, start: int = 0, size: int = 25):
        req = await self.getRequest(f"/g/s/community/joined?v=1&start={start}&size={size}")
        return CommunityList(req["communityList"]).CommunityList

    async def get_chat_threads(self, start: int = 0, size: int = 25):
        req = await self.getRequest(
            f"/g/s/chat/thread?type=joined-me&start={start}&size={size}"
        )
        return ThreadList(req["threadList"]).ThreadList

    async def get_chat_info(self, chatId: str):
        req = await self.getRequest(f"/g/s/chat/thread/{chatId}")
        return Thread(req["thread"]).Thread

    async def leave_chat(self, chatId: str):
        req = await self.deleteRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}")
        return Json(req)

    async def join_chat(self, chatId: str):
        req = await self.postRequest(f"/g/s/chat/thread/{chatId}/member/{self.uid}")
        return Json(req)

    async def start_chat(
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

        req = await self.postRequest(f"/g/s/chat/thread", data)
        return Thread(req['thread']).Thread

    async def get_from_link(self, link: str):
        req = await self.getRequest(f"/g/s/link-resolution?q={link}")
        return FromCode(req["linkInfoV2"]["extensions"]).FromCode

    async def edit_profile(
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
            data["icon"] = self.upload_image(icon)
        if backgroundColor:
            data["extensions"]["style"]["backgroundColor"] = backgroundColor
        if defaultBubbleId:
            data["extensions"] = {"defaultBubbleId": defaultBubbleId}
        if backgroundImage:
            data["extensions"]["style"] = {
                "backgroundMediaList": [[100, backgroundImage, None, None, None]]
            }

        req = await self.postRequest(f"/g/s/user-profile/{self.uid}", data)
        return Json(req)

    async def flag_community(self, comId: str, reason: str, flagType: int):
        data = {
            "objectId": comId,
            "objectType": 16,
            "flagType": flagType,
            "message": reason,
            "timestamp": int(timestamp() * 1000),
        }
        req = await self.postRequest(f"/x{comId}/s/g-flag", data)
        return Json(req)

    async def leave_community(self, comId: str):
        req = await self.postRequest(f"x/{comId}/s/community/leave")
        return Json(req)

    async def join_community(self, comId: str, InviteId: str = None):
        data = {"timestamp": int(timestamp() * 1000)}
        if InviteId:
            data["invitationId"] = InviteId

        req = await self.postRequest(f"/x{comId}/s/community/join", data)
        return Json(req)

    async def flag(
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

        data = {"message": reason, "timestamp": int(timestamp() * 1000)}

        if flagType in types:
            data["flagType"] = types.get(flagType)
        else:
            raise TypeError("choose a certain type to report")

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
            raise TypeError("Please put blog or user or wiki Id")

        req = await self.postRequest("/g/s/flag", data)
        return Json(req)

    async def unfollow(self, userId: str):
        req = await self.postRequest(f"/g/s/user-profile/{userId}/member/{self.uid}")
        return Json(req)

    async def follow(self, userId: Union[str, list]):
        data = {"timestamp": int(timestamp() * 1000)}

        if isinstance(userId, str):
            link = f"/g/s/user-profile/{userId}/member"
        elif isinstance(userId, list):
            data["targetUidList"] = userId
            link = f"/g/s/user-profile/{self.uid}/joined"

        req = await self.postRequest(link, data)
        return Json(req)

    async def get_member_following(self, userId: str, start: int = 0, size: int = 25):
        req = await self.getRequest(
            f"/g/s/user-profile/{userId}/joined?start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    async def get_member_followers(self, userId: str, start: int = 0, size: int = 25):
        req = await self.getRequest(
            f"/g/s/user-profile/{userId}/member?start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    async def get_member_visitors(self, userId: str, start: int = 0, size: int = 25):
        req = await self.getRequest(
            f"/g/s/user-profile/{userId}/visitors?start={start}&size={size}"
        )
        return VisitorsList(req["visitors"]).VisitorsList

    async def get_blocker_users(self, start: int = 0, size: int = 25):
        req = await self.getRequest(f"/g/s/block/full-list?start={start}&size={size}")
        return req["blockerUidList"]

    async def get_blocked_users(self, start: int = 0, size: int = 25):
        req = await self.getRequest(f"/g/s/block/full-list?start={start}&size={size}")
        return req["blockedUidList"]

    async def get_wall_comments(
        self, userId: str, sorting: str = "newest", start: int = 0, size: int = 25
    ):
        sorting = sorting.lower().replace("top", "vote")
        if sorting not in ["newest", "oldest", "vote"]:
            raise TypeError("حط تايب يا حمار")

        req = await self.getRequest(
            f"/g/s/user-profile/{userId}/g-comment?sort={sorting}&start={start}&size={size}"
        )
        return CommentList(req["commentList"]).CommentList

    async def get_blog_comments(
        self,
        wikiId: str = None,
        blogId: str = None,
        sorting: str = "newest",
        size: int = 25,
        start: int = 0,
    ):
        sorting = sorting.lower().replace("top", "vote")

        if sorting not in ["newest", "oldest", "vote"]:
            raise TypeError("Please insert a valid sorting")
        if blogId:
            link = (
                f"/g/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}"
            )
        elif wikiId:
            link = (
                f"/g/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}"
            )
        else:
            raise TypeError("Please choose a wiki or a blog")

        req = await self.getRequest(link)
        return CommentList(req["commentList"]).CommentList

    async def send_message(
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
                embedImage = [[100, self.upload_image(embedImage), None]]
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

        req = await self.postRequest(f"/g/s/chat/thread/{chatId}/message", data)
        return Json(req)

    async def get_community_info(self, comId: str):
        link = (
            f"/g/s-x{comId}/community/info"
            f"?withInfluencerList=1"
            f"&withTopicList=true"
            f"&influencerListOrderStrategy=fansCount"
        )
        req = await self.getRequest(link)
        return Community(req["community"]).Community

    async def mark_as_read(self, chatId: str):
        req = await self.postRequest(f"/g/s/chat/thread/{chatId}/mark-as-read")
        return Json(req)

    async def delete_message(self, messageId: str, chatId: str):
        req = await self.deleteRequest(f"/g/s/chat/thread/{chatId}/message/{messageId}")
        return Json(req)

    async def get_chat_messages(self, chatId: str, size: int = 25):
        req = await self.getRequest(
            f"/g/s/chat/thread/{chatId}/message?v=2&pagingType=t&size={size}"
        )
        return GetMessages(req["messageList"]).GetMessages

    async def get_message_info(self, messageId: str, chatId: str):
        req = await self.getRequest(f"/g/s/chat/thread/{chatId}/message/{messageId}")
        return Message(req["message"]).Message

    async def tip_coins(
        self,
        chatId: str = None,
        blogId: str = None,
        coins: int = 0,
        transactionId: str = None,
    ):
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
            raise TypeError("please put chat or blog Id")

        req = await self.postRequest(link, data)
        return Json(req)

    async def reset_password(
        self, email: str, password: str, code: str, deviceId: str = None
    ):
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

        req = await self.postRequest("/g/s/auth/reset-password", data)
        return Json(req)

    async def change_password(self, password: str, newPassword: str):
        data = {
            "secret": f"0 {password}",
            "updateSecret": f"0 {newPassword}",
            "validationContext": None,
            "deviceID": self.deviceId,
        }

        req = await self.postRequest("/g/s/auth/change-password", data)
        return Json(req)

    async def get_user_info(self, userId: str):
        req = await self.getRequest(f"/g/s/user-profile/{userId}")
        return UserProfile(req["userProfile"]).UserProfile

    async def comment(self, comment: str, userId: str = None, replyTo: str = None):
        data = {
            "content": comment,
            "stickerId": None,
            "type": 0,
            "eventSource": "UserProfileView",
            "timestamp": int(timestamp() * 1000),
        }

        if replyTo:
            data["respondTo"] = replyTo
        req = await self.postRequest(f"/g/s/user-profile/{userId}/g-comment", data)
        return Json(req)

    async def delete_comment(self, userId: str = None, commentId: str = None):
        req = await self.deleteRequest(f"/g/s/user-profile/{userId}/g-comment/{commentId}")
        return Json(req)

    async def invite_by_host(self, chatId: str, userId: Union[str, list]):
        data = {"uidList": userId, "timestamp": int(timestamp() * 1000)}
        req = await self.postRequest(f"/g/s/chat/thread/{chatId}/avchat-members", data)
        return Json(req)

    async def kick(self, chatId: str, userId: str, rejoin: bool = True):
        rejoin = 1 if rejoin else 0
        req = await self.deleteRequest(
            f"/g/s/chat/thread/{chatId}/member/{userId}?allowRejoin={rejoin}"
        )
        return Json(req)

    async def get_invise_users(self, master_type = "newest", start: int = 0, size: int = 25):

        """
            function for masteringInvite:
                master_type:
                    new/newest : invited new usres from all ndcs or
                    online : invited online users from all ndcs
        """

        req = await self.getRequest(
            f"/g/s/user-profile?type={master_type}&start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    async def invise_invite(self, chatId: str, userId: Union[str, list]):

        """
            Invite users in your room global
                arguments:
                    userId: id object for users
                    chatId: id object for chats

                use as:
                    chat_info = client.get_from_link(input("chat link:  "))
                    chat_id = chat_info.objectId
                    # need function for invite user objext

      """

        if isinstance(userId, str): userIds = [userId]
        elif isinstance(userId, list): userIds = userId
        else: raise exceptions.WrongType

        data = {
            "uids": userIds,
            "timestamp": int(timestamp() * 1000)
        }

        req = await self.postRequest(f"/g/s/chat/thread/{chatId}/member/invite", data)
        return Json(req)

    async def block(self, userId: str):
        req = await self.postRequest(f"/g/s/block/{userId}")
        return Json(req)

    async def unblock(self, userId: str):
        req = await self.deleteRequest(f"/g/s/block/{userId}")
        return Json(req)

    async def get_public_chats(
        self, filterType: str = "recommended", start: int = 0, size: int = 50
    ):
        req = await self.getRequest(
            f"/g/s/chat/thread?type=public-all&filterType={filterType}&start={start}&size={size}"
        )
        return ThreadList(req["threadList"]).ThreadList

    async def get_content_modules(self, version: int = 2):
        req = await self.getRequest(f"/g/s/home/discover/content-modules?v={version}")
        return Json(req)

    async def get_banner_ads(self, size: int = 25, pagingType: str = "t"):
        link = (
            f"/g/s/topic/0/feed/banner-ads"
            f"?moduleId=711f818f-da0c-4aa7-bfa6-d5b58c1464d0&adUnitId=703798"
            f"&size={size}"
            f"&pagingType={pagingType}"
        )

        req = await self.getRequest(link)
        return ItemList(req["itemList"]).ItemList

    async def get_announcements(self, lang: str = "en", start: int = 0, size: int = 20):
        req = await self.getRequest(
            f"/g/s/announcement?language={lang}&start={start}&size={size}"
        )
        return BlogList(req["blogList"]).BlogList

    async def get_public_ndc(self, content_language: str = "en", size: int = 25):
        """
             for content_language:
                 content_language:
                     en:  english communities
                     de:  deuth communities
                     ru:  russian communities
                     es: espaniol communities
                     pt: portuguse communities
                     fr: francias communities
                     ar:  arabic communities

                   """
        req = await self.getRequest(f"/g/s/topic/0/feed/community?language={content_language}&type=web-explore&categoryKey=recommendation&size={size}&pagingType=t")
        return CommunityList(req["communityList"]).CommunityList

    async def search_community(
        self, word: str, lang: str = "en", start: int = 0, size: int = 25
    ):
        req = await self.getRequest(
            f"/g/s/community/search?q={word}&language={lang}&completeKeyword=1&start={start}&size={size}"
        )
        return CommunityList(req["communityList"]).CommunityList

    async def invite_to_voice_chat(self, userId: str = None, chatId: str = None):
        data = {"uid": userId, "timestamp": int(timestamp() * 1000)}
        req = await self.postRequest(
            f"/g/s/chat/thread/{chatId}/vvchat-presenter/invite", data
        )
        return Json(req)

    async def get_wallet_history(self, start: int = 0, size: int = 25):
        req = await self.getRequest(f"/g/s/wallet/coin/history?start={start}&size={size}")
        return WalletHistory(req).WalletHistory

    async def get_wallet_info(self):
        req = await self.getRequest("/g/s/wallet")
        return WalletInfo(req["wallet"]).WalletInfo

    async def get_all_users(self, usersType: str = "recent", start: int = 0, size: int = 25):
        """
        Types:
            - recent
            - banned
            - featured
            - leaders
            - curators
        """
        req = await self.getRequest(
            f"/g/s/user-profile?type={usersType}&start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    async def get_chat_members(self, start: int = 0, size: int = 25, chatId: str = None):
        req = await self.getRequest(
            f"/g/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2"
        )
        return UserProfileList(req["memberList"]).UserProfileList

    async def get_from_id(
        self, objectId: str, comId: str = None, objectType: int = 2
    ):  # never tried
        data = {
            "objectId": objectId,
            "targetCode": 1,
            "objectType": objectType,
            "timestamp": int(timestamp() * 1000),
        }

        link = f"/g/s/link-resolution"

        if comId:
            link = f"/g/s-x{comId}/link-resolution"

        req = await self.postRequest(link, data)
        return FromCode(req["linkInfoV2"]["extensions"]["linkInfo"]).FromCode

    async def chat_settings(
        self,
        chatId: str,
        viewOnly: bool = None,
        doNotDisturb: bool = None,
        canInvite: bool = False,
        canTip: bool = None,
        pin: bool = None,
    ):
        res = []

        if doNotDisturb:
            if doNotDisturb:
                opt = 2
            else:
                opt = 1
            data = {"alertOption": opt, "timestamp": int(timestamp() * 1000)}
            req = await self.postRequest(
                f"/g/s/chat/thread/{chatId}/member/{self.uid}/alert", data
            )
            res.append(Json(req))

        if viewOnly is not None:
            if viewOnly:
                viewOnly = "enable"
            else:
                viewOnly = "disable"
            req = await self.postRequest(f"/g/s/chat/thread/{chatId}/view-only/{viewOnly}")
            res.append(Json(req))

        if canInvite:
            if canInvite:
                canInvite = "enable"
            else:
                canInvite = "disable"
            req = await self.postRequest(
                f"/g/s/chat/thread/{chatId}/members-can-invite/{canInvite}"
            )
            res.append(Json(req))

        if canTip:
            if canTip:
                canTip = "enable"
            else:
                canTip = "disable"
            req = await self.postRequest(
                f"/g/s/chat/thread/{chatId}/tipping-perm-status/{canTip}"
            )
            res.append(Json(req))

        if pin:
            if pin:
                pin = "pin"
            else:
                pin = "unpin"
            req = await self.postRequest(f"/g/s/chat/thread/{chatId}/{pin}")
            res.append(Json(req))

        return res

    async def like_comment(self, commentId: str, userId: str = None, blogId: str = None):
        data = {"value": 4, "timestamp": int(timestamp() * 1000)}

        if userId:
            link = (
                f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?cv=1.2&value=1"
            )
        elif blogId:
            link = f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?cv=1.2&value=1"
        else:
            raise TypeError("Please put blog or user Id")

        req = await self.postRequest(link, data)
        return Json(req)

    async def unlike_comment(self, commentId: str, blogId: str = None, userId: str = None):
        if userId:
            link = f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView"
        elif blogId:
            link = f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView"
        else:
            raise TypeError("Please put blog or user Id")

        req = await self.deleteRequest(link)
        return Json(req)

    async def register(
        self, nickname: str, email: str, password: str, code: str, deviceId: str = None
    ):
        if deviceId is None:
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

        req = await self.postRequest("/g/s/auth/register", data)
        return Json(req)

    async def ads_config(
        self,
        chatId: str,
        title: str = None,
        content: str = None,
        icon: str = None,
        background: str = None,
        ):
        res, data = [], {"timestamp": int(timestamp() * 1000)}

        if title:
            data["title"] = title

        if content:
            data["content"] = content

        if icon:
            data["icon"] = icon

        if background:
            data = {
                "media": [100, background, None],
                "timestamp": int(timestamp() * 1000),
            }
            req = await self.postRequest(
                f"/g/s/chat/thread/{chatId}/member/{self.uid}/background",
                data,
            )
            res.append(Json(req))

        req = await self.postRequest(f"/g/s/chat/thread/{chatId}", data)
        res.append(Json(req))
        return res

    async def remove_host(self, chatId: str, userId: str):
        req = await self.deleteRequest(f"/g/s/chat/thread/{chatId}/co-host/{userId}")
        return Json(req)

    async def edit_comment(self, commentId: str, comment: str, userId: str):
        data = {"content": comment, "timestamp": int(timestamp() * 1000)}
        req = await self.postRequest(f"/g/s/user-profile/{userId}/comment/{commentId}", data)
        return Comment(req).Comments

    async def get_comment_info(self, commentId: str, userId: str):
        req = await self.getRequest(f"/g/s/user-profile/{userId}/comment/{commentId}")
        return Comment(req).Comments

    async def get_notifications(self, size: int = 25, pagingType: str = "t"):
        req = await self.getRequest(f"/g/s/notification?pagingType={pagingType}&size={size}")
        return NotificationList(req).NotificationList

    async def get_notices(
        self, start: int = 0, size: int = 25, noticeType: str = "usersV2", status: int = 1
    ):
        req = await self.getRequest(
            f"/g/s/notice?type={noticeType}&status={status}&start={start}&size={size}"
        )
        return NoticeList(req).NoticeList

    async def accept_promotion(self, requestId: str):
        req = await self.postRequest(f"/g/s/notice/{requestId}/accept")
        return Json(req)

    async def decline_promotion(self, requestId: str):
        req = await self.postRequest(f"/g/s/notice/{requestId}/decline")
        return Json(req)
