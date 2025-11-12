from datetime import datetime, date, time
import re
from pydantic import BaseModel, EmailStr, validator
from typing import Dict, Optional,List, Any


#### User, login, Auth 
class RoleOut(BaseModel):
    role:Optional[str]
    class Config:
        orm_mode = True

class User(BaseModel):
    id:int
    hire_date:Optional[datetime]
    full_name:str
    department:Optional[str]
    role:Optional[str]
    #Employee:Optional[User]

class leaveCreate(BaseModel):
    id:int
    leave_date: date
    leave_type:Optional[str]
