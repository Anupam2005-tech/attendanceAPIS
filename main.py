import random
from fastapi import FastAPI, Depends,HTTPException, WebSocketDisconnect,status,WebSocket,APIRouter
from pydantic import EmailStr
import auth
from auth import Hash, get_current_user,oauth2_bearer
from schemas import   UserSchema,TokenData
from models import UserModel
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import routes

app=FastAPI()
router=APIRouter()


def get_db():
    db=SessionLocal()
    try:
        yield db

    finally:
        db.close()
Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(routes.router)


allowed_origins =[
"http://localhost:5173",
"http://localhost:8000",
"http://127.0.0.1:8000",
"http://127.0.0.1:5500",


]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  
    allow_credentials=True,          
    allow_methods=["*"],              
    allow_headers=["*"],          
)

@app.get("/")
async def root():
        return ('hello')



@app.post('/user/create')
async def create_user(payload: UserSchema, db: Session = Depends(get_db)):
    try:
        user_query = db.query(UserModel).filter(UserModel.email == payload.email).first()
        if user_query:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Use a different email')
        else:
            new_user = UserModel( email=payload.email, password=Hash.hash_password(payload.password))
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return {'message': 'User Created Successfully'}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    


connected_clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            graph_data = [
                {"name": f"Page {chr(65 + i)}", "sell": random.randint(1000, 99999)}
                for i in range(6)
            ]
            await websocket.send_json(graph_data)
            await asyncio.sleep(3) 
            
    except Exception as e:
        print(f"Client disconnected: {e}")
    finally:
        connected_clients.remove(websocket)





if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', host="localhost", port=8000, reload=True)




