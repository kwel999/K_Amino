import time
import typing_extensions as typing
from ..lib.objects import CommunityStats, JoinRequest, Json, UserProfileList
from ..lib.async_sessions import AsyncSession
from ..lib.types import ProxiesType, UserType
from .client import AsyncClient

__all__ = ('AsyncAcm',)


class AsyncAcm(AsyncSession):
    """Represents the Amino Community Manager client.

    Parameters
    ----------
    comId : `int`
        The community ID to manage.
    client : `AsyncClient`
        The amino global client object.
    proxies : `ProxiesType`, `optional`
        Proxies for HTTP requests supported by the httpx library (https://www.python-httpx.org/advanced/#routing)

    Attributes
    ----------
    comId : `int`
        The community ID to manage.

    """

    def __init__(
        self,
        comId: int,
        client: AsyncClient,
        proxies: typing.Optional[ProxiesType] = None
    ) -> None:
        self.comId = comId
        AsyncSession.__init__(self, client=client, proxies=proxies)

    async def promote(self, userId: str, rank: typing.Literal['agent', 'curator', 'leader']) -> Json:
        """Promote a user.

        Parameters
        ----------
        userId : `str`
            The user ID to promote.
        rank : `str`
            The rank to promote (agent, curator, leader).

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the rank is invalid.

        """
        role = rank.lower().replace("agent", "transfer-agent")
        if rank not in ["transfer-agent", "leader", "curator"]:
            raise ValueError('rank must be agent, curator or leader not %r' % rank)
        return Json(await self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/{role}"))

    async def accept_join_request(self, userId: str) -> Json:
        """Accept the community join request.

        Parameters
        ----------
        userId : `str`
            The user ID to accept.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest(f"/x{self.comId}/s/community/membership-request/{userId}/accept"))

    async def reject_join_request(self, userId: str) -> Json:
        """Reject the community join request.

        Parameters
        ----------
        userId : `str`
            The user ID to reject.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(await self.postRequest(f"/x{self.comId}/s/community/membership-request/{userId}/reject"))

    async def change_welcome_message(self, message: str, enabled: bool = True) -> Json:
        """Change the community welcome message.

        Parameters
        ----------
        message : `str`
            The new welcome message.
        enabled : `bool`, `optional`
            Enable the welcome message. Default is `True`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "path": "general.welcomeMessage",
            "value": {
                "enabled": enabled,
                "text": message
            },
            "timestamp": int(time.time() * 1000),
        }
        return Json(await self.postRequest(f"/x{self.comId}/s/community/configuration", data))

    async def change_guidelines(self, content: str) -> Json:
        """Change the community guidelines.

        Parameters
        ----------
        content : `str`
            The new guidelines content.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "content": content,
            "timestamp": int(time.time() * 1000)
        }
        return Json(await self.postRequest(f"/x{self.comId}/s/community/guideline", data))

    async def edit_community(
        self,
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        aminoId: typing.Optional[str] = None,
        language: typing.Optional[str] = None,
        themePackUrl: typing.Optional[str] = None
    ) -> Json:
        """Edit the community.

        Parameters
        ----------
        name : `str`, `optional`
            The new community name. If not provided, is not edited.
        description : `str`, `optional`
            The new community description. If not provided, is not edited.
        aminoId : `str`, `optional`
            The new community amino ID. If not provided, is not edited.
        language : `str`, `optional`
            The new community content-language. If not provided, is not edited.
        themePackUrl : `str`, `optional`
            The new community theme pack. If not provided, is not edited

        Returns
        -------
        Json
            The JSON response.

        """
        data: typing.Dict[str, typing.Any] = {"timestamp": int(time.time() * 1000)}
        if name:
            data["name"] = name
        if description:
            data["content"] = description
        if aminoId:
            data["endpoint"] = aminoId
        if language:
            data["primaryLanguage"] = language
        if themePackUrl:
            data["themePackUrl"] = themePackUrl
        return Json(await self.postRequest(f"/x{self.comId}/s/community/settings", data))

    async def get_community_stats(self) -> CommunityStats:
        """Get community member stats.

        Returns
        -------
        CommunityStats
            The community stats object.

        """
        return CommunityStats((await self.getRequest(f"/x{self.comId}/s/community/stats"))["communityStats"]).CommunityStats

    async def get_admin_stats(self, moderationType: typing.Literal['curator', 'leader'], start: int = 0, size: int = 25) -> Json:
        """Get community moderation stats.

        Parameters
        ----------
        moderationType : `str`
            The moderation type ('curator', 'leader').
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        Json
            The JSON response.

        Raises
        ------
        ValueError
            If the moderationType is invalid.

        """
        if moderationType not in ["leader", "curator"]:
            raise ValueError(moderationType)
        return Json(await self.getRequest(f"/x{self.comId}/s/community/stats/moderation?type={moderationType}&start={start}&size={size}"))

    async def get_join_requests(self, start: int = 0, size: int = 25) -> JoinRequest:
        """Get community pending join request list.

        Parameters
        ----------
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        JoinRequest
            The join request list object.

        """
        return JoinRequest(await self.getRequest(f"/x{self.comId}/s/community/membership-request?status=pending&start={start}&size={size}")).JoinRequest

    async def get_all_members(self, usersType: UserType = "recent", start: int = 0, size: int = 25) -> UserProfileList:
        """Get community member list.

        Parameters
        ----------
        usersType : `str`
            The member type ('recent', 'banned', 'featured', 'leaders', 'curators'). Default is 'recent'
        start : `int`, `optional`
            The start index. Default is `0`.
        size : `int`, `optional`
            The size of the list. Default is `25` (max is 100).

        Returns
        -------
        UserProfileList
            The member profile list object.

        """
        return UserProfileList((await self.getRequest(f"/x{self.comId}/s/user-profile?type={usersType}&start={start}&size={size}"))["userProfileList"]).UserProfileList

    async def add_influencer(self, userId: str, monthlyFee: int = 50) -> Json:
        """Add a new community vip user.

        Parameters
        ----------
        userId : `str`
            The user ID to add.
        monthlyFee : `int`, `optional`
            The user monthly fee, the minimum is 50 and the maximum is 500. The default is `50`.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "monthlyFee": monthlyFee,
            "timestamp": int(time.time() * 1000)
        }
        return Json(await self.postRequest(f"/x{self.comId}/s/influencer/{userId}", data))

    async def remove_influencer(self, userId: str) -> Json:
        """Remove a community vip user.

        Parameters
        ----------
        userId : `str`
            The vip user ID.

        Returns
        -------
        Json
            The JSON response.

        """
        return Json(self.deleteRequest(f"/x{self.comId}/s/influencer/{userId}"))
