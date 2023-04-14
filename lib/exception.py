# From https://github.com/okok7711/AminoAcid/blob/master/aminoacid/exceptions.py


class AminoBaseException(Exception):
    ...


class UnknownExcepion(AminoBaseException):
    ...


class AccessDenied(AminoBaseException):
    ...


class UnsupportedService(AminoBaseException):
    ...


class InvalidRequest(AminoBaseException):
    ...


class InvalidSession(AminoBaseException):
    ...


class InvalidAccountOrPassword(AminoBaseException):
    ...


class InvalidDevice(AminoBaseException):
    ...


class TooManyRequests(AminoBaseException):
    ...


class ActionNotAllowed(AminoBaseException):
    ...


class FileTooLarge(AminoBaseException):
    ...


class UnexistentData(AminoBaseException):
    ...


class MessageNeeded(AminoBaseException):
    ...


class AccountDisabled(AminoBaseException):
    ...


class InvalidEmail(AminoBaseException):
    ...


class InvalidPassword(AminoBaseException):
    ...


class EmailAlreadyTaken(AminoBaseException):
    ...


class AccountDoesntExist(AminoBaseException):
    ...


class CantFollowYourself(AminoBaseException):
    ...


class UserUnavailable(AminoBaseException):
    ...


class YouAreBanned(AminoBaseException):
    ...


class UserNotMemberOfCommunity(AminoBaseException):
    ...


class RequestRejected(AminoBaseException):
    ...


class ActivateAccount(AminoBaseException):
    ...


class CantLeaveCommunity(AminoBaseException):
    ...


class ReachedTitleLength(AminoBaseException):
    ...


class EmailFlaggedAsSpam(AminoBaseException):
    ...


class AccountDeleted(AminoBaseException):
    ...


class API_ERR_EMAIL_NO_PASSWORD(AminoBaseException):
    ...


class API_ERR_COMMUNITY_USER_CREATED_COMMUNITIES_VERIFY(AminoBaseException):
    ...


class ReachedMaxTitles(AminoBaseException):
    ...


class VerificationRequired(AminoBaseException):
    ...


class API_ERR_INVALID_AUTH_NEW_DEVICE_LINK(AminoBaseException):
    ...


class CommandCooldown(AminoBaseException):
    ...


class UserBannedByTeamAmino(AminoBaseException):
    ...


class BadImage(AminoBaseException):
    ...


class InvalidThemepack(AminoBaseException):
    ...


class InvalidVoiceNote(AminoBaseException):
    ...


class RequestedNoLongerExist(AminoBaseException):
    ...


class PageRepostedTooRecently(AminoBaseException):
    ...


class InsufficientLevel(AminoBaseException):
    ...


class WallCommentingDisabled(AminoBaseException):
    ...


class CommunityNoLongerExists(AminoBaseException):
    ...


class InvalidCodeOrLink(AminoBaseException):
    ...


class CommunityNameAlreadyTaken(AminoBaseException):
    ...


class CommunityCreateLimitReached(AminoBaseException):
    ...


class CommunityDisabled(AminoBaseException):
    ...


class CommunityDeleted(AminoBaseException):
    ...


class ReachedMaxCategories(AminoBaseException):
    ...


class DuplicatePollOption(AminoBaseException):
    ...


class ReachedMaxPollOptions(AminoBaseException):
    ...


class TooManyChats(AminoBaseException):
    ...


class ChatFull(AminoBaseException):
    ...


class TooManyInviteUsers(AminoBaseException):
    ...


class ChatInvitesDisabled(AminoBaseException):
    ...


class RemovedFromChat(AminoBaseException):
    ...


class UserNotJoined(AminoBaseException):
    ...


class API_ERR_CHAT_VVCHAT_NO_MORE_REPUTATIONS(AminoBaseException):
    ...


class MemberKickedByOrganizer(AminoBaseException):
    ...


class LevelFiveRequiredToEnableProps(AminoBaseException):
    ...


class ChatViewOnly(AminoBaseException):
    ...


class ChatMessageTooBig(AminoBaseException):
    ...


class InviteCodeNotFound(AminoBaseException):
    ...


class AlreadyRequestedJoinCommunity(AminoBaseException):
    ...


class API_ERR_PUSH_SERVER_LIMITATION_APART(AminoBaseException):
    ...


class API_ERR_PUSH_SERVER_LIMITATION_COUNT(AminoBaseException):
    ...


class API_ERR_PUSH_SERVER_LINK_NOT_IN_COMMUNITY(AminoBaseException):
    ...


class API_ERR_PUSH_SERVER_LIMITATION_TIME(AminoBaseException):
    ...


class AlreadyCheckedIn(AminoBaseException):
    ...


class AlreadyUsedMonthlyRepair(AminoBaseException):
    ...


class AccountAlreadyRestored(AminoBaseException):
    ...


class IncorrectVerificationCode(AminoBaseException):
    ...


class NotOwnerOfChatBubble(AminoBaseException):
    ...


class NotEnoughCoins(AminoBaseException):
    ...


class AlreadyPlayedLottery(AminoBaseException):
    ...


class CannotSendCoins(AminoBaseException):
    ...


class AminoIDAlreadyChanged(AminoBaseException):
    ...


class InvalidAminoID(AminoBaseException):
    ...


class InvalidName(AminoBaseException):
    ...


def CheckExceptions(data: dict):
    raise {
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
            271: API_ERR_INVALID_AUTH_NEW_DEVICE_LINK,
            291: CommandCooldown,
            293: UserBannedByTeamAmino,
            300: BadImage,
            313: InvalidThemepack,
            314: InvalidVoiceNote,
            500: RequestedNoLongerExist,
            700: RequestedNoLongerExist,
            1600: RequestedNoLongerExist,
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
        }.get(data.get("api:statuscode", 1000), UnknownExcepion)(data)
