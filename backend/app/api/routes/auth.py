from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import UserRegister
from app.core.dependencies import get_current_user, require_admin

from app.services.auth_service import (
    register_user,
    login_user,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register")
async def register(user: UserRegister):

    result = await register_user(user)

    if result is None:

        raise HTTPException(
            status_code=400,
            detail="Username or Email already exists",
        )

    return {
        "message": "User registered successfully"
    }


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    token = await login_user(
        form_data.username,
        form_data.password
    )

    if token is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    return token

@router.get("/me")
async def current_user(user=Depends(get_current_user)):
    return {
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
    }

#test admin

@router.get("/admin")
async def admin_panel(admin=Depends(require_admin)):
    return {
        "message": "Welcome Admin",
        "username": admin["username"]
    }