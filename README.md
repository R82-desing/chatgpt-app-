# DevOpsHub

Multi-service Project & Task Management application for DevOps practice.

Services used by the application:
- React frontend
- Flask REST API
- MySQL database
- Redis
- Celery background worker

Intentionally NOT included:
- Dockerfile
- docker-compose.yml
- Kubernetes manifests
- CI/CD files

Those are the DevOps exercise.

Backend environment variables:
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, REDIS_HOST, REDIS_PORT

API:
GET /api/health
GET /api/projects
POST /api/projects
GET /api/projects/<id>/tasks
POST /api/projects/<id>/tasks
PATCH /api/tasks/<id>/complete
DELETE /api/tasks/<id>
POST /api/jobs/test
