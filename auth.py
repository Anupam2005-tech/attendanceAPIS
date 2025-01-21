from datetime import timedelta, datetime, timezone, date
from typing import Optional
from fastapi import HTTPException, Depends, APIRouter, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from database import SessionLocal, Base, engine
from models import LoginHistory, UserModel
from schemas import LoginSchema, Token, TokenData
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["Authentication"])

SECRET_KEY = os.getenv("secret_key")
ALGORITHM = os.getenv("algorithm")
ACCESS_TOKEN_EXPIRE_MINUTES = 10080

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)


class Hash:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_bearer)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return TokenData(email=email)
    except JWTError:
        raise credentials_exception


@router.post("/login", response_model=Token)
async def login(
    payload: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        user_login = (
            db.query(UserModel).filter(UserModel.email == payload.username).first()
        )

        if not user_login:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
            )

        if not Hash.verify_password(payload.password, user_login.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Password"
            )



        access_token = create_access_token(
            data={"sub": user_login.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        response = JSONResponse(
            {
                "access_token": access_token,
                "token_type": "bearer",
                "message": "Login successful",
            }
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Strict",
        )

        return response

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

# @router.post('/login', response_model=Token)
# async def login(payload: LoginSchema, db: Session = Depends(get_db)):
#     try:
#         user_login = db.query(UserModel).filter(UserModel.email == payload.email).first()
#         if not user_login:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Invalid Credentials')
#         if not Hash.verify_password(payload.password, user_login.password):
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid Password')

#         access_token = create_access_token(
#             data={"sub": user_login.email},
#             expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
#         )

#         response = JSONResponse(
#             {
#                 "access_token": access_token,
#                 "token_type": "bearer",
#                 "message": "Login successful",
#             }
#         )

#         response.set_cookie(
#             key="access_token",
#             value=access_token,
#             httponly=True,
#             secure=True,
#             samesite="Strict",
#         )

#         return response

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/logout")
async def logout(
    response: Response, current_user: TokenData = Depends(get_current_user)
):
    try:
        response.delete_cookie(key="access_token")
        return {"message": "Logged out successfully"}

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
