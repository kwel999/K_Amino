from __future__ import annotations
import threading
import time
try:
    import ujson as json
except ImportError:
    import json
import websocket
from functools import wraps
from inspect import signature as fsignature
from typing import Any, Callable, Dict, List, Optional, TypeVar, TYPE_CHECKING, Union
from ..lib import *
from ..lib.objects import *
from .bot import Bot
if TYPE_CHECKING:
    from .client import Client

__all__ = (
    'Actions',
    'SetAction'
)

ET = TypeVar('ET', bound=Callable)


def create_event(func: ET) -> ET:
    @wraps(func)
    def event(self: Callbacks, *args: Any, **kwargs: Any) -> None:
        data = func(self, *args, **kwargs)
        self.call(func.__name__, data)
    event.__signature__ = fsignature(func) # type: ignore
    return event  # type: ignore


class Callbacks(Bot):
    def __init__(self, is_bot: bool = False, prefix: str = "!") -> None:
        Bot.__init__(self, prefix=prefix)
        # if the user want to use the script as a bot
        self.is_bot = is_bot
        self.handlers: Dict[str, List[Callable[[Any], Any]]] = {}
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

    def _resolve_payload(self, data: dict) -> Any:
        key = str(data['o']['payload']['notifType'])
        return self.notif_methods.get(key, self.default)(data)

    def _resolve_channel(self, data: dict) -> Any:
        return self.chat_action_methods["fetch-channel"](data)

    def _resolve_chat_action_start(self, data: dict) -> Any:
        key = data['o']['actions'] + "-start"
        return self.chat_action_methods.get(key, self.default)(data)

    def _resolve_chat_action_end(self, data: dict) -> Any:
        key = data['o']['actions'] + "-end"
        return self.chat_action_methods.get(key, self.default)(data)

    def _resolve_topics(self, data: dict) -> Any:
        key = str(data["o"]["topic"]).split(":")[2]
        return self.topics.get(key, self.default)(data)

    def _resolve_chat_message(self, data: dict) -> Any:
        key = f"{data['o']['chatMessage']['type']}:{data['o']['chatMessage'].get('mediaType', 0)}"
        return self.chat_methods.get(key, self.default)(data)

    def resolve(self, data: dict) -> Any:
        return self.methods.get(data["t"], self.default)(data)

    def call(self, callType: str, data: Any) -> None:
        if self.handlers.get(callType):
            for handler in self.handlers[callType]:
                handler(data)

    def event(self, eventType: str):
        def registerHandler(handler: Callable):
            if self.handlers.get(eventType):
                self.handlers[eventType].append(handler)
            else:
                self.handlers[eventType] = [handler]
            return handler
        return registerHandler

    @staticmethod
    def convert_event(data: Union[Dict[str, Any], Event]) -> Event:
        return Event(data["o"]).Event if not isinstance(data, Event) else data

    @staticmethod
    def convert_payload(data: Union[Dict[str, Any], Payload]) -> Payload:
        return Payload(data["o"]["payload"]).Payload if not isinstance(data, Payload) else data

    @staticmethod
    def convert_action(data: Union[Dict[str, Any], UsersActions]) -> UsersActions:
        return UsersActions(data).UsersActions

    @create_event
    def on_alert(self, data: Union[dict, Payload]) -> Optional[Payload]:
        return self.convert_payload(data)

    @create_event
    def on_member_set_you_host(self, data: Union[dict, Payload]) -> Optional[Payload]:
        return self.convert_payload(data)

    @create_event
    def on_member_remove_you_cohost(self, data: Union[dict, Payload]) -> Optional[Payload]:
        return self.convert_payload(data)

    @create_event
    def on_member_set_you_cohost(self, data: Union[dict, Payload]) -> Optional[Payload]:
        return self.convert_payload(data)

    @create_event
    def on_text_message(self, data: Union[dict, Event]) -> Optional[Event]:
        data = self.convert_event(data)
        if self.is_bot:
            self.trigger(self.build_parameters(data), str_only=True)
        return data

    @create_event
    def on_image_message(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_youtube_message(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_strike_message(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_voice_message(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_sticker_message(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def TYPE_USER_SHARE_EXURL(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def TYPE_USER_SHARE_USER(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_voice_chat_not_answered(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_voice_chat_not_cancelled(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_voice_chat_not_declined(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_video_chat_not_answered(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_video_chat_not_cancelled(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_video_chat_not_declined(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_avatar_chat_not_answered(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_avatar_chat_not_cancelled(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_avatar_chat_not_declined(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_delete_message(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_group_member_join(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_group_member_leave(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_invite(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_background_changed(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_title_changed(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_icon_changed(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_voice_chat_start(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_video_chat_start(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_avatar_chat_start(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_voice_chat_end(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_video_chat_end(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_avatar_chat_end(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_content_changed(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_screen_room_start(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_screen_room_end(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_host_transfered(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_text_message_force_removed(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_removed_message(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_text_message_removed_by_admin(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_tip(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_pin_announcement(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_voice_chat_permission_open_to_everyone(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_voice_chat_permission_invited_and_requested(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_voice_chat_permission_invite_only(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_view_only_enabled(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_view_only_disabled(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_unpin_announcement(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_tipping_enabled(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_chat_tipping_disabled(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_timestamp_message(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_welcome_message(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_invite_message(self, data: Union[dict, Event]) -> Optional[Event]:
        return self.convert_event(data)

    @create_event
    def on_user_typing_start(self, data: Union[dict, UsersActions]) -> Optional[UsersActions]:
        return self.convert_action(data)

    @create_event
    def on_user_typing_end(self, data: Union[dict, UsersActions]) -> Optional[UsersActions]:
        return self.convert_action(data)

    @create_event
    def on_online_users_update(self, data: Union[dict, UsersActions]) -> Optional[UsersActions]:
        return self.convert_action(data)

    @create_event
    def on_fetch_channel(self, data: Union[dict, Payload]) -> Optional[Payload]:
        return self.convert_payload(data)

    @create_event
    def default(self, data: dict) -> Optional[dict]:
        return data

    create_event = staticmethod(create_event)


class SetAction:
    def __init__(self, wss: Wss, data: Dict[str, Any]) -> None:
        self.action = data
        self.wss = wss

    def start(self) -> None:
        """Start the Action."""
        self.wss.send(self.action)

    def stop(self) -> None:
        """Get back to the last board."""
        act = self.action
        act["t"] = 303
        self.wss.send(self.action)


class Actions:
    def __init__(self, socket: Wss, comId: int, chatId: str) -> None:
        self.socket = socket
        self.chatId = chatId
        self.comId = comId

    def setDefaultAction(self) -> None:
        """Default browsing."""
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

    def Browsing(self, blogId: Optional[str] = None) -> SetAction:
        """Send browsing action.

        Parameters
        ----------
        blogId : str, optional
            The target blog, quiz, poll ID. Default is None.

        Returns
        -------
        SetAction
            The action object.

        """
        target = f"ndc://x{self.comId}/featured"
        data = {
            "o": {
                "actions": ["Browsing"],
                "target": target,
                "ndcId": int(self.comId),
                "id": "363483",
            },
            "t": 306,
        }
        if blogId:
            target = f"ndc://x{self.comId}/blog/"
            data["o"]["params"] = {"blogType": 1}
        self.setDefaultAction()
        return SetAction(self.socket, data)

    def Chatting(self, threadId: Optional[str] = None, threadType: int = 2) -> SetAction:
        """Send chatting action.

        Paramaters
        ----------
        threadType :
            The chat type. Default is 2.
                0: DM
                1: Private
                2: Public

        Returns
        -------
        SetAction
            The action object.

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
        return SetAction(self.socket, data)

    def PublicChats(self) -> SetAction:
        """Send public chats action.

        Returns
        -------
        SetAction
            The action object.

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

    def LeaderBoards(self) -> SetAction:
        """Send leaderboard action.

        Returns
        ------
        SetAction
            The action object.

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

    def Custom(self, actions: List[str], target: str, params: Dict[str, Any]) -> SetAction:
        """Send custom action.

        Parameters
        ----------
        actions : list
            The action type list.
        target : str
            The target ndc url.
        params : dict
            Others params (blogType, duration, threadType, threadId, etc).

        Returns
        -------
        SetAction
            The action object.

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
    def __init__(self, wss: Wss) -> None:
        self.wss = wss

    def joinVoiceChat(self, comId: int, chatId: str, joinType: int = 1) -> None:
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": joinType,
                "id": "37549515",
            },
            "t": 112,
        }
        self.wss.send(data)

    def joinVideoChat(self, comId: int, chatId: str, joinType: int = 1) -> None:
        """Join The Video Chat

        Parameters
        ----------
        comId : int
            The community ID.
        chatId : str
            The chat ID to join.
        joinType : int
            The join role. Default is 1.
                1: owner
                2: viewer

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
        self.wss.send(data)

    def startVoiceChat(self, comId: int, chatId: str) -> None:
        """Start the voice chat.

        Parameters
        ----------
        comId : int
            The community ID.
        chatId : str
            The chat ID to start the live mode.

        """
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": 1,
                "id": "2154531"
            },
            "t": 112,
        }
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
        self.wss.send(data)

    def endVoiceChat(self, comId: int, chatId: str) -> None:
        """End the voice chat.

        Parameters
        ----------
        comId : int
            The community ID.
        chatId : str
            The chat ID to end the live mode.

        """
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": 2,
                "id": "2154531"
            },
            "t": 112,
        }
        self.wss.send(data)

    def joinVideoChatAsSpectator(self, comId: int, chatId: str) -> None:
        """Join video chat as spectator

        Parameters
        ----------
        comId : int
            The community ID.
        chatId : str
            The chat ID of live mode.

        """
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": 2,
                "id": "72446",
            },
            "t": 112,
        }
        self.wss.send(data)

    def threadJoin(self, comId: int, chatId: str) -> None:
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": 1,
                "id": "10335106",
            },
            "t": 112,
        }
        self.wss.send(data)

    def channelJoin(self, comId: int, chatId: str):
        data = {
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "channelType": 5,
                "id": "10335436",
            },
            "t": 108,
        }
        self.wss.send(data)

    def GetUsersActions(self, comId: int, path: int = 0, chatId: Optional[str] = None) -> UsersActions:
        """Get users actions.
    
        This functions gets certain socket actions happening such as online users and users chatting

        Parameters
        ----------
        comId : int
            The community ID.
        path : int
            Takes an intger >= 0 and <= 5 each one sends a certain action not required -set by default to 0 // users-chatting
                0: chatting users
                1: online members
                2: users typing start (chat ID required)
                3: users typing end (chat ID required)
                4: users recording start (chat ID required)
                5: users recording end (chat ID required)
        chatId : str
            The chat ID used in certain actions such as users typing.

        Returns
        -------
        UsersActions
            The action object.

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
        self.wss.send(data)
        recv = None
        while not recv:
            recv = self.wss.receive()
        return UsersActions(recv).UsersActions

    def actions(self, comId: int, chatId: str) -> Actions:
        return Actions(self.wss, comId, chatId)


class Wss(Callbacks, WssClient, Headers):
    """Represents the amino websocket client.

    Parameters
    ----------
    client : Client
        The global client object.
    trace : bool
        Show websocket trace (logs). Default is False.
    is_bot : bool
        The client is a community bot. Default is False (command supported).

    """

    def __init__(self, client: Client, trace: bool = False, is_bot: bool = False):
        self.trace = trace
        self.socket = None
        self.headers = None
        self.client = client
        self.isOpened = False
        self.narvi = "https://service.narvii.com/api/v1/"
        self.socket_url = "wss://ws1.narvii.com"
        self.lastMessage = {}
        Headers.__init__(self, getattr(client, 'deviceId', None))
        Callbacks.__init__(self, is_bot=is_bot)
        WssClient.__init__(self, self)
        websocket.enableTrace(trace)

    def onOpen(self, *args: Any) -> None:
        self.isOpened = True
        if self.trace:
            print("[ON-OPEN] Sockets are open")

    def onClose(self, *args: Any) -> None:
        self.isOpened = False
        if self.trace:
            print("[ON-CLOSE] Sockets are closed")

    def send(self, data: dict) -> None:
        if not self.socket:
            raise RuntimeError('Socket is not connected.')
        self.socket.send(json.dumps(data))

    def receive(self) -> Optional[Dict[str, Any]]:
        if self.trace:
            print("[RECEIVE] returning last message")
        return self.lastMessage

    def on_message(self, ws, data) -> None:
        self.lastMessage = json.loads(data)
        self.resolve(self.lastMessage)
        if self.trace:
            print("[ON-MESSAGE] Received a message . . .")

    def launch(self, daemon: bool = False) -> None:
        final = f"{self.client.deviceId}|{int(time.time() * 1000)}"
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
            on_error=self.onError,
            header=self.headers  # type: ignore
        )
        if self.trace:
            print("[LAUNCH] Sockets starting . . . ")
        threading.Thread(target=self.socket.run_forever, kwargs={"ping_interval": 60}, daemon=daemon).start()
        time.sleep(5)

    def close(self) -> None:
        if self.socket:
            self.socket.close()
        if self.trace:
            print("[CLOSE] closing socket . . .")
        time.sleep(1.5)

    def onError(self, *args):
        if self.trace:
            print(f"[ERROR] Error! {args}")

    def socket_status(self) -> None:
        print("\nSockets are OPEN\n" if self.isOpened else "\nSockets are CLOSED\n")
