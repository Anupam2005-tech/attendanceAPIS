from database import Base
from sqlalchemy import Column, Integer,String,DateTime,func,ForeignKey,LargeBinary
from sqlalchemy.orm import relationship

class UserModel(Base):
        __tablename__="Userdatabase"
        id=Column(Integer,primary_key=True,index=True)
        name=Column(String)
        email=Column(String,unique=True)
        password=Column(String)
        profile_photo=Column(LargeBinary,nullable=True) 
        login_history=relationship('LoginHistory',back_populates='user')


class LoginHistory(Base):
        __tablename__ = 'login_history'
        id = Column(Integer, primary_key=True,index=True)
        user_id=Column(Integer,ForeignKey('Userdatabase.id'),nullable=False)
        datetime=Column(DateTime(timezone=True),server_default=func.now())
        device=Column(String,nullable=True)
        location=Column(String,nullable=True)
        user=relationship('UserModel',back_populates='login_history')






