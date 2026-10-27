#!/usr/bin/env python3
import os
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
# Enable CORS for any origin (Render will serve only this app)
socketio = SocketIO(app, cors_allowed_origins="*")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "todo.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('todo','in_progress','done'))
        )"""
    )
    conn.commit()
    conn.close()

def get_all_tasks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, description, status FROM tasks ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def add_task(description):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (description, status) VALUES (?, 'todo')", (description,))
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return task_id

def update_task_status(task_id, new_status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tasks SET status=? WHERE id=?", (new_status, task_id))
    conn.commit()
    conn.close()

@app.route('/')
def board():
    init_db()
    tasks = get_all_tasks()
    # split tasks by status for the template
    cols = {"todo": [], "in_progress": [], "done": []}
    for tid, desc, status in tasks:
        cols[status].append({"id": tid, "description": desc})
    return render_template('board.html', columns=cols)

@app.route('/add', methods=['POST'])
def add():
    description = request.form.get('description')
    if not description:
        return "Missing description", 400
    task_id = add_task(description)
    task = {"id": task_id, "description": description, "status": "todo"}
    # broadcast to all clients
    socketio.emit('task_added', task, broadcast=True)
    return jsonify(task), 201

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    task_id = data.get('id')
    new_status = data.get('status')
    if not task_id or new_status not in ('todo', 'in_progress', 'done'):
        return "Invalid payload", 400
    update_task_status(task_id, new_status)
    socketio.emit('task_moved', {"id": task_id, "status": new_status}, broadcast=True)
    return "", 204

@socketio.on('connect')
def handle_connect():
    # client connected – nothing special to do
    pass

if __name__ == '__main__':
    # Render provides PORT env var; default to 5000 for local runs
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
