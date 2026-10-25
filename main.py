from fastapi import FastAPI,Depends,HTTPException,Form,UploadFile,File,Cookie,Response,Request
from schemas import Todo as TodoSchema,TodoCreate
from sqlalchemy.orm import Session
from database import SessionLocal,engine,Base
from models import Todo 
from typing import List,Optional
import uuid
import io
import pandas as pd
from PyPDF2 import PdfReader
from datetime import datetime,timedelta
from jose import JWTError,jwt
Base.metadata.create_all(bind=engine)

app=FastAPI()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.post("/todos",response_model=TodoSchema)
def create(todo:TodoCreate,db:Session=Depends(get_db)): #TodoSchema handles json response
    db_todo=Todo(**todo.dict())#todo.model_dump() converts pydantic model to dict and then we unpack it to create a new Todo object
    db.add(db_todo)
    db.commit() # finally stores value in db
    db.refresh(db_todo)
    return db_todo# return object so that it can be converted to json
@app.get("/todos",response_model=list[TodoSchema])
def read(db:Session=Depends(get_db)):
    return db.query(Todo).all()
# get single todo by id
@app.get("/todos/{todo_id}",response_model=TodoSchema)
def read_todo(todo_id:int,db:Session=Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404,detail=f"Todo with id {todo_id} not found")
    return todo
@app.put("/todos/{todo_id}",response_model=TodoSchema)
def update_todo(todo_id:int,updated:TodoCreate,db:Session=Depends(get_db)):
    todo=db.query(Todo).filter(Todo.id==todo_id).first()
    if not todo:
        raise HTTPException(status_code=404,detail=f"Todo with id {todo_id} not found")
    for key ,val in updated.dict().items():
        setattr(todo,key,val)
    db.commit()
    db.refresh(todo)
    return todo
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id:int,db:Session=Depends(get_db)):
    todo=db.query(Todo).filter(Todo.id==todo_id).first()
    if not todo:
        raise HTTPException(status_code=404,detail=f"Todo with id {todo_id} not found")
    db.delete(todo)
    db.commit()
    return {"message":f"Todo with id {todo_id} deleted successfully"}

@app.post("/feedback")
def feedback(name:str=Form(...),email:str=Form(...),feedback:str=Form(...)):
    return {"name":name,"email":email,"feedback":feedback}
      
@app.post("/file-upload")
async def file_upload(file:UploadFile=File(...)):
    content= await file.read()
    try:
        text_p=content.decode("utf-8")
    except UnicodeDecodeError:
        text_p="File is not a text file"
    return {
            "File Name":file.filename,
            "File Type":file.content_type,
            "Size in Bytes":len(content),
            "Text_preview":text_p[:200]
        }
@app.post("/file-upload-multiple")
async def file_upload_multiple(files:List[UploadFile]=File(...)):
   result=[]
   for file in files:
       content=await file.read()
       try:
           text_p=content.decode("utf-8")
       except UnicodeDecodeError:
           text_p="File is not a text file"
       result.append({
            "File Name":file.filename,
            "File Type":file.content_type,
            "Size in Bytes":len(content),
            "Text_preview":text_p[:200]
        })
   return result
@app.post("/file-upload-excel")
async def file_upload_excel(file:UploadFile=File(...)):
    content=await file.read()
    name=file.filename.lower()
    if name.endswith(".csv"):
        df=pd.read_csv(io.BytesIO(content))
    elif name.endswith((".xls", ".xlsx")):
        df=pd.read_excel(io.BytesIO(content))

        return {"Type":"Excel","Data":df.head().to_dict()}
    elif name.endswith(".pdf"):
        reader=PdfReader(io.BytesIO(content))
        text="".join([p.extract_text() for p in reader.pages[:2]])
        return {"Type":"PDF","Text":text.strip()[:500]}
    return {"Error":"File type not supported"}

#user + password-> sever

sessions={}
name="Mayur"
password="Test@1234"
time=120
@app.post("/login")
def login(uname:str,passwd:str,res:Response):
    if uname==name and passwd==password:
        sid=str(uuid.uuid4())
        curr_time=datetime.now()
        exp_time=curr_time+timedelta(seconds=time)
        print(f"curr time :{curr_time}")

        sessions[sid]={"username":uname,"exp_time":exp_time}
        res.set_cookie(key="sid",value=sid,httponly=True,max_age=time)
        return {"message":"Logged in Successfully"}
    else:
        raise HTTPException(status_code=401,detail="Invalid Credentials")
@app.get("/home")        
def home(request:Request,res:Response):
    sid = request.cookies.get("sid")
    print("Cookie received:", bool(sid))
    print("Session found:", bool(sid and sid in sessions))
    if not sid or sid not in sessions:
        raise HTTPException(status_code=401,detail="Not authenticated")
    session_data=sessions[sid]
    if session_data["exp_time"]<datetime.now():
        del sessions[sid]
        raise HTTPException(status_code=401,detail="Session Expired")
    return {"user":session_data["username"]}    

@app.post("/logout")
def logout(request:Request,res:Response):
    sid = request.cookies.get("sid")
    if sid in sessions:
        del sessions[sid]
        res.delete_cookie(key="sid")
        return {"message":"Logged out Successfully"}
    else:
        raise HTTPException(status_code=401,detail="Not logged in")

req_counter={}
max_req=10
@app.get("/data")
def get_request(request:Request):
    client_ip=request.client.host
    req_counter[client_ip]=req_counter.get(client_ip,0)+1
    print(req_counter)
    if req_counter[client_ip]>max_req:
        raise HTTPException(status_code==429,"Too many request")
    return {"message":f"Thanks for connecting {req_counter[client_ip]} times"}

# sessions={}
# name="Mayur"
# password="Test@1234"
# def login(uname:str,passwd:str,res:Response):
#     if uname==name and passwd==passwd:
#         sid=str(uuid.uuid4())
#         sessions[sid]={"username":uname}
#         res.set_cookie(key=sid,value=sid,httponly=True)
#         return {"Message":"Logged in Successful"}
    
#     else:
#         raise HTTPException(status_code=401,detail="Invalid Credentials")

# @app.get("/home")

# def home(sid:Optional[str]=Cookie(None)):
#     if sid and sid not in sessions:
#         raise HTTPException(status_code=401,detail="Not Autheticated")
#     return {"user":sessions[sid]}

# @app.post("/logout")
# def logout(sid:Optional[str]=Cookie(None)):
#     if sid in sessions:
#         del sessions[sid]
#         return {"Message":"Logged out"}
#     else:
#         raise HTTPException(status_code=401,detail="Not Logged in")
