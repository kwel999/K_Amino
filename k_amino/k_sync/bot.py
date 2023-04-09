from easy_events import Events, Parameters

from .local import SubClient


class Bot(Events):
    def __init__(self, prefix: str = "!"):
        Events.__init__(self, prefix=prefix, str_only=True, first_parameter_object=True, default_event=False)

        # to make @client.command()
        self.command = self.add_event

    def build_parameters(self, obj_data):
        data = Parameters(data=obj_data.message.content, prefix=self.prefix, str_only=True)

        for k, v in obj_data.__dict__.items():
            setattr(data, k, v)

        for k, v in obj_data.message.__dict__.items():
            if k != "json":
                setattr(data, k, v)

        data.subClient = data.local = SubClient(comId=data.comId, acm=True)

        data.authorId = data.message.author.userId
        data.authorName = data.message.author.nickname
        data.messageId = data.message.messageId
        data.authorIcon = data.message.author.icon

        try: data.level = data.message.json["author"]["level"]
        except: pass
        try: data.reputation = data.message.json["author"]["reputation"]
        except: pass

        data.replySrc = None
        data.replyId = None

        if data.message.extensions and data.message.extensions.get('replyMessage') and data.message.extensions['replyMessage'].get('mediaValue'):
            data.replySrc = data.message.extensions['replyMessage']['mediaValue'].replace('_00.', '_hq.')
            data.replyId = data.message.extensions['replyMessage']['messageId']

        data.replyMsg = None

        if data.message.extensions and data.message.extensions.get('replyMessage') and data.message.extensions['replyMessage'].get('content'):
            data.replyMsg = data.message.extensions['replyMessage']['content']
            data.replyId = data.message.extensions['replyMessage']['messageId']

        return data
