# Backend Skeleton Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Create a functional FastAPI backend skeleton with Docker support, Pydantic models derived from OpenAPI, and async PostgreSQL connectivity.

**Architecture:** Modular FastAPI structure using asyncpg for raw SQL.

**Tech Stack:** Python 3.11+, FastAPI, Docker, asyncpg, Pydantic.

---

### Task 1: Initialize backend directory and requirements
**Objective:** Set up the basic folder structure and define dependencies.

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`

**Step 1: Create requirements.txt**
```text
fastapi==0.104.1
uvicorn[standard]==0.24.0.post1
asyncpg==0.29.0
pydantic==2.5.2
pydantic-settings==2.1.0
python-multipart==0.0.6
```

**Step 2: Create a minimal main.py**
```python
from fastapi import FastAPI

app = FastAPI(title="SweatCheck API")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 3: Verify**
Run: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
Expected: Server starts on localhost:8000, `/health` returns healthy.

---

### Task 2: Dockerize the backend
**Objective:** Create a Dockerfile to run the FastAPI app in a container.

**Files:**
- Create: `backend/Dockerfile`
- Create: `docker-compose.yml` (in project root)

**Step 1: Create Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Create docker-compose.yml**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/backend
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/sweatcheck
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=sweatcheck
    ports:
      - "5432:5432"
```

**Step 3: Verify**
Run: `docker-compose up --build -d`
Expected: Both containers start, `curl localhost:8000/health` works.

---

### Task 3: Implement Database Connection Utility
**Objective:** Create an asyncpg connection pool manager.

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/session.py`

**Step 1: Add Database session management**
Include logic to create a pool on startup and close it on shutdown in `main.py`.

---

### Task 4: Define Pydantic Models (from OpenAPI)
**Objective:** Create models in `app/models/` matching the `openapi.yaml` schemas.

**Files:**
- Create: `backend/app/models/activity.py`
- Create: `backend/app/models/user.py`

---

### Task 5: Implement Activity Router (Stub)
**Objective:** Create the endpoints defined in OpenAPI with stubbed responses.

**Files:**
- Create: `backend/app/api/endpoints/activity.py`
- Modify: `backend/app/main.py` to include the router.
