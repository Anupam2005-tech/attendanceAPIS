from datetime import datetime
from typing import Optional
from pydantic import BaseModel,EmailStr

class UserSchema(BaseModel):
    name:str
    email:EmailStr
    password:str

class LoginSchema(BaseModel):
    email:EmailStr
    password:str

class UserDelete(BaseModel):
    email:EmailStr
    password:str
    

class UserUpdate(BaseModel):
    email:EmailStr|None
    password:str|None
    name:str|None


class LoginHistorySchema(BaseModel):
    datetime: datetime
    device: Optional[str] = None
    location: Optional[str] = None

class Token(BaseModel):
    access_token:str
    token_type:str

class TokenData(BaseModel):
    email:Optional[str]=None




class Config:
    orm_mode=True




