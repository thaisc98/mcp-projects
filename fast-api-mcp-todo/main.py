"""
Simple Todo List API
--------------------
FastAPI application with SQLite database for managing a basic todo list.
Supports full CRUD operations with automatic interactive documentation at /docs.

Created: 2025
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from contextlib import contextmanager

app = FastAPI(
    title="Simple Todo API",
    description="Basic Todo list management API using FastAPI + SQLite",
    version="1.0.0"
)

DATABASE = "todos.db"

def init_db():
    """Create the todos table if it doesn't exist."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        conn.commit()

# Run initialization once when the module is imported
init_db()

@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # returns rows as dict-like objects
    try:
        yield conn
    finally:
        conn.close()

class TodoCreate(BaseModel):
    content: str

class TodoUpdate(BaseModel):
    content: Optional[str] = None
    completed: Optional[bool] = None

class TodoOut(BaseModel):
    id: int
    content: str
    completed: bool

    class Config:
        from_attributes = True  # allows mapping from dict/row

# ────────────────────────────────────────────────
#  ROUTES
# ────────────────────────────────────────────────

@app.get("/", summary="API welcome message")
def root():
    """Returns a simple welcome message."""
    return {"message": "Welcome to the Todo API! Visit /docs for interactive documentation."}

@app.get("/todos", response_model=List[TodoOut], summary="Get all todos")
def get_all_todos():
    """Retrieve the complete list of todos."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, content, completed FROM todos ORDER BY id")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@app.get("/todos/{todo_id}", response_model=TodoOut, summary="Get a single todo")
def get_todo(todo_id: int):
    """Fetch a specific todo by its ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, content, completed FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Todo not found")
        return dict(row)

@app.post(
    "/todos",
    response_model=TodoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new todo"
)
def create_todo(todo: TodoCreate):
    """Add a new todo item."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO todos (content, completed) VALUES (?, ?)",
            (todo.content, False)
        )
        conn.commit()
        new_id = cursor.lastrowid

        cursor.execute("SELECT id, content, completed FROM todos WHERE id = ?", (new_id,))
        row = cursor.fetchone()
        return dict(row)

@app.patch("/todos/{todo_id}", response_model=TodoOut, summary="Update a todo")
def update_todo(todo_id: int, todo_update: TodoUpdate):
    """Partially update a todo (content and/or completed status)."""
    if todo_update.content is None and todo_update.completed is None:
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM todos WHERE id = ?", (todo_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Todo not found")

        updates = []
        values = []
        if todo_update.content is not None:
            updates.append("content = ?")
            values.append(todo_update.content)
        if todo_update.completed is not None:
            updates.append("completed = ?")
            values.append(todo_update.completed)

        values.append(todo_id)
        query = f"UPDATE todos SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()

        cursor.execute("SELECT id, content, completed FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
        return dict(row)

@app.delete(
    "/todos/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a todo"
)
def delete_todo(todo_id: int):
    """Remove a todo by its ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Todo not found")
        conn.commit()
    return None