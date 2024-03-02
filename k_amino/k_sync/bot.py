import typing_extensions as typing
import easy_events
from ..lib.objects import Event
from ..lib.util import NO_ICON_URL
if typing.TYPE_CHECKING:
    from .local import SubClient  # circular import

__all__ = ('Parameters',)

C = typing.TypeVar('C', bound=typing.Callable[..., typing.Any])


class Parameters(easy_events.Parameters):
    """Represents the commmand parameters

    Parameters
    ----------
    event : Event
        The event object.
    subClient : SubClient
        The community client object.
    prefix : str, optional
        The command prefix prefix. Default is '!'.
    str_only : bool, optional
        The command argument is only str. Default is True.

    """

    def __init__(self: typing.Self, event: Event, subClient: 'SubClient', prefix: str = "!", str_only: bool = True) -> None:
        super().__init__(event.message.content, prefix, str_only)
        self.subClient = self.local = subClient
        self.message = event.message
        self.author = event.message.author
        self.event = event
        self.comId = typing.cast(int, self.event.comId)
        self.authorId = typing.cast(str, self.author.userId)
        self.chatId = typing.cast(str, self.message.chatId)
        self.authorIcon = typing.cast(str, self.message.author.icon or NO_ICON_URL)
        self.messageId = typing.cast(str, self.message.messageId)
        self.mentions = typing.cast(typing.List[str], event.message.mentionUserIds or [])
        # defaults
        self.replyId: typing.Optional[str] = None
        self.replyMsg: typing.Optional[str] = None
        self.replySrc: typing.Optional[str] = None
        # if has reply message
        if event.message.extensions and isinstance(event.message.extensions.get('replyMessage'), dict):
            self.replyId = typing.cast(str, event.message.extensions['replyMessage'].get('messageId'))
            self.replyMsg = typing.cast(str, event.message.extensions['replyMessage'].get('content'))
            if event.message.extensions['replyMessage'].get('mediaValue'):
                self.replySrc = typing.cast(str, event.message.extensions['replyMessage']['mediaValue'].replace('_00.', '_hq.'))


class Bot(easy_events.Events):
    """Represents the bot events.

    Parameters
    ----------
    prefix : `str`
        The command prefix. Default is `!`

    """
    def __init__(self: typing.Self, prefix: str = "!"):
        super().__init__(prefix=prefix, str_only=True, first_parameter_object=True, default_event=False)

    def build_parameters(self: typing.Self, obj_data: Event) -> Parameters:
        from .local import SubClient  # circular import
        subClient = SubClient(comId=obj_data.comId, client=self, acm=True)
        return Parameters(obj_data, subClient, self.prefix, str_only=True)

    @typing.overload
    def command(
        self: typing.Self,
        aliases: typing.List[str] = [],
        condition: typing.Optional[typing.Callable[..., bool]] = None,
        type: typing.Optional[str] = None,
        callback: None = None,
        event_type: typing.Optional[str] = None
    ) -> typing.Callable[[C], C]: ...
    @typing.overload
    def command(
        self: typing.Self,
        aliases: typing.List[str] = [],
        condition: typing.Optional[typing.Callable[..., bool]] = None,
        type: typing.Optional[str] = None,
        callback: C = ...,  # type: ignore
        event_type: typing.Optional[str] = None
    ) -> C: ...
    def command(
        self: typing.Self,
        aliases: typing.List[str] = [],
        condition: typing.Optional[typing.Callable[..., bool]] = None,
        type: typing.Optional[str] = None,
        callback: typing.Optional[C] = None,
        event_type: typing.Optional[str] = None
    ) -> typing.Union[typing.Callable[[C], C], C]:
        return easy_events.Decorator.add_event(self, aliases, condition, type, callback, event_type)  # type: ignore
