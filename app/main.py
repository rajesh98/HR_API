from typing import List
from fastapi import FastAPI
from fastapi import Depends,HTTPException,status,APIRouter
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func, or_, asc


from app import schemas
#from .config import settings
from .database import get_db



from . import models
from . database import engine
from .models import LeaveType, LeaveStatus


#from .router import user,auth, question,quiz,slot,event,result,category,quiztype,room,participant, stateManagement, currentStatus, resend_mail, websocket_api, sdp, clear_db


models.Base.metadata.create_all(bind=engine)



app = FastAPI(
    title="HRMS",
    description="description",
    summary="summary",
    version="0.0.1",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS", "PUT","DELETE"],
    allow_headers=["Access-Control-Allow-Headers", 'Content-Type', 'Authorization','Access-Control-Allow-Origin'],
)



@app.get('/')
def root():
    return {"message": "Welcome To HRMS"}


@app.get("/employees",)
def get_all_user( db:Session = Depends(get_db)):
    emply = db.query(models.Employee).all()
    return emply


@app.get("/employee/id/{id}",)
def get_a_user( id:int, db:Session = Depends(get_db)):
    emply = db.query(models.Employee).filter(models.Employee.employee_id==id).first()
    print(type(emply))
    if emply.manager_employee_id != None:
        manager = db.query(models.Employee).filter(models.Employee.employee_id==emply.manager_employee_id).first()
        emply.manager = manager
    return emply


@app.get("/{id}/leaves/")
def get_leaves( id:int, types: str = "all_types",leave_status:str = "all_status", db:Session = Depends(get_db)):
    #emply = db.query(models.Employee).all()

    if types!= "all_types" and types not in LeaveType:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"leave type '{types}' not found",
            ) 
    
    if leave_status != "all_status" and leave_status not in LeaveStatus:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"leave status '{leave_status}' not found",
            ) 
    
    query = db.query(models.LeaveTransaction).filter(models.LeaveTransaction.employee_id==id)


    if types != "all_types":
        query = query.filter(models.LeaveTransaction.leave_type==types)
    if leave_status != "all_status":
        query = query.filter(models.LeaveTransaction.leave_status==leave_status)

    return query.order_by(models.LeaveTransaction.leave_date.desc()).all()





@app.get("/balance/leaves/{id}/",)
def get_remaining_leave_count( id:int, types: str = "all_types", db:Session = Depends(get_db)):
    #emply = db.query(models.Employee).all()

    if types!= "all_types" and types not in LeaveType:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"leave type '{types}' not found",
            ) 
    
    total_leaves = 30
    casual = 10
    general = 5
    sick = 10
    vaccation = 4
    bereavement = 1
    matternity = 84
    patternity  = 14

    query = db.query(models.LeaveTransaction).filter(models.LeaveTransaction.employee_id==id)  #.count()
    balance = total_leaves- query.count()


    if types != "all_types":
        query = query.filter(models.LeaveTransaction.leave_type==types)
        #balance = total_leaves- query.count()

    if types == "casual":
        balance = casual - query.count()
    if types == "general":
        balance = general - query.count()
    if types == "sick":
        balance = sick - query.count()
    if types == "vaccation":
        balance = vaccation - query.count()
    if types == "bereavement":
        balance = bereavement - query.count()
    if types == "matternity":
        balance = matternity - query.count()
    if types == "patternity":
        balance = patternity - query.count()

    return balance
    


""" @app.get("/{id}/leaves/groupbytypes/")
def get_leaves( id:int, db:Session = Depends(get_db)):
    #emply = db.query(models.Employee).all()
    
    query = db.query(models.LeaveTransaction).filter(models.LeaveTransaction.employee_id==id).group_by(models.LeaveTransaction.leave_type).all()
    return query """



@app.post("/leaves", status_code=status.HTTP_201_CREATED)
def add_leave( leave:schemas.leaveCreate,  db:Session = Depends(get_db)):

    if leave.leave_type not in LeaveType:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"leave type '{leave.leave_type }' not found",
            ) 
    
    existing_leave = db.query(models.LeaveTransaction).filter(models.LeaveTransaction.employee_id==leave.id).filter(models.LeaveTransaction.leave_date==leave.leave_date)
    if existing_leave.first():
        raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"leave in that date already existd",
            ) 
    new_slot = models.LeaveTransaction(leave_date = leave.leave_date, leave_type = leave.leave_type, employee_id= leave.id)
    db.add(new_slot)
    db.commit()
    return new_slot
