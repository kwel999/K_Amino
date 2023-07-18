from __future__ import annotations
from typing import Dict, Literal, Optional, TYPE_CHECKING, Union
from time import time as timestamp
from ..lib.objects import *
from ..lib.async_sessions import AsyncSession
if TYPE_CHECKING:
    from .client import AsyncClient

__all__ = ('AsyncAcm',)


class AsyncAcm(AsyncSession):
    """Represents the Amino Community Manager client.

    Parameters
    ----------
    comId : int
        The community ID to manage.
    client : Client
        The amino global client object.
    proxies : dict, optional
        Proxies for HTTP requests supported by the httpx library (https://www.python-httpx.org/advanced/#routing)

    Attributes
    ----------
    comId : int
        The community ID to manage.

    """

    def __init__(self, comId: int, client: AsyncClient, proxies: Optional[dict] = None) -> None:
        self.comId = comId
        AsyncSession.__init__(self, client=client, proxies=proxies)

    async def promote(self, userId: str, rank: Literal['agent', 'curator', 'leader']) -> Json:
        """Promote a user.

        Parameters
        ----------
        userId : str
            The user ID to promote.
        rank : str
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
        req = await self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/{role}")
        return Json(req)

    """
    async def set_push_settings(self, activities: bool = None, broadcasts: bool = None, cid: int = 0):
        return await self.http.post('user-profile/push', dict(
            pushEnabled=bool(activities or broadcasts),
            pushExtensions=dict(
                **dict(communityBroadcastsEnabled=broadcasts) if broadcasts else {},
                **dict(communityActivitiesEnabled=activities) if activities else {},
                #systemEnabled=enable
            )
        ), cid=cid) 
    """
    async def accept_join_request(self, userId: str) -> Json:
        """Accept the community join request.

        Parameters
        ----------
        userId : str
            The user ID to accept.

        Returns
        -------
        Json
            The JSON response.

        """
        req = await self.postRequest(f"/x{self.comId}/s/community/membership-request/{userId}/accept")
        return Json(req)

    async def reject_join_request(self, userId: str) -> Json:
        """Reject the community join request.

        Parameters
        ----------
        userId : str
            The user ID to reject.

        Returns
        -------
        Json
            The JSON response.

        """
        req = await self.postRequest(f"/x{self.comId}/s/community/membership-request/{userId}/reject")
        return Json(req)

    async def change_welcome_message(self, message: str, enabled: bool = True) -> Json:
        """Change the community welcome message.

        Parameters
        ----------
        message : str
            The new welcome message.
        enabled : bool, optional
            Enable the welcome message. Default is True.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {
            "path": "general.welcomeMessage",
            "value": {"enabled": enabled, "text": message},
            "timestamp": int(timestamp() * 1000),
        }
        req = await self.postRequest(f"/x{self.comId}/s/community/configuration", data)
        return Json(req)

    async def change_guidelines(self, content: str) -> Json:
        """Change the community guidelines.

        Parameters
        ----------
        content : str
            The new guidelines content.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"content": content, "timestamp": int(timestamp() * 1000)}
        req = await self.postRequest(f"/x{self.comId}/s/community/guideline", data)
        return Json(req)

    async def edit_community(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        aminoId: Optional[str] = None,
        language: Optional[str] = None,
        themePackUrl: Optional[str] = None,
    ) -> Json:
        """Edit the community.

        Parameters
        ----------
        name : str, optional
            The new community name. If not provided, is not edited.
        description : str, optional
            The new community description. If not provided, is not edited.
        aminoId : str, optional
            The new community amino ID. If not provided, is not edited.
        language : str, optional
            The new community content-language. If not provided, is not edited.
        themePackUrl : str, optional
            The new community theme pack. If not provided, is not edited

        Returns
        -------
        Json
            The JSON response.

        """
        data: Dict[str, Union[str, int]] = {"timestamp": int(timestamp() * 1000)}
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
        req = await self.postRequest(f"/x{self.comId}/s/community/settings", data)
        return Json(req)

    async def get_community_stats(self) -> CommunityStats:
        """Get community member stats.

        Returns
        -------
        CommunityStats
            The community stats object.

        """
        req = await self.getRequest(f"/x{self.comId}/s/community/stats")
        return CommunityStats(req["communityStats"]).CommunityStats

    async def get_admin_stats(self, moderationType: Literal['curator', 'leader'], start: int = 0, size: int = 25) -> Json:
        """Get community moderation stats.

        Parameters
        ----------
        moderationType : str
            The moderation type ('curator', 'leader').
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

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
        req = await self.getRequest(f"/x{self.comId}/s/community/stats/moderation?type={moderationType}&start={start}&size={size}")
        return Json(req)

    async def get_join_requests(self, start: int = 0, size: int = 25) -> JoinRequest:
        """Get community pending join request list.

        Parameters
        ----------
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        JoinRequest
            The join request list object.

        """
        req = await self.getRequest(f"/x{self.comId}/s/community/membership-request?status=pending&start={start}&size={size}")
        return JoinRequest(req).JoinRequest

    async def get_all_members(self, usersType: str = "recent", start: int = 0, size: int = 25) -> UserProfileList:
        """Get community member list.

        Parameters
        ----------
        usersType : str
            The member type ('recent', 'banned', 'featured', 'leaders', 'curators'). Default is 'recent'
        start : int, optional
            The start index. Default is 0.
        size : int, optional
            The size of the list. Default is 25 (max is 100).

        Returns
        -------
        UserProfileList
            The member profile list object.

        """
        usersType = usersType.lower()
        req = await self.getRequest(f"/x{self.comId}/s/user-profile?type={usersType}&start={start}&size={size}")
        return UserProfileList(req["userProfileList"]).UserProfileList

    async def add_influencer(self, userId: str, monthlyFee: int = 50) -> Json:
        """Add a new community vip user.

        Parameters
        ----------
        userId : str
            The user ID to add.
        monthlyFee : int, optional
            The user monthly fee, the minimum is 50 and the maximum is 500. The default is 50.

        Returns
        -------
        Json
            The JSON response.

        """
        data = {"monthlyFee": monthlyFee, "timestamp": int(timestamp() * 1000)}
        req = await self.postRequest(f"/x{self.comId}/s/influencer/{userId}", data)
        return Json(req)

    async def remove_influencer(self, userId: str) -> Json:
        """Remove a community vip user.

        Parameters
        ----------
        userId : str
            The vip user ID.

        Returns
        -------
        Json
            The JSON response.

        """
        req = await self.deleteRequest(f"/x{self.comId}/s/influencer/{userId}")
        return Json(req)
