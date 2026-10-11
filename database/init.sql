CREATE DATABASE IF NOT EXISTS devopshub;
USE devopshub;

CREATE USER IF NOT EXISTS 'devopshub'@'%' IDENTIFIED BY 'devopshub';
GRANT ALL PRIVILEGES ON devopshub.* TO 'devopshub'@'%';
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tasks_project
        FOREIGN KEY (project_id) REFERENCES projects(id)
        ON DELETE CASCADE
);

INSERT INTO projects (name, description)
SELECT 'DevOps Practice', 'Project created by database initialization'
WHERE NOT EXISTS (
    SELECT 1 FROM projects WHERE name = 'DevOps Practice'
);
