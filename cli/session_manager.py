import aiohttp
import json
from config import Config


class SessionManager:
    def __init__(self, config: Config):
        self.config = config
        self.current_user = None

    async def login(self, user_secret):
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

    async def register(self, screen_name):
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

    def logout(self):
        self.current_user = None

    async def update_profile(self, field, value):
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

    async def fetch_user_info(self):
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

    def get_name(self):
        if self.current_user:
            return self.current_user["screen_name"]
        return "_"

    def save_session(self):
        if self.current_user:
            with open(self.config.SESSION_FILE, "w") as f:
                json.dump(self.current_user, f)

    def load_session(self):
        try:
            with open(self.config.SESSION_FILE, "r") as f:
                self.current_user = json.load(f)
            return True
        except FileNotFoundError:
            return False

    def has_session(self):
        try:
            with open(self.config.SESSION_FILE, "r") as f:
                return True
        except FileNotFoundError:
            return False
