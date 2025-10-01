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
from fastapi import Form, Request
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
from fastapi.templating import Jinja2Templates
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTMLResponse(
        content="""
        <html>
            <head><title>Realtime Notes App</title></head>
            <body>
                <h1>Welcome to the Realtime Notes App!</h1>
                <p>Use <a href='/docs'>Swagger UI</a> to explore the API.</p>
            </body>
        </html>
        """,
        status_code=200
    )

# --- Security setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
import os
# Use a fixed secret key for JWT signing and verification
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

class AdminUser(User):
    is_admin: int = 1

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
            access_token = create_access_token(data={"sub": user.username})
            return {"access_token": access_token, "token_type": "bearer"}
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

@app.post("/register-admin")
async def register_admin(user: AdminUser):
    try:
        if not user.password:
            raise HTTPException(status_code=400, detail="Password is required.")
        hashed_password = hash_password(user.password)
        user_id = db_create_user(user.username, hashed_password, is_admin=user.is_admin)
        if user_id:
            access_token = create_access_token(data={"sub": user.username})
            return {"access_token": access_token, "token_type": "bearer", "message": "Admin user registered successfully"}
        else:
            raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# --- Notes CRUD Endpoints ---
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

from fastapi.responses import RedirectResponse

# --- Admin Register ---
@app.get("/admin/register", response_class=HTMLResponse)
async def admin_register_page(request: Request):
    return templates.TemplateResponse("admin_register.html", {"request": request, "error": None})

@app.post("/admin/register", response_class=HTMLResponse)
async def admin_register(request: Request, username: str = Form(...), password: str = Form(...)):
    hashed_password = hash_password(password)
    user_id = db_create_user(username, hashed_password, is_admin=1)
    if user_id:
        return RedirectResponse("/admin/login", status_code=303)
    else:
        return templates.TemplateResponse("admin_register.html", {"request": request, "error": "Username already exists."})

# --- Admin Login ---
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})

@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = db_get_user(username)
    if user and verify_password(password, user[2]) and is_admin_user(user):
        access_token = create_access_token({"sub": username})
        response = RedirectResponse("/admin", status_code=303)
        response.set_cookie(key="admin_token", value=access_token, httponly=True, max_age=3600)
        return response
    else:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid credentials or not admin."})

# --- Admin Logout ---
@app.post("/admin/logout", response_class=HTMLResponse)
async def admin_logout(request: Request):
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie("admin_token")
    return response

# --- Admin Account ---
@app.get("/admin/account", response_class=HTMLResponse)
async def admin_account(request: Request):
    token = request.cookies.get("admin_token")
    if not token:
        return RedirectResponse("/admin/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db_get_user(username)
        if not is_admin_user(user):
            raise Exception()
    except Exception:
        return RedirectResponse("/admin/login", status_code=303)
    return templates.TemplateResponse("account.html", {"request": request, "user": user})
from fastapi.responses import HTMLResponse

def is_admin_user(user):
    # user tuple: (id, username, password, is_admin)
    return user and len(user) > 3 and user[3] == 1


# Setup Jinja2 templates
from fastapi import Request, Query
import jwt as pyjwt
templates = Jinja2Templates(directory="templates")



# --- Admin Dashboard ---
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    token = request.cookies.get("admin_token")
    debug_info = []
    if not token:
        return RedirectResponse("/admin/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db_get_user(username)
        if not is_admin_user(user):
            raise Exception()
    except Exception:
        return RedirectResponse("/admin/login", status_code=303)
    users = db_list_users()
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "token": token,
            "debug_info": None
        }
    )
    users = db_list_users()
    debug_info.append(f"Users list: {users}")
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "token": token,
            "debug_info": "\n".join(debug_info)
        }
    )
# --- Admin Create User ---
@app.post("/admin/create", response_class=HTMLResponse)
async def admin_create_user_html(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    is_admin: int = Form(0),
    token: str = Form(...)
):
    debug_info = []
    # Validate token and get user
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username_from_token = payload.get("sub")
        user = db_get_user(username_from_token)
        if not is_admin_user(user):
            debug_info.append("Unauthorized: Not admin or invalid token.")
            users = db_list_users()
            return templates.TemplateResponse(
                "admin_dashboard.html",
                {
                    "request": request,
                    "user": user,
                    "users": users,
                    "token": token,
                    "debug_info": "\n".join(debug_info)
                }
            )
    except Exception:
        debug_info.append("Unauthorized: Invalid token.")
        users = db_list_users()
        return templates.TemplateResponse(
            "admin_dashboard.html",
            {
                "request": request,
                "user": None,
                "users": users,
                "token": token,
                "debug_info": "\n".join(debug_info)
            }
        )
    hashed_password = hash_password(password)
    user_id = db_create_user(username, hashed_password, is_admin=is_admin)
    msg = "User created" if user_id else "Username already exists"
    users = db_list_users()
    debug_info.append(msg)
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "token": token,
            "debug_info": "\n".join(debug_info)
        }
    )

@app.post("/admin/delete/{user_id}", response_class=HTMLResponse)

@app.post("/admin/delete/{user_id}", response_class=HTMLResponse)
async def admin_delete_user_html(user_id: int, token: str = Form(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db_get_user(username)
        if not user or not is_admin_user(user):
            raise HTTPException(status_code=403, detail="Admin access required")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    deleted = db_delete_user(user_id)
    msg = "User deleted" if deleted else "User not found"
    return f"<html><body><h2>{msg}</h2><a href='/admin'>Back to Admin Dashboard</a></body></html>"

# --- Admin Endpoints ---
from fastapi import Security, Form


@app.get("/admin/users")
async def admin_list_users(user=Depends(get_current_user)):
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db_list_users()
    return [{"id": u[0], "username": u[1], "is_admin": bool(u[2])} for u in users]

@app.get("/admin/users/{user_id}")
async def admin_get_user(user_id: int, user=Depends(get_current_user)):
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    u = db_get_user_by_id(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": u[0], "username": u[1], "is_admin": bool(u[2])}

@app.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: int, user=Depends(get_current_user)):
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    deleted = db_delete_user(user_id)
    if deleted:
        return {"message": "User deleted"}
    raise HTTPException(status_code=404, detail="User not found")

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
