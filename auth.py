from fastapi import Header, HTTPException
from schemas import User


def get_current_user(
    x_user_uuid: str = Header(None), x_api_key: str = Header(None)
) -> User:
    if not x_user_uuid or not x_api_key:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return User(uuid=x_user_uuid, api_key=x_api_key)


def get_user(x_user_uuid: str, x_api_key: str) -> User:
    return User(uuid=x_user_uuid, api_key=x_api_key)
