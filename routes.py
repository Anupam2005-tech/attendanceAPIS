from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from schemas import LoginHistorySchema, UserUpdate
from models import LoginHistory, UserModel
from database import get_db, SessionLocal, Base
from sqlalchemy.orm import Session
from auth import get_current_user, Hash
from pathlib import Path
from io import BytesIO

router = APIRouter(tags=["User Options"])
app = FastAPI()

UPLOAD_IMAGE = Path() / "uploads"
ALLOWED_FILE_TYPE = {"image/png", "image/jpeg"}


@router.delete("/user/delete", status_code=status.HTTP_200_OK)
async def delete_current_user(
    db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)
):

    user = db.query(UserModel).filter(UserModel.email == current_user.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not authenticated")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.put("/user/update/profile", status_code=status.HTTP_200_OK)
async def update_user(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )

    if payload.email != current_user.email:
        existing_user = (
            db.query(UserModel).filter(UserModel.email == payload.email).first()
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use"
            )

    current_user.name = payload.name
    current_user.email = payload.email
    current_user.password = Hash.hash_password(payload.password)

    db.commit()
    db.refresh(current_user)

    return {"message": "User profile updated successfully", "user": current_user}


@router.post("/upload/user/profile")
async def upload_user_profile(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Session = Depends(get_current_user),
):
    try:
        query_user = (
            db.query(UserModel).filter(UserModel.email == current_user.email).first()
        )
        file_data = await file.read()
        if not query_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        elif query_user:
            if file.content_type not in ALLOWED_FILE_TYPE:
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"unsupported file type {file.filename}",
                )
            query_user.profile_photo = file_data
            db.commit()
            db.refresh(query_user)
            return "uploaded successfully"

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    

    
    
@router.get('/user/show/profile_photo')
async def get_user_profile_photo(db:Session=Depends(get_db),current_user:Session=Depends(get_current_user)):
    query_user_image=db.query(UserModel).filter(UserModel.email==current_user.email).first()
    if not query_user_image or not query_user_image.profile_photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No image found")
    
    find_image=BytesIO(query_user_image.profile_photo)
    media_type=ALLOWED_FILE_TYPE
    if query_user_image.profile_photo.startswith(b'\x89PNG'):
        media_type = "image/png"
    elif query_user_image.profile_photo.startswith(b'\xff\xd8'):
        media_type = "image/jpeg"
        
    return StreamingResponse(find_image,media_type=media_type)

