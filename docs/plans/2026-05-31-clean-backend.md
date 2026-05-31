# Backend Implementation Plan (Clean Architecture & DDD)

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build the foundation of a Clean Architecture backend with domain entities, infrastructure implementations (asyncpg), and a FastAPI presentation layer, managed by Poetry and protected by Ruff/Mypy.

**Architecture:** Domain-Driven Design (DDD) with strict layer separation.
**Tech Stack:** Python 3.11, Poetry, FastAPI, asyncpg, Testcontainers, Ruff, Mypy.

---

### Task 0: Tooling & Environment Setup
**Objective:** Initialize the project with Poetry and configure Ruff/Mypy.

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/ruff.toml`
- Create: `backend/mypy.ini`

**Step 1: Poetry Init**
Run: `cd backend && poetry init --no-interaction --name sweatcheck --dependency fastapi --dependency uvicorn --dependency asyncpg --dependency pydantic-settings --dev-dependency ruff --dev-dependency mypy --dev-dependency pytest --dev-dependency testcontainers --dev-dependency pytest-asyncio`

**Step 2: Configuration**
Configure Ruff for Swedish-friendly line lengths (if preferred) and Mypy for strict checking of the domain layer.

---

### Task 1: Project Structure & Basic Infrastructure
**Objective:** Set up the modular folder structure.

**Files:**
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/infrastructure/__init__.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/main.py`

---

### Task 2: Define Domain Entities & Interfaces
**Objective:** Create the core `Activity` entity and the `IActivityRepository` interface.

**Files:**
- Create: `backend/app/domain/models.py` (Activity entity)
- Create: `backend/app/domain/interfaces.py` (Repository/API interfaces)

---

### Task 3: Infrastructure - DB Implementation (Raw SQL)
**Objective:** Implement the `ActivityRepository` using `asyncpg` and raw SQL.

**Files:**
- Create: `backend/app/infrastructure/db/repository.py`
- Create: `backend/app/infrastructure/db/connection.py`

---

### Task 4: API Layer - DTOs & Routers
**Objective:** Map OpenAPI schemas to Pydantic and create a basic router.

**Files:**
- Create: `backend/app/api/schemas.py`
- Create: `backend/app/api/routers/activities.py`

---

### Task 5: Architecture & Quality Tests
**Objective:** Implement tests for layer boundaries and run linting/type-checking.

**Files:**
- Create: `backend/tests/architecture/test_layers.py`

**Commands:**
- `poetry run ruff check .`
- `poetry run mypy .`
- `poetry run pytest tests/architecture`

---

### Task 6: Integration Tests with Testcontainers
**Objective:** Set up a test suite that spins up a Postgres container.

**Files:**
- Create: `backend/tests/integration/conftest.py`
- Create: `backend/tests/integration/test_activity_api.py`
