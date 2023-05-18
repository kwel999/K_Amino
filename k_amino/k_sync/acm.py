from time import time as timestamp

from ..lib.objects import *
from ..lib.sessions import Session


class Acm(Session):
    def __init__(self, comId: str, proxies: dict = None):
        self.comId = comId
        self.proxies = proxies

        Session.__init__(self, proxies=self.proxies)

    def promote(self, userId: str, rank: str):
        rank = rank.lower().replace("agent", "transfer-agent")

        if rank not in ["transfer-agent", "leader", "curator"]:
            raise TypeError(rank)

        req = self.postRequest(f"/x{self.comId}/s/user-profile/{userId}/{rank}")
        return Json(req)

    """
    def set_push_settings(self, activities: bool = None, broadcasts: bool = None, cid: int = 0):
        return self.http.post('user-profile/push', dict(
            pushEnabled=bool(activities or broadcasts),
            pushExtensions=dict(
                **dict(communityBroadcastsEnabled=broadcasts) if broadcasts else {},
                **dict(communityActivitiesEnabled=activities) if activities else {},
                #systemEnabled=enable
            )
        ), cid=cid) 
    """

    def accept_join_request(self, userId: str):
        req = self.postRequest(
            f"/x{self.comId}/s/community/membership-request/{userId}/accept"
        )
        return Json(req)

    def reject_join_request(self, userId: str):
        req = self.postRequest(
            f"/x{self.comId}/s/community/membership-request/{userId}/reject"
        )
        return Json(req)

    def change_welcome_message(self, message: str, enabled: bool = True):
        data = {
            "path": "general.welcomeMessage",
            "value": {"enabled": enabled, "text": message},
            "timestamp": int(timestamp() * 1000),
        }
        req = self.postRequest(f"/x{self.comId}/s/community/configuration", data)
        return Json(req)

    def change_guidelines(self, content: str):
        data = {"content": content, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/x{self.comId}/s/community/guideline", data)
        return Json(req)

    def edit_community(
        self,
        name: str = None,
        description: str = None,
        aminoId: str = None,
        language: str = None,
        themePackUrl: str = None,
    ):
        data = {"timestamp": int(timestamp() * 1000)}

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

        req = self.postRequest(f"/x{self.comId}/s/community/settings", data)
        return Json(req)

    def get_community_stats(self):
        req = self.getRequest(f"/x{self.comId}/s/community/stats")
        return CommunityStats(req["communityStats"]).CommunityStats

    def get_admin_stats(self, moderationType: str, start: int = 0, size: int = 25):
        if moderationType not in ["leader", "curator"]:
            raise TypeError(moderationType)

        req = self.getRequest(
            f"/x{self.comId}/s/community/stats/moderation?type={moderationType}&start={start}&size={size}"
        )
        return Json(req)

    def get_join_requests(self, start: int = 0, size: int = 25):
        req = self.getRequest(
            f"/x{self.comId}/s/community/membership-request?status=pending&start={start}&size={size}"
        )
        return JoinRequest(req).JoinRequest

    def get_all_members(self, usersType: str, start: int = 0, size: int = 25):
        usersType = usersType.lower()
        req = self.getRequest(
            f"/x{self.comId}/s/user-profile?type={usersType}&start={start}&size={size}"
        )
        return UserProfileList(req["userProfileList"]).UserProfileList

    def add_influencer(self, userId: str, monthlyFee: int = 50):
        data = {"monthlyFee": monthlyFee, "timestamp": int(timestamp() * 1000)}
        req = self.postRequest(f"/x{self.comId}/s/influencer/{userId}", data)
        return Json(req)

    def remove_influencer(self, userId: str):
        req = self.deleteRequest(f"/x{self.comId}/s/influencer/{userId}")
        return Json(req)
