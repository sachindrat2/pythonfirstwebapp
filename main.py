
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from database import create_database, create_note as db_create_note, get_notes as db_get_notes, get_note as db_get_note, update_note as db_update_note, delete_note as db_delete_note


create_database()  # Ensure DB and table are created at startup

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


# Create a note
@app.post("/notes", response_model=NoteOut)
async def create_note(note: Note):
    row = db_create_note(note.title, note.content)
    return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])


# Get all notes
@app.get("/notes", response_model=list[NoteOut])
async def get_notes():
    rows = db_get_notes()
    return [NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3]) for row in rows]


# Get a single note
@app.get("/notes/{note_id}", response_model=NoteOut)
async def get_note(note_id: int):
    row = db_get_note(note_id)
    if row:
        return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])
    raise HTTPException(status_code=404, detail="Note not found")


# Update a note
@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(note_id: int, note: Note):
    row = db_update_note(note_id, note.title, note.content)
    if row:
        return NoteOut(id=row[0], title=row[1], content=row[2], created_at=row[3])
    raise HTTPException(status_code=404, detail="Note not found")


# Delete a note
@app.delete("/notes/{note_id}")
async def delete_note(note_id: int):
    deleted = db_delete_note(note_id)
    if deleted:
        return {"message": "Note deleted"}
    raise HTTPException(status_code=404, detail="Note not found")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)