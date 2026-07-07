from app.models.user import get_user_collection

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

from datetime import datetime
from app.schemas.user import UserRegister


async def register_user(user: UserRegister):

    users = get_user_collection()

    existing = await users.find_one(
        {
            "$or": [
                {"username": user.username},
                {"email": user.email},
            ]
        }
    )

    if existing:
        return None

    document = {
    "username": user.username,
    "email": user.email,
    "password": hash_password(user.password),
    "role": user.role,
    "is_active": True,
    "created_at": datetime.utcnow(),
    "last_login": None
}

    await users.insert_one(document)

    return {
        "username": document["username"],
        "email": document["email"],
         "role": document["role"]
    }


async def login_user(
    username: str,
    password: str
):

    users = get_user_collection()

    db_user = await users.find_one(
    {
        "username": username
    }
)

    if not db_user:
        return None

    if not verify_password(
        password,
        db_user["password"]
    ):
        return None

    token = create_access_token(
        {
            "sub": db_user["username"],
            "role": db_user["role"],
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }