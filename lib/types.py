import typing
import httpx
import enum

__all__ = (
    'CommentPermission',
    'FileType',
    'FilterType',
    'JoinType',
    'NoticeType',
    'ProxyType',
    'ProxiesType',
    'SortingType',
    'ThirdPartType',
    'UserType'
)

FileType: typing.TypeAlias = typing.Literal[
    "audio",
    "gif",
    "image"
]
FilterType: typing.TypeAlias = typing.Literal[
    "recommended"
]
NoticeType: typing.TypeAlias = typing.Literal[
    "usersV2"
]
ProxyType = typing.Union[
    httpx.Proxy,
    httpx.URL,
    str
]
ProxiesType = typing.Union[
    typing.Dict[
        typing.Union[
            httpx.URL,
            str
        ],
        typing.Optional[ProxyType]
    ],
    ProxyType
]
SortingType: typing.TypeAlias = typing.Literal[
    "newest",
    "oldest",
    "vote"
]
ThirdPartType: typing.TypeAlias = typing.Literal[
    "facebook",
    "google"
]
UserType: typing.TypeAlias = typing.Literal[
    "banned",
    "curators",
    "leaders",
    "featured",
    "newest",
    "recent",
    "online"
]  # newest or recent ?


# future features clues

class CommentPermission(int, enum.Enum):
    EVERYONE = enum.auto()
    FOLLOWINGS = enum.auto()
    ONLY_ME = enum.auto()


class JoinType(int, enum.Enum):
    OPEN = enum.auto()
    APPROVAL_REQUIRED = enum.auto()
    INVITE_ONLY = enum.auto()
