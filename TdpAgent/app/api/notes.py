from __future__ import annotations
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.mysql_ops import MysqlOps

router = APIRouter()

# --- Models ---

class NoteCreate(BaseModel):
    case_id: int
    source: Optional[str] = None
    detail: str
    date: Optional[datetime] = None

class NoteUpdate(BaseModel):
    source: Optional[str] = None
    detail: Optional[str] = None
    date: Optional[datetime] = None

# --- Endpoints ---

@router.post("/", status_code=201)
def create_note(note: NoteCreate):
    ops = MysqlOps()
    note_id = ops.create_note(
        case_id=note.case_id,
        source=note.source,
        detail=note.detail,
        date=note.date,
    )
    return {"id": note_id}

@router.get("/case/{case_id}")
def list_notes_for_case(case_id: int, limit: int = Query(default=50, ge=1, le=200)):
    ops = MysqlOps()
    rows = ops.list_notes_for_case(case_id, limit)
    return {
        "items": [
            {
                "id": r.id,
                "case_id": r.case_id,
                "date": r.date,
                "source": r.source,
                "detail": r.detail,
            }
            for r in rows
        ]
    }

@router.get("/{note_id}")
def get_note(note_id: int):
    ops = MysqlOps()
    r = ops.get_note_by_id(note_id)
    if not r:
        raise HTTPException(status_code=404, detail="Note not found")

    return {
        "id": r.id,
        "case_id": r.case_id,
        "date": r.date,
        "source": r.source,
        "detail": r.detail,
    }

@router.put("/{note_id}")
def update_note(note_id: int, note: NoteUpdate):
    ops = MysqlOps()
    # model_dump(exclude_unset=True) is the modern Pydantic v2 way to do .dict()
    update_data = note.model_dump(exclude_unset=True) 
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
        
    ops.update_note(note_id, update_data)
    return {"msg": "Note updated successfully"}

@router.delete("/{note_id}")
def delete_note(note_id: int):
    ops = MysqlOps()
    ops.delete_note(note_id)
    return {"msg": "Note deleted successfully"}