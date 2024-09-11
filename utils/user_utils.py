from app.models import User
from app.schemas.user_schema import UserInfo


def get_user_info(user: User) -> UserInfo:
    return UserInfo(id=user.id, screen_name=user.screen_name)
