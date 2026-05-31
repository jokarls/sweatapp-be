# Strava Integration Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Implement the connection to Strava API, including OAuth2 token management, activity retrieval, and webhook handling.

**Architecture:** Clean Architecture. Infrastructure layer implements domain interfaces. Secrets managed via environment variables.

**Tech Stack:** Python, HTTPX (async), Pydantic.

---

### Task 1: Environment & Secret Management
**Objective:** Set up configuration to handle Strava Client ID, Secret, and Redirect URI.

**Files:**
- Modify: `backend/app/core/config.py`
- Create: `backend/.env.example`

**Step 1: Define settings**
Add `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, and `STRAVA_WEBHOOK_VERIFY_TOKEN` to a Pydantic `BaseSettings` class.

---

### Task 2: Strava Infrastructure Client
**Objective:** Implement `IStravaClient` using `httpx` to fetch activity details.

**Files:**
- Create: `backend/app/infrastructure/strava/client.py`
- Test: `backend/tests/unit/infrastructure/test_strava_client.py` (Mocking HTTPX)

**Step 1: Implement `get_activity_details`**
It should take an `access_token` and `activity_id`, returning a structured dictionary (or DTO) of activity data.

---

### Task 3: Token Management Service
**Objective:** Implement a service to handle token refreshing logic.

**Files:**
- Create: `backend/app/domain/services/strava_auth.py`
- Modify: `backend/app/domain/interfaces.py` (Add token-specific methods to `IUserRepository` or a new `ITokenRepository`)

**Step 1: Implement refresh logic**
A service that checks if a token is expired, calls Strava to refresh it, and saves the new token to the DB.

---

### Task 4: Webhook Endpoint
**Objective:** Create the endpoint to receive Strava webhooks (Validation + Event processing).

**Files:**
- Create: `backend/app/api/routers/webhooks.py`
- Test: `backend/tests/integration/test_strava_webhooks.py` (Mocking the processing logic)

**Step 1: Validation handler**
Implement the GET handler that responds to Strava's challenge.

**Step 2: Event handler**
Implement the POST handler that receives `activity_id`, triggers the background task to fetch details, weather, and sends a push notification.

---

### Task 5: Background Processing Flow
**Objective:** Orchestrate the full flow: Webhook -> Fetch Strava Data -> Fetch Weather -> Create Activity in DB -> Send Push.

**Files:**
- Create: `backend/app/domain/services/activity_sync.py`
- Modify: `backend/app/main.py` (Register webhook router)

---

### Task 6: Verification with Mocked Integration Tests
**Objective:** Ensure the full flow works from webhook to DB using Testcontainers and Mocks for external APIs.
