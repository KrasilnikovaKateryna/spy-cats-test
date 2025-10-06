# SpyCats API — README

A lightweight Django + DRF service for managing **spy cats**, their **missions**, **targets**, and **notes** —with Swagger/OpenAPI docs.

---

## Prerequisites

- **Python** ≥ 3.11  
- **pip / venv** (recommended)  
- **PostgreSQL**

---

## Quick Start (Docker)

```bash
docker compose up --build
```

Now open:
- API root: http://127.0.0.1:8000/
- **Swagger UI:** http://127.0.0.1:8000/api/schema/swagger/
- **Redoc:** http://127.0.0.1:8000/api/schema/redoc/
- **Admin:** http://127.0.0.1:8000/admin/

---

### Logging all SQL queries (dev)

Already done

Add to `settings.py` (development only):

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.db.backends": {"handlers": ["console"], "level": "DEBUG"},
    },
}
```

You’ll see every query in the console.

---

## API Docs (OpenAPI / Swagger)

We use **drf-spectacular**.

**settings.py**

```python
INSTALLED_APPS += [
    "rest_framework",
    "drf_spectacular",
    "drf_spectacular_sidecar",
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SpyCats API",
    "VERSION": "1.0.0",
}
```

**urls.py**

```python
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
```

Routes:
- `/api/schema/` — OpenAPI JSON
- `/api/schema/swagger/` — Swagger UI
- `/api/schema/redoc/` — Redoc

---

## Domain Rules

- **Cat creation** validates `breed` via `GET https://api.thecatapi.com/v1/breeds` (supports `alt_names`).
  - External API down → **502**
  - Unknown breed → **400**
- **Mission completion is computed** (no DB field): `mission.is_completed` is **True** when **all** its targets have `completed=True`.
- **Create mission**: up to **3** targets in one payload.
- **Assign cat to mission**: a cat can have only **one active mission** at a time (active = mission has at least one unfinished target).
- **Complete target**: cannot complete a target if the mission is **not assigned** to a cat.
- **Notes**:
  - Each target has **at most one** note (`OneToOneField`).
  - **Create/Update note** is forbidden if the **target** or its **mission** is completed.

---

## Rate limiting

The API uses Django REST Framework throttling:

- **Authenticated users**: `240 requests/min`
- **Anonymous clients (by IP)**: `120 requests/min`

Config (in `settings.py`):
```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "240/min",
        "anon": "120/min",
    },
}
```

---

## Main Endpoints (typical routes)

> Adjust paths if your `urls.py` differs. Below reflects the common setup in this project.

### Cats
- `POST /cats/create/` — create a cat (breed validated via TheCatAPI)
  **Body:**
  ```json
  {
    "name": "Agent Whiskers",
    "years_of_experience": 4,
    "breed": "British Shorthair",
    "salary": "3500.00"
  }
  ```
- `GET /cats/` — list cats  
- `GET /cats/{id}/` — retrieve a cat  
- `PATCH /cats/{id}/` — update a cat (partial)  
- `DELETE /cats/{id}/` — delete a cat  
- `GET /cats/{id}/missions/` — list missions assigned to a specific cat

### Missions / Targets / Notes
- `POST /missions/create/` — create a mission with targets  
  **Body:**
  ```json
  {
    "cat": 1,
    "targets": [
      {"name": "Harbor Warehouse", "country": "US", "completed": false},
      {"name": "Old Bridge", "country": "UA"}
    ]
  }
  ```
- `GET /missions/` — list missions (with embedded targets & notes)  
- `GET /missions/{id}/` — retrieve a mission (with embedded targets & notes)  
- `DELETE /missions/{id}/` — delete a mission (forbidden if already assigned to a cat)  
- `PATCH /missions/{id}/assign-cat/` — assign a cat to a mission (`{"cat": 3}`)  
  *(forbidden if the cat already has an active mission)*  
- `PATCH /missions/targets/{target_id}/` — update a target (e.g., mark completed: `{"completed": true}`)  
  *(forbidden if mission isn’t assigned to a cat)*  
- `POST  /missions/targets/{target_id}/note/create/` — create note for a target  
- `PATCH /missions/targets/{target_id}/note/update/` — update note

### Missions / Targets / Notes
You can use this collection in Postman to try all endpoints:

https://.postman.co/workspace/My-Workspace~ccc776be-a122-4b31-8031-4163ce807838/collection/42850678-c4846629-9a34-4726-ba98-237bbd083976?action=share&creator=42850678&active-environment=42850678-8052c954-f114-4511-80d8-4dc739c45e65

Also you can use Swagger UI page to do the same thing.

---

## Running Tests

We use **pytest** + **pytest-django**.

**pytest.ini**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = spyCatsTest.settings
python_files = tests.py test_*.py *_tests.py
addopts = --reuse-db -q
```

**Run**
```bash
pytest                 # all tests
pytest -vv             # verbose
pytest -n auto         # parallel
```
