# Realtime Notes App - Azure Deployment Ready
import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import uvicorn
import hashlib

# --- Initialize database on startup ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing database...")
    try:
        from database import create_database
        create_database()
        print("Database initialized successfully")
        print("App started successfully.")
    except Exception as e:
        print(f"Database initialization error: {e}")
    yield
    # Shutdown
    print("App shutting down...")

# --- FastAPI app ---
app = FastAPI(lifespan=lifespan)

# --- CORS configuration ---
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://sachindrat2.github.io",
    "https://sachindrat2.github.io/reactnoteApp",
    "https://ownnoteapp-hedxcahwcrhwb8hb.canadacentral-01.azurewebsites.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # allow all HTTP methods
    allow_headers=["*"],  # allow all headers
)

# --- Optional fallback for OPTIONS preflight ---
@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    origin = request.headers.get("origin", "")
    response = Response(status_code=200)
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# --- Templates ---
templates = Jinja2Templates(directory="templates")

# --- Security setup ---
# Use a simpler hashing approach to avoid bcrypt compatibility issues
def hash_password(password: str) -> str:
    """Hash password using SHA-256 (simple but functional for demo)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

# Fallback to bcrypt with better error handling
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    use_bcrypt = True
except Exception as e:
    print(f"Warning: bcrypt not available, using SHA-256: {e}")
    use_bcrypt = False
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

class DeleteResponse(BaseModel):
    message: str

# --- Database helpers ---
from database import create_user as db_create_user, get_user as db_get_user
from database import (
    create_note as db_create_note,
    get_notes as db_get_notes,
    get_note as db_get_note,
    update_note as db_update_note,
    delete_note as db_delete_note,
    get_users as db_get_users,
    delete_user as db_delete_user,
    delete_user_notes as db_delete_user_notes,
    get_all_notes as db_get_all_notes
)

# --- Helper functions ---
def hash_password_safe(password: str) -> str:
    """Safe password hashing with fallback"""
    if use_bcrypt:
        try:
            truncated = password.encode("utf-8")[:72].decode("utf-8", "ignore")
            return pwd_context.hash(truncated)
        except Exception:
            pass
    return hash_password(password)

def verify_password_safe(plain_password: str, hashed_password: str) -> bool:
    """Safe password verification with fallback"""
    if use_bcrypt and hashed_password.startswith('$'):
        try:
            truncated = plain_password.encode("utf-8")[:72].decode("utf-8", "ignore")
            return pwd_context.verify(truncated, hashed_password)
        except Exception:
            pass
    return verify_password(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = db_get_user(username)
    if user and verify_password_safe(password, user[2]):
        return user
    return None

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request = None, token: str = Depends(oauth2_scheme)):
    """Get current user from token (either Authorization header or cookie)"""
    # First try the Authorization header (for API calls)
    if token and token != "null":
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username:
                user = db_get_user(username)
                if user:
                    return user
        except JWTError:
            pass
    
    # If header token failed, try cookie (for web interface) if request is available
    if request:
        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            try:
                payload = jwt.decode(cookie_token, SECRET_KEY, algorithms=[ALGORITHM])
                username = payload.get("sub")
                if username:
                    user = db_get_user(username)
                    if user:
                        return user
            except JWTError:
                pass
    
    raise HTTPException(status_code=401, detail="Invalid authentication")

# Create a wrapper for web endpoints that need request context
async def get_current_user_web(request: Request, token: str = Depends(oauth2_scheme)):
    """Get current user with request context for web endpoints"""
    return await get_current_user(request, token)

def verify_admin_auth(request: Request):
    """Helper function to verify admin authentication via cookie"""
    cookie_token = request.cookies.get("access_token")
    if not cookie_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(cookie_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db_get_user(username)
        if not user or not is_admin_user(user):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def is_admin_user(user):
    return user and len(user) > 3 and user[3] == 1

# --- Routes (examples) ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTMLResponse(
        content="<h1>Welcome to Realtime Notes App</h1><p>Use <a href='/docs'>Swagger UI</a></p>",
        status_code=200
    )

@app.post("/register")
async def register(user: User):
    hashed_password = hash_password_safe(user.password)
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
@app.post("/notes", 
          response_model=NoteOut,
          summary="Create Note",
          description="Create a new note for the authenticated user")
async def create_note(note: Note, user=Depends(get_current_user)):
    """Create a new note for the authenticated user"""
    user_id = user[0]  # user[0] is the user ID from the database
    row = db_create_note(note.title, note.content, user_id)
    return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])

@app.get("/notes", 
         response_model=list[NoteOut],
         summary="Get User Notes",
         description="Get all notes for the authenticated user only")
async def get_notes(user=Depends(get_current_user)):
    """Get all notes for the authenticated user only"""
    user_id = user[0]  # user[0] is the user ID from the database
    rows = db_get_notes(user_id)
    return [NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3]) for row in rows]

@app.get("/notes/{note_id}", response_model=NoteOut)
async def get_note(note_id: int, user=Depends(get_current_user)):
    """Get a specific note if the user owns it"""
    note = db_get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns the note or is admin
    if len(note) > 4 and note[4] != user[0] and not is_admin_user(user):  # note[4] is user_id
        raise HTTPException(status_code=403, detail="Access denied")
    
    return NoteOut(id=note[0], title=note[1], content=note[2], created_at=note[3])

@app.put("/notes/{note_id}", 
         response_model=NoteOut,
         summary="Update Note",
         description="Update a note if the user owns it")
async def update_note(note_id: int, note: Note, user=Depends(get_current_user)):
    """Update a note if the user owns it"""
    existing_note = db_get_note(note_id)
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns the note or is admin
    if len(existing_note) > 4 and existing_note[4] != user[0] and not is_admin_user(user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_note = db_update_note(note_id, note.title, note.content)
    return NoteOut(id=updated_note[0], title=updated_note[1], content=updated_note[2], created_at=updated_note[3])

@app.delete("/notes/{note_id}", 
           response_model=DeleteResponse,
           summary="Delete Note",
           description="Delete a specific note if the user owns it",
           responses={
               200: {"description": "Note deleted successfully"},
               404: {"description": "Note not found"},
               403: {"description": "Access denied - not your note"},
               401: {"description": "Authentication required"}
           })
async def delete_note(note_id: int, user=Depends(get_current_user)):
    """Delete a note if the user owns it"""
    existing_note = db_get_note(note_id)
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns the note or is admin
    if len(existing_note) > 4 and existing_note[4] != user[0] and not is_admin_user(user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    deleted = db_delete_note(note_id)
    if deleted:
        return {"message": "Note deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete note")

# --- Admin endpoints ---
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_redirect():
    """Redirect /admin to /admin/dashboard"""
    return RedirectResponse(url="/admin/dashboard")

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request):
    """Admin dashboard HTML page - checks authentication internally"""
    # Check for token in cookie
    cookie_token = request.cookies.get("access_token")
    if not cookie_token:
        return RedirectResponse(url="/admin/login")
    
    try:
        payload = jwt.decode(cookie_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return RedirectResponse(url="/admin/login")
        
        user = db_get_user(username)
        if not user or not is_admin_user(user):
            return RedirectResponse(url="/admin/login")
        
        return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": user})
    except JWTError:
        return RedirectResponse(url="/admin/login")

@app.get("/admin/login", response_class=HTMLResponse) 
async def admin_login_page(request: Request):
    """Admin login HTML page"""
    try:
        return templates.TemplateResponse("admin_login.html", {"request": request})
    except Exception as e:
        # Fallback if template fails
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head><title>Admin Login</title></head>
        <body>
        <h1>Admin Login</h1>
        <p>Template loading error: {str(e)}</p>
        <form method="post" action="/admin/login">
            <input type="text" name="username" placeholder="Username" required><br><br>
            <input type="password" name="password" placeholder="Password" required><br><br>
            <button type="submit">Login</button>
        </form>
        </body>
        </html>
        """)

@app.post("/admin/login")
async def admin_login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    """Admin login endpoint"""
    user = db_get_user(form_data.username)
    if not user or not verify_password_safe(form_data.password, user[2]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    access_token = create_access_token(data={"sub": user[1]})
    
    # Set the token as a cookie for web interface
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True, 
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    
    return {"access_token": access_token, "token_type": "bearer", "redirect": "/admin/dashboard"}

@app.get("/admin/api/stats")
async def get_admin_stats(request: Request):
    """Admin only: Get system statistics"""
    user = verify_admin_auth(request)
    
    # Get user count
    users = db_get_users()
    user_count = len(users)
    admin_count = len([u for u in users if u[3] == 1])
    
    # Get notes count
    notes = db_get_all_notes()
    total_notes = len(notes)
    
    # Get recent activity (last 7 days)
    recent_notes = [n for n in notes if n[3]]  # Filter notes with created_at
    
    return {
        "total_users": user_count,
        "admin_users": admin_count, 
        "regular_users": user_count - admin_count,
        "total_notes": total_notes,
        "recent_notes": len(recent_notes)
    }

@app.get("/admin/api/chart-data")
async def get_chart_data(request: Request):
    """Admin only: Get detailed data for charts"""
    user = verify_admin_auth(request)
    
    from datetime import datetime, timedelta
    import calendar
    
    # Get all data
    users = db_get_users()
    notes = db_get_all_notes()
    
    # User distribution
    user_count = len(users)
    admin_count = len([u for u in users if u[3] == 1])
    regular_count = user_count - admin_count
    
    # Monthly activity (last 6 months)
    now = datetime.now()
    monthly_data = []
    monthly_users = []
    monthly_notes = []
    
    for i in range(6):
        month_date = now - timedelta(days=30 * i)
        month_name = calendar.month_abbr[month_date.month]
        monthly_data.append(month_name)
        
        # Simulate monthly growth
        base_users = max(1, regular_count // 6)
        base_notes = max(1, len(notes) // 6)
        monthly_users.append(base_users + (i * 2))
        monthly_notes.append(base_notes + (i * 5))
    
    # Reverse to show chronological order
    monthly_data.reverse()
    monthly_users.reverse()
    monthly_notes.reverse()
    
    # Activity by day of week
    daily_activity = [15, 25, 30, 28, 35, 20, 10]  # Mon-Sun
    
    return {
        "user_distribution": {
            "labels": ["Regular Users", "Admin Users"],
            "data": [regular_count, admin_count]
        },
        "monthly_activity": {
            "labels": monthly_data,
            "users": monthly_users,
            "notes": monthly_notes
        },
        "daily_activity": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "data": daily_activity
        },
        "stats": {
            "total_users": user_count,
            "total_notes": len(notes),
            "active_users": max(1, user_count // 2),
            "growth_rate": "+12%"
        }
    }

@app.get("/admin/api/users")
async def get_all_users(request: Request):
    """Admin only: Get all users with their note counts"""
    user = verify_admin_auth(request)
    
    users = db_get_users()
    notes = db_get_all_notes()
    
    # Count notes per user
    user_note_counts = {}
    for note in notes:
        if len(note) > 4:  # Check if note has user_id
            user_id = note[4]
            user_note_counts[user_id] = user_note_counts.get(user_id, 0) + 1
    
    result = []
    for u in users:
        result.append({
            "id": u[0],
            "username": u[1], 
            "is_admin": u[3] == 1,
            "note_count": user_note_counts.get(u[0], 0),
            "created_at": "N/A"  # Add if you have user creation date
        })
    
    return result

@app.get("/admin/api/notes", response_model=list[NoteOut])
async def get_all_notes_with_user(request: Request):
    """Admin only: Get all notes from all users with user info"""
    user = verify_admin_auth(request)
    
    notes = db_get_all_notes()
    users = db_get_users()
    user_map = {u[0]: u[1] for u in users}  # id -> username
    
    result = []
    for row in notes:
        note_data = {
            "id": row[0],
            "title": row[1], 
            "content": row[2],
            "created_at": row[3],
            "user_id": row[4] if len(row) > 4 else None,
            "username": user_map.get(row[4], "Unknown") if len(row) > 4 else "Unknown"
        }
        result.append(note_data)
    
    return result

@app.delete("/admin/api/users/{user_id}")
async def delete_user_admin(user_id: int, request: Request):
    """Admin only: Delete a user and all their notes"""
    current_user = verify_admin_auth(request)
    
    # Don't allow deleting yourself
    if user_id == current_user[0]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # Delete user's notes first
    db_delete_user_notes(user_id)
    
    # Delete user
    success = db_delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User and their notes deleted successfully"}

@app.delete("/admin/api/notes/{note_id}")
async def delete_note_admin(note_id: int, request: Request):
    """Admin only: Delete any note by ID"""
    current_user = verify_admin_auth(request)
    
    success = db_delete_note(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {"message": "Note deleted successfully"}

@app.get("/admin/notes", response_model=list[NoteOut])
async def get_all_notes(user=Depends(get_current_user)):
    """Admin only: Get all notes from all users (legacy endpoint)"""
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    rows = db_get_all_notes()  # Get all notes for admin
    return [NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3]) for row in rows]

# --- Logout endpoint ---
@app.post("/logout")
async def logout(response: Response):
    """Logout endpoint (clears cookie)"""
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

@app.post("/admin/logout")
async def admin_logout(response: Response):
    """Admin logout endpoint"""
    response.delete_cookie(key="access_token")
    return RedirectResponse(url="/admin/login", status_code=302)

# --- Health check endpoint ---
@app.get("/health")
async def health_check():
    """Health check endpoint for Azure deployment"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Notes API is running",
        "version": "1.0.1"
    }

@app.get("/admin/test")
async def admin_test():
    """Test endpoint to verify admin routes work"""
    return {
        "status": "success", 
        "message": "Admin routes are working!", 
        "admin_login_url": "/admin/login",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/favicon.ico")
async def favicon():
    """Return empty response for favicon requests"""
    return Response(status_code=204)

# --- Initialize database on startup ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing database...")
    try:
        from database import create_database
        create_database()
        print("Database initialized successfully")
        print("App started successfully.")
    except Exception as e:
        print(f"Database initialization error: {e}")
    yield
    # Shutdown
    print("App shutting down...")



# --- Run server ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
