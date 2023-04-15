# those sockets are based on: Amino-Sockets & Amino.py

import threading
import time as timer
from sys import _getframe as getframe
from typing import Union

import ujson as json
import websocket

from ..lib import *
from ..lib.objects import *
from .bot import Bot


class Callbacks(Bot):
    def __init__(self, is_bot: bool = False, prefix: str = "!"):
        Bot.__init__(self, prefix=prefix)

        # if the user want to use the script as a bot
        self.is_bot = is_bot

        self.handlers = {}

        self.methods = {
            10: self._resolve_payload,
            201: self._resolve_channel,
            304: self._resolve_chat_action_start,
            306: self._resolve_chat_action_end,
            400: self._resolve_topics,
            1000: self._resolve_chat_message,
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
            "65283:0": self.on_invite_message,
        }

        self.notif_methods = {
            "18": self.on_alert,
            "53": self.on_member_set_you_host,
            "67": self.on_member_set_you_cohost,
            "68": self.on_member_remove_you_cohost,
        }

        self.chat_action_methods = {
            "fetch-channel": self.on_fetch_channel,
            "Typing-start": self.on_user_typing_start,
            "Typing-end": self.on_user_typing_end,
        }

        self.topics = {
            "online-members": self.on_online_users_update,
            "users-start-typing-at": self.on_user_typing_start,
            "users-end-typing-at": self.on_user_typing_end,
            "users-start-recording-at": self.on_voice_chat_start,
            "users-end-recording-at": self.on_voice_chat_end,
        }

    def _resolve_chat_action_start(self, data):
        key = data['o'].get('actions', 0)+"-start"
        return self.chat_action_methods.get(key, self.default)(data)

    def _resolve_chat_action_end(self, data):
        key = data['o'].get('actions', 0)+"-end"
        return self.chat_action_methods.get(key, self.default)(data)

    def _resolve_channel(self, data):
            if data['t'] == 201:
                return self.chat_action_methods.get("fetch-channel")(data)

    def _resolve_payload(self, data):
        key = f"{data['o']['payload']['notifType']}"
        return self.notif_methods.get(key)(data)

    def _resolve_chat_message(self, data):
        key = f"{data['o']['chatMessage']['type']}:{data['o']['chatMessage'].get('mediaType', 0)}"
        return self.chat_methods.get(key)(data)

    def _resolve_topics(self, data):
        key = str(data["o"].get("topic", 0)).split(":")[2]
        return self.topics.get(key)(data)

    def resolve(self, data):
        data = json.loads(data)
        return self.methods.get(data["t"])(data)

    def call(self, callType, data):
        if self.handlers.get(callType):
            for handler in self.handlers[callType]:
                handler(data)

    def event(self, eventType):
        def registerHandler(handler):
            if self.handlers.get(eventType):
                self.handlers[eventType].append(handler)
            else:
                self.handlers[eventType] = [handler]
            return handler

        return registerHandler

    def setCall(self, name, data):
        self.call(name, Event(data["o"]).Event)

    def on_text_message(self, data):
        if self.is_bot:
            new_data = Event(data["o"]).Event
            new_data = self.build_parameters(new_data)
            self.trigger(new_data, str_only=True)

        self.setCall(getframe(0).f_code.co_name, data)

    def on_alert(self, data): self.call(getframe(0).f_code.co_name, Payload(data["o"]["payload"]).Payload)
    def on_member_set_you_host(self, data): self.call(getframe(0).f_code.co_name, Payload(data["o"]["payload"]).Payload)
    def on_member_remove_you_cohost(self, data): self.call(getframe(0).f_code.co_name, Payload(data["o"]["payload"]).Payload)
    def on_member_set_you_cohost(self, data): self.call(getframe(0).f_code.co_name, Payload(data["o"]["payload"]).Payload)

    def on_image_message(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_youtube_message(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_strike_message(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_voice_message(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_sticker_message(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def TYPE_USER_SHARE_EXURL(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def TYPE_USER_SHARE_USER(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_voice_chat_not_answered(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_voice_chat_not_cancelled(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_voice_chat_not_declined(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_video_chat_not_answered(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_video_chat_not_cancelled(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_video_chat_not_declined(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_avatar_chat_not_answered(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_avatar_chat_not_cancelled(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_avatar_chat_not_declined(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_delete_message(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_group_member_join(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_group_member_leave(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_invite(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_background_changed(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_title_changed(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_icon_changed(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_voice_chat_start(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_video_chat_start(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_avatar_chat_start(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_voice_chat_end(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_video_chat_end(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_avatar_chat_end(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_content_changed(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_screen_room_start(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_screen_room_end(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_host_transfered(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_text_message_force_removed(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_removed_message(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_text_message_removed_by_admin(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_tip(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_pin_announcement(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_voice_chat_permission_open_to_everyone(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_voice_chat_permission_invited_and_requested(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_voice_chat_permission_invite_only(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_view_only_enabled(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_view_only_disabled(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_unpin_announcement(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_tipping_enabled(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_chat_tipping_disabled(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_timestamp_message(self, data): self.setCall(getframe(0).f_code.co_name, data)

    def on_welcome_message(self, data): self.setCall(getframe(0).f_code.co_name, data)
    def on_invite_message(self, data): self.setCall(getframe(0).f_code.co_name, data)

    def on_user_typing_start(self, data): self.call(getframe(0).f_code.co_name, UsersActions(data).UsersActions)
    def on_user_typing_end(self, data): self.call(getframe(0).f_code.co_name, UsersActions(data).UsersActions)
    def on_online_users_update(self, data): self.call(getframe(0).f_code.co_name, UsersActions(data).UsersActions)

    def on_fetch_channel(self, data): self.call(getframe(0).f_code.co_name, Payload(data["o"]["payload"]).Payload)

    def default(self, data): self.call(getframe(0).f_code.co_name, data)


class SetAction:
    def __init__(self, wss, data):
        self.action = data
        self.wss = wss

    def start(self):
        """
        Start the Action
        """
        self.wss.send(self.action)

    def stop(self):
        """
        Get back to the last board
        """
        act = self.action
        act["t"] = 303
        self.wss.send(self.action)


class Actions:
    def __init__(self, socket, comId, chatId):
        self.socket = socket
        self.chatId = chatId
        self.comId = comId

    def setDefaultAction(self):
        """
        Default Browsing
        """
        SetAction(
            self.socket,
            {
                "o": {
                    "actions": ["Browsing"],
                    "target": f"ndc://x{self.comId}/",
                    "ndcId": int(self.comId),
                    "params": {"duration": 27605},
                    "id": "363483",
                },
                "t": 306,
            },
        ).start()

    def Browsing(self, blogId: str = None, blogType: int = 0):
        """
        Send Browsing Action

        **Parameters**
            - **blogId**: target blogId (str)
            - **blogType**: Type Of the Blog *poll & blog & wiki* (int)

        **Return**
            - **SetAction**:  (Class)
        """
        target = f"ndc://x{self.comId}/featured"

        if blogId and blogType:
            target = f"ndc://x{self.comId}/blog/"

        data = {
            "o": {
                "actions": ["Browsing"],
                "target": target,
                "ndcId": int(self.comId),
                "params": {"blogType": blogType},
                "id": "363483",
            },
            "t": 306,
        }
        self.setDefaultAction()
        return SetAction(self.socket, data)

    def Chatting(self, threadId: str = None, threadType: int = 2):
        """
        Send Chatting Action

        **Paramaters**
            - **threadType**: 2 For Public 1 & 0 For Private (int)

        **Return**
            - **SetAction**:  (Class)
        """

        data = {
            "o": {
                "actions": ["Chatting"],
                "target": f"ndc://x{self.comId}/chat-thread/{self.chatId}",
                "ndcId": int(self.comId),
                "params": {
                    "duration": 12800,
                    "membershipStatus": 1,
                    "threadType": threadType,
                    "threadId": threadId,
                },
                "id": "1715976",
            },
            "t": 306,
        }
        # self.defaultData()
        return SetAction(self.socket, data)

    def PublicChats(self):
        """
        Send PublicChats Action

        **Return**
            - **SetAction**:  (Class)
        """
        data = {
            "o": {
                "actions": ["Browsing"],
                "target": f"ndc://x{self.comId}/public-chats",
                "ndcId": int(self.comId),
                "params": {"duration": 859},
                "id": "363483",
            },
            "t": 306,
        }
        self.setDefaultAction()
        return SetAction(self.socket, data)

    def LeaderBoards(self):
        """
        Send LeaderBoard Action

        **Return**
            - **SetAction**:  (Class)
        """
        data = {
            "o": {
                "actions": ["Browsing"],
                "target": f"ndc://x{self.comId}/leaderboards",
                "ndcId": int(self.comId),
                "params": {"duration": 859},
                "id": "363483",
            },
            "t": 306,
        }
        self.setDefaultAction()
        return SetAction(self.socket, data)

    def Custom(self, actions: Union[str, list], target: str, params: dict):
        """
        Send Custom Action

        **Parameters**
            - **actions**: List of action Types (list[str])
            - **target**: Example | ndc://x000000/leaderboards (str)
            - **params**: Set the blogType and more with params (dict)

        **Return**
            - **SetAction**:  (Class)
        """
        data = {
            "o": {
                "actions": actions,
                "target": target,
                "ndcId": int(self.comId),
                "params": params,
                "id": "363483",
            },
            "t": 306,
        }
        self.setDefaultAction()
        return SetAction(self.socket, data)


class WssClient:
    def __init__(self, wss):
        self.wss = wss

    def joinVoiceChat(self, comId: str, chatId: str, joinType: int = 1):

        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": joinType,
                "id": "37549515",
            },
            "t": 112,
        }
        timer.sleep(2.2)
        self.wss.send(data)

    def joinVideoChat(self, comId: str, chatId: str, joinType: int = 1):
        """
        Join The Video Chat

        **Parameters**
            - **comId**: ID of the Community (str)
            - **chatId**: ID of the Chat (str)
            - **joinType**: Join type to Join Video as.. (int)
        """
        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": joinType,
                "channelType": 5,
                "id": "2154531",
            },
            "t": 108,
        }
        timer.sleep(2.2)
        self.wss.send(data)

    def startVoiceChat(self, comId, chatId: str, joinType: int = 1):
        """
        Start The Voice Chat

        **Parameters**
            - **comId**: ID of the Community (str)
            - **chatId**: ID of the Chat (str)
            - **joinType**: Join type to Start voice as.. (int)
        """
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": joinType,
                "id": "2154531",
            },
            "t": 112,
        }
        timer.sleep(2.2)
        self.wss.send(data)
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "channelType": 1,
                "id": "2154531",
            },
            "t": 108,
        }
        timer.sleep(2.2)
        self.wss.send(data)

    def endVoiceChat(self, comId: str, chatId: str, leaveType: int = 2):
        """
        End The Voice Chat

        **Parameters**
            - **comId**: ID of the Community (str)
            - **chatId**: ID of the Chat (str)
            - **leaveType**: Leave type to end voice as.. (int)
        """
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": leaveType,
                "id": "2154531",
            },
            "t": 112,
        }
        timer.sleep(2.2)
        self.wss.send(data)

    def joinVideoChatAsSpectator(self, comId: str, chatId: str):
        """
        Join Video Chat As Spectator

        **Parameters**
            - **comId**: ID of the Community (str)
            - **chatId**: ID of the Chat (str)
        """
        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": 2,
                "id": "72446",
            },
            "t": 112,
        }
        timer.sleep(2.2)
        self.wss.send(data)

    def threadJoin(self, comId: str, chatId: str):
        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": 1,
                "id": "10335106",
            },
            "t": 112,
        }
        self.wss.send(data)

    def channelJoin(self, comId: str, chatId: str):
        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "channelType": 5,
                "id": "10335436",
            },
            "t": 108,
        }
        self.wss.send(data)

    def GetUsersActions(self, comId: str = None, path: int = 0, chatId: str = None):
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
            5: "users-start-recording-at",
        }

        if chatId:
            topic = f'{acts.get(path, "users-chatting")}:{chatId}'
        else:
            topic = acts.get(path, "users-chatting")

        data = {
            "o": {
                "ndcId": int(comId) if comId else 0,
                "topic": f"ndtopic:x{comId}:{topic}",
                "id": "4538416",
            },
            "t": 300,
        }

        timer.sleep(2.2)
        self.wss.send(data)

        for i in range(3):
            if self.wss.receive():
                return UsersActions(data=self.wss.receive()).UsersActions
            else:
                continue

        return UsersActions(data={}).UsersActions

    def actions(self, comId: str, chatId: str):
        return Actions(self.wss, comId, chatId)


class Wss(Callbacks, WssClient, Headers):
    def __init__(self, client, trace: bool = False, is_bot: bool = False):

        self.trace = trace
        self.socket = None
        self.headers = None
        self.client = client
        self.isOpened = False

        Headers.__init__(self)
        Callbacks.__init__(self, is_bot=is_bot)
        WssClient.__init__(self, self)

        self.narvi = "https://service.narvii.com/api/v1/"
        self.socket_url = "wss://ws1.narvii.com"
        self.lastMessage = {}
        websocket.enableTrace(trace)

    def onOpen(self, *args):
        self.isOpened = True
        if self.trace:
            print("[ON-OPEN] Sockets are open")

    def onClose(self, *args):
        self.isOpened = False
        if self.trace:
            print("[ON-CLOSE] Sockets are closed")

    def send(self, data):
        self.socket.send(json.dumps(data))

    def receive(self):
        if self.trace:
            print("[RECEIVE] returning last message")
        return self.lastMessage

    def on_message(self, ws, data):
        self.lastMessage = json.loads(data)
        self.resolve(data)
        if self.trace:
            print("[ON-MESSAGE] Received a message . . .")

    def launch(self):
        final = f"{self.client.deviceId}|{int(timer.time() * 1000)}"
        self.headers = {
            "NDCDEVICEID": self.client.deviceId,
            "NDCAUTH": self.client.sid,
            "NDC-MSG-SIG": util.generateSig(data=final),
        }

        self.socket = websocket.WebSocketApp(
            f"{self.socket_url}/?signbody={final.replace('|', '%7C')}",
            on_message=self.on_message,
            on_close=self.onClose,
            on_open=self.onOpen,
            header=self.headers,
        )

        if self.trace:
            print("[LAUNCH] Sockets starting . . . ")
        threading.Thread(
            target=self.socket.run_forever, kwargs={"ping_interval": 60}
        ).start()

    def close(self):
        self.socket.close()
        if self.trace:
            print("[CLOSE] closing socket . . .")
        timer.sleep(1.5)

    def socket_status(self):
        print("\nSockets are OPEN\n") if self.isOpened else print(
            "\nSockets are CLOSED\n"
        )
