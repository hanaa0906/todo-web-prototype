import os
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'todo.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 description TEXT NOT NULL,
                 completed INTEGER NOT NULL DEFAULT 0
               )''')
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        # Adding a task
        desc = request.form.get('description')
        if desc:
            c.execute('INSERT INTO tasks (description) VALUES (?)', (desc,))
            conn.commit()
            return redirect(url_for('index'))
    # Fetch tasks for display
    c.execute('SELECT id, description, completed FROM tasks ORDER BY id')
    tasks = c.fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/done/<int:task_id>')
def mark_done(task_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE tasks SET completed = 1 WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete(task_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Use the port provided by Render (or default 5000)
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
