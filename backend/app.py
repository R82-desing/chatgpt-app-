import os
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import redis
from celery import Celery

app = Flask(__name__)
CORS(app)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "devopshub")
DB_PASSWORD = os.getenv("DB_PASSWORD", "devopshub")
DB_NAME = os.getenv("DB_NAME", "devopshub")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

celery = Celery(
    "devopshub",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
)

cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def wait_for_db():
    for _ in range(30):
        try:
            conn = db_connection()
            conn.close()
            return
        except mysql.connector.Error:
            time.sleep(2)
    raise RuntimeError("Database is not available")


@app.get("/api/health")
def health():
    db_ok = False
    redis_ok = False
    try:
        conn = db_connection()
        conn.close()
        db_ok = True
    except Exception:
        pass
    try:
        redis_ok = bool(cache.ping())
    except Exception:
        pass

    status = "ok" if db_ok and redis_ok else "degraded"
    return jsonify({"status": status, "database": db_ok, "redis": redis_ok})


@app.get("/api/projects")
def get_projects():
    conn = db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.id, p.name, p.description,
               COUNT(t.id) AS task_count,
               SUM(CASE WHEN t.completed = 1 THEN 1 ELSE 0 END) AS completed_count
        FROM projects p
        LEFT JOIN tasks t ON p.id = t.project_id
        GROUP BY p.id
        ORDER BY p.id DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)


@app.post("/api/projects")
def create_project():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    if not name:
        return jsonify({"error": "Project name is required"}), 400

    conn = db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects (name, description) VALUES (%s, %s)",
        (name, description),
    )
    conn.commit()
    project_id = cur.lastrowid
    cur.close()
    conn.close()
    cache.delete("projects")
    return jsonify({"id": project_id, "name": name, "description": description}), 201


@app.get("/api/projects/<int:project_id>/tasks")
def get_tasks(project_id):
    conn = db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT id, project_id, title, description, completed, created_at "
        "FROM tasks WHERE project_id=%s ORDER BY id DESC",
        (project_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)


@app.post("/api/projects/<int:project_id>/tasks")
def create_task(project_id):
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    if not title:
        return jsonify({"error": "Task title is required"}), 400

    conn = db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM projects WHERE id=%s", (project_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "Project not found"}), 404

    cur.execute(
        "INSERT INTO tasks (project_id, title, description) VALUES (%s, %s, %s)",
        (project_id, title, description),
    )
    conn.commit()
    task_id = cur.lastrowid
    cur.close()
    conn.close()

    task_created.delay(task_id, title)
    return jsonify({"id": task_id, "title": title}), 201


@app.patch("/api/tasks/<int:task_id>/complete")
def complete_task(task_id):
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed = NOT completed WHERE id=%s", (task_id,))
    conn.commit()
    changed = cur.rowcount
    cur.close()
    conn.close()
    if not changed:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Task status updated"})


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
    conn.commit()
    changed = cur.rowcount
    cur.close()
    conn.close()
    if not changed:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Task deleted"})


@celery.task
def task_created(task_id, title):
    print(f"[WORKER] Task created: {task_id} - {title}")
    time.sleep(1)
    return {"task_id": task_id, "status": "processed"}


@app.post("/api/jobs/test")
def test_job():
    job = task_created.delay(0, "DevOpsHub test background job")
    return jsonify({"job_id": job.id, "message": "Background job queued"}), 202


if __name__ == "__main__":
    wait_for_db()
    app.run(host="0.0.0.0", port=5000)
