# Flask To-Do Application - Enhanced with API & Tagging

This project upgrades a basic Flask To-Do app into a more robust and extensible application.

## Key Enhancements:

1.  **Comprehensive RESTful API**:
    * Full CRUD operations for To-Do items (`/api/v1/todos`) and Tags (`/api/v1/tags`).
    * Uses standard REST principles (HTTP methods, JSON format, proper status codes).
    * Enables programmatic access for integration with other applications (e.g., mobile apps).

2.  **Tag Management System**:
    * Implemented a many-to-many relationship for flexible task categorization.
    * Allows multiple tags per To-Do, with dynamic creation and filtering by tag.

3.  **Enhanced Web UI**:
    * Integrated tag input and display into the web interface.
    * Added tag filtering and a new "Edit Details" modal for streamlined updates.

## Technical Highlights:

* **Models**: SQLAlchemy models for `Todo` and `Tag` with an association table.
* **API Design**: Modularized with Flask Blueprints.
* **Validation**: Robust input validation for API and web forms.
* **Testing**: Extensive unit tests using `pytest` and `pytest-cov`, achieving **100% test coverage** on `app.py`'s functional code. Includes comprehensive positive and negative test cases for all CRUD operations.

## Setup & Running:

1.  **Clone**: `git clone https://github.com/JmRILKayn/flask-todo.git` (Use this URL for your fork or your professor's if your changes are merged to `main`)
    * `cd flask-todo`
2.  **Env**: `python -m venv venv` & `venv\Scripts\activate` (on Windows) or `source venv/bin/activate` (on Unix/macOS)
3.  **Install**: `pip install Flask Flask-SQLAlchemy pytest pytest-flask pytest-cov`
4.  **Run App**: `python app.py` (access at `http://127.0.0.1:5000/`)
    * Initialize Database (first run or after cleaning `db.sqlite`):
        `python -c "from app import db, app; with app.app_context(): db.create_all(); print('Database initialized.')"`
5.  **Run Tests**: `pytest --cov=app --cov-report=term-missing` (should show 100% coverage)

---

## Technical Requirements Fulfilled:

This project specifically addresses the following technical requirements:

### 1. API Design:
* **RESTful Principles:** Utilizes proper resource naming (`/api/v1/todos`, `/api/v1/tags`) and appropriate HTTP methods (GET, POST, PUT/PATCH, DELETE) for resource interaction.
* **JSON Format:** Implements JSON for both request and response payloads across all API endpoints.
* **Status Codes:** Includes proper HTTP status codes (e.g., `200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`, `204 No Content`) for clear API communication.
* **API Documentation:** Comprehensive API documentation is provided within this `README.md` file (in the "Key Enhancements" section and implicitly throughout the documentation of API endpoints).

### 2. Submission:
* **Original Repository:** (URL will be provided in final submission/presentation)
* **Cloned GitHub Repository with Changes:** (URL to your fork/branch will be provided in final submission/presentation)
* **README.md:** This document itself explains all changes and project details.
* **Video Presentation:** (Direct link to YouTube/Google-video MP4 file will be provided in final submission/presentation)

---

## Repository Links

- Original Repository: `https://github.com/patrickloeber/flask-todo.git`
- Forked with Enhancements: `https://github.com/JmRILKayn/flask-todo/tree/feature/api-tags-enhancements`