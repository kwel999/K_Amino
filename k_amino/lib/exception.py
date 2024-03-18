# From https://github.com/okok7711/AminoAcid/blob/master/aminoacid/exceptions.py
import typing_extensions as typing

__all__ = (
    'API_ERR_CHAT_VVCHAT_NO_MORE_REPUTATIONS',
    'API_ERR_COMMUNITY_USER_CREATED_COMMUNITIES_VERIFY',
    'API_ERR_EMAIL_NO_PASSWORD',
    'API_ERR_PUSH_SERVER_LIMITATION_APART',
    'API_ERR_PUSH_SERVER_LIMITATION_COUNT',
    'API_ERR_PUSH_SERVER_LIMITATION_TIME',
    'API_ERR_PUSH_SERVER_LINK_NOT_IN_COMMUNITY',
    'APIError',
    'AccessDenied',
    'AccountAlreadyRestored',
    'AccountDeleted',
    'AccountDisabled',
    'AccountDoesntExist',
    'ActionNotAllowed',
    'ActivateAccount',
    'AlreadyCheckedIn',
    'AlreadyPlayedLottery',
    'AlreadyRequestedJoinCommunity',
    'AlreadyUsedMonthlyRepair',
    'AminoBaseException',
    'AminoIDAlreadyChanged',
    'BadImage',
    'CannotSendCoins',
    'CantFollowYourself',
    'CantLeaveCommunity',
    'ChatFull',
    'ChatInvitesDisabled',
    'ChatMessageTooBig',
    'ChatViewOnly',
    'CommandCooldown',
    'CommunityCreateLimitReached',
    'CommunityDeleted',
    'CommunityDisabled',
    'CommunityNameAlreadyTaken',
    'CommunityNoLongerExists',
    'DuplicatePollOption',
    'EmailAlreadyTaken',
    'EmailFlaggedAsSpam',
    'FileTooLarge',
    'IncorrectVerificationCode',
    'InsufficientLevel',
    'InvalidAccountOrPassword',
    'InvalidAminoID',
    'InvalidAuthNewDeviceLink',
    'InvalidCodeOrLink',
    'InvalidDevice',
    'InvalidEmail',
    'InvalidName',
    'InvalidPassword',
    'InvalidRequest',
    'InvalidSession',
    'InvalidThemepack',
    'InvalidVoiceNote',
    'InviteCodeNotFound',
    'LevelFiveRequiredToEnableProps',
    'MemberKickedByOrganizer',
    'MessageNeeded',
    'NotEnoughCoins',
    'NotOwnerOfChatBubble',
    'PageRepostedTooRecently',
    'ReachedMaxCategories',
    'ReachedMaxPollOptions',
    'ReachedMaxTitles',
    'ReachedTitleLength',
    'RemovedFromChat',
    'RequestRejected',
    'RequestedNoLongerExist',
    'ServerError',
    'TooManyChats',
    'TooManyInviteUsers',
    'TooManyRequests',
    'UnexistentData',
    'UnsupportedService',
    'UserBannedByTeamAmino',
    'UserNotJoined',
    'UserNotMemberOfCommunity',
    'UserUnavailable',
    'VerificationRequired',
    'WallCommentingDisabled',
    'YouAreBanned',
    'check_exceptions'
)


class AminoBaseException(Exception): ...

class APIError(AminoBaseException):
    def __init__(self, data: typing.Dict[str, typing.Any]) -> None:
        super().__init__(data)
        self.duration: str = data["api:duration"]
        self.message: str = data["api:message"]
        self.statusCode: int = data["api:statuscode"]
        self.timestamp: str = data["api:timestamp"]

class ServerError(AminoBaseException):
    def __init__(self, status: int, reason: str) -> None:
        super().__init__(f"{status} - {reason}")
        self.reason = reason
        self.status = status

class TemporaryIPBan(ServerError): ...
class PayloadTooLarge(ServerError): ...
class InternalServerError(ServerError): ...
class BadGateway(ServerError): ...
class ServiceUnavailable(ServerError): ...

# api errors
class AccessDenied(APIError): ...
class UnsupportedService(APIError): ...
class InvalidRequest(APIError): ...
class InvalidSession(APIError): ...
class InvalidAccountOrPassword(APIError): ...
class InvalidDevice(APIError): ...
class TooManyRequests(APIError): ...
class ActionNotAllowed(APIError): ...
class FileTooLarge(APIError): ...
class UnexistentData(APIError): ...
class MessageNeeded(APIError): ...
class AccountDisabled(APIError): ...
class InvalidEmail(APIError): ...
class InvalidPassword(APIError): ...
class EmailAlreadyTaken(APIError): ...
class AccountDoesntExist(APIError): ...
class CantFollowYourself(APIError): ...
class UserUnavailable(APIError): ...
class YouAreBanned(APIError): ...
class UserNotMemberOfCommunity(APIError): ...
class RequestRejected(APIError): ...
class ActivateAccount(APIError): ...
class CantLeaveCommunity(APIError): ...
class ReachedTitleLength(APIError): ...
class EmailFlaggedAsSpam(APIError): ...
class AccountDeleted(APIError): ...
class API_ERR_EMAIL_NO_PASSWORD(APIError): ...
class API_ERR_COMMUNITY_USER_CREATED_COMMUNITIES_VERIFY(APIError): ...
class ReachedMaxTitles(APIError): ...
class VerificationRequired(APIError): ...
class InvalidAuthNewDeviceLink(APIError): ...
class CommandCooldown(APIError): ...
class UserBannedByTeamAmino(APIError): ...
class BadImage(APIError): ...
class InvalidThemepack(APIError): ...
class InvalidVoiceNote(APIError): ...
class RequestedNoLongerExist(APIError): ...
class PageRepostedTooRecently(APIError): ...
class InsufficientLevel(APIError): ...
class WallCommentingDisabled(APIError): ...
class CommunityNoLongerExists(APIError): ...
class InvalidCodeOrLink(APIError): ...
class CommunityNameAlreadyTaken(APIError): ...
class CommunityCreateLimitReached(APIError): ...
class CommunityDisabled(APIError): ...
class CommunityDeleted(APIError): ...
class ReachedMaxCategories(APIError): ...
class DuplicatePollOption(APIError): ...
class ReachedMaxPollOptions(APIError): ...
class TooManyChats(APIError): ...
class ChatFull(APIError): ...
class TooManyInviteUsers(APIError): ...
class ChatInvitesDisabled(APIError): ...
class RemovedFromChat(APIError): ...
class UserNotJoined(APIError): ...
class API_ERR_CHAT_VVCHAT_NO_MORE_REPUTATIONS(APIError): ...
class MemberKickedByOrganizer(APIError): ...
class LevelFiveRequiredToEnableProps(APIError): ...
class ChatViewOnly(APIError): ...
class ChatMessageTooBig(APIError): ...
class InviteCodeNotFound(APIError): ...
class AlreadyRequestedJoinCommunity(APIError): ...
class API_ERR_PUSH_SERVER_LIMITATION_APART(APIError): ...
class API_ERR_PUSH_SERVER_LIMITATION_COUNT(APIError): ...
class API_ERR_PUSH_SERVER_LINK_NOT_IN_COMMUNITY(APIError): ...
class API_ERR_PUSH_SERVER_LIMITATION_TIME(APIError): ...
class AlreadyCheckedIn(APIError): ...
class AlreadyUsedMonthlyRepair(APIError): ...
class AccountAlreadyRestored(APIError): ...
class IncorrectVerificationCode(APIError): ...
class NotOwnerOfChatBubble(APIError): ...
class NotEnoughCoins(APIError): ...
class AlreadyPlayedLottery(APIError): ...
class CannotSendCoins(APIError): ...
class AminoIDAlreadyChanged(APIError): ...
class InvalidAminoID(APIError): ...
class InvalidName(APIError): ...


def check_server_exceptions(status: int, reason: str) -> ServerError:
    return {
        403: TemporaryIPBan,
        413: PayloadTooLarge,
        500: InternalServerError,
        502: BadGateway,
        503: ServiceUnavailable
    }.get(status, ServerError)(status, reason)


def check_exceptions(data: typing.Dict[str, typing.Any]) -> APIError:
    """Raise an exception from the amino API.

    Parameters
    ----------
    data : dict
        The data from the amino API.

    """
    return {
        100: UnsupportedService,
        102: FileTooLarge,
        103: InvalidRequest,
        104: InvalidRequest,
        105: InvalidSession,
        106: AccessDenied,
        107: UnexistentData,
        110: ActionNotAllowed,
        113: MessageNeeded,
        200: InvalidAccountOrPassword,
        201: AccountDisabled,
        210: AccountDisabled,
        213: InvalidEmail,
        214: InvalidPassword,
        215: EmailAlreadyTaken,
        216: AccountDoesntExist,
        218: InvalidDevice,
        219: TooManyRequests,
        221: CantFollowYourself,
        225: UserUnavailable,
        229: YouAreBanned,
        230: UserNotMemberOfCommunity,
        235: RequestRejected,
        238: ActivateAccount,
        239: CantLeaveCommunity,
        240: ReachedTitleLength,
        241: EmailFlaggedAsSpam,
        246: AccountDeleted,
        251: API_ERR_EMAIL_NO_PASSWORD,
        257: API_ERR_COMMUNITY_USER_CREATED_COMMUNITIES_VERIFY,
        262: ReachedMaxTitles,
        270: VerificationRequired,
        271: InvalidAuthNewDeviceLink,
        291: CommandCooldown,
        293: UserBannedByTeamAmino,
        300: BadImage,
        313: InvalidThemepack,
        314: InvalidVoiceNote,
        500: RequestedNoLongerExist,
        700: RequestedNoLongerExist,
        503: PageRepostedTooRecently,
        551: InsufficientLevel,
        702: WallCommentingDisabled,
        801: CommunityNoLongerExists,
        802: InvalidCodeOrLink,
        805: CommunityNameAlreadyTaken,
        806: CommunityCreateLimitReached,
        814: CommunityDisabled,
        833: CommunityDeleted,
        1002: ReachedMaxCategories,
        1501: DuplicatePollOption,
        1507: ReachedMaxPollOptions,
        1600: RequestedNoLongerExist,
        1602: TooManyChats,
        1605: ChatFull,
        1606: TooManyInviteUsers,
        1611: ChatInvitesDisabled,
        1612: RemovedFromChat,
        1613: UserNotJoined,
        1627: API_ERR_CHAT_VVCHAT_NO_MORE_REPUTATIONS,
        1637: MemberKickedByOrganizer,
        1661: LevelFiveRequiredToEnableProps,
        1663: ChatViewOnly,
        1664: ChatMessageTooBig,
        1900: InviteCodeNotFound,
        2001: AlreadyRequestedJoinCommunity,
        2501: API_ERR_PUSH_SERVER_LIMITATION_APART,
        2502: API_ERR_PUSH_SERVER_LIMITATION_COUNT,
        2503: API_ERR_PUSH_SERVER_LINK_NOT_IN_COMMUNITY,
        2504: API_ERR_PUSH_SERVER_LIMITATION_TIME,
        2601: AlreadyCheckedIn,
        2611: AlreadyUsedMonthlyRepair,
        2800: AccountAlreadyRestored,
        3102: IncorrectVerificationCode,
        3905: NotOwnerOfChatBubble,
        4300: NotEnoughCoins,
        4400: AlreadyPlayedLottery,
        4500: CannotSendCoins,
        4501: CannotSendCoins,
        6001: AminoIDAlreadyChanged,
        6002: InvalidAminoID,
        9901: InvalidName,
    }.get(data.get("api:statuscode", 1000), APIError)(data)
