import asyncio
from time import time as timestamp

import aiohttp
import ujson as json

from ..lib import *
from ..lib.objects import *


class SAcm(Headers):
    def __init__(self, comId: str):
        if not comId: self.comId = None
        if comId: self.comId = comId

        Headers.__init__(self)

        self.uid = headers.userId
        self.headers = self.app_headers
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args) -> None:
        await self.session.close()

    def __del__(self):
        loop = asyncio.get_event_loop()
        try:
            loop.create_task(self._close_session())
        except RuntimeError:
            loop.run_until_complete(self._close_session())

    async def _close_session(self):
        await self.session.close()

    async def promote(self, userId: str, rank: str):
        if rank.lower() not in ["agent", "leader", "curator"]: raise TypeError(rank)
        rank = rank.replace("agent", "transfer-agent")

        async with self.session.post(api(f"/x{self.comId}/s/user-profile/{userId}/{rank}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def accept_join_request(self, userId: str):
        async with self.session.post(api(f"/x{self.comId}/s/community/membership-request/{userId}/accept"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(req.json())

    async def reject_join_request(self, userId: str):
        async with self.session.post(api(f"/x{self.comId}/s/community/membership-request/{userId}/reject"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def change_welcome_message(self, message: str, enabled: bool = True):
        data = json.dumps({
            "path": "general.welcomeMessage",
            "value": {"enabled": enabled, "text": message},
            "timestamp": int(timestamp() * 1000)
        })
        async with self.session.post(api(f"/x{self.comId}/s/community/configuration"), data=data, headers=self.updateHeaders(data=data)) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def change_guidelines(self, content: str):
        data = json.dumps({"content": content, "timestamp": int(timestamp() * 1000)})
        async with self.session.post(api(f"/x{self.comId}/s/community/guideline"), headers=self.updateHeaders(data=data), data=data) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def edit_community(self, name: str = None, description: str = None, aminoId: str = None, lang: str = None, themePackUrl: str = None):
        data = {"timestamp": int(timestamp() * 1000)}

        if name: data["name"] = name
        if description: data["content"] = description
        if aminoId: data["endpoint"] = aminoId
        if lang: data["primaryLanguage"] = lang
        if themePackUrl: data["themePackUrl"] = themePackUrl

        data = json.dumps(data)
        async with self.session.post(api(f"/x{self.comId}/s/community/settings"), data=data, headers=self.updateHeaders(data=data)) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def get_community_stats(self):
        async with self.session.get(api(f"/x{self.comId}/s/community/stats"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return CommunityStats((await req.json())["communityStats"]).CommunityStats

    async def get_admin_stats(self, type: str, start: int = 0, size: int = 25):
        type = type.lower()

        if type == "leader": pass
        elif type == "curator": pass
        else: raise TypeError(type)

        async with self.session.get(api(f"/x{self.comId}/s/community/stats/moderation?type={type}&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def get_join_requests(self, start: int = 0, size: int = 25):
        async with self.session.get(api(f"/x{self.comId}/s/community/membership-request?status=pending&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return JoinRequest(await req.json()).JoinRequest

    async def get_all_members(self, type: str, start: int = 0, size: int = 25):
        type = type.lower()
        async with self.session.get(api(f"/x{self.comId}/s/user-profile?type={type}&start={start}&size={size}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return UserProfileList((await req.json())["userProfileList"]).UserProfileList

    async def add_influencer(self, userId: str, monthlyFee: int = 50):
        data = json.dumps({"monthlyFee": monthlyFee, "timestamp": int(timestamp() * 1000)})
        async with self.session.post(api(f"/x{self.comId}/s/influencer/{userId}"), data=data, headers=self.updateHeaders(data=data)) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())

    async def remove_influencer(self, userId: str):
        async with self.session.delete(api(f"/x{self.comId}/s/influencer/{userId}"), headers=self.headers) as req:
            if req.status != 200: return CheckExceptions(await req.json())
            else: return Json(await req.json())
