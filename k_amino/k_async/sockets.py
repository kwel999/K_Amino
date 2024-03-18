import abc
import asyncio
import functools
import inspect
import logging
import time
import socket
import typing_extensions as typing
import ujson
import websockets
from .bot import AsyncBot
from ..lib.objects import Event, Payload, UsersActions
from ..lib.util import generateSig

__all__ = (
    'AsyncActions',
    'AsyncSetAction'
)

C = typing.TypeVar('C', bound=typing.Callable[..., typing.Any])
P = typing.ParamSpec('P')
R = typing.TypeVar('R')

CoroutineFunction = typing.Callable[P, typing.Awaitable[R]]

logger = logging.getLogger('websockets.client')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


def create_event(func: typing.Callable[P, typing.Awaitable[R]]) -> typing.Callable[P, typing.Awaitable[R]]:
    @functools.wraps(func)
    async def event(*args: P.args, **kwargs: P.kwargs) -> R:
        data = await func(*args, **kwargs)
        await typing.cast(AsyncCallbacks, args[0]).call(func.__name__, data)
        return data
    event.__signature__ = inspect.signature(func)  # type: ignore
    return event


class AsyncCallbacks(AsyncBot):
    def __init__(self, is_bot: bool = False, prefix: str = "!") -> None:
        AsyncBot.__init__(self, prefix=prefix)
        # if the user want to use the script as a bot
        self.is_bot = is_bot
        self.handlers: typing.Dict[str, typing.List[CoroutineFunction[[Event], typing.Any]]] = {}
        self.methods: typing.Dict[int, CoroutineFunction[[typing.Dict[str, typing.Any]], typing.Any]] = {
            10: self._resolve_payload,
            201: self._resolve_channel,
            304: self._resolve_chat_action_start,
            306: self._resolve_chat_action_end,
            400: self._resolve_topics,
            1000: self._resolve_chat_message,
        }
        self.chat_methods: typing.Dict[str, CoroutineFunction[[typing.Union[typing.Dict[str, typing.Any], Event]], Event]] = {
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
        self.notif_methods: typing.Dict[str, CoroutineFunction[[typing.Union[typing.Dict[str, typing.Any], Payload]], Payload]] = {
            "18": self.on_alert,
            "53": self.on_member_set_you_host,
            "67": self.on_member_set_you_cohost,
            "68": self.on_member_remove_you_cohost,
        }
        self.chat_action_methods: typing.Dict[str, CoroutineFunction[[typing.Union[typing.Dict[str, typing.Any], UsersActions]], UsersActions]] = {
            "Typing-start": self.on_user_typing_start,
            "Typing-end": self.on_user_typing_end,
        }
        self.channel_methods: typing.Dict[str, CoroutineFunction[[typing.Union[typing.Dict[str, typing.Any], Payload]], Payload]] = {
            "fetch-channel": self.on_fetch_channel
        }
        self.topics: typing.Dict[str, CoroutineFunction[[typing.Dict[str, typing.Any]], typing.Any]] = {
            "online-members": self.on_online_users_update,
            "users-start-typing-at": self.on_user_typing_start,
            "users-end-typing-at": self.on_user_typing_end,
            "users-start-recording-at": self.on_voice_chat_start,
            "users-end-recording-at": self.on_voice_chat_end,
        }

    async def _resolve_payload(self, data: typing.Dict[str, typing.Any]) -> typing.Any:
        key = str(data['o']['payload']['notifType'])
        return self.notif_methods.get(key, self.default)(data)

    async def _resolve_channel(self, data: typing.Dict[str, typing.Any]) -> typing.Any:
        return self.channel_methods.get("fetch-channel", self.default)(data)

    async def _resolve_chat_action_start(self, data: typing.Dict[str, typing.Any]) -> typing.Any:
        key = data['o']['actions'] + "-start"
        return self.chat_action_methods.get(key, self.default)(data)

    async def _resolve_chat_action_end(self, data: typing.Dict[str, typing.Any]) -> typing.Any:
        key = data['o']['actions'] + "-end"
        return self.chat_action_methods.get(key, self.default)(data)

    async def _resolve_topics(self, data: typing.Dict[str, typing.Any]) -> typing.Any:
        key = str(data["o"]["topic"]).split(":")[2]
        return self.topics.get(key, self.default)(data)

    async def _resolve_chat_message(self, data: typing.Dict[str, typing.Any]) -> typing.Any:
        key = f"{data['o']['chatMessage']['type']}:{data['o']['chatMessage'].get('mediaType', 0)}"
        return self.chat_methods.get(key, self.default)(data)

    async def resolve(self, data: typing.Dict[str, typing.Any]) -> typing.Any:
        return self.methods.get(data["t"], self.default)(data)

    async def call(self, callType: str, data: typing.Any) -> None:
        if self.handlers.get(callType):
            for handler in self.handlers[callType]:
                handler(data)

    def event(self, eventType: str) -> typing.Callable[[C], C]:
        def registerHandler(handler: C) -> C:
            if self.handlers.get(eventType):
                self.handlers[eventType].append(handler)
            else:
                self.handlers[eventType] = [handler]
            return handler
        return registerHandler

    @staticmethod
    async def convert_event(data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return Event(data["o"]).Event if not isinstance(data, Event) else data

    @staticmethod
    async def convert_payload(data: typing.Union[typing.Dict[str, typing.Any], Payload]) -> Payload:
        return Payload(data["o"]["payload"]).Payload if not isinstance(data, Payload) else data

    @staticmethod
    async def convert_action(data: typing.Union[typing.Dict[str, typing.Any], UsersActions]) -> UsersActions:
        return UsersActions(data).UsersActions

    @create_event
    async def on_alert(self, data: typing.Union[typing.Dict[str, typing.Any], Payload]) -> Payload:
        return await self.convert_payload(data)

    @create_event
    async def on_member_set_you_host(self, data: typing.Union[typing.Dict[str, typing.Any], Payload]) -> Payload:
        return await self.convert_payload(data)

    @create_event
    async def on_member_remove_you_cohost(self, data: typing.Union[typing.Dict[str, typing.Any], Payload]) -> Payload:
        return await self.convert_payload(data)

    @create_event
    async def on_member_set_you_cohost(self, data: typing.Union[typing.Dict[str, typing.Any], Payload]) -> Payload:
        return await self.convert_payload(data)

    @create_event
    async def on_text_message(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        data = await self.convert_event(data)
        if self.is_bot:
            params = await self.build_parameters(data)
            await self.trigger(params, str_only=True)
        return data

    @create_event
    async def on_image_message(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_youtube_message(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_strike_message(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_voice_message(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_sticker_message(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def TYPE_USER_SHARE_EXURL(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def TYPE_USER_SHARE_USER(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_voice_chat_not_answered(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_voice_chat_not_cancelled(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_voice_chat_not_declined(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_video_chat_not_answered(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_video_chat_not_cancelled(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_video_chat_not_declined(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_avatar_chat_not_answered(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_avatar_chat_not_cancelled(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_avatar_chat_not_declined(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_delete_message(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_group_member_join(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_group_member_leave(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_invite(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_background_changed(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_title_changed(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_icon_changed(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_voice_chat_start(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_video_chat_start(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_avatar_chat_start(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_voice_chat_end(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_video_chat_end(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_avatar_chat_end(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_content_changed(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_screen_room_start(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_screen_room_end(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_host_transfered(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_text_message_force_removed(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_removed_message(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_text_message_removed_by_admin(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_tip(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_pin_announcement(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_voice_chat_permission_open_to_everyone(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_voice_chat_permission_invited_and_requested(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_voice_chat_permission_invite_only(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_view_only_enabled(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_view_only_disabled(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_unpin_announcement(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_tipping_enabled(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_chat_tipping_disabled(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_timestamp_message(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_welcome_message(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_invite_message(self, data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
        return await self.convert_event(data)

    @create_event
    async def on_user_typing_start(self, data: typing.Union[typing.Dict[str, typing.Any], UsersActions]) -> UsersActions:
        return await self.convert_action(data)

    @create_event
    async def on_user_typing_end(self, data: typing.Union[typing.Dict[str, typing.Any], UsersActions]) -> UsersActions:
        return await self.convert_action(data)

    @create_event
    async def on_online_users_update(self, data: typing.Union[typing.Dict[str, typing.Any], UsersActions]) -> UsersActions:
        return await self.convert_action(data)

    @create_event
    async def on_fetch_channel(self, data: typing.Union[typing.Dict[str, typing.Any], Payload]) -> Payload:
        return await self.convert_payload(data)

    @create_event
    async def default(self, data: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        return data

    create_event = staticmethod(create_event)


class AsyncSetAction:
    def __init__(self, wss: 'AsyncWssClient', data: typing.Dict[str, typing.Any]) -> None:
        self.action = data
        self.wss = wss

    async def start(self) -> None:
        """Start the Action."""
        await self.wss.send(self.action)

    async def stop(self) -> None:
        """Get back to the last board."""
        act = self.action
        act["t"] = 303
        await self.wss.send(self.action)


class AsyncActions:
    def __init__(self, socket: 'AsyncWssClient', comId: int, chatId: str) -> None:
        self.socket = socket
        self.chatId = chatId
        self.comId = comId

    async def setDefaultAction(self) -> AsyncSetAction:
        """Default browsing."""
        return AsyncSetAction(self.socket, {
            "o": {
                "actions": ["Browsing"],
                "target": f"ndc://x{self.comId}/",
                "ndcId": int(self.comId),
                "params": {"duration": 27605},
                "id": "363483",
            },
            "t": 306
        })

    async def Browsing(self, blogId: typing.Optional[str] = None) -> AsyncSetAction:
        """Send browsing action.

        Parameters
        ----------
        blogId : `str`, `optional`
            The target blog, quiz, poll ID. Default is `None`.

        Returns
        -------
        AsyncSetAction
            The action object.

        """
        data: typing.Dict[str, typing.Any] = {
            "o": {
                "actions": ["Browsing"],
                "target": f"ndc://x{self.comId}/featured",
                "ndcId": int(self.comId),
                "id": "363483",
            },
            "t": 306
        }
        if blogId:
            data["o"]["target"] = f"ndc://x{self.comId}/blog"
            data["o"]["params"] = {"blogType": 1}
        await (await self.setDefaultAction()).start()
        return AsyncSetAction(self.socket, data)

    async def Chatting(self, chatId: typing.Optional[str] = None, chatType: int = 2) -> AsyncSetAction:
        """Send chatting action.

        Paramaters
        ----------

        chatId: str, optional
            The ID of the chat to send the action. If not provided used the init chatId
        chatType : int, optional
            The chat type. Default is `2`.
                0: DM
                1: Private
                2: Public

        Returns
        -------
        AsyncSetAction
            The action object.

        """
        chatId = chatId or self.chatId
        return AsyncSetAction(self.socket, {
            "o": {
                "actions": ["Chatting"],
                "target": f"ndc://x{self.comId}/chat-thread/{chatId}",
                "ndcId": int(self.comId),
                "params": {
                    "duration": 12800,
                    "membershipStatus": 1,
                    "threadType": chatType,
                    "threadId": chatId
                },
                "id": "1715976",
            },
            "t": 306,
        })

    async def PublicChats(self) -> AsyncSetAction:
        """Send public chats action.

        Returns
        -------
        AsyncSetAction
            The action object.

        """
        await (await self.setDefaultAction()).start()
        return AsyncSetAction(self.socket, {
            "o": {
                "actions": ["Browsing"],
                "target": f"ndc://x{self.comId}/public-chats",
                "ndcId": int(self.comId),
                "params": {"duration": 859},
                "id": "363483",
            },
            "t": 306,
        })

    async def LeaderBoards(self) -> AsyncSetAction:
        """Send leaderboard action.

        Returns
        ------
        AsyncSetAction
            The action object.

        """
        await (await self.setDefaultAction()).start()
        return AsyncSetAction(self.socket, {
            "o": {
                "actions": ["Browsing"],
                "target": f"ndc://x{self.comId}/leaderboards",
                "ndcId": int(self.comId),
                "params": {"duration": 859},
                "id": "363483",
            },
            "t": 306,
        })

    async def Custom(self, actions: typing.List[str], target: str, params: typing.Dict[str, typing.Any]) -> AsyncSetAction:
        """Send custom action.

        Parameters
        ----------
        actions : `list[str]`
            The action type list.
        target : `str`
            The target ndc url.
        params : dict[str, Any]
            Others params (blogType, duration, threadType, threadId, etc).

        Returns
        -------
        AsyncSetAction
            The action object.

        """
        await (await self.setDefaultAction()).start()
        return AsyncSetAction(self.socket, {
            "o": {
                "actions": actions,
                "target": target,
                "ndcId": int(self.comId),
                "params": params,
                "id": "363483",
            },
            "t": 306,
        })


class AsyncWssClient:
    socket: typing.Optional[websockets.WebSocketClientProtocol]
    lastMessage: typing.Optional[typing.Dict[str, typing.Any]]
    @property
    @abc.abstractmethod
    def trace(self) -> bool: ...

    async def send(self, data: typing.Dict[str, typing.Any]) -> None:
        if not self.socket:
            raise RuntimeError('Socket is not connected.')
        await self.socket.send(ujson.dumps(data))

    async def receive(self) -> typing.Optional[typing.Dict[str, typing.Any]]:
        if self.trace:
            print("[RECEIVE] returning last message")
        return self.lastMessage

    async def joinVoiceChat(self, comId: int, chatId: str, joinType: int = 1) -> None:
        await self.send({
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": joinType,
                "id": "37549515",
            },
            "t": 112,
        })

    async def joinVideoChat(self, comId: int, chatId: str, joinType: typing.Literal[1, 2] = 1) -> None:
        """Join The Video Chat

        Parameters
        ----------
        comId : `int`
            The community ID.
        chatId : `str`
            The chat ID to join.
        joinType : `int`
            The join role. Default is `1`.
                1: owner
                2: viewer

        """
        await self.send({
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": joinType,
                "channelType": 5,
                "id": "2154531",
            },
            "t": 108,
        })

    async def startVoiceChat(self, comId: int, chatId: str) -> None:
        """Start the voice chat.

        Parameters
        ----------
        comId : `int`
            The community ID.
        chatId : `str`
            The chat ID to start the live mode.

        """
        await self.send({
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": 1,
                "id": "2154531"
            },
            "t": 112,
        })
        await self.send({
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "channelType": 1,
                "id": "2154531",
            },
            "t": 108,
        })

    async def endVoiceChat(self, comId: int, chatId: str) -> None:
        """End the voice chat.

        Parameters
        ----------
        comId : `int`
            The community ID.
        chatId : `str`
            The chat ID to end the live mode.

        """
        await self.send({
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": 2,
                "id": "2154531"
            },
            "t": 112,
        })

    async def joinVideoChatAsSpectator(self, comId: int, chatId: str) -> None:
        """Join video chat as spectator

        Parameters
        ----------
        comId : `int`
            The community ID.
        chatId : `str`
            The chat ID of live mode.

        """
        await self.send({
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": 2,
                "id": "72446",
            },
            "t": 112,
        })

    async def threadJoin(self, comId: int, chatId: str) -> None:
        await self.send({
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "joinRole": 1,
                "id": "10335106",
            },
            "t": 112,
        })

    async def channelJoin(self, comId: int, chatId: str) -> None:
        await self.send({
            "o": {
                "ndcId": comId,
                "threadId": chatId,
                "channelType": 5,
                "id": "10335436",
            },
            "t": 108,
        })

    @typing.overload
    async def GetUsersActions(self, comId: int, path: typing.Literal[0, 1], chatId: typing.Optional[str] = None) -> UsersActions: ...
    @typing.overload
    async def GetUsersActions(self, comId: int, path: typing.Literal[2, 3, 4, 5], chatId: str) -> UsersActions: ...
    async def GetUsersActions(self, comId: int, path: int, chatId: typing.Optional[str] = None) -> UsersActions:
        """Get users actions.
    
        This functions gets certain socket actions happening such as online users and users chatting

        Parameters
        ----------
        comId : `int`
            The community ID.
        path : `int`
            Takes an intger >= 0 and <= 5 each one sends a certain action not required -set by default to 0 // users-chatting
                0: chatting users
                1: online members
                2: users typing start (chat ID required)
                3: users typing end (chat ID required)
                4: users recording start (chat ID required)
                5: users recording end (chat ID required)
        chatId : `str`
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
        await self.send({
            "o": {
                "ndcId": comId if comId else 0,
                "topic": f"ndtopic:x{comId}:{topic}",
                "id": "4538416",
            },
            "t": 300
        })
        recv = None
        while not recv:
            recv = await self.receive()
        return UsersActions(recv).UsersActions

    async def actions(self, comId: int, chatId: str) -> AsyncActions:
        return AsyncActions(self, comId, chatId)


class AsyncWss(AsyncCallbacks, AsyncWssClient):
    """Represents the amino websocket client (Base).

    Parameters
    ----------
    trace : `bool`
        Show websocket trace (logs). Default is `False`.
    is_bot : `bool`
        The client is a community bot. Default is `False` (command supported).

    """

    @property
    @abc.abstractmethod
    def deviceId(self) -> str: ...
    @property
    @abc.abstractmethod
    def sid(self) -> typing.Optional[str]: ...

    @property
    def trace(self) -> bool:
        return getattr(self, '_trace')

    @trace.setter
    def trace(self, value: bool) -> None:
        logger.addHandler(logging.StreamHandler() if value else logging.NullHandler())
        setattr(self, '_trace', value)

    def __init__(self, trace: bool, is_bot: bool) -> None:
        self.trace = trace
        self.isOpened = False
        self.narvi = "https://service.aminoapps.com/api/v1/"
        self.socket: typing.Optional[websockets.WebSocketClientProtocol] = None
        self.socket_url = "wss://ws1.narvii.com"
        self.socket_task: typing.Optional[asyncio.Task[None]] = None
        self.lastMessage = None
        AsyncCallbacks.__init__(self, is_bot=is_bot)
        AsyncWssClient.__init__(self)

    async def ws_task(self) -> None:
        """Internal websocket task"""
        # duplicated task
        if self.isOpened:
            return
        # on-open
        self.isOpened = True
        if self.trace:
            print("[ON-OPEN] Sockets are open")
        # on-message
        while self.socket and not self.socket.closed:
            try:
                self.lastMessage = typing.cast(typing.Dict[str, typing.Any], ujson.loads(await self.socket.recv()))
                await self.resolve(self.lastMessage)
            except websockets.exceptions.ConnectionClosed:
                pass
            except Exception as exc:
                # on-error
                if self.trace:
                    print(f"[ERROR] Error! {exc!r}")
                break
            if self.trace:
                print("[ON-MESSAGE] Received a message . . .")
        # on-close
        if self.trace:
            print("[ON-CLOSE] Sockets are closed")
        if self.isOpened and self.socket_task:  # loop closed by error
            self.isOpened = False
            await self.launch()  # reconnect
        else:  # close() called
            self.isOpened = False
            self.socket_task = None

    async def launch(self) -> None:
        if self.isOpened:
            return
        final = f"{self.deviceId}|{int(time.time() * 1000)}"
        headers = {
            "NDCDEVICEID": self.deviceId,
            "NDCAUTH": typing.cast(str, self.sid),
            "NDC-MSG-SIG": generateSig(data=final),
        }
        for tries in range(2, -1, -1):
            try:
                self.socket = await websockets.connect(
                    f"{self.socket_url}/?signbody={final.replace('|', '%7C')}",
                    additional_headers=headers,
                    user_agent_header=None,
                    compression=None,
                    logger=logger
                )
            except socket.gaierror:
                if tries == 0:
                    raise
                time.sleep(5)
                continue
            except (TimeoutError, ConnectionError):
                if tries == 0:
                    raise
                time.sleep(1)
                continue
            else:
                break
        if self.trace:
            print("[LAUNCH] Sockets starting . . . ")
        self.socket_task = asyncio.create_task(self.ws_task())
        time.sleep(5)

    async def close(self) -> None:
        self.isOpened = False
        if self.socket:
            await self.socket.close()
            self.socket = None
        if self.trace:
            print("[CLOSE] closing socket . . .")
        time.sleep(1.5)

    async def socket_status(self) -> None:
        print("\nSockets are OPEN\n" if self.isOpened else "\nSockets are CLOSED\n")
