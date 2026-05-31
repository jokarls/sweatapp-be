# Flutter Frontend Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build the SweatCheck mobile application using Flutter, consuming the backend API.

**Architecture:** Cleanish structure with a focus on Bloc/Provider for state management and an auto-generated API client.

**Tech Stack:** Flutter, Dart, Dio, OpenAPI Generator.

---

### Task 1: Initialize Flutter Project
**Objective:** Create the base Flutter project and configure `pubspec.yaml`.

**Files:**
- Create: `mobile/pubspec.yaml`
- Setup: Base directory structure (`lib/api`, `lib/blocs`, `lib/models`, `lib/screens`).

---

### Task 2: API Client Generation
**Objective:** Use `openapi-generator` to generate the Dart client from `openapi.yaml`.

**Dependencies:** `dio`, `openapi_generator_annotations`.
**Dev Dependencies:** `build_runner`, `openapi_generator`.

---

### Task 3: Theme & Navigation
**Objective:** Setup a dark theme (matching the sweat/sporty vibe) and define GoRouter/Navigator routes.

---

### Task 4: Activity List Screen
**Objective:** Fetch and display a list of recent activities from the backend.

---

### Task 5: Sweat Input Screen
**Objective:** Form to input weight before/after and other manual data, triggering the PATCH update.

---

### Task 6: Stats & Profile Screen
**Objective:** Visualize sweat stats and user profile settings.
