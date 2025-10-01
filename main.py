from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import uvicorn
import secrets
from database import create_user as db_create_user, get_user as db_get_user
from fastapi.middleware.cors import CORSMiddleware

# --- FastAPI app ---

app = FastAPI()
origins = [
    "http://localhost:8081",  # your Kotlin Web frontend
    "http://127.0.0.1:8081",
    "http://localhost:8080",   # your Kotlin frontend
    "http://127.0.0.1:8080",
    # you can add more origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # allow these origins
    allow_credentials=True,      # allow cookies / auth headers
    allow_methods=["*"],         # allow GET, POST, PUT, DELETE, etc
    allow_headers=["*"],         # allow headers
)


# --- Root Endpoint ---
from fastapi.responses import HTMLResponse
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head><title>Realtime Notes App</title></head>
        <body>
            <h1>Welcome to the Realtime Notes App!</h1>
            <p>Use <a href='/docs'>Swagger UI</a> to explore the API.</p>
        </body>
    </html>
    """

# --- Security setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = secrets.token_urlsafe(32)


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


# --- Routes ---

@app.post("/register")
async def register(user: User):
    try:
        if not user.password:
            raise HTTPException(status_code=400, detail="Password is required.")
        hashed_password = hash_password(user.password)
        user_id = db_create_user(user.username, hashed_password)
        if user_id:
            return {"message": "User registered successfully"}
        else:
            raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user[1]})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Notes CRUD Endpoints ---
from database import (
    create_note as db_create_note,
    get_notes as db_get_notes,
    get_note as db_get_note,
    update_note as db_update_note,
    delete_note as db_delete_note
)

@app.post("/notes", response_model=NoteOut)
async def create_note(note: Note, user=Depends(get_current_user)):
    row = db_create_note(note.title, note.content)
    return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])

@app.get("/notes", response_model=list[NoteOut])
async def get_notes(user=Depends(get_current_user)):
    rows = db_get_notes()
    return [NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3]) for row in rows]

@app.get("/notes/{note_id}", response_model=NoteOut)
async def get_note(note_id: int, user=Depends(get_current_user)):
    row = db_get_note(note_id)
    if row:
        return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])
    raise HTTPException(status_code=404, detail="Note not found")

@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(note_id: int, note: Note, user=Depends(get_current_user)):
    row = db_update_note(note_id, note.title, note.content)
    if row:
        return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])
    raise HTTPException(status_code=404, detail="Note not found")

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, user=Depends(get_current_user)):
    deleted = db_delete_note(note_id)
    if deleted:
        return {"message": "Note deleted"}
    raise HTTPException(status_code=404, detail="Note not found")

# --- Run server ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
