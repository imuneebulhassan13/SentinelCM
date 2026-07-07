from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = "analyst"


#class UserLogin(BaseModel):
#    username: str
#   password: str


class UserResponse(BaseModel):
    username: str
    email: EmailStr
    role: str