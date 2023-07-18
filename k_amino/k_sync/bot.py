from typing import Optional, cast
from easy_events import Events, Decorator, Parameters as _Parameters
from .local import SubClient
from ..lib.objects import Event

__all__ = ('Bot', 'Parameters')


class Parameters(_Parameters):
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

    def __init__(self, event: Event, subClient: SubClient, prefix: str = "!", str_only: bool = True) -> None:
        super().__init__(event.message.content, prefix, str_only)
        self.subCient = self.local = subClient
        self.message = event.message
        self.author = event.message.author
        self.event = event
        self.comId = cast(int, self.event.comId)
        self.authorId = cast(str, self.author.userId)
        self.messageId = cast(str, self.message.messageId)
        # defaults
        self.replyId: Optional[str] = None
        self.replyMsg: Optional[str] = None
        self.replySrc: Optional[str] = None
        # if has reply message
        if event.message.extensions and isinstance(event.message.extensions.get('replyMessage'), dict):
            self.replyId = cast(str, event.message.extensions['replyMessage'].get('messageId'))
            self.replyMsg = cast(str, event.message.extensions['replyMessage'].get('content'))
            if event.message.extensions['replyMessage'].get('mediaValue'):
                self.replySrc = cast(str, event.message.extensions['replyMessage']['mediaValue'].replace('_00.', '_hq.'))


class Bot(Events):
    """Represents the bot events.

    Parameters
    ----------
    prefix : str
        The command prefix. Default is '!'

    """
    def __init__(self, prefix: str = "!"):
        super().__init__(prefix=prefix, str_only=True, first_parameter_object=True, default_event=False)

    def build_parameters(self, obj_data: Event) -> Parameters:
        subClient = SubClient(comId=cast(int, obj_data.comId), client=self, acm=True)
        return Parameters(obj_data, subClient, self.prefix, str_only=True)

    command = Decorator.add_event
