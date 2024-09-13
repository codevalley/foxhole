import aiohttp
import json
from cli.config import Config
from typing import Optional, Tuple, Dict, Any


class SessionManager:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.current_user: Optional[Dict[str, Any]] = None

    async def login(self, user_secret: str) -> bool:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.config.API_URL}/auth/token", data={"user_secret": user_secret}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.current_user = {
                        "access_token": data["access_token"],
                        "user_secret": user_secret,
                    }
                    await self.fetch_user_info()
                    return True
                return False

    async def register(self, screen_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.config.API_URL}/auth/register",
                json={"screen_name": screen_name},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.current_user = {
                        "id": data["id"],
                        "screen_name": data["screen_name"],
                        "user_secret": data["user_secret"],
                    }
                    await self.login(data["user_secret"])
                    return True, self.current_user
                return False, None

    def logout(self) -> None:
        self.current_user = None

    async def update_profile(self, field: str, value: str) -> bool:
        if not self.current_user:
            return False
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.current_user['access_token']}"}
            async with session.put(
                f"{self.config.API_URL}/auth/users/me",
                headers=headers,
                json={field: value},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.current_user.update(data)
                    return True
                return False

    async def fetch_user_info(self) -> None:
        if not self.current_user:
            return
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.current_user['access_token']}"}
            async with session.get(
                f"{self.config.API_URL}/auth/users/me", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.current_user.update(data)

    def get_name(self) -> Any:
        if self.current_user and "screen_name" in self.current_user:
            return self.current_user["screen_name"]
        return "_"

    def save_session(self) -> None:
        if self.current_user and "user_secret" in self.current_user:
            with open(self.config.SESSION_FILE, "w") as f:
                json.dump({"user_secret": self.current_user["user_secret"]}, f)

    async def load_session(self) -> bool:
        try:
            with open(self.config.SESSION_FILE, "r") as f:
                data = json.load(f)
                user_secret = data.get("user_secret")
                if user_secret:
                    return await self.login(user_secret)
            return False
        except FileNotFoundError:
            return False

    def has_session(self) -> bool:
        try:
            with open(self.config.SESSION_FILE, "r") as f:
                data = json.load(f)
                return "user_secret" in data
        except FileNotFoundError:
            return False
