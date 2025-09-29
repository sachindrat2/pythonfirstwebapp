
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import uvicorn
from database import create_database, create_note as db_create_note, get_notes as db_get_notes, get_note as db_get_note, update_note as db_update_note, delete_note as db_delete_note
import sqlite3
from passlib.context import CryptContext



create_database()  # Ensure DB and table are created at startup

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User model
class User(BaseModel):
    username: str
    password: str

def create_users_table():
    conn = sqlite3.connect("notes_app.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

create_users_table()

def get_user(username: str):
    conn = sqlite3.connect("notes_app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username: str, password: str):
    hashed_password = pwd_context.hash(password)
    conn = sqlite3.connect("notes_app.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return None
    conn.close()
    return user_id

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if user and pwd_context.verify(password, user[2]):
        return user
    return None

class Note(BaseModel):
    title: str
    content: str

class NoteOut(Note):
    id: int
    created_at: str


app = FastAPI()



@app.get("/")
async def read_root():
    return {"message": "Welcome to the Realtime Notes App!"}

# Register endpoint
@app.post("/register")
async def register(user: User):
    user_id = create_user(user.username, user.password)
    if user_id:
        return {"message": "User registered successfully"}
    raise HTTPException(status_code=400, detail="Username already exists")

# Login endpoint (token)
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # For demo, return username as token (not secure for production)
    return {"access_token": user[1], "token_type": "bearer"}

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user



# Create a note (authenticated)
@app.post("/notes", response_model=NoteOut)
async def create_note(note: Note, user=Depends(get_current_user)):
    row = db_create_note(note.title, note.content)
    return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])



# Get all notes (authenticated)
@app.get("/notes", response_model=list[NoteOut])
async def get_notes(user=Depends(get_current_user)):
    rows = db_get_notes()
    return [NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3]) for row in rows]



# Get a single note (authenticated)
@app.get("/notes/{note_id}", response_model=NoteOut)
async def get_note(note_id: int, user=Depends(get_current_user)):
    row = db_get_note(note_id)
    if row:
        return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])
    raise HTTPException(status_code=404, detail="Note not found")



# Update a note (authenticated)
@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(note_id: int, note: Note, user=Depends(get_current_user)):
    row = db_update_note(note_id, note.title, note.content)
    if row:
        return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])
    raise HTTPException(status_code=404, detail="Note not found")



# Delete a note (authenticated)
@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, user=Depends(get_current_user)):
    deleted = db_delete_note(note_id)
    if deleted:
        return {"message": "Note deleted"}
    raise HTTPException(status_code=404, detail="Note not found")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)