
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

# --- Test Swagger visibility ---
@app.get("/test-visibility")
def test_visibility():
    return {"status": "visible"}

# --- Health check endpoint ---
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cors_origins": len(origins),
        "message": "API is running"
    }

# --- CORS test endpoint ---
@app.get("/cors-test")
async def cors_test(request: Request):
    return {
        "message": "CORS test successful",
        "origin": request.headers.get("origin"),
        "allowed_origins": origins,
        "user_agent": request.headers.get("user-agent"),
        "timestamp": datetime.utcnow().isoformat()
    }

# --- CORS ---
origins = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:8080",
    "http://127.0.0.1:8083",
    "http://192.168.182.108:8080",
    "http://localhost:8080",  # for local testing
    "http://127.0.0.1:8080",
    "http://localhost:3000",  # React frontend
    "http://127.0.0.1:3000",
    "https://ownnoteapp-hedxcahwcrhwb8hb.canadacentral-01.azurewebsites.net",  # deployed backend
    "https://sachindrat2.github.io",  # GitHub Pages frontend
    "https://sachindrat2.github.io/reactnoteApp",  # GitHub Pages frontend with path
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# --- CORS preflight handler ---
@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    return {"message": "OK"}

# --- Logout endpoint ---
@app.post("/logout")
async def logout():
    # For JWT, logout is handled client-side by deleting the token.
    # Optionally, you can instruct the client to remove the token.
    return {"message": "Logged out. Please remove the token from your client."}

# --- Templates ---
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
    user_id = user[0]  # user[0] is the user ID from the database
    row = db_create_note(note.title, note.content, user_id)
    return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])

@app.get("/notes", response_model=list[NoteOut])
async def get_notes(user=Depends(get_current_user)):
    user_id = user[0]  # user[0] is the user ID from the database
    rows = db_get_notes(user_id)
    return [NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3]) for row in rows]

@app.get("/admin/notes", response_model=list[NoteOut])
async def get_all_notes(user=Depends(get_current_user)):
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    rows = db_get_notes()  # Get all notes for admin
    return [NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3]) for row in rows]

@app.get("/notes/{note_id}", response_model=NoteOut)
async def get_note(note_id: int, user=Depends(get_current_user)):
    note = db_get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns the note or is admin
    if note[4] != user[0] and not is_admin_user(user):  # note[4] is user_id, user[0] is current user id
        raise HTTPException(status_code=403, detail="Access denied")
    
    return NoteOut(id=note[0], title=note[1], content=note[2], created_at=note[3])

@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(note_id: int, note: Note, user=Depends(get_current_user)):
    existing_note = db_get_note(note_id)
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns the note or is admin
    if existing_note[4] != user[0] and not is_admin_user(user):  # existing_note[4] is user_id
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_note = db_update_note(note_id, note.title, note.content)
    return NoteOut(id=updated_note[0], title=updated_note[1], content=updated_note[2], created_at=updated_note[3])

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, user=Depends(get_current_user)):
    existing_note = db_get_note(note_id)
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns the note or is admin
    if existing_note[4] != user[0] and not is_admin_user(user):  # existing_note[4] is user_id
        raise HTTPException(status_code=403, detail="Access denied")
    
    deleted = db_delete_note(note_id)
    if deleted:
        return {"message": "Note deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete note")

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
