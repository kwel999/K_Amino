# those sockets are based on: Amino-Sockets / Amino.py
# Modified by SirLez, zett.0, Bovonos

import asyncio
import threading
import time
from sys import _getframe as getframe
from typing import Union, BinaryIO

import ujson as json
import websockets

from ..lib import *


class Callbacks:
    def __init__(self):
        self.handlers = {}

        self.methods = {
            10: self._resolve_payload,
            400: self._resolve_topics,
            1000: self._resolve_chat_message
        }

        self.chat_methods = {
            "0:0": self.on_text_message,
            "0:100": self.on_image_message,
            "0:103": self.on_youtube_message,
            "1:0": self.on_strike_message,
            "2:110": self.on_voice_message,
            "3:113": self.on_sticker_message,
            "50:0": self.TYPE_USER_SHARE_EXURL,
            "51:0": self.TYPE_USER_SHARE_USER,
            "52:0": self.on_voice_chat_not_answered,
            "53:0": self.on_voice_chat_not_cancelled,
            "54:0": self.on_voice_chat_not_declined,
            "55:0": self.on_video_chat_not_answered,
            "56:0": self.on_video_chat_not_cancelled,
            "57:0": self.on_video_chat_not_declined,
            "58:0": self.on_avatar_chat_not_answered,
            "59:0": self.on_avatar_chat_not_cancelled,
            "60:0": self.on_avatar_chat_not_declined,
            "100:0": self.on_delete_message,
            "101:0": self.on_group_member_join,
            "102:0": self.on_group_member_leave,
            "103:0": self.on_chat_invite,
            "104:0": self.on_chat_background_changed,
            "105:0": self.on_chat_title_changed,
            "106:0": self.on_chat_icon_changed,
            "107:0": self.on_voice_chat_start,
            "108:0": self.on_video_chat_start,
            "109:0": self.on_avatar_chat_start,
            "110:0": self.on_voice_chat_end,
            "111:0": self.on_video_chat_end,
            "112:0": self.on_avatar_chat_end,
            "113:0": self.on_chat_content_changed,
            "114:0": self.on_screen_room_start,
            "115:0": self.on_screen_room_end,
            "116:0": self.on_chat_host_transfered,
            "117:0": self.on_text_message_force_removed,
            "118:0": self.on_chat_removed_message,
            "119:0": self.on_text_message_removed_by_admin,
            "120:0": self.on_chat_tip,
            "121:0": self.on_chat_pin_announcement,
            "122:0": self.on_voice_chat_permission_open_to_everyone,
            "123:0": self.on_voice_chat_permission_invited_and_requested,
            "124:0": self.on_voice_chat_permission_invite_only,
            "125:0": self.on_chat_view_only_enabled,
            "126:0": self.on_chat_view_only_disabled,
            "127:0": self.on_chat_unpin_announcement,
            "128:0": self.on_chat_tipping_enabled,
            "129:0": self.on_chat_tipping_disabled,
            "65281:0": self.on_timestamp_message,
            "65282:0": self.on_welcome_message,
            "65283:0": self.on_invite_message
        }

        self.notif_methods = {
            "53": self.on_member_set_you_host,
            "67": self.on_member_set_you_cohost,
            "68": self.on_member_remove_you_cohost
        }

        self.topics = {
            "online-members": self.on_online_users_update,
            "users-start-typing-at": self.on_user_typing_start,
            "users-end-typing-at": self.on_user_typing_end,
            "users-start-recording-at": self.on_voice_chat_start,
            "users-end-recording-at": self.on_voice_chat_end
        }

    async def _resolve_payload(self, data):
        key = f"{data['o']['payload']['notifType']}"
        return await self.notif_methods.get(key, self.default)(data)

    async def _resolve_chat_message(self, data):
        key = f"{data['o']['chatMessage']['type']}:{data['o']['chatMessage'].get('mediaType', 0)}"
        return await self.chat_methods.get(key, self.default)(data)

    async def _resolve_topics(self, data):
        key = str(data['o'].get('topic', 0)).split(":")[2]
        return await self.topics.get(key, self.default)(data)

    def resolve(self, data):
        data = json.loads(data)
        return asyncio.create_task(self.methods.get(data["t"], self.default)(data))

    async def call(self, type, data):
        if type in self.handlers:
            for handler in self.handlers[type]:
                await handler(data)

    def event(self, type):
        def registerHandler(handler):
            if type in self.handlers:
                self.handlers[type].append(handler)
            else:
                self.handlers[type] = [handler]
            return handler

        return registerHandler

    async def on_member_set_you_host(self, data): await self.call(getframe(0).f_code.co_name, Payload(data["o"]).Payload)
    async def on_member_remove_you_cohost(self, data): await self.call(getframe(0).f_code.co_name, Payload(data["o"]).Payload)
    async def on_member_set_you_cohost(self, data): await self.call(getframe(0).f_code.co_name, Payload(data["o"]).Payload)

    async def on_text_message(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_image_message(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_youtube_message(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_strike_message(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_voice_message(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_sticker_message(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def TYPE_USER_SHARE_EXURL(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def TYPE_USER_SHARE_USER(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_voice_chat_not_answered(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_voice_chat_not_cancelled(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_voice_chat_not_declined(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_video_chat_not_answered(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_video_chat_not_cancelled(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_video_chat_not_declined(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_avatar_chat_not_answered(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_avatar_chat_not_cancelled(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_avatar_chat_not_declined(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_delete_message(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_group_member_join(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_group_member_leave(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_invite(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_background_changed(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_title_changed(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_icon_changed(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_voice_chat_start(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_video_chat_start(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_avatar_chat_start(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_voice_chat_end(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_video_chat_end(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_avatar_chat_end(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_content_changed(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_screen_room_start(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_screen_room_end(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_host_transfered(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_text_message_force_removed(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_removed_message(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_text_message_removed_by_admin(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_tip(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_pin_announcement(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_voice_chat_permission_open_to_everyone(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_voice_chat_permission_invited_and_requested(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_voice_chat_permission_invite_only(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_view_only_enabled(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_view_only_disabled(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_unpin_announcement(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_tipping_enabled(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_chat_tipping_disabled(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_timestamp_message(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_welcome_message(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)
    async def on_invite_message(self, data): await self.call(getframe(0).f_code.co_name, Event(data["o"]).Event)

    async def on_user_typing_start(self, data): await self.call(getframe(0).f_code.co_name, UsersActions(data).UsersActions)
    async def on_user_typing_end(self, data): await self.call(getframe(0).f_code.co_name, UsersActions(data).UsersActions)
    async def on_online_users_update(self, data): await self.call(getframe(0).f_code.co_name, UsersActions(data).UsersActions)

    async def default(self, data): await self.call(getframe(0).f_code.co_name, data)


class SetAction:
    def __init__(self, wss, data):
        self.action = data
        self.wss = wss

    def start(self):
        """
        Start the Action
        """
        self.wss.send(self.action)

    async def stop(self):
        """
        Get back to the last board
        """
        act = self.action
        act["t"] = 303
        await self.wss.send(self.action)


class Actions:
    def __init__(self, socket, comId, chatId):
        self.socket = socket
        self.chatId = chatId
        self.comId = comId

    def sendDefaultAction(self):
        SetAction(self.socket, {
            "o": {"actions": ["Browsing"], "target": f"ndc://x{self.comId}/", "ndcId": int(self.comId),
                  "params": {"duration": 27605}, "id": "363483"}, "t": 306}).start()

    def Browsing(self, blogId: str = None, blogType: int = 0):

        if blogId and blogType:
            target = f"ndc://x{self.comId}/blog/"
        else:
            target = f"ndc://x{self.comId}/featured"

        data = {
            "o": {
                "actions": ["Browsing"],
                "target": target,
                "ndcId": int(self.comId),
                "params": {"blogType": blogType},
                "id": "363483"
            },
            "t": 306
        }
        self.sendDefaultAction()
        return SetAction(self.socket, data)

    def Chatting(self, threadType: int = 2):

        data = {
            "o": {
                "actions": ["Chatting"],
                "target": f"ndc://x{self.comId}/chat-thread/{self.chatId}",
                "ndcId": int(self.comId),
                "params": {
                    "duration": 12800,
                    "membershipStatus": 1,
                    "threadType": threadType
                },
                "id": "1715976"
            },
            "t": 306
        }
        self.sendDefaultAction()
        return SetAction(self.socket, data)

    def PublicChats(self):

        data = {
            "o": {
                "actions": ["Browsing"],
                "target": f"ndc://x{self.comId}/public-chats",
                "ndcId": int(self.comId),
                "params": {"duration": 859},
                "id": "363483"
            },
            "t": 306
        }
        self.sendDefaultAction()
        return SetAction(self.socket, data)

    def LeaderBoards(self):

        data = {
            "o": {
                "actions": ["Browsing"],
                "target": f"ndc://x{self.comId}/leaderboards",
                "ndcId": int(self.comId),
                "params": {"duration": 859},
                "id": "363483"
            },
            "t": 306
        }
        self.sendDefaultAction()
        return SetAction(self.socket, data)

    def Custom(self, actions: Union[str, list], target: str, params: dict):

        data = {
            "o": {
                "actions": actions,
                "target": target,
                "ndcId": int(self.comId),
                "params": params,
                "id": "363483"
            },
            "t": 306
        }
        self.sendDefaultAction()
        return SetAction(self.socket, data)


class WssClient:
    def __init__(self, wss):
        self.wss = wss

    async def joinVoiceChat(self, comId: str, chatId: str, joinType: int = 1):

        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": joinType,
                "id": "37549515"
            },
            "t": 112
        }
        await asyncio.sleep(2)
        await self.wss.send(data)

    async def joinVideoChat(self, comId: str, chatId: str, joinType: int = 1):

        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": joinType,
                "channelType": 5,
                "id": "2154531"
            },
            "t": 108
        }
        await asyncio.sleep(2)
        await self.wss.send(data)

    async def startVoiceChat(self, comId, chatId: str, joinType: int = 1):

        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": joinType,
                "id": "2154531"
            },
            "t": 112
        }
        await asyncio.sleep(2)
        await self.wss.send(data)
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "channelType": 1,
                "id": "2154531"
            },
            "t": 108
        }
        await asyncio.sleep(2)
        await self.wss.send(data)

    async def endVoiceChat(self, comId: str, chatId: str, leaveType: int = 2):

        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": leaveType,
                "id": "2154531"
            },
            "t": 112
        }
        await asyncio.sleep(2)
        await self.wss.send(data)

    async def joinVideoChatAsSpectator(self, comId: str, chatId: str):

        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": 2,
                "id": "72446"
            },
            "t": 112
        }
        await asyncio.sleep(2)
        await self.wss.send(data)

    async def threadJoin(self, comId: str, chatId: str):
        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": 1,
                "id": "10335106"
            },
            "t": 112
        }
        await self.wss.send(data)

    async def channelJoin(self, comId: str, chatId: str):
        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "channelType": 5,
                "id": "10335436"
            },
            "t": 108
        }
        await self.wss.send(data)

    async def videoPlayer(self, comId: str, chatId: str, path: str, title: str, background: str, duration: int):
        await self.actions(comId, chatId).Chatting().start()
        await self.threadJoin(comId, chatId)
        await self.channelJoin(comId, chatId)
        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "playlist": {
                    "currentItemIndex": 0,
                    "currentItemStatus": 1,
                    "items": [{
                        "author": None,
                        "duration": duration,
                        "isDone": False,
                        "mediaList": [[100, background, None]],
                        "title": title,
                        "type": 1,
                        "url": f"file://{path}"
                    }]
                },
                "id": "3423239"
            },
            "t": 120
        }
        await self.wss.send(data)
        await asyncio.sleep(2)
        data["o"]["playlist"]["currentItemStatus"] = 2
        data["o"]["playlist"]["items"][0]["isDone"] = True
        await self.wss.send(data)

    async def playVideo(self, comId: str, chatId: str, path: str, title: str, background: BinaryIO, duration: int):

        threading.Thread(target=self.videoPlayer, args=(comId, chatId, path, title, await self.wss.uploadMedia(background, "image"), duration)).start()

    async def GetUsersActions(self, comId: str, path: int = 0, chatId: str = None):
        """
            Get users actions:
            This functions gets certain socket actions happening
            such as online users and users chatting

            Parameters
            ----------
            comId : int
                the community id -required
            path : int
                takes an intger >= 0 and <= 5 each one sends a certain action
                not required -set by default to 0 // users-chatting
            chatId : str
                the chatId used in certain actions such as 'users-start-typing-at -Optional
                
            Returns
            ----------
            A Class property if there is a new message it will contain a userProfileList
            you can explore 'UsersActions' in objects file  
        """
        acts = {
            0: "users-chatting",
            1: "online-members",
            2: "users-start-typing-at",
            3: "users-end-typing-at",
            4: "users-start-recording-at",
            5: "users-start-recording-at"
        }

        if chatId: topic = f'{acts.get(path, "users-chatting")}:{chatId}'
        else: topic = acts.get(path, "users-chatting")

        data = {
            "o": {
                "ndcId": int(comId),
                "topic": f"ndtopic:x{comId}:{topic}",
                "id": "4538416"
            },
            "t": 300
        }

        asyncio.sleep(2.2)
        await self.wss.send(data)
        if (await self.wss.receive()): return UsersActions((await self.wss.receive())).UsersActions
        else: print('\nWaiting for messages . . .\n')

    async def actions(self, comId: str, chatId: str):
        threading.Thread(target=await self.wss.sendWebActive, args=(comId, )).start()
        return Actions(self.wss, comId, chatId)

class Wss(Callbacks, WssClient, Headers):
    def __init__(self, client, Session, Trace):
        self.client = client
        self.ses = Session

        Headers.__init__(self)
        Callbacks.__init__(self)
        WssClient.__init__(self, self)

        self.narvi = "https://service.narvii.com/api/v1/"
        self.socket_url = "wss://ws1.narvii.com"
        self.lastMessage = {}
        self.isOpened = False
        self.Trace = Trace
        self.Ran = False
        self.socket: websockets = None

        self.web_headers = self.web_headers
        self.headers = self.headers

    def receive(self):
        return self.lastMessage

    async def send(self, data):
        if self.Trace:print("Sending Data")
        data = json.dumps(data)
        await self.socket.send(data)

    async def on_message(self, data):
        self.resolve(data)

    async def Runner(self):
        final = f"{self.client.deviceId}|{int(time.time() * 1000)}"
        self.headers = {
            "NDCDEVICEID": self.client.deviceId,
            "NDCAUTH": self.client.sid,
            "NDC-MSG-SIG": util.generateSig(data=final)}
        try:
            async with websockets.connect(f"{self.socket_url}/?signbody={final.replace('|', '%7C')}", extra_headers=self.headers) as webs:
                self.socket = webs
                self.Ran = True
                if self.Trace: print("[Starting][Runner] Socket Started")
                while self.Ran:
                    try: message = await webs.recv()
                    except websockets.exceptions.ConnectionClosedOK: continue
                    await self.on_message(message)
        except RuntimeError: pass

    async def Launch(self):
        if self.Trace: print("[Starting][Launch] Running Amino Sockets")
        asyncio.create_task(self.Runner())
        while True:
            await asyncio.sleep(360)
            if self.socket.closed: return
            await self.close()
            asyncio.create_task(self.Runner())

    async def Start(self):
        if self.Trace:print("[Starting][Start] Starting Socket")
        threading.Thread(target = asyncio.run, args = (self.Launch(), )).start()

    async def close(self):
        if self.Trace:print("[Closing][close] Closing Socket")

        self.Ran = False
        try:
            if self.socket is not None:await self.socket.close()
            else:
                await asyncio.sleep(2.2)
                await self.socket.close()
        except Exception as e:
            if self.Trace: print(f"[Closing][close] Error occured {e}")

    async def uploadMedia(self, file: BinaryIO, fileType: str):
        if fileType == "audio":typee = "audio/aac"
        elif fileType == "image":typee = "image/jpg"
        else:raise TypeError("Wrong fileType")

        data = file.read()
        self.headers["content-type"] = typee
        self.headers["content-length"] = str(len(data))

        async with self.ses.post(f"{self.narvi}/g/s/media/upload", data=data, headers=headers) as response:
            if await response.json()["api:statuscode"] != 0: return CheckExceptions(await response.json())
            return await response.json()["mediaValue"]

    async def sendWebActive(self, comId: str):
        data = {"ndcId": comId}
        async with self.ses.post(webApi("/community/stats/web-user-active-time"), json=data, headers=self.web_headers) as response:
            if await response.json()["code"] != 200: return CheckExceptions(await response.json())
            return await response
