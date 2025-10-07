import os
from fastapi import FastAPI, HTTPException, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import uvicorn

# --- FastAPI app ---
app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:8080",
    "http://192.168.182.108:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")

# --- Security setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = os.environ.get("NOTES_APP_SECRET_KEY", "supersecretkey123")

# --- Models ---
class User(BaseModel):
    username: str
    password: str

class Note(BaseModel):
    title: str
    content: str

class NoteOut(Note):
    id: int
    created_at: str

# --- Database helpers ---
from database import create_user as db_create_user, get_user as db_get_user
from database import (
    create_note as db_create_note,
    get_notes as db_get_notes,
    get_note as db_get_note,
    update_note as db_update_note,
    delete_note as db_delete_note,
    list_users as db_list_users,
    get_user_by_id as db_get_user_by_id,
    delete_user as db_delete_user
)

# --- Helper functions ---
def hash_password(password: str) -> str:
    truncated = password.encode("utf-8")[:72].decode("utf-8", "ignore")
    return pwd_context.hash(truncated)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    truncated = plain_password.encode("utf-8")[:72].decode("utf-8", "ignore")
    return pwd_context.verify(truncated, hashed_password)

def authenticate_user(username: str, password: str):
    user = db_get_user(username)
    if user and verify_password(password, user[2]):
        return user
    return None

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    user = db_get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user

def is_admin_user(user):
    return user and len(user) > 3 and user[3] == 1


# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTMLResponse(
        content="<h1>Welcome to Realtime Notes App</h1><p>Use <a href='/docs'>Swagger UI</a></p>",
        status_code=200
    )

@app.post("/register")
async def register(user: User):
    hashed_password = hash_password(user.password)
    user_id = db_create_user(user.username, hashed_password)
    if user_id:
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user[1]})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Notes CRUD endpoints ---
@app.post("/notes", response_model=NoteOut)
async def create_note(note: Note, user=Depends(get_current_user)):
    row = db_create_note(note.title, note.content)
    return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])

@app.get("/notes", response_model=list[NoteOut])
async def get_notes(user=Depends(get_current_user)):
    rows = db_get_notes()
    return [NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3]) for row in rows]

# --- Admin dashboard route ---
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user=Depends(get_current_user)):
    if not is_admin_user(user):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": user})

# --- Startup for Azure ---
@app.on_event("startup")
async def startup_event():
    print("App started successfully.")

# --- Run server ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
