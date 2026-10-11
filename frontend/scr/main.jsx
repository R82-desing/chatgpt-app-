import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

function App() {
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [taskTitle, setTaskTitle] = useState("");

  async function loadProjects() {
    const res = await fetch(`${API}/projects`);
    setProjects(await res.json());
  }

  async function loadTasks(id) {
    const res = await fetch(`${API}/projects/${id}/tasks`);
    setTasks(await res.json());
  }

  async function addProject(e) {
    e.preventDefault();
    if (!projectName.trim()) return;
    await fetch(`${API}/projects`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({name: projectName, description: projectDescription})
    });
    setProjectName("");
    setProjectDescription("");
    loadProjects();
  }

  async function addTask(e) {
    e.preventDefault();
    if (!selected || !taskTitle.trim()) return;
    await fetch(`${API}/projects/${selected.id}/tasks`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({title: taskTitle})
    });
    setTaskTitle("");
    loadTasks(selected.id);
    loadProjects();
  }

  async function toggleTask(id) {
    await fetch(`${API}/tasks/${id}/complete`, {method: "PATCH"});
    loadTasks(selected.id);
    loadProjects();
  }

  async function deleteTask(id) {
    await fetch(`${API}/tasks/${id}`, {method: "DELETE"});
    loadTasks(selected.id);
    loadProjects();
  }

  async function queueJob() {
    await fetch(`${API}/jobs/test`, {method: "POST"});
    alert("Background job queued. Check worker logs.");
  }

  useEffect(() => { loadProjects(); }, []);

  return (
    <div className="app">
      <header>
        <div>
          <h1>DevOpsHub</h1>
          <p>Project & Task Management</p>
        </div>
        <button onClick={queueJob}>Test Background Job</button>
      </header>

      <main>
        <section className="panel">
          <h2>Create Project</h2>
          <form onSubmit={addProject}>
            <input placeholder="Project name" value={projectName}
              onChange={e => setProjectName(e.target.value)} />
            <textarea placeholder="Description" value={projectDescription}
              onChange={e => setProjectDescription(e.target.value)} />
            <button>Add Project</button>
          </form>

          <h2>Projects</h2>
          {projects.map(p => (
            <button
              className={`project ${selected?.id === p.id ? "active" : ""}`}
              key={p.id}
              onClick={() => { setSelected(p); loadTasks(p.id); }}
            >
              <strong>{p.name}</strong>
              <span>{p.completed_count || 0}/{p.task_count || 0} completed</span>
            </button>
          ))}
        </section>

        <section className="panel content">
          {selected ? (
            <>
              <h2>{selected.name}</h2>
              <p className="muted">{selected.description}</p>

              <form onSubmit={addTask} className="task-form">
                <input placeholder="New task" value={taskTitle}
                  onChange={e => setTaskTitle(e.target.value)} />
                <button>Add Task</button>
              </form>

              <div className="tasks">
                {tasks.map(t => (
                  <div className={`task ${t.completed ? "done" : ""}`} key={t.id}>
                    <div>
                      <strong>{t.title}</strong>
                      <small>{t.completed ? "Completed" : "Pending"}</small>
                    </div>
                    <div>
                      <button onClick={() => toggleTask(t.id)}>
                        {t.completed ? "Undo" : "Complete"}
                      </button>
                      <button onClick={() => deleteTask(t.id)}>Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty">
              <h2>Select a project</h2>
              <p>Create a project or select one from the left.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
