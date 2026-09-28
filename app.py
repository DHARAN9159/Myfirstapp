import os
import sqlite3
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)
DB = os.environ.get("DB_PATH", "tasks.db")


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, done INTEGER DEFAULT 0)")
    return conn


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/tasks")
def list_tasks():
    with db() as c:
        return jsonify([dict(r) for r in c.execute("SELECT * FROM tasks ORDER BY id DESC")])


@app.post("/api/tasks")
def add_task():
    title = (request.json or {}).get("title", "").strip()
    if not title:
        return {"error": "Title is required"}, 400
    with db() as c:
        cur = c.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
        return {"id": cur.lastrowid, "title": title, "done": 0}, 201


@app.patch("/api/tasks/<int:task_id>")
def toggle_task(task_id):
    with db() as c:
        c.execute("UPDATE tasks SET done = 1 - done WHERE id = ?", (task_id,))
    return {"ok": True}


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    with db() as c:
        c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return {"ok": True}


PAGE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Today</title>
<style>
:root{--bg:#eef2f6;--card:#fff;--ink:#1b2a33;--muted:#6b7c88;--brand:#0f4c5c;--accent:#e09f3e;--line:#d6dee5}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.5 Georgia,'Times New Roman',serif;display:flex;justify-content:center;padding:48px 16px}
main{width:100%;max-width:520px}
h1{font-size:2.4rem;margin:0 0 4px;color:var(--brand)}
p.sub{margin:0 0 24px;color:var(--muted);font-family:system-ui,sans-serif;font-size:.95rem}
form{display:flex;gap:8px;margin-bottom:20px}
input[type=text]{flex:1;padding:12px 14px;border:1px solid var(--line);border-radius:8px;font:inherit;background:var(--card)}
button{font-family:system-ui,sans-serif;cursor:pointer}
form button{padding:0 18px;border:0;border-radius:8px;background:var(--brand);color:#fff;font-weight:600}
:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
ul{list-style:none;margin:0;padding:0;background:var(--card);border:1px solid var(--line);border-radius:10px}
li{display:flex;align-items:center;gap:12px;padding:14px 16px;border-bottom:1px solid var(--line)}
li:last-child{border-bottom:0}
li.done span{text-decoration:line-through;color:var(--muted)}
li span{flex:1}
li input{width:20px;height:20px;accent-color:var(--brand)}
li button{background:none;border:0;color:var(--muted);font-size:.9rem}
li button:hover{color:#b3261e}
.empty{padding:24px;text-align:center;color:var(--muted);font-family:system-ui,sans-serif}
</style></head>
<body><main>
<h1>Today</h1>
<p class="sub" id="count">Loading…</p>
<form id="f"><input type="text" id="t" placeholder="What needs doing?" aria-label="New task" required><button>Add task</button></form>
<ul id="list"></ul>
</main>
<script>
const list=document.getElementById('list'),count=document.getElementById('count');
async function load(){
  const tasks=await (await fetch('/api/tasks')).json();
  const open=tasks.filter(t=>!t.done).length;
  count.textContent=tasks.length?`${open} open, ${tasks.length-open} done`:'Nothing yet';
  list.innerHTML=tasks.length?'':'<div class="empty">Add your first task above.</div>';
  tasks.forEach(t=>{
    const li=document.createElement('li'); if(t.done) li.className='done';
    const cb=document.createElement('input'); cb.type='checkbox'; cb.checked=!!t.done;
    cb.onchange=async()=>{await fetch('/api/tasks/'+t.id,{method:'PATCH'});load()};
    const s=document.createElement('span'); s.textContent=t.title;
    const d=document.createElement('button'); d.textContent='Delete';
    d.onclick=async()=>{await fetch('/api/tasks/'+t.id,{method:'DELETE'});load()};
    li.append(cb,s,d); list.append(li);
  });
}
document.getElementById('f').onsubmit=async e=>{
  e.preventDefault(); const i=document.getElementById('t');
  await fetch('/api/tasks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:i.value})});
  i.value=''; load();
};
load();
</script></body></html>"""


@app.get("/")
def index():
    return render_template_string(PAGE)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
